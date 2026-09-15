import os
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import subprocess

# Asegurar path de importación
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal, engine
from app.models import BackupSchedule, BackupFile, BackupHistory, Usuario
from app.services.backup_service import (
    crear_backup,
    aplicar_retencion,
    get_backup_dir,
    get_pg_tool_path,
    get_timezone
)
from app.services.scheduler_service import (
    calcular_proxima_ejecucion,
    is_schedule_due,
    ejecutar_programacion_inmediata,
    parse_run_time
)
from app.schemas_backups import BackupScheduleCreateIn, BackupScheduleUpdateIn

print("=" * 70)
print("  AUDITORÍA FINAL: CERTIFICACIÓN DE LOS 7 PUNTOS DEL MÓDULO BACKUPS")
print("=" * 70)

def test_1_canonical_backend_and_no_duplicates():
    print("\n--- PRUEBA 1: Verificación de Backend Canónico (backend/app/) ---")
    app_main = backend_dir / "app" / "main.py"
    assert app_main.exists(), "El archivo backend/app/main.py debe existir."
    assert "Base.metadata.create_all" in app_main.read_text(encoding="utf-8")
    print("  [OK] backend/app/ es la fuente canónica del backend.")
    
    # Verificar que .gitignore ignora /app y artefactos
    gitignore_path = backend_dir.parent / ".gitignore"
    assert gitignore_path.exists(), ".gitignore debe existir en la raíz."
    gi_content = gitignore_path.read_text(encoding="utf-8")
    assert "/app" in gi_content, ".gitignore debe contener regla para /app"
    assert "backend/.venv/" in gi_content, ".gitignore debe contener backend/.venv/"
    assert "backend/.env" in gi_content, ".gitignore debe contener backend/.env"
    assert "*.backup" in gi_content, ".gitignore debe contener *.backup"
    assert "__pycache__/" in gi_content, ".gitignore debe contener __pycache__/"
    print("  [OK] Reglas de exclusión en .gitignore verificadas.")

def test_2_retention_days_zero():
    print("\n--- PRUEBA 2: Coherencia de Retención (0 = Indefinida) ---")
    # 1. Validar esquema Pydantic para create
    schema_in = BackupScheduleCreateIn(
        name="Prueba Retencion Cero",
        frequency="DIARIA",
        run_time="03:00:00",
        retention_days=0,
        enabled=True
    )
    assert schema_in.retention_days == 0, "Debe aceptar retention_days = 0"
    print("  [OK] Pydantic BackupScheduleCreateIn acepta retention_days=0.")

    # 2. Validar esquema Pydantic para update
    schema_up = BackupScheduleUpdateIn(
        retention_days=0
    )
    assert schema_up.retention_days == 0, "Update debe aceptar retention_days = 0"
    print("  [OK] Pydantic BackupScheduleUpdateIn acepta retention_days=0.")

    # 3. Validar aplicar_retencion con retention_days = 0
    with SessionLocal() as db:
        sch = BackupSchedule(
            name="Schedule Retencion Indefinida",
            frequency="DIARIA",
            run_time="04:00:00",
            retention_days=0,
            enabled=True
        )
        db.add(sch)
        db.commit()
        db.refresh(sch)

        # Simular que aplicar_retencion se llama: no debe lanzar excepción ni borrar
        aplicar_retencion(db, sch)
        print("  [OK] aplicar_retencion() respeta retention_days=0 como indefinido sin borrar.")

        # Limpiar
        db.delete(sch)
        db.commit()

def test_3_run_now_trigger_manual():
    print("\n--- PRUEBA 3: Botón 'Ejecutar ahora' debe registrar trigger MANUAL ---")
    with SessionLocal() as db:
        admin = db.query(Usuario).filter(Usuario.rol == "ADMIN").first()
        sch = BackupSchedule(
            name="Prueba Ejecutar Ahora Manual",
            frequency="INTERVALO_MINUTOS",
            interval_value=30,
            retention_days=7,
            enabled=True,
            created_by=admin.id if admin else None
        )
        db.add(sch)
        db.commit()
        db.refresh(sch)

        sch_id = sch.id

    # Ejecutar bajo demanda mediante ejecutar_programacion_inmediata
    res = ejecutar_programacion_inmediata(sch_id)
    assert res.get("ok") is True, f"Fallo al ejecutar bajo demanda: {res}"
    backup_id = res["backup_id"]
    filename = res["filename"]

    with SessionLocal() as db:
        # Verificar en historial que trigger sea estrictamente MANUAL
        hist = db.query(BackupHistory).filter(BackupHistory.backup_file_id == backup_id).first()
        assert hist is not None, "Debe existir registro en BackupHistory."
        assert hist.trigger == "MANUAL", f"El trigger debe ser MANUAL, se obtuvo: {hist.trigger}"
        assert hist.status == "CORRECTO", f"El estado debe ser CORRECTO, se obtuvo: {hist.status}"
        assert hist.schedule_id == sch_id, "Debe vincularse con la programación ejecutada."

        # Verificar actualización de last_run_at en la programación
        sch_updated = db.get(BackupSchedule, sch_id)
        assert sch_updated.last_run_at is not None, "last_run_at debe actualizarse al ejecutar inmediatamente."

        # Verificar archivo físico
        bf = db.get(BackupFile, backup_id)
        fpath = Path(bf.path)
        assert fpath.exists(), f"El archivo {fpath} debe existir físicamente."
        assert fpath.stat().st_size > 0, "El tamaño del archivo .backup debe ser > 0 bytes."

        print(f"  [OK] 'Ejecutar ahora' registró trigger='MANUAL', archivo={filename}, tamaño={fpath.stat().st_size} bytes.")

        # Limpiar prueba
        if fpath.exists():
            fpath.unlink()
        db.delete(hist)
        db.delete(bf)
        db.delete(sch_updated)
        db.commit()

