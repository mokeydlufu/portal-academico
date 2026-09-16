import os
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import desc
from jose import jwt, JWTError

from ..database import get_db
from ..models import BackupFile, BackupSchedule, BackupHistory, RestoreHistory, Usuario
from ..auth import current_user, SECRET_KEY, ALGORITHM
from ..schemas_backups import (
    BackupCreateIn,
    BackupFileOut,
    BackupScheduleCreateIn,
    BackupScheduleUpdateIn,
    BackupScheduleOut,
    BackupHistoryOut,
    RestoreCreateIn,
    RestoreHistoryOut,
    BackupSummaryOut,
    HealthCheckOut,
    BackupFileOnDiskOut,
    RecoveryPreviewOut,
    RecoverMatriculaIn
)
from ..services.backup_service import (
    crear_backup,
    eliminar_backup,
    obtener_archivo_para_descarga,
    restaurar_backup_prueba,
    check_backup_health,
    format_size,
    get_timezone,
    preview_recovery_data,
    recover_matricula_data
)
from ..services.scheduler_service import (
    calcular_proxima_ejecucion,
    calcular_proximo_backup_global,
    ejecutar_programacion_inmediata
)

router = APIRouter(prefix="/api/backups", tags=["Copias de Seguridad"])

# ==================== CONTROL DE ROLES ====================

oauth2_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def require_admin(user: Usuario = Depends(current_user)) -> Usuario:
    if user.rol not in ["ADMIN", "ADMINISTRADOR"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido: El módulo de Copias de Seguridad requiere privilegios de Administrador"
        )
    return user

def require_admin_download(
    header_token: str | None = Depends(oauth2_optional),
    query_token: str | None = Query(None, alias="token"),
    db: Session = Depends(get_db)
) -> Usuario:
    raw_token = header_token or query_token
    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no proporcionado")
    try:
        payload = jwt.decode(raw_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user = db.get(Usuario, user_id)
    if not user or not user.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autorizado")
    if user.rol not in ["ADMIN", "ADMINISTRADOR"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido a Administradores")
    return user

def require_admin_or_supervisor(user: Usuario = Depends(current_user)) -> Usuario:
    if user.rol not in ["ADMIN", "ADMINISTRADOR", "SUPERVISOR"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido: Privilegios insuficientes para consultar el módulo de Backups"
        )
    return user

def format_dt(dt: datetime | None) -> str | None:
    if not dt:
        return None
    tz = get_timezone()
    if dt.tzinfo is None:
        from datetime import timezone
        dt = dt.replace(tzinfo=timezone.utc).astimezone(tz)
    else:
        dt = dt.astimezone(tz)
    return dt.strftime("%d/%m/%Y %H:%M:%S")

def format_duration(start: datetime, end: datetime | None) -> str | None:
    if not end:
        return "--"
    diff = (end - start).total_seconds()
    if diff < 60:
        return f"{diff:.1f} seg"
    return f"{diff / 60:.1f} min"

# ==================== 1. RESUMEN Y HEALTH CHECK ====================

@router.get("/summary", response_model=BackupSummaryOut)
def obtener_resumen(
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_admin_or_supervisor)
):
    health = check_backup_health(db)
    backup_count = db.query(BackupFile).filter(BackupFile.status == "CORRECTO").count()

    last_backup = db.query(BackupFile).filter(BackupFile.status == "CORRECTO").order_by(desc(BackupFile.created_at)).first()
    next_date, next_name = calcular_proximo_backup_global(db)

    if not health["is_operational"]:
        status_str = "Configuración incompleta"
    elif backup_count == 0 and not next_date:
        status_str = "Sin configuración"
    else:
        last_hist = db.query(BackupHistory).order_by(desc(BackupHistory.started_at)).first()
        if last_hist and last_hist.status == "ERROR":
            status_str = "Error"
        else:
            status_str = "Correcto"

    return BackupSummaryOut(
        last_backup_date=format_dt(last_backup.created_at) if last_backup else None,
        last_backup_file=last_backup.filename if last_backup else None,
        last_backup_description=last_backup.description if last_backup else None,
        last_backup_status=last_backup.status if last_backup else None,
        next_backup_date=next_date,
        next_backup_schedule=next_name,
        backup_count=backup_count,
        status=status_str,
        health=HealthCheckOut(**health)
    )

# ==================== 2. PROGRAMACIONES (RUTAS ESTÁTICAS) ====================

@router.get("/schedules", response_model=list[BackupScheduleOut])
def listar_programaciones(
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_admin_or_supervisor)
):
    schedules = db.query(BackupSchedule).order_by(BackupSchedule.id.asc()).all()
    res = []
    for s in schedules:
        nxt = calcular_proxima_ejecucion(s)
        res.append(BackupScheduleOut(
            id=s.id,
            name=s.name,
            frequency=s.frequency,
            run_time=s.run_time,
            day_of_week=s.day_of_week,
            interval_value=s.interval_value,
            retention_days=s.retention_days,
            enabled=s.enabled,
            last_run_at=format_dt(s.last_run_at),
            next_run_at=format_dt(nxt) if nxt else None,
            created_at=format_dt(s.created_at) or ""
        ))
    return res

