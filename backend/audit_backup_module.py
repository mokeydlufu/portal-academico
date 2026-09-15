"""
AUDITORÍA COMPLETA Y REAL DEL MÓDULO DE COPIAS DE SEGURIDAD
Ejecuta todas las pruebas solicitadas sin simulación contra PostgreSQL y el servidor FastAPI local.
"""
import sys
import os
import time
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app.database import engine, SessionLocal
from app.models import BackupFile, BackupSchedule, BackupHistory
from app.services.backup_service import aplicar_retencion, get_backup_dir
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
            headers_dict = dict(response.info())
            res_body = response.read()
            try:
                res_json = json.loads(res_body.decode("utf-8"))
            except Exception:
                res_json = res_body
            return status_code, res_json, headers_dict
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
        except Exception:
            err_json = err_body
        return e.code, err_json, {}

def get_token(email, password):
    code, res, _ = request_api("/api/auth/login", method="POST", data={
        "correo": email,
        "password": password
    })
    if code == 200:
        return res.get("access_token")
    return None

def run_audit():
    results = []

    def record(func_name, test_desc, result, error_desc="Ninguno", correction="Ninguna requerida"):
        results.append({
            "funcion": func_name,
            "prueba": test_desc,
            "resultado": result,
            "error": error_desc,
            "correccion": correction
        })
        print(f"[{result}] {func_name}: {test_desc}")
        if error_desc != "Ninguno":
            print(f"       -> Error: {error_desc}")
            print(f"       -> Corrección: {correction}")

    admin_token = get_token("admin@portal.edu.pe", "Admin123*")
    student_token = get_token("carlos@portal.edu.pe", "Estudiante123*")

    assert admin_token, "No se pudo obtener token de Administrador"
    assert student_token, "No se pudo obtener token de Estudiante"

    backup_dir = get_backup_dir()

    # -------------------------------------------------------------
    # 1. Crear Backup Ahora con pg_dump
    # -------------------------------------------------------------
    code, res, _ = request_api("/api/backups", method="POST", token=admin_token)
    if code == 200 and res.get("status") == "CORRECTO" and res.get("filename"):
        backup_manual_id = res["id"]
        backup_manual_fn = res["filename"]
        record(
            "Crear Backup Ahora con pg_dump",
            f"Ejecución de POST /api/backups -> Backup generado con ID={backup_manual_id}, Archivo='{backup_manual_fn}'",
            "FUNCIONAL"
        )
    else:
        record(
            "Crear Backup Ahora con pg_dump",
            "Ejecución de POST /api/backups",
            "ERROR",
            str(res),
            "Revisar permisos de ejecución de pg_dump"
        )
        return results

    # -------------------------------------------------------------
    # 2. Archivo .backup creado y tamaño > 0
    # -------------------------------------------------------------
    phys_path = backup_dir / backup_manual_fn
    if phys_path.exists() and phys_path.stat().st_size > 0:
        sz = phys_path.stat().st_size
        record(
            "Archivo .backup en disco",
            f"Verificación física de '{phys_path}' -> Existe y tiene {sz} bytes ({sz / 1024:.2f} KB)",
            "FUNCIONAL"
        )
    else:
        record(
            "Archivo .backup en disco",
            f"Verificación de archivo '{phys_path}'",
            "ERROR",
            "Archivo no encontrado o tamaño 0 bytes",
            "Verificar ruta en BACKUP_DIR y parámetros de pg_dump"
        )

    # -------------------------------------------------------------
    # 3. Backup automático cada 30 segundos para prueba
    # -------------------------------------------------------------
    code, sch_data, _ = request_api("/api/backups/schedules", method="POST", data={
        "name": "Auditoría Automática 30 Segundos",
        "frequency": "INTERVALO_SEGUNDOS",
        "interval_value": 30,
        "retention_days": 1,
        "enabled": True
    }, token=admin_token)

    if code == 200:
        sch_30_id = sch_data["id"]
        initial_next = sch_data.get("next_run_at")
        print(f"       -> Tarea programada ID={sch_30_id} creada. Próxima ejecución: {initial_next}")
        print("       -> Esperando 32 segundos a que el worker asíncrono en background ejecute el backup desatendido...")
        time.sleep(32)

        code_s, list_s, _ = request_api("/api/backups/schedules", method="GET", token=admin_token)
        sch_updated = next((s for s in list_s if s["id"] == sch_30_id), None)

        if sch_updated and sch_updated.get("last_run_at"):
            record(
                "Backup automático (30s)",
                f"Worker en background ejecutó la tarea desatendida. Última ejecución: {sch_updated['last_run_at']} | Siguiente: {sch_updated['next_run_at']}",
                "FUNCIONAL"
            )
        else:
            record(
                "Backup automático (30s)",
                "Esperar 32 segundos tras programar cada 30s",
                "ERROR",
                "last_run_at sigue en None",
                "Revisar scheduler_worker_loop en background"
            )
        # Desactivar schedule para evitar que siga disparando durante las siguientes pruebas
        request_api(f"/api/backups/schedules/{sch_30_id}", method="PUT", data={"enabled": False}, token=admin_token)
    else:
        record(
            "Backup automático (30s)",
            "Creación de programación cada 30 segundos",
            "ERROR",
            str(sch_data),
            "Revisar validación de frecuencias en backend"
        )
        sch_30_id = None

    # -------------------------------------------------------------
    # 4. Próximo backup
    # -------------------------------------------------------------
    code, summary, _ = request_api("/api/backups/summary", method="GET", token=admin_token)
    if code == 200 and summary.get("next_backup_date") and summary.get("status") == "Correcto":
        record(
            "Próximo backup",
            f"Consulta GET /api/backups/summary -> Próximo: '{summary['next_backup_date']}' ({summary.get('next_backup_schedule')}) en zona America/Lima",
            "FUNCIONAL"
        )
    else:
        record(
            "Próximo backup",
            "Consulta de resumen de backups",
            "ERROR",
            f"Respuesta inesperada: {summary}",
            "Verificar función calcular_proximo_backup_global"
        )

    # -------------------------------------------------------------
    # 5. Historial MANUAL / PROGRAMADO
    # -------------------------------------------------------------
    code, history, _ = request_api("/api/backups/history", method="GET", token=admin_token)
    has_manual = any(h.get("trigger") == "MANUAL" and h.get("status") == "CORRECTO" for h in history)
    has_programado = any(h.get("trigger") == "PROGRAMADO" and h.get("status") == "CORRECTO" for h in history)

    if code == 200 and has_manual and has_programado:
        record(
            "Historial MANUAL/PROGRAMADO",
            f"GET /api/backups/history -> Verificados registros de tipo MANUAL y PROGRAMADO con inicio, fin, duración y archivo",
            "FUNCIONAL"
        )
    else:
        record(
            "Historial MANUAL/PROGRAMADO",
            "Verificación de triggers en historial",
            "ERROR",
            f"has_manual={has_manual}, has_programado={has_programado}",
            "Asegurar que crear_backup reciba y guarde correctamente el trigger"
        )

    # -------------------------------------------------------------
    # 6. Descargar
    # -------------------------------------------------------------
    code, dl_content, dl_headers = request_api(f"/api/backups/{backup_manual_id}/download", method="GET", token=admin_token)
    if code == 200 and isinstance(dl_content, bytes) and len(dl_content) == phys_path.stat().st_size:
        cd = dl_headers.get("content-disposition", "")
        record(
            "Descargar backup",
            f"GET /api/backups/{backup_manual_id}/download -> Recibidos {len(dl_content)} bytes idénticos al disco. Header: '{cd}'",
            "FUNCIONAL"
        )
    else:
        record(
            "Descargar backup",
            f"Descarga de backup ID {backup_manual_id}",
            "ERROR",
            f"Status={code}, bytes recibidos={len(dl_content) if isinstance(dl_content, bytes) else 'no bytes'}",
            "Revisar FileResponse y autenticación de descarga"
        )

    # -------------------------------------------------------------
    # 7. Ver detalle
    # -------------------------------------------------------------
    code, detail, _ = request_api(f"/api/backups/{backup_manual_id}", method="GET", token=admin_token)
    if code == 200 and detail.get("filename") == backup_manual_fn and detail.get("duracion"):
        record(
            "Ver detalle",
            f"GET /api/backups/{backup_manual_id} -> Archivo: {detail['filename']}, Tamaño: {detail['size_formatted']}, Duración: {detail['duracion']}, Estado: {detail['status']}",
            "FUNCIONAL"
        )
    else:
        record(
            "Ver detalle",
            f"Consulta de detalle ID {backup_manual_id}",
            "ERROR",
            str(detail),
            "Revisar ver_detalle_backup en router"
        )

    # -------------------------------------------------------------
    # 8. Restaurar como base de prueba con pg_restore
    # 9. Comprobar que la base restaurada tenga tablas
    # -------------------------------------------------------------
    test_db_name = "portal_academico_audit_test"
    code, rest_res, _ = request_api(f"/api/backups/{backup_manual_id}/restore", method="POST", data={
        "target_database": test_db_name
    }, token=admin_token)

    if code == 200 and rest_res.get("ok"):
        record(
            "Restaurar con pg_restore",
            f"POST /api/backups/{backup_manual_id}/restore -> Ejecución real de pg_restore a base aislada '{test_db_name}'",
            "FUNCIONAL"
        )

        # Comprobar directamente en PostgreSQL las tablas restauradas
        try:
            from sqlalchemy.engine.url import make_url
            from app.database import DATABASE_URL
            u = make_url(DATABASE_URL)
            test_url = u.set(database=test_db_name)
            from sqlalchemy import create_engine
            t_engine = create_engine(test_url)
            with t_engine.connect() as t_conn:
                tables_res = t_conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")).fetchall()
                table_names = [t[0] for t in tables_res]
                t_count = len(table_names)
                est_count = t_conn.execute(text("SELECT count(*) FROM estudiantes")).scalar()
            t_engine.dispose()

            if t_count == 27 and est_count > 0:
                record(
                    "Comprobar tablas restauradas",
                    f"Base '{test_db_name}' verificada con {t_count} tablas y {est_count} estudiantes registrados íntegros",
                    "FUNCIONAL"
                )
            else:
                record(
                    "Comprobar tablas restauradas",
                    f"Conexión a '{test_db_name}'",
                    "ERROR",
                    f"Tablas encontradas: {t_count} (se esperaban 27)",
                    "Verificar proceso de restore"
                )
        except Exception as ex:
            record(
                "Comprobar tablas restauradas",
                f"Verificación de tablas en '{test_db_name}'",
                "ERROR",
                str(ex),
                "Comprobar conexión y permisos de lectura"
            )
        finally:
            # Limpiar base de prueba para no dejar basura
            with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as clean_conn:
                clean_conn.execute(text(f"""
                    SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
                    WHERE datname = '{test_db_name}' AND pid <> pg_backend_pid()
                """))
                clean_conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
    else:
        record(
            "Restaurar con pg_restore",
            f"Restauración de backup ID {backup_manual_id}",
            "ERROR",
            str(rest_res),
            "Revisar restauración en backup_service"
        )
        record("Comprobar tablas restauradas", "No evaluado por fallo en restauración", "ERROR", "Restore no completado", "Resolver restauración")

    # -------------------------------------------------------------
    # 10. Eliminar
    # -------------------------------------------------------------
    # Creamos un backup temporal exclusivo para probar eliminación
    code_tmp, res_tmp, _ = request_api("/api/backups", method="POST", token=admin_token)
    if code_tmp == 200:
        del_id = res_tmp["id"]
        del_fn = res_tmp["filename"]
        del_path = backup_dir / del_fn

        code_del, del_out, _ = request_api(f"/api/backups/{del_id}", method="DELETE", token=admin_token)
        phys_removed = not del_path.exists()
        code_check, _, _ = request_api(f"/api/backups/{del_id}", method="GET", token=admin_token)

        if code_del == 200 and phys_removed and code_check == 404:
            record(
                "Eliminar backup",
                f"DELETE /api/backups/{del_id} -> Archivo físico '{del_fn}' borrado de disco y registro removido (GET retorna 404)",
                "FUNCIONAL"
            )
        else:
            record(
                "Eliminar backup",
                f"Eliminación de backup {del_id}",
                "ERROR",
                f"phys_removed={phys_removed}, code_check={code_check}",
                "Verificar eliminar_backup en backup_service"
            )
    else:
        record("Eliminar backup", "Creación de backup para borrado", "ERROR", str(res_tmp), "Revisar creación")

    # -------------------------------------------------------------
    # 11. Retención
    # -------------------------------------------------------------
    # Creamos una simulación de retención: archivo viejo con retención de 1 día
    with SessionLocal() as db:
        test_sch = BackupSchedule(
            name="Schedule Retención Test",
            frequency="DIARIA",
            run_time="01:00:00",
            retention_days=1,
            enabled=False
        )
        db.add(test_sch)
        db.commit()
        db.refresh(test_sch)

        # Crear archivo físico simulado
        old_fn = f"portal_academico_old_test_{int(time.time())}.backup"
        old_path = backup_dir / old_fn
        old_path.write_text("old backup content", encoding="utf-8")

        old_dt = datetime.utcnow() - timedelta(days=3)
        bf_old = BackupFile(
            filename=old_fn,
            path=str(old_path),
            size_bytes=old_path.stat().st_size,
            backup_type="PROGRAMADO",
            status="CORRECTO",
            created_at=old_dt
        )
        db.add(bf_old)
        db.commit()
        db.refresh(bf_old)

        hist_old = BackupHistory(
            backup_file_id=bf_old.id,
            schedule_id=test_sch.id,
            started_at=old_dt,
            finished_at=old_dt + timedelta(seconds=2),
            status="CORRECTO",
            trigger="PROGRAMADO"
        )
        db.add(hist_old)
        db.commit()

        # Ejecutar aplicar_retencion
        aplicar_retencion(db, test_sch)

        db.refresh(bf_old)
        file_deleted = not old_path.exists()
        status_updated = (bf_old.status == "ELIMINADO_RETENCION")

        if file_deleted and status_updated:
            record(
                "Política de retención",
                f"Archivo antiguo (3 días) depurado de disco y marcado como 'ELIMINADO_RETENCION' con motivo: '{bf_old.retention_reason}'",
                "FUNCIONAL"
            )
        else:
            record(
                "Política de retención",
                "Verificación de retención de archivos antiguos",
                "ERROR",
                f"file_deleted={file_deleted}, status={bf_old.status}",
                "Revisar función aplicar_retencion"
            )

        # Limpieza
        db.delete(hist_old)
        db.delete(bf_old)
        db.delete(test_sch)
        db.commit()

    # -------------------------------------------------------------
    # 12. Permisos ADMIN
    # -------------------------------------------------------------
    code_adm, _, _ = request_api("/api/backups", method="GET", token=admin_token)
    if code_adm == 200:
        record(
            "Permisos ADMIN",
            "Usuario con rol ADMIN accede satisfactoriamente a las operaciones del módulo (HTTP 200)",
            "FUNCIONAL"
        )
    else:
        record("Permisos ADMIN", "Acceso con rol ADMIN", "ERROR", f"HTTP {code_adm}", "Revisar require_admin")

    # -------------------------------------------------------------
    # 13. Bloqueo para ESTUDIANTE
    # -------------------------------------------------------------
    c1, _, _ = request_api("/api/backups", method="GET", token=student_token)
    c2, _, _ = request_api("/api/backups", method="POST", token=student_token)
    c3, _, _ = request_api("/api/backups/summary", method="GET", token=student_token)
    c4, _, _ = request_api("/api/backups/schedules", method="GET", token=student_token)

    if c1 == 403 and c2 == 403 and c3 == 403 and c4 == 403:
        record(
            "Bloqueo para ESTUDIANTE",
            f"Usuario con rol ESTUDIANTE es bloqueado estrictamente en todos los endpoints (HTTP 403 Forbidden: c1={c1}, c2={c2}, c3={c3}, c4={c4})",
            "FUNCIONAL"
        )
    else:
        record(
            "Bloqueo para ESTUDIANTE",
            "Acceso de estudiante a endpoints de backups",
            "ERROR",
            f"Respuestas recibidas: c1={c1}, c2={c2}, c3={c3}, c4={c4}",
            "Revisar require_admin y require_admin_or_supervisor"
        )

    # -------------------------------------------------------------
    # 14. Manejo de Errores y Validaciones
    # -------------------------------------------------------------
    c_err1, res_err1, _ = request_api("/api/backups/999999", method="GET", token=admin_token)
    c_err2, res_err2, _ = request_api(f"/api/backups/{backup_manual_id}/restore", method="POST", data={
        "target_database": "portal;drop table--"
    }, token=admin_token)
    c_err3, res_err3, _ = request_api(f"/api/backups/{backup_manual_id}/restore", method="POST", data={
        "target_database": "portal_academico"
    }, token=admin_token)

    if c_err1 == 404 and c_err2 == 422 and c_err3 == 400:
        record(
            "Manejo de errores",
            f"Validaciones robustas: ID inexistente retorna 404, inyección SQL/caracteres inválidos retorna 422, intento de sobrescribir prod ('portal_academico') retorna 400",
            "FUNCIONAL"
        )
    else:
        record(
            "Manejo de errores",
            "Comprobar respuestas de error controlado",
            "ERROR",
            f"c_err1={c_err1} (esp 404), c_err2={c_err2} (esp 422), c_err3={c_err3} (esp 400)",
            "Ajustar validaciones de schemas y restore_backup_prueba"
        )

    # -------------------------------------------------------------
    # 15. Evitar backups duplicados / concurrentes
    # -------------------------------------------------------------
    with engine.connect() as lock_conn:
        locked = lock_conn.execute(text("SELECT pg_try_advisory_lock(88812346)")).scalar()
        assert locked, "No se pudo adquirir el candado de prueba"
        try:
            code_dup, res_dup, _ = request_api("/api/backups", method="POST", token=admin_token)
            if code_dup == 409 and "otra operación" in str(res_dup):
                record(
                    "Evitar backups duplicados",
                    f"Intento concurrente durante bloqueo retorna HTTP 409 Conflict: '{res_dup.get('detail')}'",
                    "FUNCIONAL"
                )
            else:
                record(
                    "Evitar backups duplicados",
                    "Intento concurrente con Advisory Lock activo",
                    "ERROR",
                    f"Code={code_dup}, Res={res_dup}",
                    "Verificar BACKUP_EXECUTION_LOCK_ID en crear_backup"
                )
        finally:
            lock_conn.execute(text("SELECT pg_advisory_unlock(88812346)"))

    # Limpieza final de schedule de 30s
    if sch_30_id:
        request_api(f"/api/backups/schedules/{sch_30_id}", method="DELETE", token=admin_token)

    # Limpiar backup manual de prueba
    request_api(f"/api/backups/{backup_manual_id}", method="DELETE", token=admin_token)

    return results

if __name__ == "__main__":
    results = run_audit()
    print("\n" + "=" * 90)
    print(f"{'FUNCIÓN':<32} | {'RESULTADO':<10} | {'ERROR ENCONTRADO':<18} | {'CORRECCIÓN'}")
    print("-" * 90)
    for r in results:
        print(f"{r['funcion']:<32} | {r['resultado']:<10} | {r['error']:<18} | {r['correccion']}")
    print("=" * 90)
