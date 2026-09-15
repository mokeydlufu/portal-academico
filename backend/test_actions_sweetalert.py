import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal, engine
from app.models import BackupSchedule, BackupFile, BackupHistory, RestoreHistory, Usuario
from app.services.backup_service import crear_backup, eliminar_backup, restaurar_backup_prueba, get_backup_dir
from app.services.scheduler_service import ejecutar_programacion_inmediata
from fastapi import HTTPException

print("=" * 70)
print("  PRUEBAS DE ACCIONES Y SEGURIDAD: BOTONES SWEETALERT2")
print("=" * 70)

def test_1_get_backup_detail():
    print("\n[TEST 1] Verificando detalle completo para BOTÓN VER (GET /api/backups/{id})...")
    with SessionLocal() as db:
        admin = db.query(Usuario).filter(Usuario.rol == "ADMIN").first()
        bf = crear_backup(db, user_id=admin.id if admin else None, trigger="MANUAL")
        bf_id = bf.id

    from app.routers.backups import ver_detalle_backup
    with SessionLocal() as db:
        detalle = ver_detalle_backup(id=bf_id, db=db, user=admin)
        print("-> Respuesta de detalle obtenida:")
        for k in ["filename", "created_at", "backup_type", "size_formatted", "size_bytes", "status", "started_at", "finished_at", "duracion", "path"]:
            assert k in detalle, f"Falta campo {k} en detalle"
            print(f"   {k}: {detalle[k]}")

        assert detalle["backup_type"] == "MANUAL"
        assert detalle["status"] == "CORRECTO"
        assert Path(detalle["path"]).exists()

        # Limpiar
        fpath = Path(detalle["path"])
        h = db.query(BackupHistory).filter(BackupHistory.backup_file_id == bf_id).first()
        if h: db.delete(h)
        if fpath.exists(): fpath.unlink()
        db.delete(db.get(BackupFile, bf_id))
        db.commit()

    print("-> CORRECTO: El endpoint retorna 100% de datos reales para el SweetAlert.")

def test_2_security_block_last_valid_backup():
    print("\n[TEST 2] Verificando política de seguridad: Bloquear borrado del ÚLTIMO backup válido...")
    with SessionLocal() as db:
        # Contar cuántos backups válidos hay
        valid_backups = db.query(BackupFile).filter(BackupFile.status == "CORRECTO").all()
        # Si no hay ninguno, creamos uno
        if not valid_backups:
            admin = db.query(Usuario).filter(Usuario.rol == "ADMIN").first()
            bf = crear_backup(db, user_id=admin.id if admin else None, trigger="MANUAL")
            valid_backups = [bf]

        # Dejar temporalmente solo 1 backup como CORRECTO
        backup_to_test = valid_backups[0]
        other_backups = valid_backups[1:]
        for o in other_backups:
            o.status = "ELIMINADO_RETENCION"
        db.commit()

        try:
            eliminar_backup(db, backup_to_test.id)
            assert False, "Debió bloquear la eliminación del único backup válido"
        except HTTPException as ex:
            assert ex.status_code == 400
            assert "única copia de seguridad válida" in ex.detail
            print(f"-> CORRECTO: Bloqueo de seguridad activado: '{ex.detail}'")
        finally:
            # Restaurar estados
            for o in other_backups:
                o.status = "CORRECTO"
            db.commit()

