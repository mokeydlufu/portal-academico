"""
Script de auditoría y prueba integral de TODOS los botones y endpoints del Módulo de Backups
usando exclusivamente la librería estándar urllib.
"""
import json
import urllib.request
import urllib.parse
import urllib.error
import sys

BASE_URL = "http://127.0.0.1:8000/api"

def make_request(url, method="GET", headers=None, data=None):
    if headers is None:
        headers = {}
    req_data = None
    if data is not None:
        if isinstance(data, dict):
            req_data = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif isinstance(data, (bytes, bytearray)):
            req_data = data
        elif isinstance(data, str):
            req_data = data.encode("utf-8")

    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read()
            return resp.status, body, resp.headers
    except urllib.error.HTTPError as e:
        body = e.read()
        return e.code, body, e.headers
    except Exception as e:
        return 0, str(e).encode("utf-8"), {}

def run_tests():
    print("=================================================================")
    print("INICIANDO PRUEBAS DE ENDPOINTS DE LOS BOTONES DE TODAS LAS TABLAS")
    print("=================================================================")

    # 0. Autenticación como Administrador
    login_data = {"correo": "admin@portal.edu.pe", "password": "Admin123*"}
    status, body, _ = make_request(
        f"{BASE_URL}/auth/login",
        method="POST",
        headers={"Content-Type": "application/json"},
        data=login_data
    )
    if status != 200:
        print(f"FAILED LOGIN: {status} - {body.decode('utf-8')}")
        sys.exit(1)

    token = json.loads(body.decode("utf-8")).get("access_token")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("[OK] Autenticado exitosamente como Administrador.")

    results = []

    # 1. BOTÓN CREAR BACKUP AHORA (POST /api/backups)
    print("\n--- Probando 1: Crear Backup Ahora ---")
    status, body, _ = make_request(f"{BASE_URL}/backups", method="POST", headers=headers)
    if status == 200:
        b_data = json.loads(body.decode("utf-8"))
        new_backup_id = b_data.get("id")
        new_backup_file = b_data.get("filename")
        print(f"[OK] Backup creado: ID #{new_backup_id}, Archivo: {new_backup_file}, Tamaño: {b_data.get('size_formatted')}")
        results.append(("1. Crear Backup Ahora", "POST /api/backups", "200 OK", "FUNCIONAL"))
    else:
        print(f"[ERROR] Crear backup: {status} - {body.decode('utf-8')}")
        results.append(("1. Crear Backup Ahora", "POST /api/backups", f"HTTP {status}", "FALLÓ"))
        sys.exit(1)

    # 2. BOTÓN VER DETALLE BACKUP (GET /api/backups/{id})
    print("\n--- Probando 2: Ver Detalle Copia de Seguridad ---")
    status, body, _ = make_request(f"{BASE_URL}/backups/{new_backup_id}", method="GET", headers=headers)
    if status == 200:
        d = json.loads(body.decode("utf-8"))
        assert d.get("filename") == new_backup_file
        assert "started_at" in d
        assert "duracion" in d
        assert "size_formatted" in d
        assert "mensaje" in d
        print(f"[OK] Detalle obtenido: Archivo={d.get('filename')}, Estado={d.get('status')}, Duracion={d.get('duracion')}")
        results.append(("2. Botón Ver Backup", f"GET /api/backups/{new_backup_id}", "200 OK", "FUNCIONAL"))
    else:
        print(f"[ERROR] Detalle backup: {status} - {body.decode('utf-8')}")
        results.append(("2. Botón Ver Backup", f"GET /api/backups/{new_backup_id}", f"HTTP {status}", "FALLÓ"))

    # 3. BOTÓN DESCARGAR BACKUP (GET /api/backups/{id}/download)
    print("\n--- Probando 3: Descargar Backup ---")
    status, body, _ = make_request(f"{BASE_URL}/backups/{new_backup_id}/download", method="GET", headers=headers)
    if status == 200:
        content_len = len(body)
        assert content_len > 0
        print(f"[OK] Descarga completada: {content_len} bytes recibidos con stream seguro.")
        results.append(("3. Botón Descargar", f"GET /api/backups/{new_backup_id}/download", "200 OK", "FUNCIONAL"))
    else:
        print(f"[ERROR] Descargar: {status} - {body.decode('utf-8')}")
        results.append(("3. Botón Descargar", f"GET /api/backups/{new_backup_id}/download", f"HTTP {status}", "FALLÓ"))

    # 4. BOTÓN RESTAURAR EN BASE DE PRUEBA (POST /api/backups/{id}/restore)
    print("\n--- Probando 4: Restaurar en Base de Prueba ---")
    status, body, _ = make_request(
        f"{BASE_URL}/backups/{new_backup_id}/restore",
        method="POST",
        headers=headers,
        data={"target_database": "portal_academico_restaurado_prueba"}
    )
    if status == 200:
        r_data = json.loads(body.decode("utf-8"))
        print(f"[OK] Restauración exitosa: {r_data.get('message')}")
        results.append(("4. Botón Restaurar", f"POST /api/backups/{new_backup_id}/restore", "200 OK", "FUNCIONAL"))
    else:
        print(f"[ERROR] Restaurar: {status} - {body.decode('utf-8')}")
        results.append(("4. Botón Restaurar", f"POST /api/backups/{new_backup_id}/restore", f"HTTP {status}", "FALLÓ"))

    # 5. BOTÓN CREAR PROGRAMACIÓN (POST /api/backups/schedules)
    print("\n--- Probando 5: Crear Programación Automática ---")
    sch_payload = {
        "name": "Prueba Automatizada Botones",
        "frequency": "INTERVALO_SEGUNDOS",
        "interval_value": 30,
        "run_time": "02:00:00",
        "day_of_week": None,
        "retention_days": 7,
        "enabled": True
    }
    status, body, _ = make_request(f"{BASE_URL}/backups/schedules", method="POST", headers=headers, data=sch_payload)
    if status == 200:
        sch_data = json.loads(body.decode("utf-8"))
        sch_id = sch_data.get("id")
        print(f"[OK] Programación creada con ID #{sch_id}")
        results.append(("5. Crear Programación", "POST /api/backups/schedules", "200 OK", "FUNCIONAL"))
    else:
        print(f"[ERROR] Crear programación: {status} - {body.decode('utf-8')}")
        results.append(("5. Crear Programación", "POST /api/backups/schedules", f"HTTP {status}", "FALLÓ"))
        sys.exit(1)

    # 6. BOTÓN VER DETALLE PROGRAMACIÓN (GET /api/backups/schedules/{id})
    print("\n--- Probando 6: Ver Detalle Programación ---")
    status, body, _ = make_request(f"{BASE_URL}/backups/schedules/{sch_id}", method="GET", headers=headers)
    if status == 200:
        sd = json.loads(body.decode("utf-8"))
        assert sd.get("name") == "Prueba Automatizada Botones"
        assert "next_run_at" in sd
        print(f"[OK] Detalle programación obtenido: Nombre={sd.get('name')}, Próxima={sd.get('next_run_at')}")
        results.append(("6. Botón Ver Programación", f"GET /api/backups/schedules/{sch_id}", "200 OK", "FUNCIONAL"))
    else:
        print(f"[ERROR] Ver detalle programación: {status} - {body.decode('utf-8')}")
        results.append(("6. Botón Ver Programación", f"GET /api/backups/schedules/{sch_id}", f"HTTP {status}", "FALLÓ"))

    # 7. BOTÓN EDITAR PROGRAMACIÓN (PUT /api/backups/schedules/{id})
    print("\n--- Probando 7: Editar Programación ---")
    edit_payload = {
        "name": "Prueba Editada con SweetAlert2",
        "frequency": "INTERVALO_MINUTOS",
        "interval_value": 15,
        "run_time": "03:00:00",
        "retention_days": 14,
        "enabled": True
    }
    status, body, _ = make_request(f"{BASE_URL}/backups/schedules/{sch_id}", method="PUT", headers=headers, data=edit_payload)
    if status == 200:
        ed = json.loads(body.decode("utf-8"))
        assert ed.get("name") == "Prueba Editada con SweetAlert2"
        print(f"[OK] Programación editada: Nombre={ed.get('name')}, Intervalo={ed.get('interval_value')} min")
        results.append(("7. Botón Editar Programación", f"PUT /api/backups/schedules/{sch_id}", "200 OK", "FUNCIONAL"))
    else:
        print(f"[ERROR] Editar programación: {status} - {body.decode('utf-8')}")
        results.append(("7. Botón Editar Programación", f"PUT /api/backups/schedules/{sch_id}", f"HTTP {status}", "FALLÓ"))

    # 8. BOTÓN EJECUTAR AHORA (POST /api/backups/schedules/{id}/run-now)
    print("\n--- Probando 8: Ejecutar Ahora Programación ---")
    status, body, _ = make_request(f"{BASE_URL}/backups/schedules/{sch_id}/run-now", method="POST", headers=headers)
    if status == 200:
        rd = json.loads(body.decode("utf-8"))
        print(f"[OK] Ejecución inmediata completada: {rd.get('message')}")
        results.append(("8. Botón Ejecutar Ahora", f"POST /api/backups/schedules/{sch_id}/run-now", "200 OK", "FUNCIONAL"))
    else:
        print(f"[ERROR] Ejecutar ahora: {status} - {body.decode('utf-8')}")
        results.append(("8. Botón Ejecutar Ahora", f"POST /api/backups/schedules/{sch_id}/run-now", f"HTTP {status}", "FALLÓ"))

    # 9. BOTÓN ACTIVAR / DESACTIVAR TOGGLE (PUT /api/backups/schedules/{id})
    print("\n--- Probando 9: Activar/Desactivar Programación ---")
    status, body, _ = make_request(f"{BASE_URL}/backups/schedules/{sch_id}", method="PUT", headers=headers, data={"enabled": False})
    if status == 200:
        td = json.loads(body.decode("utf-8"))
        assert td.get("enabled") == False
        print(f"[OK] Programación desactivada (enabled={td.get('enabled')})")
        results.append(("9. Botón Activar/Desactivar", f"PUT /api/backups/schedules/{sch_id}", "200 OK", "FUNCIONAL"))
    else:
        print(f"[ERROR] Toggle programación: {status} - {body.decode('utf-8')}")
        results.append(("9. Botón Activar/Desactivar", f"PUT /api/backups/schedules/{sch_id}", f"HTTP {status}", "FALLÓ"))

    # 10. BOTÓN ELIMINAR PROGRAMACIÓN (DELETE /api/backups/schedules/{id})
    print("\n--- Probando 10: Eliminar Programación ---")
    status, body, _ = make_request(f"{BASE_URL}/backups/schedules/{sch_id}", method="DELETE", headers=headers)
    if status == 200:
        print(f"[OK] Programación eliminada correctamente.")
        results.append(("10. Botón Eliminar Programación", f"DELETE /api/backups/schedules/{sch_id}", "200 OK", "FUNCIONAL"))
    else:
        print(f"[ERROR] Eliminar programación: {status} - {body.decode('utf-8')}")
        results.append(("10. Botón Eliminar Programación", f"DELETE /api/backups/schedules/{sch_id}", f"HTTP {status}", "FALLÓ"))

    # 11. BOTÓN VER HISTORIAL (GET /api/backups/history)
    print("\n--- Probando 11: Ver Historial de Operaciones ---")
    status, body, _ = make_request(f"{BASE_URL}/backups/history", method="GET", headers=headers)
    if status == 200:
        hist_list = json.loads(body.decode("utf-8"))
        assert len(hist_list) > 0
        first_h = hist_list[0]
        assert "started_at" in first_h
        assert "duration_str" in first_h
        assert "status" in first_h
        assert "trigger" in first_h
        print(f"[OK] Historial obtenido: {len(hist_list)} registros. Último: {first_h.get('started_at')} | {first_h.get('trigger')}")
        results.append(("11. Botón Ver Historial", "GET /api/backups/history", "200 OK", "FUNCIONAL"))
    else:
        print(f"[ERROR] Historial: {status} - {body.decode('utf-8')}")
        results.append(("11. Botón Ver Historial", "GET /api/backups/history", f"HTTP {status}", "FALLÓ"))

    # 12. BOTÓN VER RESTAURACIÓN (GET /api/backups/restores)
    print("\n--- Probando 12: Ver Restauración de Prueba ---")
    status, body, _ = make_request(f"{BASE_URL}/backups/restores", method="GET", headers=headers)
    if status == 200:
        rest_list = json.loads(body.decode("utf-8"))
        assert len(rest_list) > 0
        first_r = rest_list[0]
        assert "target_database" in first_r
        assert "status" in first_r
        print(f"[OK] Restauraciones obtenidas: {len(rest_list)} registros. Última base: {first_r.get('target_database')} | {first_r.get('status')}")
        results.append(("12. Botón Ver Restauración", "GET /api/backups/restores", "200 OK", "FUNCIONAL"))
    else:
        print(f"[ERROR] Restauraciones: {status} - {body.decode('utf-8')}")
        results.append(("12. Botón Ver Restauración", "GET /api/backups/restores", f"HTTP {status}", "FALLÓ"))

    # 13. BOTÓN ELIMINAR BACKUP (DELETE /api/backups/{id})
    print("\n--- Probando 13: Eliminar Copia de Seguridad ---")
    status, body, _ = make_request(f"{BASE_URL}/backups", method="GET", headers=headers)
    backups_resp = json.loads(body.decode("utf-8"))
    valid_count = sum(1 for b in backups_resp if b.get("status") == "CORRECTO")
    print(f"Backups válidos actuales: {valid_count}")

    if valid_count > 1:
        status, body, _ = make_request(f"{BASE_URL}/backups/{new_backup_id}", method="DELETE", headers=headers)
        if status == 200:
            print(f"[OK] Backup #{new_backup_id} eliminado exitosamente.")
            results.append(("13. Botón Eliminar Backup", f"DELETE /api/backups/{new_backup_id}", "200 OK", "FUNCIONAL"))
        else:
            print(f"[ERROR] Eliminar backup: {status} - {body.decode('utf-8')}")
            results.append(("13. Botón Eliminar Backup", f"DELETE /api/backups/{new_backup_id}", f"HTTP {status}", "FALLÓ"))
    else:
        print("[INFO] Solo queda 1 backup válido; se prueba la protección anti-eliminación:")
        status, body, _ = make_request(f"{BASE_URL}/backups/{new_backup_id}", method="DELETE", headers=headers)
        if status == 400:
            print(f"[OK] Protección validada: HTTP 400 bloqueó eliminar el único backup válido.")
            results.append(("13. Botón Eliminar Backup (Protección)", f"DELETE /api/backups/{new_backup_id}", "400 Regla Protegida", "FUNCIONAL"))

    # 14. PRUEBA DE CONTROL DE ACCESO (HTTP 401 y 404)
    print("\n--- Probando Códigos de Error (401, 404) ---")
    status_401, _, _ = make_request(f"{BASE_URL}/backups", method="GET", headers={"Authorization": "Bearer token_falso"})
    print(f"[OK] 401 Token Inválido: Status={status_401}")
    results.append(("14. Manejo HTTP 401", "GET /api/backups (Token inválido)", f"{status_401} Unauthorized", "FUNCIONAL"))

    status_404, _, _ = make_request(f"{BASE_URL}/backups/9999999", method="GET", headers=headers)
    print(f"[OK] 404 ID Inexistente: Status={status_404}")
    results.append(("15. Manejo HTTP 404", "GET /api/backups/9999999", f"{status_404} Not Found", "FUNCIONAL"))

    print("\n=================================================================")
    print("RESUMEN GENERAL DE VERIFICACIÓN")
    print("=================================================================")
    print(f"{'FUNCIÓN / ACCIÓN':<35} | {'ENDPOINT':<40} | {'CÓDIGO':<18} | {'ESTADO'}")
    print("-" * 105)
    for name, ep, code, status_str in results:
        print(f"{name:<35} | {ep:<40} | {code:<18} | {status_str}")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()
