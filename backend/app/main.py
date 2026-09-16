import os
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, date
from fastapi import FastAPI, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from .database import Base, engine, get_db, SessionLocal
from . import models, schemas
from .auth import verify_password, create_token, current_user, pwd_context
from .services.pdf_service import generar_boleta_simple_pdf, generar_boleta_detallada_pdf, generar_record_academico_pdf
from .services.scheduler_service import scheduler_worker_loop
from .routers import backups

Base.metadata.create_all(bind=engine)

# Garantizar columnas de descripción para copias de seguridad y restauraciones
try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE backup_files ADD COLUMN IF NOT EXISTS description VARCHAR(255);"))
        conn.execute(text("ALTER TABLE restore_history ADD COLUMN IF NOT EXISTS description VARCHAR(255);"))
        conn.commit()
except Exception as e:
    print(f"[DB-MIGRATION] Aviso al verificar columnas de backup: {e}")

# Crea o sincroniza usuarios iniciales (Administrador y Estudiante)
try:
    with SessionLocal() as db:
        # 1. Administrador
        admin = db.query(models.Usuario).filter(models.Usuario.correo == "admin@portal.edu.pe").first()
        if not admin:
            db.add(models.Usuario(
                nombre="Administrador",
                correo="admin@portal.edu.pe",
                password_hash=pwd_context.hash("Admin123*"),
                rol="ADMIN",
                activo=True
            ))
        else:
            admin.password_hash = pwd_context.hash("Admin123*")
            admin.activo = True

        # 2. Estudiante Carlos Quispe
        carlos = db.query(models.Usuario).filter(models.Usuario.correo == "carlos@portal.edu.pe").first()
        if not carlos:
            carlos = models.Usuario(
                nombre="Carlos Alexander Quispe Espino",
                correo="carlos@portal.edu.pe",
                password_hash=pwd_context.hash("Estudiante123*"),
                rol="ESTUDIANTE",
                activo=True
            )
            db.add(carlos)
            db.flush()
        else:
            carlos.password_hash = pwd_context.hash("Estudiante123*")
            carlos.rol = "ESTUDIANTE"
            carlos.activo = True
            db.flush()

        # 3. Perfil del estudiante Carlos
        est = db.query(models.Estudiante).filter(
            (models.Estudiante.usuario_id == carlos.id) | (models.Estudiante.correo == "carlos@portal.edu.pe")
        ).first()
        if not est:
            db.add(models.Estudiante(
                codigo="2026001",
                nombres="CARLOS ALEXANDER",
                apellidos="QUISPE ESPINO",
                dni="76543210",
                correo="carlos@portal.edu.pe",
                carrera="INGENIERÍA DE SISTEMAS DE INFORMACIÓN",
                ciclo=7,
                fecha_ingreso=date(2023, 3, 15),
                estado="ACTIVO",
                usuario_id=carlos.id
            ))
        else:
            est.usuario_id = carlos.id
            est.correo = "carlos@portal.edu.pe"

        db.commit()
except Exception as e:
    print(f"[INIT-AUTH] Aviso al inicializar usuarios demo: {e}")

# Ejecutar migración y seed académico inicial si no existen matrículas
try:
    with engine.connect() as conn:
        has_academic_data = False
        try:
            res = conn.execute(text("SELECT COUNT(*) FROM matriculas")).scalar()
            has_academic_data = (res is not None and res > 0)
        except Exception:
            has_academic_data = False

        if not has_academic_data:
            print("[AUTO-SEED] Matrículas vacías detectadas. Iniciando seed académico...")
            candidates = [
                Path(__file__).resolve().parent.parent.parent / "database" / "run_migration_and_seed.py",
                Path("/app/database/run_migration_and_seed.py"),
                Path("database/run_migration_and_seed.py")
            ]
            seed_script = next((p for p in candidates if p.exists()), None)
            if seed_script:
                import importlib.util
                spec = importlib.util.spec_from_file_location("auto_seed_module", str(seed_script))
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    if hasattr(mod, "run_migration_and_seed"):
                        mod.run_migration_and_seed()
                        print("[AUTO-SEED] Migración y seed completados exitosamente.")
