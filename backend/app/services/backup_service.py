import os
import re
import glob
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.engine.url import make_url
from fastapi import HTTPException

from ..database import DATABASE_URL, engine
from ..models import BackupFile, BackupSchedule, BackupHistory, RestoreHistory, Usuario

def get_timezone() -> ZoneInfo:
    tz_str = os.getenv("BACKUP_TIMEZONE", "America/Lima")
    try:
        return ZoneInfo(tz_str)
    except Exception:
        return ZoneInfo("America/Lima")

def get_backup_dir() -> Path:
    backup_dir_str = os.getenv("BACKUP_DIR", "storage/backups")
    backup_dir_path = Path(backup_dir_str)
    if not backup_dir_path.is_absolute():
        # d:\portal_academico_php_fastapi_postgres\backend
        base_dir = Path(__file__).resolve().parent.parent.parent
        backup_dir_path = base_dir / backup_dir_path

    backup_dir_path.mkdir(parents=True, exist_ok=True)
    return backup_dir_path

def get_pg_tool_path(tool_name: str) -> str | None:
    """
    Detecta la ruta del ejecutable pg_dump o pg_restore:
    1. Variable de entorno (PG_DUMP_PATH / PG_RESTORE_PATH)
    2. PATH del sistema
    3. Rutas estándar de PostgreSQL en Windows
    """
    env_var_name = f"{tool_name.upper()}_PATH"
    custom_path = os.getenv(env_var_name, "").strip()
    if custom_path and Path(custom_path).exists():
        return str(Path(custom_path).resolve())

    # Búsqueda en rutas conocidas de Linux (Debian / Ubuntu / PGDG)
    for pattern in ["/usr/lib/postgresql/*/bin", "/usr/local/bin"]:
        for bin_dir in sorted(glob.glob(pattern), reverse=True):
            candidate = Path(bin_dir) / tool_name
            if candidate.exists() and os.access(candidate, os.X_OK):
                return str(candidate.resolve())

    # Búsqueda en PATH
    in_path = shutil.which(tool_name) or shutil.which(f"{tool_name}.exe")
    if in_path:
        return str(Path(in_path).resolve())

    # Búsqueda en rutas conocidas de Windows
    windows_search_patterns = [
        r"D:\Program Files\PostgreSQL\*\bin",
        r"C:\Program Files\PostgreSQL\*\bin",
        r"C:\Program Files (x86)\PostgreSQL\*\bin",
        r"D:\PostgreSQL\*\bin",
        r"C:\PostgreSQL\*\bin",
    ]
    for pattern in windows_search_patterns:
        for bin_dir in glob.glob(pattern):
            candidate = Path(bin_dir) / f"{tool_name}.exe"
            if candidate.exists():
                return str(candidate.resolve())

    return None

def format_size(bytes_num: int) -> str:
    if bytes_num < 1024:
        return f"{bytes_num} B"
    elif bytes_num < 1024 * 1024:
        return f"{bytes_num / 1024:.2f} KB"
    elif bytes_num < 1024 * 1024 * 1024:
        return f"{bytes_num / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_num / (1024 * 1024 * 1024):.2f} GB"

def sanitize_error(msg: str, password: str | None) -> str:
    if not msg:
        return ""
    if password:
        msg = msg.replace(password, "******")
    return msg.strip()

def check_backup_health(db: Session) -> dict:
    pg_dump_path = get_pg_tool_path("pg_dump")
    pg_restore_path = get_pg_tool_path("pg_restore")
    backup_dir = get_backup_dir()

    # Comprobar escritura en BACKUP_DIR
    dir_writable = False
    try:
        test_file = backup_dir / ".health_check_test.tmp"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        dir_writable = True
    except Exception:
        dir_writable = False

    # Comprobar base de datos
    db_connected = False
    try:
        db.execute(text("SELECT 1")).scalar()
        db_connected = True
    except Exception:
        db_connected = False

    is_operational = bool(pg_dump_path and pg_restore_path and dir_writable and db_connected)

    message = "Sistema de backups: Operativo"
    if not is_operational:
        reasons = []
        if not pg_dump_path:
            reasons.append("No se encontró pg_dump. Configure PG_DUMP_PATH en .env")
        if not pg_restore_path:
            reasons.append("No se encontró pg_restore. Configure PG_RESTORE_PATH en .env")
        if not dir_writable:
            reasons.append(f"El directorio {backup_dir} no tiene permisos de escritura")
        if not db_connected:
            reasons.append("No se pudo establecer conexión con PostgreSQL")
        message = "Configuración incompleta: " + " | ".join(reasons)

    return {
        "pg_dump_found": bool(pg_dump_path),
        "pg_dump_path": pg_dump_path,
        "pg_restore_found": bool(pg_restore_path),
        "pg_restore_path": pg_restore_path,
        "backup_dir_writable": dir_writable,
        "backup_dir_path": str(backup_dir),
        "database_connected": db_connected,
        "is_operational": is_operational,
        "message": message
    }

