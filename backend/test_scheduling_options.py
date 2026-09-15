"""
Test script para validar todas las opciones del módulo de programación automática de backups:
- Formato HH:MM:SS
- Frecuencias: DIARIA, SEMANAL, INTERVALO_HORAS, INTERVALO_MINUTOS, INTERVALO_SEGUNDOS
- Validación de mínimo 10 segundos para pruebas
- Cálculo de próxima ejecución en America/Lima
- Botón / Endpoint 'Ejecutar ahora' (run-now)
- Protección anti-colisión (no 2 backups al mismo tiempo)
- Auditoría completa en historial (inicio, fin, duración, estado, archivo)
- Ejecución desatendida desde el backend (async background worker)
"""
import sys
import os
import time
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app.database import engine
from sqlalchemy import text

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
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            res_body = response.read().decode("utf-8")
            try:
                res_json = json.loads(res_body)
            except Exception:
                res_json = res_body
            return status_code, res_json
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
        except Exception:
            err_json = err_body
        return e.code, err_json

def get_admin_token():
    code, res = request_api("/api/auth/login", method="POST", data={
        "correo": "admin@portal.edu.pe",
        "password": "Admin123*"
    })
    assert code == 200, f"Login falló ({code}): {res}"
    return res["access_token"]

def main():
    print("=" * 65)
    print(" INICIANDO PRUEBAS DE PROGRAMACIÓN AUTOMÁTICA DE BACKUPS")
    print("=" * 65)

    token = get_admin_token()

    # Limpieza preventiva inicial de pruebas anteriores
    code_s, list_s = request_api("/api/backups/schedules", method="GET", token=token)
    if code_s == 200 and isinstance(list_s, list):
        for s in list_s:
            if "Prueba" in s.get("name", "") or "Copia Cada" in s.get("name", ""):
                request_api(f"/api/backups/schedules/{s['id']}", method="DELETE", token=token)

    # 1. PRUEBA: Frecuencia DIARIA con HH:MM:SS
    print("\n[TEST 1] Programación DIARIA con HH:MM:SS (03:15:45)...")
    code, sch_diaria = request_api("/api/backups/schedules", method="POST", data={
        "name": "Copia Diaria de Prueba con Segundos",
        "frequency": "DIARIA",
        "run_time": "03:15:45",
        "retention_days": 5,
        "enabled": True
    }, token=token)
    assert code == 200, f"Error al crear ({code}): {sch_diaria}"
    print(f"-> Creada ID={sch_diaria['id']}, Frecuencia={sch_diaria['frequency']}, Hora={sch_diaria['run_time']}")
    print(f"-> Próxima ejecución calculada: {sch_diaria['next_run_at']}")
    assert ":45" in sch_diaria["next_run_at"], "Próxima ejecución debe incluir los segundos exactos"
    assert sch_diaria["run_time"] == "03:15:45"

    # 2. PRUEBA: Frecuencia SEMANAL con día y HH:MM:SS
    print("\n[TEST 2] Programación SEMANAL con día y HH:MM:SS (Lunes 14:30:15)...")
    code, sch_semanal = request_api("/api/backups/schedules", method="POST", data={
        "name": "Copia Semanal de Prueba",
        "frequency": "SEMANAL",
        "day_of_week": "Lunes",
        "run_time": "14:30:15",
        "retention_days": 14,
        "enabled": True
    }, token=token)
    assert code == 200, f"Error al crear ({code}): {sch_semanal}"
    print(f"-> Creada ID={sch_semanal['id']}, Día={sch_semanal['day_of_week']}, Hora={sch_semanal['run_time']}")
    print(f"-> Próxima ejecución calculada: {sch_semanal['next_run_at']}")
    assert ":15" in sch_semanal["next_run_at"]

    # 3. PRUEBA: Frecuencia CADA N HORAS
    print("\n[TEST 3] Programación INTERVALO_HORAS (Cada 4 horas)...")
    code, sch_horas = request_api("/api/backups/schedules", method="POST", data={
        "name": "Copia Cada 4 Horas",
        "frequency": "INTERVALO_HORAS",
        "interval_value": 4,
        "retention_days": 7,
        "enabled": True
    }, token=token)
    assert code == 200, f"Error al crear ({code}): {sch_horas}"
    print(f"-> Creada ID={sch_horas['id']}, Intervalo={sch_horas['interval_value']} horas")
    print(f"-> Próxima ejecución calculada: {sch_horas['next_run_at']}")

    # 4. PRUEBA: Frecuencia CADA N MINUTOS
    print("\n[TEST 4] Programación INTERVALO_MINUTOS (Cada 20 minutos)...")
    code, sch_minutos = request_api("/api/backups/schedules", method="POST", data={
        "name": "Copia Cada 20 Minutos",
        "frequency": "INTERVALO_MINUTOS",
        "interval_value": 20,
        "retention_days": 3,
        "enabled": True
    }, token=token)
    assert code == 200, f"Error al crear ({code}): {sch_minutos}"
    print(f"-> Creada ID={sch_minutos['id']}, Intervalo={sch_minutos['interval_value']} minutos")
    print(f"-> Próxima ejecución calculada: {sch_minutos['next_run_at']}")

    # 5. PRUEBA: Validación de mínimo 10 segundos para INTERVALO_SEGUNDOS
    print("\n[TEST 5] Validación de mínimo 10 segundos en INTERVALO_SEGUNDOS...")
    code_invalido, res_invalido = request_api("/api/backups/schedules", method="POST", data={
        "name": "Copia Inválida 5 Segundos",
        "frequency": "INTERVALO_SEGUNDOS",
        "interval_value": 5,
        "retention_days": 1,
        "enabled": True
    }, token=token)
    print(f"-> Intento con 5 segundos: Status HTTP={code_invalido}")
    assert code_invalido in [400, 422], f"Debe rechazar intervalos menores a 10 segundos: {res_invalido}"
    print("-> Rechazado correctamente por regla de negocio (mínimo 10s para pruebas).")

    # 6. PRUEBA: Programación INTERVALO_SEGUNDOS (Cada 10 segundos) y ejecución real en background
    print("\n[TEST 6] Creando programación de prueba cada 10 segundos y verificando ejecución automática en background...")
    code, sch_segundos = request_api("/api/backups/schedules", method="POST", data={
        "name": "Prueba Automatizada Cada 10 Segundos",
        "frequency": "INTERVALO_SEGUNDOS",
        "interval_value": 10,
        "retention_days": 1,
        "enabled": True
    }, token=token)
    assert code == 200, f"Error al crear ({code}): {sch_segundos}"
    sch_id = sch_segundos["id"]
    print(f"-> Programación ID={sch_id} creada exitosamente.")
    print(f"-> Próxima ejecución: {sch_segundos['next_run_at']}")

    print("-> Esperando 12 segundos para que el worker asíncrono en segundo plano dispare el backup...")
    time.sleep(13)

    # Verificar que el background scheduler ejecutó el backup
    code_sch, res_sch = request_api("/api/backups/schedules", method="GET", token=token)
    assert code_sch == 200
    current_sch = next((s for s in res_sch if s["id"] == sch_id), None)
    assert current_sch is not None
    print(f"-> Estado de la tarea tras espera: Última ejecución={current_sch['last_run_at']}, Próxima={current_sch['next_run_at']}")
    assert current_sch["last_run_at"] is not None, "El worker asíncrono debió ejecutar el backup automáticamente"

    # 7. PRUEBA: Verificar registro en historial (inicio, fin, duración, estado, archivo)
    print("\n[TEST 7] Verificando auditoría en GET /api/backups/history...")
    code_hist, history = request_api("/api/backups/history", method="GET", token=token)
    assert code_hist == 200
    sched_hist = next((h for h in history if h.get("schedule_id") == sch_id), None)
    assert sched_hist is not None, "Debe existir un registro de historial vinculado a la programación"

    print(f"-> Registro de auditoría encontrado:")
    print(f"   ID Historial: {sched_hist['id']}")
    print(f"   Inicio:       {sched_hist['started_at']}")
    print(f"   Fin:          {sched_hist['finished_at']}")
    print(f"   Duración:     {sched_hist['duration_str']}")
    print(f"   Estado:       {sched_hist['status']}")
    print(f"   Archivo:      {sched_hist['filename']}")
    print(f"   Disparador:   {sched_hist['trigger']}")
    assert sched_hist["status"] == "CORRECTO"
    assert sched_hist["filename"] is not None and ".backup" in sched_hist["filename"]
    assert sched_hist["finished_at"] is not None

    # 8. PRUEBA: Botón / Endpoint 'Ejecutar ahora' (run-now)
    print("\n[TEST 8] Probando botón 'Ejecutar ahora' (POST /api/backups/schedules/{id}/run-now)...")
    code_now, now_data = request_api(f"/api/backups/schedules/{sch_id}/run-now", method="POST", token=token)
    assert code_now == 200, f"Fallo al ejecutar ahora ({code_now}): {now_data}"
    print(f"-> Respuesta inmediata: {now_data['message']}")
    print(f"-> Backup generado: ID={now_data['backup_id']}, Archivo={now_data['filename']}, Tamaño={now_data['size']} bytes")

    # 9. PRUEBA: Anti-colisión (evitar 2 backups simultáneos)
    print("\n[TEST 9] Verificando protección anti-colisión (PostgreSQL Advisory Lock 88812346)...")
    # Deshabilitar la programación de 10s para que no dispare mientras probamos el bloqueo
    request_api(f"/api/backups/schedules/{sch_id}", method="PUT", data={"enabled": False}, token=token)
    time.sleep(2) # Breve espera para asegurar que la sesión anterior liberó el lock

    with engine.connect() as conn:
        # Simulamos un proceso externo que toma el candado
        lock_ok = conn.execute(text("SELECT pg_try_advisory_lock(88812346)")).scalar()
        assert lock_ok, "No se pudo adquirir el candado de prueba"
        try:
            # Intentar ejecutar un backup mientras el candado está tomado
            code_col, res_col = request_api("/api/backups", method="POST", token=token)
            print(f"-> Intento concurrente durante bloqueo: Status HTTP={code_col}")
            assert code_col == 409, f"Esperaba 409 Conflict, obtuvo {code_col}: {res_col}"
            print(f"-> Mensaje recibido: {res_col.get('detail')}")
            print("-> CORRECTO: Bloqueo anti-colisión evitó que 2 backups se ejecuten al mismo tiempo.")
        finally:
            conn.execute(text("SELECT pg_advisory_unlock(88812346)"))

    # Limpieza de tareas de prueba creadas
    print("\n[LIMPIEZA] Depurando tareas de prueba creadas...")
    for s_id in [sch_diaria["id"], sch_semanal["id"], sch_horas["id"], sch_minutos["id"], sch_segundos["id"]]:
        request_api(f"/api/backups/schedules/{s_id}", method="DELETE", token=token)
    print("-> Tareas de prueba eliminadas correctamente.")

    print("\n" + "=" * 65)
    print(" ¡TODAS LAS OPCIONES DE PROGRAMACIÓN FUNCIONAN AL 100%! ")
    print("=" * 65)

if __name__ == "__main__":
    main()