@router.post("/schedules", response_model=BackupScheduleOut)
def crear_programacion(
    data: BackupScheduleCreateIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_admin)
):
    sch = BackupSchedule(
        name=data.name,
        frequency=data.frequency.upper(),
        run_time=data.run_time,
        day_of_week=data.day_of_week,
        interval_value=data.interval_value,
        retention_days=data.retention_days,
        enabled=data.enabled,
        created_by=user.id
    )
    db.add(sch)
    db.commit()
    db.refresh(sch)

    nxt = calcular_proxima_ejecucion(sch)
    return BackupScheduleOut(
        id=sch.id,
        name=sch.name,
        frequency=sch.frequency,
        run_time=sch.run_time,
        day_of_week=sch.day_of_week,
        interval_value=sch.interval_value,
        retention_days=sch.retention_days,
        enabled=sch.enabled,
        last_run_at=None,
        next_run_at=format_dt(nxt) if nxt else None,
        created_at=format_dt(sch.created_at) or ""
    )

@router.get("/schedules/{id}", response_model=BackupScheduleOut)
def obtener_programacion_detalle(
    id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_admin_or_supervisor)
):
    sch = db.get(BackupSchedule, id)
    if not sch:
        raise HTTPException(404, "Programación no encontrada")
    nxt = calcular_proxima_ejecucion(sch)
    return BackupScheduleOut(
        id=sch.id,
        name=sch.name,
        frequency=sch.frequency,
        run_time=sch.run_time,
        day_of_week=sch.day_of_week,
        interval_value=sch.interval_value,
        retention_days=sch.retention_days,
        enabled=sch.enabled,
        last_run_at=format_dt(sch.last_run_at),
        next_run_at=format_dt(nxt) if nxt else None,
        created_at=format_dt(sch.created_at) or ""
    )

@router.put("/schedules/{id}", response_model=BackupScheduleOut)
def editar_programacion(
    id: int,
    data: BackupScheduleUpdateIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_admin)
):
    sch = db.get(BackupSchedule, id)
    if not sch:
        raise HTTPException(404, "Programación no encontrada")

    if data.name is not None:
        sch.name = data.name
    if data.frequency is not None:
        sch.frequency = data.frequency.upper()
    if data.run_time is not None:
        sch.run_time = data.run_time
    if data.day_of_week is not None:
        sch.day_of_week = data.day_of_week
    if data.interval_value is not None:
        sch.interval_value = data.interval_value
    if data.retention_days is not None:
        sch.retention_days = data.retention_days
    if data.enabled is not None:
        sch.enabled = data.enabled

    db.commit()
    db.refresh(sch)

    nxt = calcular_proxima_ejecucion(sch)
    return BackupScheduleOut(
        id=sch.id,
        name=sch.name,
        frequency=sch.frequency,
        run_time=sch.run_time,
        day_of_week=sch.day_of_week,
        interval_value=sch.interval_value,
        retention_days=sch.retention_days,
        enabled=sch.enabled,
        last_run_at=format_dt(sch.last_run_at),
        next_run_at=format_dt(nxt) if nxt else None,
        created_at=format_dt(sch.created_at) or ""
    )