# ==================== CLONACIÓN DE ESQUEMAS DE RESPALDO EN POSTGRESQL ====================

def clonar_esquema_backup(db: Session, schema_name: str) -> dict:
    """
    Clona todas las tablas académicas y del dominio desde el esquema 'public'
    hacia un esquema de respaldo aislado dentro de PostgreSQL (ej: 'backup_20260917_195500').
    Esto permite que el docente, administrador o evaluador pueda ver y consultar
    directamente los datos respaldados en la base de datos de Render vía PSQL / pgAdmin / DBeaver.
    """
    tablas_excluidas = {"backup_files", "backup_history", "backup_schedules", "restore_history"}
    tablas_clonadas = 0

    try:
        # 1. Crear el esquema aislado
        db.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
        db.commit()

        # 2. Listar tablas reales en public
        res = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_type = 'BASE TABLE'
        """)).fetchall()
        tablas = [r[0] for r in res if r[0] not in tablas_excluidas]

        # 3. Clonar cada tabla usando AS TABLE (copia exacta de estructura y datos)
        for tbl in tablas:
            try:
                db.execute(text(f'DROP TABLE IF EXISTS "{schema_name}"."{tbl}" CASCADE'))
                db.execute(text(f'CREATE TABLE "{schema_name}"."{tbl}" AS TABLE public."{tbl}"'))
                db.commit()
                tablas_clonadas += 1
            except Exception as ex_tbl:
                db.rollback()
                print(f"[BACKUP-SCHEMA] Advertencia al clonar tabla {tbl} en {schema_name}: {ex_tbl}")

    except Exception as ex:
        db.rollback()
        print(f"[BACKUP-SCHEMA] Error general al clonar esquema {schema_name}: {ex}")

    return {
        "schema_name": schema_name,
        "tablas_clonadas": tablas_clonadas
    }

def eliminar_esquema_backup(db: Session, schema_name: str | None):
    """
    Elimina un esquema de respaldo en PostgreSQL si existe.
    """
    if not schema_name or not schema_name.startswith("backup_"):
        return
    try:
        db.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
        db.commit()
    except Exception as ex:
        db.rollback()
        print(f"[BACKUP-SCHEMA] Advertencia al eliminar esquema {schema_name}: {ex}")

# Identificador constante para PostgreSQL Advisory Lock al ejecutar un backup
BACKUP_EXECUTION_LOCK_ID = 88812346

def crear_backup(
    db: Session,
    user_id: int | None = None,
    trigger: str = "MANUAL",
    schedule_id: int | None = None,
    description: str | None = None
) -> BackupFile:
    """
    Genera un respaldo real con pg_dump en formato Custom (-F c).
    Verifica que el archivo exista, tenga tamaño > 0 y sea legible con pg_restore --list.
    Evita estrictamente que se ejecuten 2 backups simultáneos mediante un Advisory Lock en conexión dedicada.
    """
    # 1. Prevenir colisión: Solo 1 backup en ejecución a la vez
    with engine.connect() as lock_conn:
        got_lock = lock_conn.execute(
            text("SELECT pg_try_advisory_lock(:lock_id)"),
            {"lock_id": BACKUP_EXECUTION_LOCK_ID}
        ).scalar()

        if not got_lock:
            raise HTTPException(
                status_code=409,
                detail="Ya existe otra operación de copia de seguridad en ejecución. Por favor espere a que concluya."
            )

        try:
            return _ejecutar_crear_backup_proceso(db, user_id, trigger, schedule_id, description)
        finally:
            try:
                lock_conn.execute(
                    text("SELECT pg_advisory_unlock(:lock_id)"),
                    {"lock_id": BACKUP_EXECUTION_LOCK_ID}
                )
            except Exception:
                pass

def _ejecutar_crear_backup_proceso(
    db: Session,
    user_id: int | None = None,
    trigger: str = "MANUAL",
    schedule_id: int | None = None,
    description: str | None = None
) -> BackupFile:
    pg_dump_path = get_pg_tool_path("pg_dump")
    if not pg_dump_path:
        raise HTTPException(500, "No se encontró pg_dump en el servidor. Configure PG_DUMP_PATH en backend/.env")

    pg_restore_path = get_pg_tool_path("pg_restore")
    backup_dir = get_backup_dir()
    tz = get_timezone()
    now_local = datetime.now(tz)
    now_utc = datetime.utcnow()

    filename = f"portal_academico_{now_local.strftime('%Y%m%d_%H%M%S')}.backup"
    schema_name = f"backup_{now_local.strftime('%Y%m%d_%H%M%S')}"
    output_path = backup_dir / filename

    # Registrar en historial con estado EN_PROCESO
    history_entry = BackupHistory(
        schedule_id=schedule_id,
        started_at=now_utc,
        status="EN_PROCESO",
        trigger=trigger,
        created_by=user_id
    )
    db.add(history_entry)
    db.commit()
    db.refresh(history_entry)

    url = make_url(DATABASE_URL)
    env = os.environ.copy()
    if url.password:
        env["PGPASSWORD"] = url.password
    if "sslmode" in url.query:
        env["PGSSLMODE"] = url.query["sslmode"]
    elif url.host and url.host not in ("localhost", "127.0.0.1"):
        env["PGSSLMODE"] = "require"

    cmd = [
        pg_dump_path,
        "-h", url.host or "localhost",
        "-p", str(url.port or 5432),
        "-U", url.username or "postgres",
        "-w",
        "-F", "c",
        "-b",
        "-v",
        "-f", str(output_path),
        url.database or "portal_academico"
    ]

    try:
        proc = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=300
        )
    except subprocess.TimeoutExpired:
        if output_path.exists():
            output_path.unlink()
        history_entry.status = "ERROR"
        history_entry.finished_at = datetime.utcnow()
        history_entry.message = "Tiempo de espera agotado al generar la copia de seguridad (>300s)."
        db.commit()
        raise HTTPException(500, history_entry.message)
    except Exception as e:
        if output_path.exists():
            output_path.unlink()
        history_entry.status = "ERROR"
        history_entry.finished_at = datetime.utcnow()
        history_entry.message = sanitize_error(str(e), url.password)
        db.commit()
        raise HTTPException(500, f"Error al ejecutar pg_dump: {history_entry.message}")

    stderr_clean = sanitize_error(proc.stderr, url.password)

    # 1. Comprobar código de retorno
    if proc.returncode != 0:
        if output_path.exists():
            output_path.unlink()
        history_entry.status = "ERROR"
        history_entry.finished_at = datetime.utcnow()
        history_entry.message = f"pg_dump falló con código {proc.returncode}. {stderr_clean}"
        db.commit()
        raise HTTPException(500, f"Error al crear el backup: {history_entry.message}")

    # 2. Comprobar existencia y tamaño
    if not output_path.exists() or output_path.stat().st_size == 0:
        if output_path.exists():
            output_path.unlink()
        history_entry.status = "ERROR"
        history_entry.finished_at = datetime.utcnow()
        history_entry.message = "El archivo de respaldo no fue generado o tiene tamaño 0 bytes."
        db.commit()
        raise HTTPException(500, history_entry.message)

    file_size = output_path.stat().st_size

    # 3. Comprobar integridad con pg_restore --list
    if pg_restore_path:
        check_proc = subprocess.run(
            [pg_restore_path, "--list", str(output_path)],
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        if check_proc.returncode != 0:
            output_path.unlink()
            history_entry.status = "ERROR"
            history_entry.finished_at = datetime.utcnow()
            history_entry.message = "El archivo generado no superó la prueba de integridad de archivo de PostgreSQL."
            db.commit()
            raise HTTPException(500, history_entry.message)

    # Clonar esquema de respaldo directamente en PostgreSQL (Render / Local)
    clon_res = clonar_esquema_backup(db, schema_name)

    # Registrar el archivo en backup_files
    backup_file = BackupFile(
        filename=filename,
        description=description.strip() if (description and description.strip()) else None,
        schema_name=schema_name,
        path=str(output_path),
        size_bytes=file_size,
        backup_type=trigger,
        status="CORRECTO",
        created_at=now_utc,
        created_by=user_id
    )
    db.add(backup_file)
    db.commit()
    db.refresh(backup_file)

    # Actualizar historial
    history_entry.backup_file_id = backup_file.id
    history_entry.finished_at = datetime.utcnow()
    history_entry.status = "CORRECTO"
    history_entry.message = f"Copia de seguridad creada con éxito. Tamaño: {format_size(file_size)}. Esquema en PostgreSQL: {schema_name} ({clon_res.get('tablas_clonadas', 0)} tablas clonadas)."
    db.commit()

    # Si fue generado por programación, verificar política de retención
    if schedule_id:
        schedule = db.get(BackupSchedule, schedule_id)
        if schedule:
            schedule.last_run_at = now_utc
            db.commit()
            aplicar_retencion(db, schedule)

    return backup_file

def aplicar_retencion(db: Session, schedule: BackupSchedule):
    """
    Elimina físicamente los respaldos que excedan la retención en días,
    pero PRESERVA el registro histórico marcándolo como ELIMINADO_RETENCION.
    """
    if schedule.retention_days <= 0:
        return

    limite = datetime.utcnow() - timedelta(days=schedule.retention_days)

    # Buscar archivos generados por esta programación anteriores al límite
    hist_entries = db.query(BackupHistory).filter(
        BackupHistory.schedule_id == schedule.id,
        BackupHistory.started_at < limite,
        BackupHistory.backup_file_id.isnot(None)
    ).all()

    for h in hist_entries:
        if not h.backup_file_id:
            continue
        bf = db.get(BackupFile, h.backup_file_id)
        if bf and bf.status == "CORRECTO":
            fpath = Path(bf.path)
            try:
                if fpath.exists():
                    fpath.unlink()
            except Exception:
                pass
            if bf.schema_name:
                eliminar_esquema_backup(db, bf.schema_name)
            bf.status = "ELIMINADO_RETENCION"
            bf.retention_deleted_at = datetime.utcnow()
            bf.retention_reason = f"Eliminado automáticamente por política de retención de {schedule.retention_days} días."

    db.commit()

def obtener_archivo_para_descarga(db: Session, backup_id: int) -> tuple[Path, str]:
    """
    Valida que el archivo exista en la base de datos y evita ataques de Path Traversal.
    """
    backup = db.get(BackupFile, backup_id)
    if not backup:
        raise HTTPException(404, "Copia de seguridad no encontrada")
    if backup.status != "CORRECTO":
        raise HTTPException(400, f"El archivo no se encuentra disponible (Estado: {backup.status})")

    file_path = Path(backup.path).resolve()
    base_dir = get_backup_dir().resolve()

    # Verificación estricta contra Path Traversal
    try:
        file_path.relative_to(base_dir)
    except ValueError:
        raise HTTPException(403, "Acceso no autorizado a la ruta del archivo")

    if not file_path.exists():
        raise HTTPException(404, "El archivo físico ya no existe en el almacenamiento")

    return file_path, backup.filename

def eliminar_backup(db: Session, backup_id: int, user_id: int | None = None) -> bool:
    """
    Elimina el archivo físico de disco de forma segura y actualiza el registro.
    """
    backup = db.get(BackupFile, backup_id)
    if not backup:
        raise HTTPException(404, "Copia de seguridad no encontrada")

    # 1. NO permitir eliminar si se encuentra en proceso de restauración
    restoring = db.query(RestoreHistory).filter(
        RestoreHistory.backup_file_id == backup.id,
        RestoreHistory.status == "EN_PROCESO"
    ).first()
    if restoring:
        raise HTTPException(400, "No se puede eliminar la copia de seguridad porque se encuentra actualmente en proceso de restauración.")

    # 2. NO permitir eliminar si está en proceso de creación/generación
    if backup.status == "EN_PROCESO":
        raise HTTPException(400, "No se puede eliminar una copia de seguridad que se encuentra en proceso de generación.")

    in_progress = db.query(BackupHistory).filter(
        BackupHistory.backup_file_id == backup.id,
        BackupHistory.status == "EN_PROCESO"
    ).first()
    if in_progress:
        raise HTTPException(400, "No se puede eliminar una copia de seguridad cuya generación aún no ha concluido.")

    # 3. NO permitir eliminar el último backup válido existente en el sistema
    valid_count = db.query(BackupFile).filter(
        BackupFile.status == "CORRECTO",
        BackupFile.id != backup.id
    ).count()
    if backup.status == "CORRECTO" and valid_count == 0:
        raise HTTPException(400, "Política de seguridad: No se puede eliminar la única copia de seguridad válida existente en el sistema.")

    file_path = Path(backup.path).resolve()
    base_dir = get_backup_dir().resolve()

    try:
        file_path.relative_to(base_dir)
    except ValueError:
        raise HTTPException(403, "Acceso no autorizado a la ruta del archivo")

    if file_path.exists():
        file_path.unlink()

    # Eliminar esquema clonado en PostgreSQL si existe
    if backup.schema_name:
        eliminar_esquema_backup(db, backup.schema_name)

    # Eliminar registro en base de datos (cascade mantiene historial con backup_file_id=NULL)
    db.delete(backup)
    db.commit()
    return True

def restaurar_backup_prueba(
    db: Session,
    backup_id: int,
    target_db: str,
    user_id: int | None = None,
    description: str | None = None,
    overwrite_existing: bool = False
) -> dict:
    """
    Restaura una copia de seguridad como BASE DE DATOS DE PRUEBA.
    Evita SQL Injection, prohíbe terminantemente restaurar o eliminar la base de producción portal_academico,
    ofrece resolución de nombres si la base ya existe, ejecuta pg_restore y registra la bitácora con conteo de registros.
    """
    # 1. Normalización y validación de seguridad en el nombre de la base de datos
    target_db = target_db.strip().lower()
    if not re.match(r"^[a-z0-9_]+$", target_db):
        raise HTTPException(400, "Nombre de base de datos inválido. Solo se permiten letras minúsculas, números y guión bajo.")

    url = make_url(DATABASE_URL)
    prod_db_name = (url.database or "portal_academico").lower()
    forbidden_dbs = {prod_db_name, "portal_academico", "postgres", "template0", "template1"}

    if target_db in forbidden_dbs:
        raise HTTPException(
            400,
            "Por seguridad, está terminantemente prohibido restaurar directamente o sobrescribir la base principal 'portal_academico' o bases del sistema."
        )

    backup = db.get(BackupFile, backup_id)
    if not backup:
        raise HTTPException(404, "Copia de seguridad no encontrada")

    file_path = Path(backup.path).resolve()
    base_dir = get_backup_dir().resolve()

    try:
        file_path.relative_to(base_dir)
    except ValueError:
        raise HTTPException(403, "Ruta de archivo no autorizada")

    if not file_path.exists():
        raise HTTPException(404, "El archivo de respaldo no existe en el disco")

    pg_restore_path = get_pg_tool_path("pg_restore")
    if not pg_restore_path:
        raise HTTPException(500, "No se encontró pg_restore en el servidor. Configure PG_RESTORE_PATH en backend/.env")

    # 2. Comprobar si la base de destino ya existe en PostgreSQL
    db_exists = db.execute(text("SELECT 1 FROM pg_database WHERE datname = :target"), {"target": target_db}).scalar()
    if db_exists:
        if not overwrite_existing:
            # Generar sugerencia automática de nombre (ej: target_db_2, target_db_3)
            base_prefix = re.sub(r'_\d+$', '', target_db)
            num = 2
            suggested = f"{base_prefix}_{num}"
            while db.execute(text("SELECT 1 FROM pg_database WHERE datname = :target"), {"target": suggested}).scalar():
                num += 1
                suggested = f"{base_prefix}_{num}"

            raise HTTPException(
                status_code=409,
                detail={
                    "code": "DATABASE_EXISTS",
                    "message": f"La base de datos de prueba '{target_db}' ya existe en el servidor PostgreSQL.",
                    "target_database": target_db,
                    "suggested_database": suggested
                }
            )
        else:
            # Eliminar de forma segura ÚNICAMENTE la base de prueba previa
            if target_db in forbidden_dbs:
                raise HTTPException(400, "Prohibido eliminar o sobrescribir la base de producción 'portal_academico'.")
            limpiar_db(target_db)

    # Iniciar registro en restore_history
    now_utc = datetime.utcnow()
    restore_entry = RestoreHistory(
        backup_file_id=backup.id,
        target_database=target_db,
        description=description.strip() if (description and description.strip()) else None,
        started_at=now_utc,
        status="EN_PROCESO",
        created_by=user_id
    )
    db.add(restore_entry)
    db.commit()
    db.refresh(restore_entry)

    # 3. Crear la base de datos destino con conexión AUTOCOMMIT
    maint_url = url.set(database="postgres")
    from sqlalchemy import create_engine
    maint_engine = create_engine(maint_url, isolation_level="AUTOCOMMIT")

    try:
        with maint_engine.connect() as mconn:
            mconn.execute(text(f'CREATE DATABASE "{target_db}" WITH ENCODING = \'UTF8\''))
    except Exception as e:
        restore_entry.status = "ERROR"
        restore_entry.finished_at = datetime.utcnow()
        restore_entry.message = sanitize_error(f"Fallo al crear la base de datos destino: {e}", url.password)
        db.commit()
        raise HTTPException(500, restore_entry.message)
    finally:
        maint_engine.dispose()

    # 4. Ejecutar pg_restore
    env = os.environ.copy()
    if url.password:
        env["PGPASSWORD"] = url.password
    if "sslmode" in url.query:
        env["PGSSLMODE"] = url.query["sslmode"]
    elif url.host and url.host not in ("localhost", "127.0.0.1"):
        env["PGSSLMODE"] = "require"

    cmd = [
        pg_restore_path,
        "-h", url.host or "localhost",
        "-p", str(url.port or 5432),
        "-U", url.username or "postgres",
        "-w",
        "-d", target_db,
        "-v",
        str(file_path)
    ]

    try:
        proc = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=300
        )
    except subprocess.TimeoutExpired:
        limpiar_db(target_db)
        restore_entry.status = "ERROR"
        restore_entry.finished_at = datetime.utcnow()
        restore_entry.message = "Tiempo de espera agotado al restaurar la base de prueba (>300s)."
        db.commit()
        raise HTTPException(500, restore_entry.message)
    except Exception as e:
        limpiar_db(target_db)
        restore_entry.status = "ERROR"
        restore_entry.finished_at = datetime.utcnow()
        restore_entry.message = sanitize_error(str(e), url.password)
        db.commit()
        raise HTTPException(500, f"Error al ejecutar pg_restore: {restore_entry.message}")

    stderr_clean = sanitize_error(proc.stderr, url.password)

    # pg_restore retorna 0 en éxito, y 1 en advertencias menores (warnings de permisos/roles)
    if proc.returncode > 1:
        limpiar_db(target_db)
        restore_entry.status = "ERROR"
        restore_entry.finished_at = datetime.utcnow()
        restore_entry.message = f"pg_restore falló con código {proc.returncode}. {stderr_clean}"
        db.commit()
        raise HTTPException(500, f"Error al restaurar: {restore_entry.message}")

    # 5. Verificar que existan tablas y contar registros reales
    restored_url = url.set(database=target_db)
    rest_engine = create_engine(restored_url)
    table_count = 0
    estudiantes_count = 0
    matriculas_count = 0
    total_registros = 0
    try:
        with rest_engine.connect() as rconn:
            table_count = rconn.execute(text(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
            )).scalar() or 0

            has_est = rconn.execute(text(
                "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'estudiantes'"
            )).scalar()
            if has_est:
                estudiantes_count = rconn.execute(text("SELECT count(*) FROM estudiantes")).scalar() or 0

            has_mat = rconn.execute(text(
                "SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'matriculas'"
            )).scalar()
            if has_mat:
                matriculas_count = rconn.execute(text("SELECT count(*) FROM matriculas")).scalar() or 0

            all_tables = rconn.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
            )).scalars().all()
            for tname in all_tables:
                try:
                    c = rconn.execute(text(f'SELECT count(*) FROM "{tname}"')).scalar() or 0
                    total_registros += c
                except Exception:
                    pass
    except Exception as e:
        stderr_clean += f" (Advertencia al verificar registros: {e})"
    finally:
        rest_engine.dispose()

    restore_entry.finished_at = datetime.utcnow()
    restore_entry.status = "CORRECTO"
    restore_entry.message = (
        f"Restauración verificada con éxito como base de prueba '{target_db}'. "
        f"Tablas: {table_count}, Estudiantes: {estudiantes_count}, Matrículas: {matriculas_count}, Total registros: {total_registros}."
    )
    db.commit()

    return {
        "ok": True,
        "restore_id": restore_entry.id,
        "message": restore_entry.message,
        "target_database": target_db,
        "table_count": table_count,
        "estudiantes_count": estudiantes_count,
        "matriculas_count": matriculas_count,
        "total_registros": total_registros,
        "backup_filename": backup.filename
    }

def limpiar_db(target_db: str):
    """Limpia de forma segura una base de prueba fallida o temporal."""
    try:
        url = make_url(DATABASE_URL)
        maint_url = url.set(database="postgres")
        from sqlalchemy import create_engine
        maint_engine = create_engine(maint_url, isolation_level="AUTOCOMMIT")
        with maint_engine.connect() as mconn:
            mconn.execute(text(f'DROP DATABASE IF EXISTS "{target_db}" WITH (FORCE)'))
        maint_engine.dispose()
    except Exception:
        pass

# ==================== RECUPERACIÓN DE DATOS SELECTIVA ====================

def preview_recovery_data(db: Session, restore_id: int) -> dict:
    restore = db.get(RestoreHistory, restore_id)
    if not restore:
        raise HTTPException(404, "Registro de restauración no encontrado")
    if restore.status != "CORRECTO":
        raise HTTPException(400, "Solo se pueden recuperar datos de una base de prueba con estado CORRECTO")

    url = make_url(DATABASE_URL)
    # Comprobar si la base destino existe en PostgreSQL
    db_exists = db.execute(
        text("SELECT 1 FROM pg_database WHERE datname = :target"),
        {"target": restore.target_database}
    ).scalar()
    if not db_exists:
        raise HTTPException(400, f"La base de datos de prueba '{restore.target_database}' no existe en PostgreSQL. Ejecute una nueva prueba de restauración.")

    from sqlalchemy import create_engine
    target_url = url.set(database=restore.target_database)
    test_engine = create_engine(target_url)

    matriculas_recuperables = []
    matriculas_existentes = []
    test_rows = []

    try:
        with test_engine.connect() as tconn:
            # Comprobar si existe la tabla matriculas en la base de prueba
            has_table = tconn.execute(
                text("SELECT 1 FROM information_schema.tables WHERE table_name = 'matriculas' AND table_schema = 'public'")
            ).scalar()
            if not has_table:
                return {
                    "restore_id": restore.id,
                    "target_database": restore.target_database,
                    "description": restore.description,
                    "total_matriculas_en_prueba": 0,
                    "matriculas_recuperables": [],
                    "matriculas_existentes": [],
                    "message": "La base restaurada no contiene la tabla de matrículas."
                }

            query_test = text("""
                SELECT 
                    m.id AS id_en_prueba,
                    m.estudiante_id,
                    COALESCE(e.codigo, 'SIN-COD') AS est_codigo,
                    COALESCE(e.nombres, 'Sin Nombre') AS est_nombres,
                    COALESCE(e.apellidos, 'Sin Apellidos') AS est_apellidos,
                    e.dni AS est_dni,
                    e.correo AS est_correo,
                    e.carrera AS est_carrera,
                    e.ciclo AS est_ciclo,
                    m.curso_id,
                    COALESCE(c.codigo, 'CUR-00') AS cur_codigo,
                    COALESCE(c.nombre, 'Asignatura') AS cur_nombre,
                    m.periodo,
                    m.estado,
                    m.nota
                FROM matriculas m
                LEFT JOIN estudiantes e ON e.id = m.estudiante_id
                LEFT JOIN cursos c ON c.id = m.curso_id
                ORDER BY m.id ASC
            """)
            test_rows = tconn.execute(query_test).mappings().all()

        from .. import models
        for r in test_rows:
            item = {
                "id_en_prueba": r["id_en_prueba"],
                "estudiante_id": r["estudiante_id"],
                "estudiante_codigo": r["est_codigo"],
                "estudiante_nombres": r["est_nombres"],
                "estudiante_apellidos": r["est_apellidos"],
                "curso_id": r["curso_id"],
                "curso_codigo": r["cur_codigo"],
                "curso_nombre": r["cur_nombre"],
                "periodo": r["periodo"],
                "estado": r["estado"] or "MATRICULADO",
                "nota": float(r["nota"]) if r["nota"] is not None else None
            }

            # Validar si existe en la base principal (comparando por estudiante, curso y periodo)
            main_match = db.query(models.Matricula).join(models.Estudiante).join(models.Curso).filter(
                models.Estudiante.codigo == r["est_codigo"],
                models.Curso.codigo == r["cur_codigo"],
                models.Matricula.periodo == r["periodo"]
            ).first()

            if main_match:
                item["existe_en_principal"] = True
                matriculas_existentes.append(item)
            else:
                item["existe_en_principal"] = False
                matriculas_recuperables.append(item)

    except Exception as e:
        raise HTTPException(500, f"Error al inspeccionar la base de prueba: {e}")
    finally:
        test_engine.dispose()

    return {
        "restore_id": restore.id,
        "target_database": restore.target_database,
        "description": restore.description,
        "total_matriculas_en_prueba": len(test_rows),
        "matriculas_recuperables": matriculas_recuperables,
        "matriculas_existentes": matriculas_existentes,
        "message": f"Se encontraron {len(matriculas_recuperables)} matrículas ausentes/eliminadas listas para recuperar."
    }

def recover_matricula_data(db: Session, restore_id: int, matricula_id: int, user_id: int | None = None) -> dict:
    from datetime import date
    from .. import models
    from ..auth import pwd_context

    restore = db.get(RestoreHistory, restore_id)
    if not restore:
        raise HTTPException(404, "Registro de restauración no encontrado")
    if restore.status != "CORRECTO":
        raise HTTPException(400, "Solo se pueden recuperar datos de una base de prueba con estado CORRECTO")

    url = make_url(DATABASE_URL)
    db_exists = db.execute(
        text("SELECT 1 FROM pg_database WHERE datname = :target"),
        {"target": restore.target_database}
    ).scalar()
    if not db_exists:
        raise HTTPException(400, f"La base de prueba '{restore.target_database}' no existe en PostgreSQL.")

    from sqlalchemy import create_engine
    target_url = url.set(database=restore.target_database)
    test_engine = create_engine(target_url)

    try:
        with test_engine.connect() as tconn:
            query = text("""
                SELECT 
                    m.id AS id_en_prueba,
                    m.estudiante_id,
                    e.codigo AS est_codigo,
                    e.nombres AS est_nombres,
                    e.apellidos AS est_apellidos,
                    e.dni AS est_dni,
                    e.correo AS est_correo,
                    e.carrera AS est_carrera,
                    e.ciclo AS est_ciclo,
                    e.fecha_ingreso AS est_fecha_ingreso,
                    e.telefono AS est_telefono,
                    e.direccion AS est_direccion,
                    m.curso_id,
                    c.codigo AS cur_codigo,
                    c.nombre AS cur_nombre,
                    c.creditos AS cur_creditos,
                    c.docente AS cur_docente,
                    c.ciclo AS cur_ciclo,
                    m.periodo,
                    m.estado,
                    m.nota
                FROM matriculas m
                JOIN estudiantes e ON e.id = m.estudiante_id
                JOIN cursos c ON c.id = m.curso_id
                WHERE m.id = :mid
            """)
            r = tconn.execute(query, {"mid": matricula_id}).mappings().first()
            if not r:
                raise HTTPException(404, "La matrícula seleccionada no existe en la base de datos de prueba")

            # Consultar posibles notas asociadas
            notas_query = text("""
                SELECT n.valor, n.observaciones, ev.orden, ev.nombre AS eval_nombre
                FROM notas n
                JOIN evaluaciones ev ON ev.id = n.evaluacion_id
                WHERE n.matricula_id = :mid
            """)
            test_notas = tconn.execute(notas_query, {"mid": matricula_id}).mappings().all()

        # 1. Verificar si ya existe en la base principal (NO duplicar registros existentes)
        existente = db.query(models.Matricula).join(models.Estudiante).join(models.Curso).filter(
            models.Estudiante.codigo == r["est_codigo"],
            models.Curso.codigo == r["cur_codigo"],
            models.Matricula.periodo == r["periodo"]
        ).first()
        if existente:
            raise HTTPException(400, f"La matrícula del estudiante {r['est_apellidos']} en {r['cur_nombre']} ({r['periodo']}) ya existe en la base principal portal_academico.")

        # 2. Asegurar que el estudiante existe en la base principal
        est = db.query(models.Estudiante).filter(models.Estudiante.codigo == r["est_codigo"]).first()
        if not est:
            usr = db.query(models.Usuario).filter(models.Usuario.correo == r["est_correo"]).first()
            if not usr:
                usr = models.Usuario(
                    nombre=f"{r['est_nombres']} {r['est_apellidos']}",
                    correo=r["est_correo"],
                    password_hash=pwd_context.hash("Estudiante123*"),
                    rol="ESTUDIANTE",
                    activo=True
                )
                db.add(usr)
                db.flush()
            est = models.Estudiante(
                codigo=r["est_codigo"],
                nombres=r["est_nombres"],
                apellidos=r["est_apellidos"],
                dni=r["est_dni"],
                correo=r["est_correo"],
                carrera=r["est_carrera"],
                ciclo=r["est_ciclo"],
                fecha_ingreso=r["est_fecha_ingreso"] or date.today(),
                telefono=r["est_telefono"],
                direccion=r["est_direccion"],
                estado="ACTIVO",
                usuario_id=usr.id
            )
            db.add(est)
            db.flush()

        # 3. Asegurar que el curso existe en la base principal
        cur = db.query(models.Curso).filter(models.Curso.codigo == r["cur_codigo"]).first()
        if not cur:
            cur = models.Curso(
                codigo=r["cur_codigo"],
                nombre=r["cur_nombre"],
                creditos=r["cur_creditos"] or 4,
                docente=r["cur_docente"] or "Docente",
                ciclo=r["cur_ciclo"] or 1
            )
            db.add(cur)
            db.flush()

        # 4. Resolver periodo y seccion en la base principal
        periodo_obj = db.query(models.Periodo).filter(models.Periodo.codigo == r["periodo"]).first()
        periodo_id = periodo_obj.id if periodo_obj else None
        seccion_id = None
        if periodo_id:
            seccion = db.query(models.Seccion).filter(
                models.Seccion.curso_id == cur.id,
                models.Seccion.periodo_id == periodo_id
            ).first()
            if seccion:
                seccion_id = seccion.id

        # 5. Insertar la matrícula recuperada en la base principal
        nueva_matricula = models.Matricula(
            estudiante_id=est.id,
            curso_id=cur.id,
            periodo=r["periodo"],
            estado=r["estado"] or "MATRICULADO",
            nota=r["nota"],
            seccion_id=seccion_id,
            periodo_id=periodo_id
        )
        db.add(nueva_matricula)
        db.flush()

        # 6. Reinsertar notas si existen evaluaciones configuradas en la sección
        if seccion_id and test_notas:
            evaluaciones = db.query(models.Evaluacion).filter(models.Evaluacion.seccion_id == seccion_id).all()
            eval_by_order = {ev.orden: ev.id for ev in evaluaciones}
            for tn in test_notas:
                ev_id = eval_by_order.get(tn["orden"])
                if ev_id:
                    db.add(models.Nota(
                        matricula_id=nueva_matricula.id,
                        evaluacion_id=ev_id,
                        valor=tn["valor"],
                        observaciones=tn["observaciones"]
                    ))

        db.commit()
        db.refresh(nueva_matricula)

        return {
            "ok": True,
            "message": f"Matrícula de {est.apellidos}, {est.nombres} en {cur.nombre} recuperada exitosamente en la base principal.",
            "matricula_id": nueva_matricula.id,
            "estudiante": f"{est.apellidos}, {est.nombres}",
            "codigo_estudiante": est.codigo,
            "curso": cur.nombre,
            "codigo_curso": cur.codigo,
            "periodo": nueva_matricula.periodo,
            "estado": nueva_matricula.estado
        }

    finally:
        test_engine.dispose()