except Exception as e:
    print(f"[AUTO-SEED] Aviso durante verificación/seed académico: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicia el worker del scheduler de backups con bloqueo consultivo anti-colisión
    scheduler_task = asyncio.create_task(scheduler_worker_loop())
    yield
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="Portal Académico API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

# Incluir router del Módulo de Copias de Seguridad
app.include_router(backups.router)

# ==================== HELPERS ====================

def get_current_estudiante(user: models.Usuario = Depends(current_user), db: Session = Depends(get_db)) -> models.Estudiante:
    est = db.query(models.Estudiante).filter(
        (models.Estudiante.usuario_id == user.id) | (models.Estudiante.correo == user.correo)
    ).first()
    if not est:
        raise HTTPException(status_code=403, detail="El usuario autenticado no tiene un perfil de estudiante asociado")
    return est

def get_matricula_grades_summary(matricula: models.Matricula, db: Session) -> dict:
    evaluaciones = []
    # Obtener evaluaciones de la sección
    if matricula.seccion_id:
        evaluaciones = db.query(models.Evaluacion).filter(
            models.Evaluacion.seccion_id == matricula.seccion_id
        ).order_by(models.Evaluacion.orden).all()
    elif matricula.curso_id:
        # Fallback a evaluaciones de alguna sección del curso
        sec = db.query(models.Seccion).filter(models.Seccion.curso_id == matricula.curso_id).first()
        if sec:
            evaluaciones = db.query(models.Evaluacion).filter(
                models.Evaluacion.seccion_id == sec.id
            ).order_by(models.Evaluacion.orden).all()

    # Obtener notas asignadas a esta matrícula
    notas_map = {}
    notas_db = db.query(models.Nota).filter(models.Nota.matricula_id == matricula.id).all()
    for n in notas_db:
        notas_map[n.evaluacion_id] = float(n.valor) if n.valor is not None else None

    eval_detalles = []
    weighted_sum = 0.0
    weights_graded = 0.0
    total_weights = 0.0
    all_graded = len(evaluaciones) > 0

    for ev in evaluaciones:
        peso_float = float(ev.peso)
        total_weights += peso_float
        nota_val = notas_map.get(ev.id)
        is_graded = nota_val is not None
        if is_graded:
            weighted_sum += nota_val * (peso_float / 100.0)
            weights_graded += peso_float
        else:
            all_graded = False

        eval_detalles.append(schemas.EvaluacionDetalleOut(
            evaluacion_id=ev.id,
            evaluacion=ev.nombre,
            tipo=ev.tipo.codigo if ev.tipo else "EV",
            peso=peso_float,
            nota=nota_val,
            estado="CALIFICADO" if is_graded else "PENDIENTE"
        ))

    promedio_actual = None
    if weights_graded > 0:
        # Promedio ponderado normalizado a la proporción calificada
        promedio_actual = round(weighted_sum / (weights_graded / 100.0), 2)

    promedio_final = None
    if all_graded and total_weights > 0:
        promedio_final = round(weighted_sum, 2)
        estado_curso = "APROBADO" if promedio_final >= 10.5 else "DESAPROBADO"
    else:
        if promedio_actual is not None:
            estado_curso = "APROBADO" if promedio_actual >= 10.5 else "EN CURSO"
        else:
            estado_curso = "EN CURSO"

    return {
        "evaluaciones": eval_detalles,
        "promedio_actual": promedio_actual,
        "promedio_final": promedio_final if promedio_final is not None else promedio_actual,
        "estado_curso": estado_curso
    }

# ==================== AUTH & PROFILE ====================

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/auth/login", response_model=schemas.TokenOut)
def login(data: schemas.LoginIn, db: Session = Depends(get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.correo == data.correo).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Credenciales incorrectas")
    return {
        "access_token": create_token({"sub": str(user.id), "rol": user.rol}),
        "nombre": user.nombre,
        "rol": user.rol
    }

@app.post("/api/auth/change-password")
def change_password(
    data: schemas.ChangePasswordIn,
    user: models.Usuario = Depends(current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(data.password_actual, user.password_hash):
        raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta")
    if len(data.password_nueva) < 6:
        raise HTTPException(status_code=400, detail="La nueva contraseña debe tener al menos 6 caracteres")
    user.password_hash = pwd_context.hash(data.password_nueva)
    db.commit()
    return {"ok": True, "message": "Contraseña actualizada exitosamente"}

@app.get("/api/estudiante/me", response_model=schemas.EstudianteMeOut)
def estudiante_me(
    est: models.Estudiante = Depends(get_current_estudiante),
    user: models.Usuario = Depends(current_user)
):
    return schemas.EstudianteMeOut(
        id=est.id,
        codigo=est.codigo,
        nombres=est.nombres,
        apellidos=est.apellidos,
        nombre_completo=f"{est.apellidos}, {est.nombres}",
        carrera=est.carrera,
        ciclo=est.ciclo,
        correo=est.correo,
        dni=est.dni
    )

@app.get("/api/periodos", response_model=list[schemas.PeriodoOut])
def listar_periodos(db: Session = Depends(get_db), _=Depends(current_user)):
    return db.query(models.Periodo).order_by(models.Periodo.activo.desc(), models.Periodo.id.desc()).all()

# ==================== ESTUDIANTE: NOTAS DEL PERIODO ====================

@app.get("/api/estudiante/me/matriculas", response_model=list[schemas.CursoMatriculadoOut])
def listar_matriculas_estudiante(
    periodo_id: int | None = None,
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    query = db.query(models.Matricula).filter(models.Matricula.estudiante_id == est.id)

    if periodo_id:
        query = query.filter(
            (models.Matricula.periodo_id == periodo_id) |
            (models.Matricula.periodo == db.query(models.Periodo.codigo).filter(models.Periodo.id == periodo_id).scalar_subquery())
        )
    else:
        # Por defecto, seleccionar el periodo activo
        p_act = db.query(models.Periodo).filter(models.Periodo.activo == True).first()
        if p_act:
            query = query.filter(
                (models.Matricula.periodo_id == p_act.id) | (models.Matricula.periodo == p_act.codigo)
            )

    matriculas = query.order_by(models.Matricula.id.asc()).all()

    resultado = []
    for m in matriculas:
        c = m.curso
        secc_codigo = m.seccion.codigo if m.seccion else "SECC-01"
        docente_nombre = m.seccion.docente.nombres + " " + m.seccion.docente.apellidos if (m.seccion and m.seccion.docente) else c.docente
        tiene_silabo = bool(c.silabo and Path(c.silabo.ruta_archivo).exists())
        
        resultado.append(schemas.CursoMatriculadoOut(
            matricula_id=m.id,
            curso_id=c.id,
            codigo=c.codigo,
            curso=c.nombre,
            creditos=c.creditos,
            seccion=secc_codigo,
            docente=docente_nombre,
            estado=m.estado if m.estado else "M",
            tiene_silabo=tiene_silabo
        ))

    return resultado

@app.get("/api/matriculas/{matricula_id}/notas", response_model=schemas.NotasCursoOut)
def ver_notas_matricula(
    matricula_id: int,
    user: models.Usuario = Depends(current_user),
    db: Session = Depends(get_db)
):
    m = db.get(models.Matricula, matricula_id)
    if not m:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada")

    # Validación de propiedad: sólo el estudiante dueño o un admin puede ver las notas
    if user.rol != "ADMIN":
        est = get_current_estudiante(user, db)
        if m.estudiante_id != est.id:
            raise HTTPException(status_code=403, detail="No tiene autorización para consultar las notas de esta matrícula")

    c = m.curso
    secc_codigo = m.seccion.codigo if m.seccion else "SECC-01"
    docente_nombre = m.seccion.docente.nombres + " " + m.seccion.docente.apellidos if (m.seccion and m.seccion.docente) else c.docente

    summary = get_matricula_grades_summary(m, db)

    return schemas.NotasCursoOut(
        matricula_id=m.id,
        curso=c.nombre,
        codigo=c.codigo,
        docente=docente_nombre,
        periodo=m.periodo,
        seccion=secc_codigo,
        evaluaciones=summary["evaluaciones"],
        promedio_actual=summary["promedio_actual"],
        promedio_final=summary["promedio_final"],
        estado_curso=summary["estado_curso"]
    )

@app.get("/api/matriculas/{matricula_id}/silabo")
def ver_silabo_matricula(
    matricula_id: int,
    user: models.Usuario = Depends(current_user),
    db: Session = Depends(get_db)
):
    m = db.get(models.Matricula, matricula_id)
    if not m:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada")

    # Validación de propiedad
    if user.rol != "ADMIN":
        est = get_current_estudiante(user, db)
        if m.estudiante_id != est.id:
            raise HTTPException(status_code=403, detail="No tiene autorización para acceder al sílabo de esta matrícula")

    c = m.curso
    silabo = c.silabo
    if not silabo or not silabo.ruta_archivo or not Path(silabo.ruta_archivo).exists():
        raise HTTPException(status_code=404, detail="Sílabo no disponible.")

    return FileResponse(
        path=silabo.ruta_archivo,
        media_type="application/pdf",
        filename=silabo.nombre_archivo,
        headers={"Content-Disposition": f'inline; filename="{silabo.nombre_archivo}"'}
    )

@app.get("/api/estudiante/me/boleta")
def descargar_boleta_simple(
    periodo_id: int | None = None,
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    # Buscar el periodo
    if periodo_id:
        p = db.get(models.Periodo, periodo_id)
    else:
        p = db.query(models.Periodo).filter(models.Periodo.activo == True).first()

    periodo_cod = p.codigo if p else "2026 II-B"

    # Obtener matrículas del estudiante en ese periodo
    matriculas = db.query(models.Matricula).filter(
        models.Matricula.estudiante_id == est.id,
        (models.Matricula.periodo_id == p.id if p else True) | (models.Matricula.periodo == periodo_cod)
    ).all()

    cursos_info = []
    total_creditos = 0
    suma_ponderada = 0.0
    creditos_con_nota = 0

    for m in matriculas:
        c = m.curso
        summary = get_matricula_grades_summary(m, db)
        prom = summary["promedio_final"] or summary["promedio_actual"]
        cred = c.creditos
        total_creditos += cred

        if prom is not None:
            suma_ponderada += prom * cred
            creditos_con_nota += cred

        cursos_info.append({
            "codigo": c.codigo,
            "curso": c.nombre,
            "seccion": m.seccion.codigo if m.seccion else "SECC-01",
            "creditos": cred,
            "promedio": prom,
            "estado_curso": summary["estado_curso"]
        })

    promedio_ponderado = round(suma_ponderada / creditos_con_nota, 2) if creditos_con_nota > 0 else 0.0

    estudiante_dict = {
        "nombre_completo": f"{est.apellidos}, {est.nombres}",
        "codigo": est.codigo,
        "carrera": est.carrera,
        "dni": est.dni,
        "ciclo": est.ciclo
    }

    pdf_bytes = generar_boleta_simple_pdf(estudiante_dict, periodo_cod, cursos_info, promedio_ponderado, total_creditos)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="Boleta_Notas_{est.codigo}_{periodo_cod}.pdf"'}
    )

@app.get("/api/estudiante/me/boleta-detallada")
def descargar_boleta_detallada(
    periodo_id: int | None = None,
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    if periodo_id:
        p = db.get(models.Periodo, periodo_id)
    else:
        p = db.query(models.Periodo).filter(models.Periodo.activo == True).first()

    periodo_cod = p.codigo if p else "2026 II-B"

    matriculas = db.query(models.Matricula).filter(
        models.Matricula.estudiante_id == est.id,
        (models.Matricula.periodo_id == p.id if p else True) | (models.Matricula.periodo == periodo_cod)
    ).all()

    cursos_detallados = []
    total_creditos = 0
    suma_ponderada = 0.0
    creditos_con_nota = 0

    for m in matriculas:
        c = m.curso
        summary = get_matricula_grades_summary(m, db)
        prom = summary["promedio_final"] or summary["promedio_actual"]
        cred = c.creditos
        total_creditos += cred

        if prom is not None:
            suma_ponderada += prom * cred
            creditos_con_nota += cred

        docente_nombre = m.seccion.docente.nombres + " " + m.seccion.docente.apellidos if (m.seccion and m.seccion.docente) else c.docente

        cursos_detallados.append({
            "codigo": c.codigo,
            "curso": c.nombre,
            "seccion": m.seccion.codigo if m.seccion else "SECC-01",
            "docente": docente_nombre,
            "creditos": cred,
            "evaluaciones": [ev.model_dump() for ev in summary["evaluaciones"]],
            "promedio_actual": prom,
            "estado_curso": summary["estado_curso"]
        })

    promedio_ponderado = round(suma_ponderada / creditos_con_nota, 2) if creditos_con_nota > 0 else 0.0

    estudiante_dict = {
        "nombre_completo": f"{est.apellidos}, {est.nombres}",
        "codigo": est.codigo,
        "carrera": est.carrera,
        "dni": est.dni,
        "ciclo": est.ciclo
    }

    pdf_bytes = generar_boleta_detallada_pdf(estudiante_dict, periodo_cod, cursos_detallados, promedio_ponderado, total_creditos)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="Boleta_Detallada_{est.codigo}_{periodo_cod}.pdf"'}
    )

# ==================== ESTUDIANTE: MÓDULOS INTEGRALES ====================

@app.get("/api/estudiante/dashboard")
def estudiante_dashboard(
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    # 1. Matrículas activas
    matriculas = db.query(models.Matricula).filter(
        models.Matricula.estudiante_id == est.id,
        models.Matricula.periodo == "2026 II-B"
    ).all()

    # 2. Promedio actual del ciclo
    suma_pond = 0.0
    cred_total = 0
    cursos_actuales = []
    ultimas_notas = []
    proximas_evals = []

    for m in matriculas:
        c = m.curso
        summary = get_matricula_grades_summary(m, db)
        prom = summary["promedio_final"] or summary["promedio_actual"]
        cred = c.creditos
        cred_total += cred
        if prom is not None:
            suma_pond += prom * cred

        cursos_actuales.append({
            "matricula_id": m.id,
            "codigo": c.codigo,
            "curso": c.nombre,
            "creditos": cred,
            "seccion": m.seccion.codigo if m.seccion else "SECC-01",
            "docente": m.seccion.docente.nombres + " " + m.seccion.docente.apellidos if (m.seccion and m.seccion.docente) else c.docente,
            "promedio": prom,
            "estado": summary["estado_curso"]
        })

        for ev in summary["evaluaciones"]:
            if ev.nota is not None:
                ultimas_notas.append({
                    "curso": c.nombre,
                    "evaluacion": ev.evaluacion,
                    "tipo": ev.tipo,
                    "peso": ev.peso,
                    "nota": ev.nota,
                    "fecha": "10/09/2026"
                })
            else:
                proximas_evals.append({
                    "curso": c.nombre,
                    "evaluacion": ev.evaluacion,
                    "tipo": ev.tipo,
                    "peso": ev.peso,
                    "fecha": "25/09/2026",
                    "estado": "PROGRAMADO"
                })

    promedio_ciclo = round(suma_pond / cred_total, 2) if cred_total > 0 else 0.0

    # 3. Asistencias generales
    m_ids = [m.id for m in matriculas]
    total_asis = db.query(models.Asistencia).filter(models.Asistencia.matricula_id.in_(m_ids)).count() if m_ids else 0
    presentes = db.query(models.Asistencia).filter(
        models.Asistencia.matricula_id.in_(m_ids),
        models.Asistencia.estado.in_(["PRESENTE", "JUSTIFICADO"])
    ).count() if m_ids else 0
    pct_asistencia = round((presentes / total_asis) * 100, 1) if total_asis > 0 else 94.0

    # 4. Trámites pendientes
    tramites_pendientes = db.query(models.Tramite).filter(
        models.Tramite.estudiante_id == est.id,
        models.Tramite.estado.in_(["PENDIENTE", "EN REVISION"])
    ).count()

    # 5. Pagos pendientes
    pagos_pend = db.query(models.Pago).filter(
        models.Pago.estudiante_id == est.id,
        models.Pago.estado == "PENDIENTE"
    ).all()
    monto_pendiente = sum(float(p.monto) for p in pagos_pend)

    # 6. Avisos
    avisos = db.query(models.AvisoAcademico).order_by(models.AvisoAcademico.fecha.desc()).limit(5).all()

    return {
        "estudiante": {
            "nombre_completo": f"{est.apellidos}, {est.nombres}",
            "codigo": est.codigo,
            "carrera": est.carrera,
            "ciclo": est.ciclo
        },
        "resumen": {
            "cursos_matriculados": len(matriculas),
            "creditos_totales": cred_total,
            "promedio_ciclo": promedio_ciclo,
            "porcentaje_asistencia": pct_asistencia,
            "tramites_pendientes": tramites_pendientes,
            "pagos_pendientes": monto_pendiente
        },
        "proximas_evaluaciones": proximas_evals[:4],
        "ultimas_notas": ultimas_notas[-5:],
        "avisos": [{"id": a.id, "titulo": a.titulo, "contenido": a.contenido, "fecha": str(a.fecha), "tipo": a.tipo} for a in avisos],
        "cursos_actuales": cursos_actuales
    }

@app.get("/api/estudiante/perfil", response_model=schemas.EstudianteMeOut)
def estudiante_perfil_get(
    est: models.Estudiante = Depends(get_current_estudiante)
):
    return schemas.EstudianteMeOut(
        id=est.id,
        codigo=est.codigo,
        nombres=est.nombres,
        apellidos=est.apellidos,
        nombre_completo=f"{est.apellidos}, {est.nombres}",
        carrera=est.carrera,
        ciclo=est.ciclo,
        correo=est.correo,
        dni=est.dni,
        telefono=est.telefono or "987654321",
        direccion=est.direccion or "Av. Universitaria 1450, Lima",
        estado=est.estado
    )

@app.put("/api/estudiante/perfil")
def estudiante_perfil_update(
    data: schemas.PerfilUpdateIn,
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    if data.telefono is not None:
        est.telefono = data.telefono
    if data.direccion is not None:
        est.direccion = data.direccion
    db.commit()
    return {"ok": True, "message": "Datos de contacto actualizados correctamente"}

@app.get("/api/estudiante/matricula/detalle")
def estudiante_matricula_detalle(
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    matriculas = db.query(models.Matricula).filter(
        models.Matricula.estudiante_id == est.id,
        models.Matricula.periodo == "2026 II-B"
    ).all()

    cursos_res = []
    total_cred = 0
    for m in matriculas:
        c = m.curso
        total_cred += c.creditos
        horario_str = "Lunes 08:00 - 10:15"
        aula_str = "Aula B-201"
        if m.seccion and m.seccion.horarios:
            h = m.seccion.horarios[0]
            horario_str = f"{h.dia} {h.hora_inicio} - {h.hora_fin}"
            aula_str = h.aula

        docente_nombre = m.seccion.docente.nombres + " " + m.seccion.docente.apellidos if (m.seccion and m.seccion.docente) else c.docente

        cursos_res.append({
            "matricula_id": m.id,
            "curso_id": c.id,
            "codigo": c.codigo,
            "curso": c.nombre,
            "creditos": c.creditos,
            "seccion": m.seccion.codigo if m.seccion else "SECC-01",
            "docente": docente_nombre,
            "horario": horario_str,
            "aula": aula_str,
            "modalidad": "PRESENCIAL",
            "estado": m.estado if m.estado else "MATRICULADO",
            "tiene_silabo": bool(c.silabo)
        })

    return {
        "periodo": "2026 II-B",
        "creditos_matriculados": total_cred,
        "estado_matricula": "MATRICULADO REGULAR",
        "fecha_matricula": "15/08/2026",
        "cursos": cursos_res
    }

@app.get("/api/estudiante/horario")
def estudiante_horario_get(
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    matriculas = db.query(models.Matricula).filter(
        models.Matricula.estudiante_id == est.id,
        models.Matricula.periodo == "2026 II-B"
    ).all()

    dias_orden = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    dias_map = {d: [] for d in dias_orden[:6]}
    todas_clases = []

    for m in matriculas:
        c = m.curso
        docente_nombre = m.seccion.docente.nombres + " " + m.seccion.docente.apellidos if (m.seccion and m.seccion.docente) else c.docente
        secc_codigo = m.seccion.codigo if m.seccion else "SECC-01"

        if m.seccion and m.seccion.horarios:
            for h in m.seccion.horarios:
                item = {
                    "dia": h.dia,
                    "hora_inicio": h.hora_inicio,
                    "hora_fin": h.hora_fin,
                    "curso": c.nombre,
                    "codigo": c.codigo,
                    "seccion": secc_codigo,
                    "docente": docente_nombre,
                    "aula": h.aula,
                    "modalidad": h.modalidad
                }
                todas_clases.append(item)
                if h.dia in dias_map:
                    dias_map[h.dia].append(item)
        else:
            # Asignar un horario referencial
            item = {
                "dia": "Lunes",
                "hora_inicio": "08:00",
                "hora_fin": "10:15",
                "curso": c.nombre,
                "codigo": c.codigo,
                "seccion": secc_codigo,
                "docente": docente_nombre,
                "aula": "Aula B-201",
                "modalidad": "PRESENCIAL"
            }
            todas_clases.append(item)
            dias_map["Lunes"].append(item)

    # Ordenar clases por hora de inicio
    todas_clases.sort(key=lambda x: (dias_orden.index(x["dia"]) if x["dia"] in dias_orden else 99, x["hora_inicio"]))
    for d in dias_map:
        dias_map[d].sort(key=lambda x: x["hora_inicio"])

    return {
        "periodo": "2026 II-B",
        "carrera": est.carrera,
        "clases": todas_clases,
        "por_dia": dias_map
    }

@app.get("/api/estudiante/record-academico")
def estudiante_record_academico(
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    matriculas = db.query(models.Matricula).filter(models.Matricula.estudiante_id == est.id).order_by(models.Matricula.id.asc()).all()
    cursos_record = []
    total_creditos = 0
    creditos_aprobados = 0
    suma_ponderada = 0.0

    for m in matriculas:
        c = m.curso
        summary = get_matricula_grades_summary(m, db)
        prom = summary["promedio_final"] or summary["promedio_actual"]
        cred = c.creditos
        total_creditos += cred

        if prom is not None and prom >= 10.5:
            creditos_aprobados += cred
            suma_ponderada += prom * cred

        docente_nombre = m.seccion.docente.nombres + " " + m.seccion.docente.apellidos if (m.seccion and m.seccion.docente) else c.docente
        cursos_record.append({
            "codigo": c.codigo,
            "curso": c.nombre,
            "docente": docente_nombre,
            "seccion": m.seccion.codigo if m.seccion else "SECC-01",
            "periodo": m.periodo,
            "creditos": cred,
            "promedio": prom,
            "estado": summary["estado_curso"]
        })

    prom_acumulado = round(suma_ponderada / creditos_aprobados, 2) if creditos_aprobados > 0 else 0.0
    cursos_aprob_cnt = sum(1 for cr in cursos_record if (cr["promedio"] is not None and cr["promedio"] >= 10.5) or cr["estado"] == "APROBADO")
    cursos_desap_cnt = sum(1 for cr in cursos_record if (cr["promedio"] is not None and cr["promedio"] < 10.5 and cr["estado"] != "EN CURSO"))

    return {
        "estudiante": f"{est.apellidos}, {est.nombres}",
        "codigo": est.codigo,
        "carrera": est.carrera,
        "ciclo": est.ciclo,
        "total_cursos": len(cursos_record),
        "cursos_aprobados": cursos_aprob_cnt,
        "cursos_desaprobados": cursos_desap_cnt,
        "total_creditos": total_creditos,
        "creditos_aprobados": creditos_aprobados,
        "creditos_pendientes": max(0, 210 - creditos_aprobados),
        "promedio_acumulado": prom_acumulado,
        "cursos": cursos_record
    }

@app.get("/api/estudiante/record-academico/pdf")
def estudiante_record_pdf(
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    record_data = estudiante_record_academico(est, db)
    est_data = {
        "nombre_completo": f"{est.apellidos}, {est.nombres}",
        "codigo": est.codigo,
        "carrera": est.carrera,
        "dni": est.dni,
        "ciclo": est.ciclo
    }
    pdf_bytes = generar_record_academico_pdf(est_data, record_data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="Record_Academico_{est.codigo}.pdf"'}
    )

@app.get("/api/estudiante/avance-curricular")
def estudiante_avance_curricular(
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    matriculas = db.query(models.Matricula).filter(models.Matricula.estudiante_id == est.id).all()
    cursos_matriculados_ids = {m.curso_id for m in matriculas}

    # Malla Curricular oficial de 10 ciclos para Ingeniería de Sistemas de Información
    malla_base = [
        # Ciclo 1
        {"ciclo": 1, "codigo": "MAT-101", "nombre": "CÁLCULO I", "creditos": 4, "prereq": "Ninguno"},
        {"ciclo": 1, "codigo": "FIS-101", "nombre": "FÍSICA GENERAL", "creditos": 4, "prereq": "Ninguno"},
        {"ciclo": 1, "codigo": "PRO-101", "nombre": "FUNDAMENTOS DE PROGRAMACIÓN", "creditos": 4, "prereq": "Ninguno"},
        {"ciclo": 1, "codigo": "HUM-101", "nombre": "COMUNICACIÓN EFECTIVA", "creditos": 3, "prereq": "Ninguno"},
        # Ciclo 2
        {"ciclo": 2, "codigo": "MAT-201", "nombre": "CÁLCULO II", "creditos": 4, "prereq": "MAT-101"},
        {"ciclo": 2, "codigo": "PRO-201", "nombre": "PROGRAMACIÓN ORIENTADA A OBJETOS", "creditos": 4, "prereq": "PRO-101"},
        {"ciclo": 2, "codigo": "EST-201", "nombre": "ESTADÍSTICA Y PROBABILIDADES", "creditos": 4, "prereq": "MAT-101"},
        {"ciclo": 2, "codigo": "DIS-201", "nombre": "MATEMÁTICA DISCRETA", "creditos": 3, "prereq": "Ninguno"},
        # Ciclo 3
        {"ciclo": 3, "codigo": "EST-301", "nombre": "ESTRUCTURA DE DATOS Y ALGORITMOS", "creditos": 4, "prereq": "PRO-201"},
        {"ciclo": 3, "codigo": "ARQ-301", "nombre": "ARQUITECTURA DE COMPUTADORAS", "creditos": 4, "prereq": "FIS-101"},
        {"ciclo": 3, "codigo": "RED-301", "nombre": "FUNDAMENTOS DE REDES", "creditos": 4, "prereq": "Ninguno"},
        {"ciclo": 3, "codigo": "ECO-301", "nombre": "ECONOMÍA Y GESTIÓN EMPRESARIAL", "creditos": 3, "prereq": "Ninguno"},
        # Ciclo 4
        {"ciclo": 4, "codigo": "SIS-401", "nombre": "SISTEMAS OPERATIVOS", "creditos": 4, "prereq": "ARQ-301"},
        {"ciclo": 4, "codigo": "BD-401", "nombre": "BASES DE DATOS I", "creditos": 4, "prereq": "EST-301"},
        {"ciclo": 4, "codigo": "ING-401", "nombre": "INGENIERÍA DE REQUERIMIENTOS", "creditos": 4, "prereq": "PRO-201"},
        {"ciclo": 4, "codigo": "MET-401", "nombre": "METODOLOGÍAS ÁGILES", "creditos": 3, "prereq": "Ninguno"},
        # Ciclo 5
        {"ciclo": 5, "codigo": "BD-501", "nombre": "BASES DE DATOS AVANZADAS", "creditos": 4, "prereq": "BD-401"},
        {"ciclo": 5, "codigo": "WEB-501", "nombre": "DESARROLLO WEB FULL-STACK", "creditos": 4, "prereq": "BD-401"},
        {"ciclo": 5, "codigo": "GES-501", "nombre": "GESTIÓN DE PROYECTOS DE TI", "creditos": 4, "prereq": "ING-401"},
        {"ciclo": 5, "codigo": "ETN-501", "nombre": "EXPERIENCIA FORMATIVA EN TRABAJO I", "creditos": 3, "prereq": "80 Créditos"},
        # Ciclo 6
        {"ciclo": 6, "codigo": "SEG-601", "nombre": "SEGURIDAD DE LA INFORMACIÓN", "creditos": 4, "prereq": "RED-301"},
        {"ciclo": 6, "codigo": "INT-601", "nombre": "INTELIGENCIA DE NEGOCIOS (BI)", "creditos": 4, "prereq": "BD-501"},
        {"ciclo": 6, "codigo": "ETN-601", "nombre": "EXPERIENCIA FORMATIVA EN TRABAJO II", "creditos": 3, "prereq": "ETN-501"},
        {"ciclo": 6, "codigo": "DIS-601", "nombre": "DISEÑO DE INTERFACES Y UX", "creditos": 3, "prereq": "WEB-501"},
        # Ciclo 7 (CURSANDO ACTUALMENTE)
        {"ciclo": 7, "codigo": "ETN24-002", "nombre": "EXPERIENCIA FORMATIVA EN SITUACIÓN REAL DE TRABAJO", "creditos": 3, "prereq": "ETN-601"},
        {"ciclo": 7, "codigo": "EIS-038", "nombre": "SOLUCIONES MÓVILES Y CLOUD", "creditos": 4, "prereq": "WEB-501"},
        {"ciclo": 7, "codigo": "EIS-037", "nombre": "MODELAMIENTO DE BASE DE DATOS", "creditos": 4, "prereq": "BD-501"},
        {"ciclo": 7, "codigo": "EIS-039", "nombre": "VALIDACIÓN Y PRUEBAS DE SOFTWARE", "creditos": 4, "prereq": "ING-401"},
        # Ciclo 8 (CURSOS MATRICULADOS COMPLEMENTARIOS / ADELANTO)
        {"ciclo": 8, "codigo": "EIS-040", "nombre": "ARQUITECTURA DE SOFTWARE", "creditos": 4, "prereq": "EIS-039"},
        {"ciclo": 8, "codigo": "EIS-042", "nombre": "GESTIÓN DE BASES DE DATOS", "creditos": 4, "prereq": "EIS-037"},
        {"ciclo": 8, "codigo": "ETR-010", "nombre": "EXPERIENCIA FORMATIVA EN SITUACIÓN REAL DE TRABAJO IV", "creditos": 3, "prereq": "ETN24-002"},
        # Ciclo 9
        {"ciclo": 9, "codigo": "TES-901", "nombre": "PROYECTO DE INVESTIGACIÓN I (TESIS I)", "creditos": 5, "prereq": "160 Créditos"},
        {"ciclo": 9, "codigo": "AUD-901", "nombre": "AUDITORÍA DE SISTEMAS", "creditos": 4, "prereq": "SEG-601"},
        {"ciclo": 9, "codigo": "DIR-901", "nombre": "DIRECCIÓN ESTRATÉGICA DE TI", "creditos": 4, "prereq": "GES-501"},
        # Ciclo 10
        {"ciclo": 10, "codigo": "TES-101", "nombre": "PROYECTO DE INVESTIGACIÓN II (TESIS II)", "creditos": 5, "prereq": "TES-901"},
        {"ciclo": 10, "codigo": "ETI-101", "nombre": "ÉTICA PROFESIONAL Y DEONTOLOGÍA", "creditos": 3, "prereq": "180 Créditos"},
        {"ciclo": 10, "codigo": "EMP-101", "nombre": "EMPRENDIMIENTO E INNOVACIÓN TECH", "creditos": 4, "prereq": "DIR-901"}
    ]

    cursos_malla = []
    creditos_aprobados = 0
    creditos_cursando = 0
    cursos_aprob_count = 0
    cursos_pend_count = 0

    for item in malla_base:
        c_ciclo = item["ciclo"]
        c_cod = item["codigo"]
        c_cred = item["creditos"]

        # Buscar si está en las matrículas
        m_encontrada = next((m for m in matriculas if m.curso.codigo == c_cod), None)

        if m_encontrada:
            summary = get_matricula_grades_summary(m_encontrada, db)
            prom = summary["promedio_final"] or summary["promedio_actual"]
            estado = "AMARILLO" # Cursando
            nota_str = f"{prom:.2f}" if prom is not None else "--"
            creditos_cursando += c_cred
        elif c_ciclo < est.ciclo:
            # Ciclos previos aprobados
            estado = "VERDE"
            nota_str = "16.00"
            creditos_aprobados += c_cred
            cursos_aprob_count += 1
        else:
            # Ciclos futuros
            estado = "GRIS"
            nota_str = "--"
            cursos_pend_count += 1

        cursos_malla.append({
            "ciclo": c_ciclo,
            "codigo": c_cod,
            "nombre": item["nombre"],
            "creditos": c_cred,
            "prereq": item["prereq"],
            "estado": estado, # VERDE, AMARILLO, GRIS, ROJO
            "nota": nota_str
        })

    creditos_totales = sum(item["creditos"] for item in malla_base)
    porcentaje = round(((creditos_aprobados + creditos_cursando) / creditos_totales) * 100, 1)

    return {
        "carrera": est.carrera,
        "plan_estudios": "PLAN 2023 - COMPETENCIAS PROFESIONALES",
        "ciclo_actual": est.ciclo,
        "total_ciclos": 10,
        "creditos_totales": creditos_totales,
        "creditos_aprobados": creditos_aprobados,
        "creditos_cursando": creditos_cursando,
        "creditos_pendientes": max(0, creditos_totales - creditos_aprobados - creditos_cursando),
        "cursos_aprobados": cursos_aprob_count,
        "cursos_pendientes": cursos_pend_count,
        "porcentaje_avance": porcentaje,
        "malla": cursos_malla
    }

@app.get("/api/estudiante/rendimiento-historico")
def estudiante_rendimiento_historico(
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    matriculas = db.query(models.Matricula).filter(models.Matricula.estudiante_id == est.id).all()
    
    # Detalle de cursos cursados actualmente en Ciclo 7
    cursos_c7 = []
    for m in matriculas:
        summary = get_matricula_grades_summary(m, db)
        prom = summary["promedio_final"] or summary["promedio_actual"]
        cursos_c7.append({
            "codigo": m.curso.codigo,
            "curso": m.curso.nombre,
            "creditos": m.curso.creditos,
            "nota": prom if prom is not None else 16.0,
            "estado": summary["estado_curso"]
        })

    cursos_por_ciclo = {
        1: [
            {"codigo": "MAT-101", "curso": "CÁLCULO I", "creditos": 4, "nota": 15.5, "estado": "APROBADO"},
            {"codigo": "FIS-101", "curso": "FÍSICA GENERAL", "creditos": 4, "nota": 14.8, "estado": "APROBADO"},
            {"codigo": "PRO-101", "curso": "FUNDAMENTOS DE PROGRAMACIÓN", "creditos": 4, "nota": 16.0, "estado": "APROBADO"},
            {"codigo": "HUM-101", "curso": "COMUNICACIÓN EFECTIVA", "creditos": 3, "nota": 14.5, "estado": "APROBADO"},
        ],
        2: [
            {"codigo": "MAT-201", "curso": "CÁLCULO II", "creditos": 4, "nota": 15.0, "estado": "APROBADO"},
            {"codigo": "PRO-201", "curso": "PROGRAMACIÓN ORIENTADA A OBJETOS", "creditos": 4, "nota": 16.5, "estado": "APROBADO"},
            {"codigo": "EST-201", "curso": "ESTADÍSTICA Y PROBABILIDADES", "creditos": 4, "nota": 15.8, "estado": "APROBADO"},
            {"codigo": "DIS-201", "curso": "MATEMÁTICA DISCRETA", "creditos": 3, "nota": 16.0, "estado": "APROBADO"},
        ],
        3: [
            {"codigo": "EST-301", "curso": "ESTRUCTURA DE DATOS Y ALGORITMOS", "creditos": 4, "nota": 16.2, "estado": "APROBADO"},
            {"codigo": "ARQ-301", "curso": "ARQUITECTURA DE COMPUTADORAS", "creditos": 4, "nota": 15.8, "estado": "APROBADO"},
            {"codigo": "RED-301", "curso": "FUNDAMENTOS DE REDES", "creditos": 4, "nota": 16.0, "estado": "APROBADO"},
            {"codigo": "ECO-301", "curso": "ECONOMÍA Y GESTIÓN EMPRESARIAL", "creditos": 3, "nota": 16.0, "estado": "APROBADO"},
        ],
        4: [
            {"codigo": "SIS-401", "curso": "SISTEMAS OPERATIVOS", "creditos": 4, "nota": 16.5, "estado": "APROBADO"},
            {"codigo": "BD-401", "curso": "BASES DE DATOS I", "creditos": 4, "nota": 16.8, "estado": "APROBADO"},
            {"codigo": "ING-401", "curso": "INGENIERÍA DE REQUERIMIENTOS", "creditos": 4, "nota": 16.0, "estado": "APROBADO"},
            {"codigo": "MET-401", "curso": "METODOLOGÍAS ÁGILES", "creditos": 3, "nota": 16.2, "estado": "APROBADO"},
        ],
        5: [
            {"codigo": "BD-501", "curso": "BASES DE DATOS AVANZADAS", "creditos": 4, "nota": 16.0, "estado": "APROBADO"},
            {"codigo": "WEB-501", "curso": "DESARROLLO WEB FULL-STACK", "creditos": 4, "nota": 16.5, "estado": "APROBADO"},
            {"codigo": "GES-501", "curso": "GESTIÓN DE PROYECTOS DE TI", "creditos": 4, "nota": 15.8, "estado": "APROBADO"},
            {"codigo": "ETN-501", "curso": "EXPERIENCIA FORMATIVA EN TRABAJO I", "creditos": 3, "nota": 16.2, "estado": "APROBADO"},
        ],
        6: [
            {"codigo": "SEG-601", "curso": "SEGURIDAD DE LA INFORMACIÓN", "creditos": 4, "nota": 16.5, "estado": "APROBADO"},
            {"codigo": "INT-601", "curso": "INTELIGENCIA DE NEGOCIOS (BI)", "creditos": 4, "nota": 16.8, "estado": "APROBADO"},
            {"codigo": "ETN-601", "curso": "EXPERIENCIA FORMATIVA EN TRABAJO II", "creditos": 3, "nota": 16.5, "estado": "APROBADO"},
            {"codigo": "DIS-601", "curso": "DISEÑO DE INTERFACES Y UX", "creditos": 3, "nota": 16.2, "estado": "APROBADO"},
        ],
        7: cursos_c7
    }

    # Generar histórico semestral consistente
    semestres = [
        {"periodo": "2023-I", "ciclo": 1, "cursos": 4, "creditos": 15, "promedio": 15.2, "aprobados": 4, "desaprobados": 0, "estado": "APROBADO"},
        {"periodo": "2023-II", "ciclo": 2, "cursos": 4, "creditos": 15, "promedio": 15.8, "aprobados": 4, "desaprobados": 0, "estado": "APROBADO"},
        {"periodo": "2024-I", "ciclo": 3, "cursos": 4, "creditos": 15, "promedio": 16.0, "aprobados": 4, "desaprobados": 0, "estado": "APROBADO"},
        {"periodo": "2024-II", "ciclo": 4, "cursos": 4, "creditos": 15, "promedio": 16.4, "aprobados": 4, "desaprobados": 0, "estado": "APROBADO"},
        {"periodo": "2025-I", "ciclo": 5, "cursos": 4, "creditos": 15, "promedio": 16.1, "aprobados": 4, "desaprobados": 0, "estado": "APROBADO"},
        {"periodo": "2025-II", "ciclo": 6, "cursos": 4, "creditos": 14, "promedio": 16.5, "aprobados": 4, "desaprobados": 0, "estado": "APROBADO"},
        {"periodo": "2026 II-B", "ciclo": 7, "cursos": len(matriculas), "creditos": sum(m.curso.creditos for m in matriculas), "promedio": 16.14, "aprobados": len(matriculas), "desaprobados": 0, "estado": "EN CURSO"}
    ]

    return {
        "estudiante": f"{est.apellidos}, {est.nombres}",
        "carrera": est.carrera,
        "promedio_general": 16.1,
        "semestres": semestres,
        "cursos_por_ciclo": cursos_por_ciclo
    }

@app.get("/api/estudiante/asistencias/detalle")
def estudiante_asistencias_detalle(
    curso_id: int | None = None,
    periodo_id: int | None = None,
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    query_m = db.query(models.Matricula).filter(models.Matricula.estudiante_id == est.id)
    if curso_id:
        query_m = query_m.filter(models.Matricula.curso_id == curso_id)
    matriculas = query_m.all()
    m_ids = [m.id for m in matriculas]

    logs = db.query(models.Asistencia).filter(models.Asistencia.matricula_id.in_(m_ids)).order_by(models.Asistencia.fecha.desc()).all() if m_ids else []

    total_sesiones = len(logs)
    presentes = sum(1 for a in logs if a.estado == "PRESENTE")
    faltas = sum(1 for a in logs if a.estado == "FALTA")
    tardanzas = sum(1 for a in logs if a.estado == "TARDANZA")
    justificados = sum(1 for a in logs if a.estado == "JUSTIFICADO")
    pct = round(((presentes + justificados) / total_sesiones) * 100, 1) if total_sesiones > 0 else 94.0

    matricula_dict = {m.id: m for m in matriculas}
    detalle_logs = []
    for log in logs:
        m = matricula_dict.get(log.matricula_id)
        c_nom = m.curso.nombre if m else "Curso"
        detalle_logs.append({
            "id": log.id,
            "fecha": str(log.fecha),
            "hora": log.hora,
            "curso": c_nom,
            "estado": log.estado,
            "observacion": log.observacion or "--"
        })

    return {
        "resumen": {
            "porcentaje_asistencia": pct,
            "total_sesiones": total_sesiones,
            "presentes": presentes,
            "faltas": faltas,
            "tardanzas": tardanzas,
            "justificados": justificados
        },
        "logs": detalle_logs
    }

@app.get("/api/estudiante/encuestas")
def estudiante_encuestas_list(
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    matriculas = db.query(models.Matricula).filter(
        models.Matricula.estudiante_id == est.id,
        models.Matricula.periodo == "2026 II-B"
    ).all()

    respuestas = {e.seccion_id: e for e in db.query(models.EncuestaDocente).filter(models.EncuestaDocente.estudiante_id == est.id).all()}

    encuestas = []
    for m in matriculas:
        c = m.curso
        sec = m.seccion
        sec_id = sec.id if sec else m.id
        doc_nom = sec.docente.nombres + " " + sec.docente.apellidos if (sec and sec.docente) else c.docente
        resp = respuestas.get(sec_id)

        encuestas.append({
            "seccion_id": sec_id,
            "curso_id": c.id,
            "codigo": c.codigo,
            "curso": c.nombre,
            "docente": doc_nom,
            "periodo": "2026 II-B",
            "fecha_inicio": "15/08/2026",
            "fecha_fin": "30/10/2026",
            "estado": "Completada" if resp else "Pendiente",
            "calificacion": resp.calificacion if resp else None,
            "comentarios": resp.comentarios if resp else None
        })

    return {
        "periodo": "2026 II-B",
        "encuestas": encuestas
    }

@app.post("/api/estudiante/encuestas/{seccion_id}/responder")
def estudiante_encuesta_responder(
    seccion_id: int,
    data: schemas.EncuestaSubmitIn,
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    encuesta = db.query(models.EncuestaDocente).filter(
        models.EncuestaDocente.estudiante_id == est.id,
        models.EncuestaDocente.seccion_id == seccion_id
    ).first()

    if not encuesta:
        encuesta = models.EncuestaDocente(
            estudiante_id=est.id,
            seccion_id=seccion_id,
            calificacion=data.calificacion,
            comentarios=data.comentarios,
            estado="COMPLETADA"
        )
        db.add(encuesta)
    else:
        encuesta.calificacion = data.calificacion
        encuesta.comentarios = data.comentarios

    db.commit()
    return {"ok": True, "message": "Encuesta registrada exitosamente"}

@app.get("/api/estudiante/tramites")
def estudiante_tramites_list(
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    tramites_db = db.query(models.Tramite).filter(models.Tramite.estudiante_id == est.id).order_by(models.Tramite.fecha_solicitud.desc()).all()
    
    pendientes = sum(1 for t in tramites_db if t.estado == "PENDIENTE")
    en_revision = sum(1 for t in tramites_db if t.estado == "EN REVISION")
    aprobados = sum(1 for t in tramites_db if t.estado == "APROBADO")
    rechazados = sum(1 for t in tramites_db if t.estado == "RECHAZADO")

    return {
        "resumen": {
            "pendientes": pendientes,
            "en_revision": en_revision,
            "aprobados": aprobados,
            "rechazados": rechazados
        },
        "tramites": [
            {
                "id": t.id,
                "codigo": t.codigo,
                "tipo": t.tipo,
                "motivo": t.motivo,
                "descripcion": t.descripcion,
                "estado": t.estado,
                "fecha_solicitud": t.fecha_solicitud.strftime("%d/%m/%Y"),
                "respuesta": t.respuesta
            } for t in tramites_db
        ]
    }

@app.post("/api/estudiante/tramites")
def estudiante_tramite_crear(
    data: schemas.TramiteCreateIn,
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    count = db.query(models.Tramite).count()
    cod = f"TRM-2026-{(count + 1):03d}"
    desc = data.descripcion or ""
    if data.archivo:
        desc = f"{desc} [Adjunto: {data.archivo}]".strip()

    nuevo = models.Tramite(
        estudiante_id=est.id,
        codigo=cod,
        tipo=data.tipo,
        motivo=data.motivo,
        descripcion=desc,
        estado="PENDIENTE"
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return {"ok": True, "message": "Solicitud de trámite registrada con éxito", "codigo": cod}

@app.get("/api/estudiante/pagos")
def estudiante_pagos_list(
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    pagos = db.query(models.Pago).filter(models.Pago.estudiante_id == est.id).order_by(models.Pago.fecha_vencimiento.asc()).all()

    total_deuda = sum(float(p.monto) for p in pagos)
    total_pagado = sum(float(p.monto) for p in pagos if p.estado == "CANCELADO")
    total_pendiente = sum(float(p.monto) for p in pagos if p.estado == "PENDIENTE")

    return {
        "resumen": {
            "deuda_total": total_deuda,
            "pagado": total_pagado,
            "pendiente": total_pendiente
        },
        "pagos": [
            {
                "id": p.id,
                "concepto": p.concepto,
                "monto": float(p.monto),
                "fecha_vencimiento": str(p.fecha_vencimiento),
                "fecha_pago": str(p.fecha_pago) if p.fecha_pago else "--",
                "estado": p.estado,
                "nro_operacion": p.nro_operacion or "--"
            } for p in pagos
        ]
    }

@app.get("/api/estudiante/bienestar")
def estudiante_bienestar_get(
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    ficha = db.query(models.FichaBienestar).filter(models.FichaBienestar.estudiante_id == est.id).first()
    if not ficha:
        ficha = models.FichaBienestar(
            estudiante_id=est.id,
            contacto_emergencia="Rosa María Espino",
            telefono_emergencia="991234567",
            parentesco_contacto="Madre",
            direccion_actual="Av. Universitaria 1450, Lima",
            ocupacion_padres="Padre: Ingeniero / Madre: Docente",
            ingreso_familiar=4500.0,
            condicion_vivienda="Propia",
            seguro_salud="Seguro Estudiantil",
            alergias_condiciones="Ninguna"
        )
        db.add(ficha)
        db.commit()
        db.refresh(ficha)

    return {
        "contacto_emergencia": ficha.contacto_emergencia,
        "telefono_emergencia": ficha.telefono_emergencia,
        "parentesco_contacto": ficha.parentesco_contacto,
        "direccion_actual": ficha.direccion_actual,
        "ocupacion_padres": ficha.ocupacion_padres,
        "ingreso_familiar": float(ficha.ingreso_familiar) if ficha.ingreso_familiar else 0.0,
        "condicion_vivienda": ficha.condicion_vivienda,
        "seguro_salud": ficha.seguro_salud,
        "alergias_condiciones": ficha.alergias_condiciones
    }

@app.put("/api/estudiante/bienestar")
def estudiante_bienestar_update(
    data: schemas.BienestarUpdateIn,
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    ficha = db.query(models.FichaBienestar).filter(models.FichaBienestar.estudiante_id == est.id).first()
    if not ficha:
        ficha = models.FichaBienestar(estudiante_id=est.id)
        db.add(ficha)

    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(ficha, k, v)
    ficha.fecha_actualizacion = datetime.utcnow()
    db.commit()
    return {"ok": True, "message": "Ficha integral de bienestar actualizada correctamente"}

@app.get("/api/estudiante/recuperacion")
def estudiante_recuperacion_get(
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    matriculas = db.query(models.Matricula).filter(
        models.Matricula.estudiante_id == est.id,
        models.Matricula.periodo == "2026 II-B"
    ).all()

    solicitudes_list = db.query(models.SolicitudRecuperacion).filter(models.SolicitudRecuperacion.estudiante_id == est.id).order_by(models.SolicitudRecuperacion.fecha_solicitud.desc()).all()
    solicitudes = {s.matricula_id: s for s in solicitudes_list}

    cursos_eval = []
    for m in matriculas:
        summary = get_matricula_grades_summary(m, db)
        prom = summary["promedio_final"] or summary["promedio_actual"]
        sol = solicitudes.get(m.id)

        # Regla académica: disponible para solicitar recuperación si promedio < 11 o a solicitud del alumno
        cursos_eval.append({
            "matricula_id": m.id,
            "codigo": m.curso.codigo,
            "curso": m.curso.nombre,
            "nota": prom,
            "fecha": "2026-10-15",
            "estado": sol.estado if sol else "DISPONIBLE",
            "puede_solicitar": sol is None
        })

    mis_solicitudes = []
    for s in solicitudes_list:
        mat = db.get(models.Matricula, s.matricula_id)
        c_nom = mat.curso.nombre if mat and mat.curso else "Asignatura"
        c_cod = mat.curso.codigo if mat and mat.curso else "COD"
        c_nota = float(mat.nota) if mat and mat.nota else 0.0
        mis_solicitudes.append({
            "id": s.id,
            "matricula_id": s.matricula_id,
            "codigo": c_cod,
            "curso": c_nom,
            "nota": c_nota,
            "fecha": str(s.fecha_examen) if s.fecha_examen else (s.fecha_solicitud.strftime("%d/%m/%Y") if s.fecha_solicitud else "2026-10-15"),
            "motivo": s.motivo or "Examen de recuperación ordinario",
            "estado": s.estado
        })

    return {
        "periodo": "2026 II-B",
        "requisitos": "Tener matrícula vigente en el periodo y haber rendido las evaluaciones ordinarias con al menos 70% de asistencia.",
        "cursos": cursos_eval,
        "mis_solicitudes": mis_solicitudes
    }

@app.post("/api/estudiante/recuperacion")
def estudiante_recuperacion_post(
    data: schemas.RecuperacionCreateIn,
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    sol = db.query(models.SolicitudRecuperacion).filter(
        models.SolicitudRecuperacion.estudiante_id == est.id,
        models.SolicitudRecuperacion.matricula_id == data.matricula_id
    ).first()
    if sol:
        raise HTTPException(400, "Ya existe una solicitud registrada para esta asignatura")

    nueva = models.SolicitudRecuperacion(
        estudiante_id=est.id,
        matricula_id=data.matricula_id,
        motivo=data.motivo or "Examen de recuperación ordinario",
        estado="PENDIENTE"
    )
    db.add(nueva)
    db.commit()
    return {"ok": True, "message": "Solicitud de examen de recuperación registrada correctamente"}

@app.get("/api/estudiante/reprogramacion")
def estudiante_reprogramacion_get(
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    matriculas = db.query(models.Matricula).filter(
        models.Matricula.estudiante_id == est.id,
        models.Matricula.periodo == "2026 II-B"
    ).all()

    evaluaciones_elegibles = []
    solicitudes_rep_list = db.query(models.SolicitudReprogramacion).filter(models.SolicitudReprogramacion.estudiante_id == est.id).order_by(models.SolicitudReprogramacion.fecha_solicitud.desc()).all()
    solicitudes = {s.evaluacion_id: s for s in solicitudes_rep_list}

    for m in matriculas:
        c = m.curso
        summary = get_matricula_grades_summary(m, db)
        for ev in summary["evaluaciones"]:
            sol = solicitudes.get(ev.evaluacion_id)
            evaluaciones_elegibles.append({
                "evaluacion_id": ev.evaluacion_id,
                "matricula_id": m.id,
                "curso": c.nombre,
                "evaluacion": ev.evaluacion,
                "fecha_original": "2026-09-25",
                "motivo": sol.motivo if sol else "--",
                "estado": sol.estado if sol else "HABILITADO",
                "puede_solicitar": sol is None
            })

    mis_solicitudes_rep = []
    for s in solicitudes_rep_list:
        mat = db.get(models.Matricula, s.matricula_id)
        ev = db.get(models.Evaluacion, s.evaluacion_id)
        c_nom = mat.curso.nombre if mat and mat.curso else "Asignatura"
        ev_nom = ev.nombre if ev else "Evaluación"
        mis_solicitudes_rep.append({
            "id": s.id,
            "evaluacion_id": s.evaluacion_id,
            "matricula_id": s.matricula_id,
            "curso": c_nom,
            "evaluacion": ev_nom,
            "fecha_original": "2026-09-25",
            "fecha_solicitada": str(s.fecha_solicitada) if s.fecha_solicitada else "--",
            "motivo": s.motivo,
            "sustento": s.sustento or "--",
            "estado": s.estado,
            "fecha_solicitud": s.fecha_solicitud.strftime("%d/%m/%Y") if s.fecha_solicitud else "--"
        })

    return {
        "periodo": "2026 II-B",
        "normativa": "Presentar justificación documentada (médica o laboral) dentro de las 48 horas posteriores a la fecha original del examen.",
        "evaluaciones": evaluaciones_elegibles,
        "mis_solicitudes": mis_solicitudes_rep
    }

@app.post("/api/estudiante/reprogramacion")
def estudiante_reprogramacion_post(
    data: schemas.ReprogramacionCreateIn,
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    nueva = models.SolicitudReprogramacion(
        estudiante_id=est.id,
        evaluacion_id=data.evaluacion_id,
        matricula_id=data.matricula_id,
        motivo=data.motivo,
        fecha_solicitada=data.fecha_solicitada,
        sustento=data.sustento,
        estado="PENDIENTE"
    )
    db.add(nueva)
    db.commit()
    return {"ok": True, "message": "Solicitud de reprogramación de evaluación enviada con éxito"}

@app.get("/api/bolsa-laboral")
def listar_bolsa_laboral(
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    empleos = db.query(models.Empleo).order_by(models.Empleo.fecha_publicacion.desc()).all()
    postulaciones_ids = {p.empleo_id for p in db.query(models.Postulacion).filter(models.Postulacion.estudiante_id == est.id).all()}

    resultado = []
    for e in empleos:
        resultado.append({
            "id": e.id,
            "empresa": e.empresa,
            "puesto": e.puesto,
            "modalidad": e.modalidad,
            "ubicacion": e.ubicacion,
            "descripcion": e.descripcion,
            "requisitos": e.requisitos,
            "funciones": e.funciones or "Funciones inherentes al puesto.",
            "remuneracion": e.remuneracion or "Convenio de Prácticas",
            "fecha_publicacion": str(e.fecha_publicacion),
            "fecha_limite": str(e.fecha_limite) if e.fecha_limite else "Convocatoria Abierta",
            "ya_postulo": e.id in postulaciones_ids
        })

    return {"carrera": est.carrera, "ofertas": resultado}

@app.post("/api/bolsa-laboral/{empleo_id}/postular")
def postular_empleo(
    empleo_id: int,
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    emp = db.get(models.Empleo, empleo_id)
    if not emp:
        raise HTTPException(404, "Oferta laboral no encontrada")

    existente = db.query(models.Postulacion).filter(
        models.Postulacion.estudiante_id == est.id,
        models.Postulacion.empleo_id == empleo_id
    ).first()
    if existente:
        raise HTTPException(400, "Ya has postulado previamente a esta vacante")

    nueva = models.Postulacion(
        estudiante_id=est.id,
        empleo_id=empleo_id,
        estado="ENVIADA"
    )
    db.add(nueva)
    db.commit()
    return {"ok": True, "message": f"Postulación exitosa a '{emp.puesto}' en '{emp.empresa}'"}

@app.get("/api/estudiante/postulaciones")
def listar_mis_postulaciones(
    est: models.Estudiante = Depends(get_current_estudiante),
    db: Session = Depends(get_db)
):
    postulaciones = db.query(models.Postulacion).filter(models.Postulacion.estudiante_id == est.id).order_by(models.Postulacion.fecha_postulacion.desc()).all()
    return [
        {
            "id": p.id,
            "empresa": p.empleo.empresa,
            "puesto": p.empleo.puesto,
            "fecha": p.fecha_postulacion.strftime("%d/%m/%Y"),
            "estado": p.estado
        } for p in postulaciones
    ]

# ==================== ENDPOINTS ADMINISTRATIVOS (PRESERVADOS) ====================

@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db), _=Depends(current_user)):
    return {
        "estudiantes": db.query(func.count(models.Estudiante.id)).scalar(),
        "cursos": db.query(func.count(models.Curso.id)).scalar(),
        "matriculas": db.query(func.count(models.Matricula.id)).scalar(),
        "activos": db.query(func.count(models.Estudiante.id)).filter(models.Estudiante.estado == "ACTIVO").scalar(),
    }

@app.get("/api/estudiantes", response_model=list[schemas.EstudianteOut])
def listar_estudiantes(db: Session = Depends(get_db), _=Depends(current_user)):
    return db.query(models.Estudiante).order_by(models.Estudiante.id.desc()).all()

@app.post("/api/estudiantes", response_model=schemas.EstudianteOut)
def crear_estudiante(data: schemas.EstudianteCreate, db: Session = Depends(get_db), _=Depends(current_user)):
    # 1. Validar duplicados de código, DNI o correo
    existente = db.query(models.Estudiante).filter(
        (models.Estudiante.codigo == data.codigo) |
        (models.Estudiante.dni == data.dni) |
        (models.Estudiante.correo == data.correo)
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe un estudiante con ese código, DNI o correo institucional")

    dump_data = data.model_dump()
    if not dump_data.get("fecha_ingreso"):
        dump_data["fecha_ingreso"] = date.today()

    # 2. Asegurar usuario de acceso con rol ESTUDIANTE y contraseña por defecto
    user = db.query(models.Usuario).filter(models.Usuario.correo == data.correo).first()
    if not user:
        user = models.Usuario(
            nombre=f"{data.nombres} {data.apellidos}",
            correo=data.correo,
            password_hash=pwd_context.hash("Estudiante123*"),
            rol="ESTUDIANTE",
            activo=(data.estado == "ACTIVO")
        )
        db.add(user)
        db.flush()
    else:
        user.rol = "ESTUDIANTE"
        user.activo = (data.estado == "ACTIVO")

    dump_data["usuario_id"] = user.id

    # 3. Vincular con carrera_id si existe
    carrera = db.query(models.Carrera).filter(
        (models.Carrera.nombre.ilike(f"%{data.carrera}%")) |
        (models.Carrera.codigo.ilike(f"%{data.carrera}%"))
    ).first()
    if carrera:
        dump_data["carrera_id"] = carrera.id

    obj = models.Estudiante(**dump_data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.put("/api/estudiantes/{id}", response_model=schemas.EstudianteOut)
def editar_estudiante(id: int, data: schemas.EstudianteUpdate, db: Session = Depends(get_db), _=Depends(current_user)):
    obj = db.get(models.Estudiante, id)
    if not obj:
        raise HTTPException(404, "Estudiante no encontrado")
    
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(obj, k, v)
    
    # Sincronizar estado del usuario si se actualizó
    if "estado" in update_data and obj.usuario_id:
        user = db.get(models.Usuario, obj.usuario_id)
        if user:
            user.activo = (update_data["estado"] == "ACTIVO")

    db.commit()
    db.refresh(obj)
    return obj

@app.delete("/api/estudiantes/{id}")
def eliminar_estudiante(id: int, db: Session = Depends(get_db), _=Depends(current_user)):
    obj = db.get(models.Estudiante, id)
    if not obj:
        raise HTTPException(404, "Estudiante no encontrado")
    db.delete(obj)
    db.commit()
    return {"ok": True}

@app.get("/api/cursos", response_model=list[schemas.CursoOut])
def listar_cursos(db: Session = Depends(get_db), _=Depends(current_user)):
    return db.query(models.Curso).order_by(models.Curso.id.desc()).all()

@app.post("/api/cursos", response_model=schemas.CursoOut)
def crear_curso(data: schemas.CursoCreate, db: Session = Depends(get_db), _=Depends(current_user)):
    existente = db.query(models.Curso).filter(models.Curso.codigo == data.codigo).first()
    if existente:
        raise HTTPException(status_code=400, detail=f"Ya existe un curso registrado con el código {data.codigo}")
    obj = models.Curso(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.put("/api/cursos/{id}", response_model=schemas.CursoOut)
def editar_curso(id: int, data: schemas.CursoUpdate, db: Session = Depends(get_db), _=Depends(current_user)):
    obj = db.get(models.Curso, id)
    if not obj:
        raise HTTPException(404, "Curso no encontrado")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

@app.delete("/api/cursos/{id}")
def eliminar_curso(id: int, db: Session = Depends(get_db), _=Depends(current_user)):
    obj = db.get(models.Curso, id)
    if not obj:
        raise HTTPException(404, "Curso no encontrado")
    db.delete(obj)
    db.commit()
    return {"ok": True}

@app.get("/api/matriculas")
def listar_matriculas(db: Session = Depends(get_db), _=Depends(current_user)):
    rows = db.query(models.Matricula).order_by(models.Matricula.id.desc()).all()
    return [{
        "id": m.id,
        "estudiante_id": m.estudiante_id,
        "curso_id": m.curso_id,
        "periodo": m.periodo,
        "nota": float(m.nota) if m.nota is not None else None,
        "estado": m.estado,
        "estudiante": f"{m.estudiante.nombres} {m.estudiante.apellidos}" if m.estudiante else "",
        "curso": m.curso.nombre if m.curso else ""
    } for m in rows]

@app.post("/api/matriculas", response_model=schemas.MatriculaOut)
def crear_matricula(data: schemas.MatriculaCreate, db: Session = Depends(get_db), _=Depends(current_user)):
    # Evitar duplicados
    existente = db.query(models.Matricula).filter(
        models.Matricula.estudiante_id == data.estudiante_id,
        models.Matricula.curso_id == data.curso_id,
        models.Matricula.periodo == data.periodo
    ).first()
    if existente:
        raise HTTPException(status_code=400, detail="El estudiante ya está matriculado en este curso para el periodo indicado")

    dump_data = data.model_dump()
    periodo = db.query(models.Periodo).filter(models.Periodo.codigo == data.periodo).first()
    if periodo:
        dump_data["periodo_id"] = periodo.id
        seccion = db.query(models.Seccion).filter(
            models.Seccion.curso_id == data.curso_id,
            models.Seccion.periodo_id == periodo.id
        ).first()
        if seccion:
            dump_data["seccion_id"] = seccion.id

    obj = models.Matricula(**dump_data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.put("/api/matriculas/{id}", response_model=schemas.MatriculaOut)
def editar_matricula(id: int, data: schemas.MatriculaUpdate, db: Session = Depends(get_db), _=Depends(current_user)):
    obj = db.get(models.Matricula, id)
    if not obj:
        raise HTTPException(404, "Matrícula no encontrada")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

@app.delete("/api/matriculas/{id}")
def eliminar_matricula(id: int, db: Session = Depends(get_db), _=Depends(current_user)):
    obj = db.get(models.Matricula, id)
    if not obj:
        raise HTTPException(404, "Matrícula no encontrada")
    db.delete(obj)
    db.commit()
    return {"ok": True}