@router.delete("/schedules/{id}")
def eliminar_programacion(
    id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_admin)
):
    sch = db.get(BackupSchedule, id)
    if not sch:
        raise HTTPException(404, "Programación no encontrada")
    db.delete(sch)
    db.commit()
    return {"ok": True, "message": "Programación eliminada exitosamente"}

@router.post("/schedules/{id}/run-now")
def probar_programacion_ahora(
    id: int,
    user: Usuario = Depends(require_admin)
):
    res = ejecutar_programacion_inmediata(id, user_id=user.id)
    return res

# ==================== 3. HISTORIAL Y RESTAURACIONES (RUTAS ESTÁTICAS) ====================

@router.get("/history", response_model=list[BackupHistoryOut])
def listar_historial(
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_admin_or_supervisor)
):
    rows = db.query(BackupHistory).order_by(desc(BackupHistory.started_at)).limit(100).all()
    resultado = []
    for r in rows:
        fn = r.backup_file.filename if r.backup_file else None
        desc_val = r.backup_file.description if r.backup_file else None
        sn = r.schedule.name if r.schedule else None
        resultado.append(BackupHistoryOut(
            id=r.id,
            backup_file_id=r.backup_file_id,
            filename=fn,
            description=desc_val,
            schedule_id=r.schedule_id,
            schedule_name=sn,
            started_at=format_dt(r.started_at) or "",
            finished_at=format_dt(r.finished_at),
            duration_str=format_duration(r.started_at, r.finished_at),
            status=r.status,
            trigger=r.trigger,
            message=r.message,
            user_name=r.usuario.nombre if r.usuario else "Sistema"
        ))
    return resultado

@router.get("/restores", response_model=list[RestoreHistoryOut])
def listar_restauraciones(
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_admin_or_supervisor)
):
    import re
    rows = db.query(RestoreHistory).order_by(desc(RestoreHistory.started_at)).limit(100).all()
    resultado = []
    for r in rows:
        fn = r.backup_file.filename if r.backup_file else None
        b_desc = r.backup_file.description if r.backup_file else None
        t_count, e_count, m_count = None, None, None
        if r.message:
            mt = re.search(r"Tablas:\s*(\d+)", r.message)
            if mt:
                t_count = int(mt.group(1))
            me = re.search(r"Estudiantes:\s*(\d+)", r.message)
            if me:
                e_count = int(me.group(1))
            mm = re.search(r"Matrículas:\s*(\d+)", r.message)
            if mm:
                m_count = int(mm.group(1))
            if t_count is None:
                mt_leg = re.search(r"Tablas restauradas:\s*(\d+)", r.message)
                if mt_leg:
                    t_count = int(mt_leg.group(1))
        resultado.append(RestoreHistoryOut(
            id=r.id,
            backup_file_id=r.backup_file_id,
            filename=fn,
            target_database=r.target_database,
            description=r.description,
            backup_description=b_desc,
            started_at=format_dt(r.started_at) or "",
            finished_at=format_dt(r.finished_at),
            duration_str=format_duration(r.started_at, r.finished_at),
            status=r.status,
            message=r.message,
            user_name=r.usuario.nombre if r.usuario else "Sistema",
            table_count=t_count,
            estudiantes_count=e_count,
            matriculas_count=m_count
        ))
    return resultado