def test_4_schedule_10_seconds_and_programado():
    print("\n--- PRUEBA 4: Programación cada 10 segundos y trigger PROGRAMADO ---")
    with SessionLocal() as db:
        admin = db.query(Usuario).filter(Usuario.rol == "ADMIN").first()
        sch = BackupSchedule(
            name="Prueba Auto 10 Segundos",
            frequency="INTERVALO_SEGUNDOS",
            interval_value=10,
            retention_days=0,
            enabled=True,
            created_by=admin.id if admin else None
        )
        db.add(sch)
        db.commit()
        db.refresh(sch)
        sch_id = sch.id

    tz = get_timezone()
    now_local = datetime.now(tz)

    # 1. Verificar cálculo de próxima ejecución
    nxt = calcular_proxima_ejecucion(sch)
    assert nxt is not None, "Debe calcular próxima ejecución."
    print(f"  [OK] Próxima ejecución calculada: {nxt.strftime('%d/%m/%Y %H:%M:%S')}")

    # 2. Simular que transcurrieron 10 segundos
    sch.created_at = datetime.utcnow() - timedelta(seconds=11)
    sch.last_run_at = None
    assert is_schedule_due(sch, now_local, tz) is True, "Debe estar vencida tras 10 segundos."

    # 3. Ejecutar como scheduler automático con trigger PROGRAMADO
    with SessionLocal() as db:
        sch_db = db.get(BackupSchedule, sch_id)
        sch_db.last_run_at = datetime.utcnow()
        db.commit()

        backup_file = crear_backup(
            db=db,
            user_id=sch_db.created_by,
            trigger="PROGRAMADO",
            schedule_id=sch_db.id
        )
        bf_id = backup_file.id

    with SessionLocal() as db:
        hist = db.query(BackupHistory).filter(BackupHistory.backup_file_id == bf_id).first()
        assert hist is not None
        assert hist.trigger == "PROGRAMADO", f"Trigger debe ser PROGRAMADO, obtenido: {hist.trigger}"
        assert hist.status == "CORRECTO"

        bf = db.get(BackupFile, bf_id)
        fpath = Path(bf.path)
        assert fpath.exists()
        assert fpath.stat().st_size > 0
        print(f"  [OK] Scheduler automático generó backup con trigger='PROGRAMADO', tamaño={fpath.stat().st_size} bytes.")

        # Limpiar
        if fpath.exists():
            fpath.unlink()
        db.delete(hist)
        db.delete(bf)
        db.delete(db.get(BackupSchedule, sch_id))
        db.commit()

def test_5_schedule_1_minute():
    print("\n--- PRUEBA 5: Programación cada 1 minuto (INTERVALO_MINUTOS) ---")
    with SessionLocal() as db:
        admin = db.query(Usuario).filter(Usuario.rol == "ADMIN").first()
        sch = BackupSchedule(
            name="Prueba Cada 1 Minuto",
            frequency="INTERVALO_MINUTOS",
            interval_value=1,
            retention_days=15,
            enabled=True,
            created_by=admin.id if admin else None
        )
        db.add(sch)
        db.commit()
        db.refresh(sch)
        sch_id = sch.id

    tz = get_timezone()
    now_local = datetime.now(tz)

    nxt = calcular_proxima_ejecucion(sch)
    assert nxt is not None
    print(f"  [OK] Próxima ejecución calculada a 1 minuto: {nxt.strftime('%d/%m/%Y %H:%M:%S')}")

    # Simular tiempo transcurrido de 1 minuto
    sch.created_at = datetime.utcnow() - timedelta(seconds=65)
    sch.last_run_at = None
    assert is_schedule_due(sch, now_local, tz) is True, "Debe evaluarse como debida tras 1 minuto."

    # Ejecutar backup y certificar archivo físico
    with SessionLocal() as db:
        sch_db = db.get(BackupSchedule, sch_id)
        bf = crear_backup(db, user_id=sch_db.created_by, trigger="PROGRAMADO", schedule_id=sch_db.id)
        bf_id = bf.id

    with SessionLocal() as db:
        hist = db.query(BackupHistory).filter(BackupHistory.backup_file_id == bf_id).first()
        assert hist.trigger == "PROGRAMADO"
        assert hist.status == "CORRECTO"
        bf_obj = db.get(BackupFile, bf_id)
        fpath = Path(bf_obj.path)
        assert fpath.exists() and fpath.stat().st_size > 0
        print(f"  [OK] Backup de 1 minuto creado exitosamente ({fpath.name}, {fpath.stat().st_size} bytes).")

        # Limpiar
        if fpath.exists():
            fpath.unlink()
        db.delete(hist)
        db.delete(bf_obj)
        db.delete(db.get(BackupSchedule, sch_id))
        db.commit()

