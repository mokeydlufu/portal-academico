import sys
import os
import json
import urllib.request
import urllib.error
from pathlib import Path
from sqlalchemy import text, create_engine

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app.database import engine, DATABASE_URL
from app.auth import create_token
from app.services.backup_service import get_backup_dir

BASE_URL = "http://127.0.0.1:8000"

def request_api(path, method="GET", data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read()
            if "application/json" in content_type:
                return resp.status, json.loads(raw.decode("utf-8")), raw
            return resp.status, raw, raw
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            err_json = json.loads(raw.decode("utf-8"))
        except Exception:
            err_json = raw.decode("utf-8")
        return e.code, err_json, raw

def run_tests():
    print("=" * 60)
    print(" INICIANDO PRUEBAS DEL MÓDULO DE COPIAS DE SEGURIDAD")
    print(f" URL de prueba: {BASE_URL}")
    print("=" * 60)

    # 1. Obtener tokens
    with engine.connect() as conn:
        admin_id = conn.execute(text("SELECT id FROM usuarios WHERE correo = 'admin@portal.edu.pe'")).scalar()
        student_id = conn.execute(text("SELECT id FROM usuarios WHERE correo = 'carlos@portal.edu.pe'")).scalar()

    admin_token = create_token({"sub": str(admin_id), "rol": "ADMIN"})
    student_token = create_token({"sub": str(student_id), "rol": "ESTUDIANTE"})

    # -------------------------------------------------------------
    # PRUEBA 1: Control de roles - Estudiante debe recibir 403
    # -------------------------------------------------------------
    print("\n[TEST 1] Verificando restricción de rol (Estudiante -> 403 Forbidden)...")
    status, body, _ = request_api("/api/backups/summary", token=student_token)
    assert status == 403, f"Esperado 403 pero se obtuvo {status}: {body}"
    print("-> CORRECTO: El estudiante no tiene acceso al módulo (403 Forbidden).")

    # -------------------------------------------------------------
    # PRUEBA 2: Resumen y Health Check para Administrador
    # -------------------------------------------------------------
    print("\n[TEST 2] Verificando GET /api/backups/summary como Administrador...")
    status, data_sum, _ = request_api("/api/backups/summary", token=admin_token)
    assert status == 200, f"Error en summary: {data_sum}"
    print("-> Resumen obtenido:", json.dumps(data_sum, indent=2, ensure_ascii=False))
    assert data_sum["health"]["pg_dump_found"] is True, "pg_dump no fue detectado"
    assert data_sum["health"]["pg_restore_found"] is True, "pg_restore no fue detectado"
    assert data_sum["health"]["is_operational"] is True, "El sistema no reporta estado operativo"
    print("-> CORRECTO: Sistema de backups 100% Operativo.")

    # -------------------------------------------------------------
    # PRUEBA 3: Crear Backup Ahora (pg_dump real)
    # -------------------------------------------------------------
    print("\n[TEST 3] Ejecutando POST /api/backups (Creación real de backup)...")
    status, backup_data, _ = request_api("/api/backups", method="POST", token=admin_token)
    assert status == 200, f"Error creando backup: {backup_data}"
    backup_id = backup_data["id"]
    filename = backup_data["filename"]
    print(f"-> Backup creado con éxito: ID={backup_id}, Archivo={filename}, Tamaño={backup_data['size_formatted']}")

    # Verificar que el archivo existe físicamente en disco y tiene tamaño > 0
    backup_dir = get_backup_dir()
    physical_file = backup_dir / filename
    assert physical_file.exists(), f"El archivo {physical_file} no existe en disco"
    assert physical_file.stat().st_size > 0, "El archivo tiene tamaño 0"
    print(f"-> Archivo verificado en disco: {physical_file} ({physical_file.stat().st_size} bytes)")

    # -------------------------------------------------------------
    # PRUEBA 4: Listar Backups Guardados y Ver Detalle
    # -------------------------------------------------------------
    print("\n[TEST 4] Verificando GET /api/backups y GET /api/backups/{id}...")
    status, backups_list, _ = request_api("/api/backups", token=admin_token)
    assert status == 200
    assert any(b["id"] == backup_id for b in backups_list), "El backup creado no aparece en la lista"
    print(f"-> Total backups listados: {len(backups_list)}")

    status, det_data, _ = request_api(f"/api/backups/{backup_id}", token=admin_token)
    assert status == 200
    assert det_data["filename"] == filename
    print("-> Detalle obtenido correctamente:", det_data["filename"], det_data["size_formatted"])

    # -------------------------------------------------------------
    # PRUEBA 5: Descarga protegida de Backup
    # -------------------------------------------------------------
    print("\n[TEST 5] Verificando GET /api/backups/{id}/download...")
    status, down_bytes, _ = request_api(f"/api/backups/{backup_id}/download", token=admin_token)
    assert status == 200, f"Error en descarga: {status}"
    assert len(down_bytes) == physical_file.stat().st_size, "El contenido descargado difiere del archivo en disco"
    print(f"-> Descarga verificada: {len(down_bytes)} bytes recibidos.")

    # -------------------------------------------------------------
    # PRUEBA 6: Programación Automática y Prueba Inmediata (run-now)
    # -------------------------------------------------------------
    print("\n[TEST 6] Creando programación y probando ejecución inmediata (run-now)...")
    status, sch_data, _ = request_api("/api/backups/schedules", method="POST", token=admin_token, data={
        "name": "Backup Automatizado de Madrugada",
        "frequency": "DIARIA",
        "run_time": "04:30",
        "retention_days": 7,
        "enabled": True
    })
    assert status == 200, f"Error creando programación: {sch_data}"
    sch_id = sch_data["id"]
    print(f"-> Programación creada: ID={sch_id}, Nombre='{sch_data['name']}', Próxima={sch_data['next_run_at']}")

    # Ejecutar inmediatamente la programación
    status, sch_run_data, _ = request_api(f"/api/backups/schedules/{sch_id}/run-now", method="POST", token=admin_token)
    assert status == 200, f"Error en run-now: {sch_run_data}"
    print("-> Ejecución inmediata completada:", sch_run_data["message"])

    # -------------------------------------------------------------
    # PRUEBA 7: Historial de ejecuciones
    # -------------------------------------------------------------
    print("\n[TEST 7] Verificando GET /api/backups/history...")
    status, hist_list, _ = request_api("/api/backups/history", token=admin_token)
    assert status == 200
    assert len(hist_list) >= 2, "Deberían existir al menos 2 registros en historial"
    print("-> Últimos registros del historial:")
    for h in hist_list[:2]:
        print(f"   [{h['started_at']}] Disparador: {h['trigger']} | Estado: {h['status']} | Archivo: {h['filename']}")
        assert h["status"] == "CORRECTO", f"Historial reporta error: {h}"

    # -------------------------------------------------------------
    # PRUEBA 8: Restauración como Base de Datos de Prueba
    # -------------------------------------------------------------
    test_db_name = "portal_academico_restaurado_prueba"
    print(f"\n[TEST 8] Restaurando backup ID={backup_id} en base de datos de prueba '{test_db_name}'...")

    # Limpiar si existiera previamente
    from sqlalchemy.engine.url import make_url
    url = make_url(DATABASE_URL)
    maint_engine = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with maint_engine.connect() as mconn:
        mconn.execute(text(f'DROP DATABASE IF EXISTS "{test_db_name}" WITH (FORCE)'))

    status, rest_data, _ = request_api(f"/api/backups/{backup_id}/restore", method="POST", token=admin_token, data={
        "target_database": test_db_name
    })
    assert status == 200, f"Error en restauración: {rest_data}"
    print("-> Respuesta de restauración:", rest_data)
    assert rest_data["ok"] is True
    assert rest_data["table_count"] > 10, f"Se esperaban más de 10 tablas pero se obtuvieron {rest_data['table_count']}"
    print(f"-> Base de datos '{test_db_name}' creada y verificada con {rest_data['table_count']} tablas.")

    # -------------------------------------------------------------
    # PRUEBA 9: Historial de Restauraciones
    # -------------------------------------------------------------
    print("\n[TEST 9] Verificando GET /api/backups/restores...")
    status, r_hist_list, _ = request_api("/api/backups/restores", token=admin_token)
    assert status == 200
    assert len(r_hist_list) >= 1
    assert r_hist_list[0]["target_database"] == test_db_name
    assert r_hist_list[0]["status"] == "CORRECTO"
    print("-> Bitácora de restauración confirmada como CORRECTO.")

    # Limpiar base de prueba en PostgreSQL
    with maint_engine.connect() as mconn:
        mconn.execute(text(f'DROP DATABASE IF EXISTS "{test_db_name}" WITH (FORCE)'))
    maint_engine.dispose()
    print(f"-> Base de datos de prueba '{test_db_name}' limpiada correctamente.")

    # -------------------------------------------------------------
    # PRUEBA 10: Eliminar un backup de prueba y verificar borrado físico
    # -------------------------------------------------------------
    print("\n[TEST 10] Eliminando backup de prueba y verificando remoción de archivo físico...")
    status, tmp_backup, _ = request_api("/api/backups", method="POST", token=admin_token)
    tmp_id = tmp_backup["id"]
    tmp_path = backup_dir / tmp_backup["filename"]
    assert tmp_path.exists(), "El archivo temporal no se creó"

    status, del_res, _ = request_api(f"/api/backups/{tmp_id}", method="DELETE", token=admin_token)
    assert status == 200
    assert not tmp_path.exists(), "El archivo físico no fue eliminado tras DELETE"
    print("-> CORRECTO: El archivo físico fue eliminado y el registro depurado sin inconsistencias.")

    # Limpiar programación de prueba
    request_api(f"/api/backups/schedules/{sch_id}", method="DELETE", token=admin_token)

    print("\n" + "=" * 60)
    print(" ¡TODAS LAS 10 PRUEBAS AUTOMATIZADAS PASARON EXITOSAMENTE! ")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