@router.get("/restores/{id}", response_model=RestoreHistoryOut)
def ver_detalle_restauracion_endpoint(
    id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_admin_or_supervisor)
):
    import re
    r = db.get(RestoreHistory, id)
    if not r:
        raise HTTPException(404, "Restauración no encontrada")
    fn = r.backup_file.filename if r.backup_file else None
    b_desc = r.backup_file.description if r.backup_file else None
    t_count, e_count, m_count = None, None, None
    if r.message:
        mt = re.search(r"Tablas:\s*(\d+)", r.message)
        if mt:
            t_count = int(mt.group(1))
        me = re.search(r"Estudiantes:\s*(\d+)", r.message)
        if me:
            e_count = int(me.group(1))
        mm = re.search(r"Matrículas:\s*(\d+)", r.message)
        if mm:
            m_count = int(mm.group(1))
        if t_count is None:
            mt_leg = re.search(r"Tablas restauradas:\s*(\d+)", r.message)
            if mt_leg:
                t_count = int(mt_leg.group(1))
    return RestoreHistoryOut(
        id=r.id,
        backup_file_id=r.backup_file_id,
        filename=fn,
        target_database=r.target_database,
        description=r.description,
        backup_description=b_desc,
        started_at=format_dt(r.started_at) or "",
        finished_at=format_dt(r.finished_at),
        duration_str=format_duration(r.started_at, r.finished_at),
        status=r.status,
        message=r.message,
        user_name=r.usuario.nombre if r.usuario else "Sistema",
        table_count=t_count,
        estudiantes_count=e_count,
        matriculas_count=m_count
    )

# ==================== 3.1. RECUPERACIÓN SELECTIVA DE DATOS DESDE BASE RESTAURADA ====================

@router.get("/restores/{id}/preview-recovery", response_model=RecoveryPreviewOut)
def previsualizar_recuperacion_restauracion(
    id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_admin)
):
    """
    Inspecciona la base de datos de prueba restaurada y compara contra la base principal portal_academico,
    identificando registros faltantes o eliminados listos para recuperar selectivamente.
    """
    return preview_recovery_data(db, restore_id=id)

@router.post("/restores/{id}/recover-matricula")
def recuperar_matricula_endpoint(
    id: int,
    data: RecoverMatriculaIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_admin)
):
    """
    Copia selectivamente una matrícula (y sus notas asociadas) desde la base de prueba hacia la base
    principal portal_academico, sin duplicar registros existentes ni sobrescribir toda la base.
    """
    return recover_matricula_data(db, restore_id=id, matricula_id=data.matricula_id, user_id=user.id)

# ==================== 4. LISTADO Y CREACIÓN DE BACKUPS ====================

@router.get("", response_model=list[BackupFileOut])
def listar_backups(
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_admin_or_supervisor)
):
    backups = db.query(BackupFile).order_by(desc(BackupFile.created_at)).all()
    resultado = []
    for b in backups:
        resultado.append(BackupFileOut(
            id=b.id,
            filename=b.filename,
            description=b.description,
            size_bytes=b.size_bytes,
            size_formatted=format_size(b.size_bytes),
            backup_type=b.backup_type,
            status=b.status,
            created_at=format_dt(b.created_at) or "",
            created_by_name=b.usuario.nombre if b.usuario else "Sistema",
            retention_deleted_at=format_dt(b.retention_deleted_at),
            retention_reason=b.retention_reason
        ))
    return resultado

@router.post("", response_model=BackupFileOut)
def crear_backup_manual(
    data: BackupCreateIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_admin)
):
    if not data or not data.description or not data.description.strip():
        raise HTTPException(status_code=422, detail="El nombre de la copia es obligatorio")
    backup_file = crear_backup(db, user_id=user.id, trigger="MANUAL", description=data.description.strip())
    return BackupFileOut(
        id=backup_file.id,
        filename=backup_file.filename,
        description=backup_file.description,
        size_bytes=backup_file.size_bytes,
        size_formatted=format_size(backup_file.size_bytes),
        backup_type=backup_file.backup_type,
        status=backup_file.status,
        created_at=format_dt(backup_file.created_at) or "",
        created_by_name=user.nombre,
        retention_deleted_at=None,
        retention_reason=None
    )

# ==================== 5. EXPLORADOR DE ARCHIVOS EN DISCO (BACKUP_DIR) ====================