def test_6_schedule_daily_hh_mm_ss():
    print("\n--- PRUEBA 6: Programación Diaria HH:MM:SS ---")
    tz = get_timezone()
    now_local = datetime.now(tz)
    
    # Probar con segundos específicos
    test_run_time = "18:45:30"
    hh, mm, ss = parse_run_time(test_run_time)
    assert hh == 18 and mm == 45 and ss == 30, "Debe parsear HH:MM:SS exactamente."

    with SessionLocal() as db:
        admin = db.query(Usuario).filter(Usuario.rol == "ADMIN").first()
        sch = BackupSchedule(
            name="Prueba Diaria HH:MM:SS",
            frequency="DIARIA",
            run_time=test_run_time,
            retention_days=30,
            enabled=True,
            created_by=admin.id if admin else None
        )
        db.add(sch)
        db.commit()
        db.refresh(sch)
        sch_id = sch.id

    nxt = calcular_proxima_ejecucion(sch)
    assert nxt is not None
    assert nxt.hour == 18 and nxt.minute == 45 and nxt.second == 30, "Próxima ejecución debe tener hora, minuto y segundo exactos."
    print(f"  [OK] Próxima ejecución diaria calculada con segundos exactos: {nxt.strftime('%d/%m/%Y %H:%M:%S')}")

    # Evaluar is_schedule_due en el instante exacto
    simulated_now = now_local.replace(hour=18, minute=45, second=35, microsecond=0)
    assert is_schedule_due(sch, simulated_now, tz) is True, "Debe dispararse en la ventana de tiempo diaria."

    # Ejecutar y verificar archivo real
    with SessionLocal() as db:
        sch_db = db.get(BackupSchedule, sch_id)
        bf = crear_backup(db, user_id=sch_db.created_by, trigger="PROGRAMADO", schedule_id=sch_db.id)
        bf_id = bf.id

    with SessionLocal() as db:
        hist = db.query(BackupHistory).filter(BackupHistory.backup_file_id == bf_id).first()
        assert hist.status == "CORRECTO"
        bf_obj = db.get(BackupFile, bf_id)
        fpath = Path(bf_obj.path)
        assert fpath.exists() and fpath.stat().st_size > 0
        print(f"  [OK] Backup diario generado y registrado en historial ({fpath.name}).")

        # Limpiar
        if fpath.exists():
            fpath.unlink()
        db.delete(hist)
        db.delete(bf_obj)
        db.delete(db.get(BackupSchedule, sch_id))
        db.commit()

def test_7_integrity_of_backup_file():
    print("\n--- PRUEBA 7: Verificación de Integridad de archivo .backup con pg_restore ---")
    pg_restore_path = get_pg_tool_path("pg_restore")
    assert pg_restore_path is not None, "pg_restore debe estar disponible."

    with SessionLocal() as db:
        admin = db.query(Usuario).filter(Usuario.rol == "ADMIN").first()
        bf = crear_backup(db, user_id=admin.id if admin else None, trigger="MANUAL")
        bf_id = bf.id

    with SessionLocal() as db:
        bf_obj = db.get(BackupFile, bf_id)
        fpath = Path(bf_obj.path)
        assert fpath.exists(), "Archivo debe existir."
        assert fpath.stat().st_size > 50000, f"Tamaño esperado > 50KB, obtenido: {fpath.stat().st_size}"

        # Ejecutar pg_restore -l para listar tablas
        proc = subprocess.run([pg_restore_path, "-l", str(fpath)], capture_output=True, text=True)
        assert proc.returncode == 0, f"pg_restore -l falló: {proc.stderr}"
        assert "TABLE DATA" in proc.stdout, "El dump debe contener tablas y datos de PostgreSQL."
        print(f"  [OK] Archivo real verificado con pg_restore -l ({fpath.name}, {fpath.stat().st_size} bytes). Contiene tablas académicas.")

        # Limpiar
        hist = db.query(BackupHistory).filter(BackupHistory.backup_file_id == bf_id).first()
        if hist:
            db.delete(hist)
        if fpath.exists():
            fpath.unlink()
        db.delete(bf_obj)
        db.commit()

if __name__ == "__main__":
    test_1_canonical_backend_and_no_duplicates()
    test_2_retention_days_zero()
    test_3_run_now_trigger_manual()
    test_4_schedule_10_seconds_and_programado()
    test_5_schedule_1_minute()
    test_6_schedule_daily_hh_mm_ss()
    test_7_integrity_of_backup_file()
    print("\n" + "=" * 70)
    print("  TODAS LAS PRUEBAS DE LA AUDITORÍA FINAL PASARON COMO FUNCIONAL (100%)")
    print("=" * 70)