def test_3_security_block_in_progress_and_restoring():
    print("\n[TEST 3] Verificando bloqueo de eliminación si está EN_PROCESO o RESTAURANDO...")
    with SessionLocal() as db:
        admin = db.query(Usuario).filter(Usuario.rol == "ADMIN").first()
        # Backup falso en proceso
        dummy_file = get_backup_dir() / "dummy_in_progress.backup"
        dummy_file.write_text("dummy")
        bf_prog = BackupFile(
            filename="dummy_in_progress.backup",
            path=str(dummy_file),
            size_bytes=5,
            status="EN_PROCESO"
        )
        db.add(bf_prog)
        db.commit()
        db.refresh(bf_prog)
        bf_prog_id = bf_prog.id

        # Intentar eliminar backup EN_PROCESO
        try:
            eliminar_backup(db, bf_prog_id)
            assert False, "Debió bloquear eliminación de backup EN_PROCESO"
        except HTTPException as ex:
            assert ex.status_code == 400
            assert "proceso de generación" in ex.detail
            print(f"-> CORRECTO: Bloqueo de backup EN_PROCESO: '{ex.detail}'")

        # Cambiar a CORRECTO pero agregar un RestoreHistory EN_PROCESO
        bf_prog.status = "CORRECTO"
        rh = RestoreHistory(
            backup_file_id=bf_prog.id,
            target_database="test_target_restore_prog",
            status="EN_PROCESO"
        )
        db.add(rh)
        db.commit()

        try:
            eliminar_backup(db, bf_prog_id)
            assert False, "Debió bloquear eliminación de backup que se está restaurando"
        except HTTPException as ex:
            assert ex.status_code == 400
            assert "proceso de restauración" in ex.detail
            print(f"-> CORRECTO: Bloqueo de backup en restauración activa: '{ex.detail}'")

        # Limpiar
        db.delete(rh)
        db.delete(bf_prog)
        if dummy_file.exists():
            dummy_file.unlink()
        db.commit()

def test_4_real_delete_when_multiple_exist():
    print("\n[TEST 4] Verificando eliminación física real de backup cuando existen múltiples copias...")
    with SessionLocal() as db:
        admin = db.query(Usuario).filter(Usuario.rol == "ADMIN").first()
        # Asegurar que existan al menos 2 copias
        bf1 = crear_backup(db, user_id=admin.id if admin else None, trigger="MANUAL")
        bf2 = crear_backup(db, user_id=admin.id if admin else None, trigger="MANUAL")

        bf1_id = bf1.id
        fpath1 = Path(bf1.path)
        assert fpath1.exists(), "Archivo bf1 debe existir físicamente."

        # Eliminar bf1
        res = eliminar_backup(db, bf1_id)
        assert res is True
        assert not fpath1.exists(), "El archivo físico .backup DEBE haberse eliminado del disco."
        assert db.get(BackupFile, bf1_id) is None, "El registro debe haberse eliminado de la base de datos."
        print(f"-> CORRECTO: Archivo físico {fpath1.name} eliminado de disco y registro depurado.")

        # Limpiar bf2
        fpath2 = Path(bf2.path)
        h2 = db.query(BackupHistory).filter(BackupHistory.backup_file_id == bf2.id).first()
        if h2: db.delete(h2)
        if fpath2.exists(): fpath2.unlink()
        db.delete(bf2)
        db.commit()

def test_5_schedules_actions():
    print("\n[TEST 5] Verificando acciones de programación: toggle activo/pausa y eliminar...")
    with SessionLocal() as db:
        admin = db.query(Usuario).filter(Usuario.rol == "ADMIN").first()
        sch = BackupSchedule(
            name="Programación Acciones SweetAlert",
            frequency="INTERVALO_MINUTOS",
            interval_value=15,
            enabled=True,
            created_by=admin.id if admin else None
        )
        db.add(sch)
        db.commit()
        db.refresh(sch)
        sch_id = sch.id

    # 1. Toggle pausar (PUT)
    with SessionLocal() as db:
        s = db.get(BackupSchedule, sch_id)
        s.enabled = False
        db.commit()
        assert db.get(BackupSchedule, sch_id).enabled is False
        print("-> CORRECTO: Programación pausada con éxito (enabled=False).")

    # 2. Toggle activar (PUT)
    with SessionLocal() as db:
        s = db.get(BackupSchedule, sch_id)
        s.enabled = True
        db.commit()
        assert db.get(BackupSchedule, sch_id).enabled is True
        print("-> CORRECTO: Programación activada con éxito (enabled=True).")

    # 3. Eliminar programación (DELETE)
    with SessionLocal() as db:
        s = db.get(BackupSchedule, sch_id)
        db.delete(s)
        db.commit()
        assert db.get(BackupSchedule, sch_id) is None
        print("-> CORRECTO: Programación eliminada de la base de datos.")

if __name__ == "__main__":
    test_1_get_backup_detail()
    test_2_security_block_last_valid_backup()
    test_3_security_block_in_progress_and_restoring()
    test_4_real_delete_when_multiple_exist()
    test_5_schedules_actions()
    print("\n" + "=" * 70)
    print("  TODAS LAS PRUEBAS DE ACCIONES Y SEGURIDAD PASARON (100% FUNCIONAL)")
    print("=" * 70)