@router.get("/files", response_model=list[BackupFileOnDiskOut])
def explorador_archivos_disco(
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_admin)
):
    """
    Escanea el BACKUP_DIR real en disco y cruza con la base de datos.
    Detecta archivos huérfanos (en disco pero sin registro en BD).
    Compatible con BACKUP_DIR local o montado en la nube (Docker volume, NFS, etc.).
    """
    from pathlib import Path
    from ..services.backup_service import get_backup_dir, format_size

    backup_dir = get_backup_dir()
    tz = get_timezone()

    # Obtener todos los registros de BD indexados por filename
    db_records = {b.filename: b for b in db.query(BackupFile).all()}

    resultado = []

    # Escanear todos los archivos .backup en el directorio
    try:
        archivos_disco = sorted(
            backup_dir.glob("*.backup"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
    except Exception:
        archivos_disco = []

    for archivo in archivos_disco:
        try:
            stat = archivo.stat()
            size_bytes = stat.st_size
            # Fecha de modificación del archivo físico en zona horaria local
            mod_dt = datetime.fromtimestamp(stat.st_mtime, tz=tz)
            modified_at = mod_dt.strftime("%d/%m/%Y %H:%M:%S")

            db_record = db_records.get(archivo.name)

            if db_record:
                created_by_name = db_record.usuario.nombre if db_record.usuario else "Sistema"
                resultado.append(BackupFileOnDiskOut(
                    filename=archivo.name,
                    size_bytes=size_bytes,
                    size_formatted=format_size(size_bytes),
                    modified_at=modified_at,
                    db_id=db_record.id,
                    db_status=db_record.status,
                    db_type=db_record.backup_type,
                    db_created_by=created_by_name,
                    db_description=db_record.description,
                    is_orphan=False
                ))
            else:
                # Archivo en disco sin registro en BD (huérfano)
                resultado.append(BackupFileOnDiskOut(
                    filename=archivo.name,
                    size_bytes=size_bytes,
                    size_formatted=format_size(size_bytes),
                    modified_at=modified_at,
                    db_id=None,
                    db_status=None,
                    db_type=None,
                    db_created_by=None,
                    db_description=None,
                    is_orphan=True
                ))
        except Exception:
            continue

    return resultado

# ==================== 6. RUTAS PARAMETRIZADAS (/{id}) ====================


@router.get("/{id}")
def ver_detalle_backup(
    id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_admin_or_supervisor)
):
    b = db.get(BackupFile, id)
    if not b:
        raise HTTPException(404, "Copia de seguridad no encontrada")

    hist = db.query(BackupHistory).filter(BackupHistory.backup_file_id == b.id).order_by(desc(BackupHistory.started_at)).first()
    duracion = format_duration(hist.started_at, hist.finished_at) if hist else "--"
    started_at = format_dt(hist.started_at) if (hist and hist.started_at) else format_dt(b.created_at)
    finished_at = format_dt(hist.finished_at) if (hist and hist.finished_at) else (format_dt(b.created_at) if b.status == "CORRECTO" else "--")

    return {
        "id": b.id,
        "filename": b.filename,
        "description": b.description,
        "path": b.path,
        "size_bytes": b.size_bytes,
        "size_formatted": format_size(b.size_bytes),
        "backup_type": b.backup_type or (hist.trigger if hist else "MANUAL"),
        "status": b.status,
        "created_at": format_dt(b.created_at),
        "started_at": started_at,
        "finished_at": finished_at,
        "usuario": b.usuario.nombre if b.usuario else "Sistema",
        "duracion": duracion,
        "mensaje": hist.message if hist else "Generado correctamente",
        "retention_deleted_at": format_dt(b.retention_deleted_at),
        "retention_reason": b.retention_reason
    }

@router.get("/{id}/download")
def descargar_backup(
    id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_admin_download)
):
    file_path, filename = obtener_archivo_para_descarga(db, id)
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.post("/{id}/restore")
def restaurar_backup_endpoint(
    id: int,
    data: RestoreCreateIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_admin)
):
    if not data or not data.description or not data.description.strip():
        raise HTTPException(status_code=422, detail="El nombre de la restauración es obligatorio")
    resultado = restaurar_backup_prueba(
        db=db,
        backup_id=id,
        target_db=data.target_database,
        description=data.description.strip(),
        user_id=user.id,
        overwrite_existing=data.overwrite_existing
    )
    return resultado

@router.delete("/{id}")
def eliminar_backup_endpoint(
    id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(require_admin)
):
    eliminar_backup(db, id, user_id=user.id)
    return {"ok": True, "message": "Copia de seguridad eliminada exitosamente del almacenamiento y registro"}
