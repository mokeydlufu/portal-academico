#!/usr/bin/env python3
"""
====================================================================
  PORTAL ACADÉMICO - LIMPIEZA DE DATOS DE PRUEBA
  Versión: 1.0  |  Fecha: 2026-09-15
====================================================================
  PROPÓSITO:
    Eliminar ÚNICAMENTE los datos generados durante pruebas de
    desarrollo. Deja el sistema limpio y listo para producción.

  QUÉ ELIMINA:
    - Archivos .backup del disco (BACKUP_DIR)
    - Registros de backup_files en BD
    - Historial de ejecuciones (backup_history)
    - Historial de restauraciones (restore_history)
    - Programaciones automáticas (backup_schedules)
    - Bases de datos PostgreSQL: portal_academico_restaurado_*

  QUÉ PRESERVA:
    - Estructura de tablas (sin tocar)
    - Migraciones SQL
    - Cuenta ADMIN y todos los usuarios
    - Estudiantes, cursos, matrículas, notas
    - Código fuente y configuración
    - La base de datos portal_academico (producción)

  USO:
    python limpiar_pruebas.py            # modo interactivo con confirmación
    python limpiar_pruebas.py --audit    # solo auditar sin borrar nada
    python limpiar_pruebas.py --force    # ejecutar sin confirmación manual
====================================================================
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# ── Cargar .env desde backend/ ──────────────────────────────────────────────
def cargar_env():
    env_path = Path(__file__).parent / "backend" / ".env"
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())

cargar_env()

DATABASE_URL = os.getenv("DATABASE_URL", "")
BACKUP_DIR   = os.getenv("BACKUP_DIR", "storage/backups")
BASE_DIR     = Path(__file__).parent / "backend"
BACKUP_PATH  = BASE_DIR / BACKUP_DIR if not Path(BACKUP_DIR).is_absolute() else Path(BACKUP_DIR)

# ── Colores de consola ───────────────────────────────────────────────────────
class C:
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"
    DIM    = "\033[2m"

def titulo(txt):  print(f"\n{C.BOLD}{C.CYAN}{'='*60}{C.RESET}\n{C.BOLD}{C.CYAN}  {txt}{C.RESET}\n{C.BOLD}{C.CYAN}{'='*60}{C.RESET}")
def ok(txt):      print(f"  {C.GREEN}OK{C.RESET}  {txt}")
def warn(txt):    print(f"  {C.YELLOW}!!{C.RESET}  {txt}")
def err(txt):     print(f"  {C.RED}XX{C.RESET}  {txt}")
def info(txt):    print(f"       {txt}")
def sec(txt):     print(f"\n{C.BOLD}  [{txt}]{C.RESET}")

def fmt(b):
    if b < 1024:         return f"{b} B"
    elif b < 1048576:    return f"{b/1024:.1f} KB"
    elif b < 1073741824: return f"{b/1048576:.1f} MB"
    else:                return f"{b/1073741824:.1f} GB"

# ── Conexiones a PostgreSQL ──────────────────────────────────────────────────
def engine_prod():
    from sqlalchemy import create_engine
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL no configurada en backend/.env")
    return create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")

def engine_postgres():
    from sqlalchemy import create_engine
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL no configurada en backend/.env")
    url = DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
    return create_engine(url, isolation_level="AUTOCOMMIT")

# ════════════════════════════════════════════════════════════════════════════
# AUDITORÍA
# ════════════════════════════════════════════════════════════════════════════
def auditar():
    from sqlalchemy import text

    titulo("AUDITORIA DE DATOS DE PRUEBA")
    r = {}

    # 1. Archivos en disco
    sec("1. Archivos .backup en disco")
    archivos = sorted(BACKUP_PATH.glob("*.backup"), reverse=True) if BACKUP_PATH.exists() else []
    tam = sum(f.stat().st_size for f in archivos)
    r["archivos"] = archivos
    r["tam_total"] = tam
    if archivos:
        warn(f"{len(archivos)} archivos .backup  —  {fmt(tam)} en total")
        for f in archivos[:5]:
            info(f"• {f.name}  ({fmt(f.stat().st_size)})")
        if len(archivos) > 5:
            info(f"  ... y {len(archivos)-5} archivos mas")
    else:
        ok("Sin archivos .backup en disco")

    # 2. Registros en BD
    sec("2. Registros en base de datos")
    try:
        eng = engine_prod()
        with eng.connect() as conn:
            bf  = conn.execute(text("SELECT COUNT(*) FROM backup_files")).scalar()
            bh  = conn.execute(text("SELECT COUNT(*) FROM backup_history")).scalar()
            rh  = conn.execute(text("SELECT COUNT(*) FROM restore_history")).scalar()
            sch = conn.execute(text("SELECT COUNT(*) FROM backup_schedules")).scalar()
        eng.dispose()
        r.update({"bf": bf, "bh": bh, "rh": rh, "sch": sch})
        warn(f"backup_files:     {bf} registros")
        warn(f"backup_history:   {bh} registros")
        warn(f"restore_history:  {rh} registros")
        warn(f"backup_schedules: {sch} programaciones")

        # Detalle de programaciones
        if sch > 0:
            eng2 = engine_prod()
            with eng2.connect() as conn:
                rows = conn.execute(text(
                    "SELECT id, name, frequency, enabled FROM backup_schedules ORDER BY id"
                )).fetchall()
            eng2.dispose()
            info("Programaciones encontradas:")
            for row in rows:
                estado = "ACTIVA" if row[3] else "PAUSADA"
                info(f"  ID={row[0]} | {row[1]} | {row[2]} | {estado}")

    except Exception as e:
        err(f"No se pudo conectar a la BD: {e}")
        r["db_error"] = str(e)
        r.update({"bf": 0, "bh": 0, "rh": 0, "sch": 0})

    # 3. Bases de datos de prueba
    sec("3. Bases de datos PostgreSQL de prueba")
    try:
        eng = engine_postgres()
        with eng.connect() as conn:
            rows = conn.execute(text(
                "SELECT datname FROM pg_database "
                "WHERE datname LIKE 'portal_academico_restaurado%' "
                "   OR (datname LIKE '%prueba%' AND datname != 'portal_academico') "
                "ORDER BY datname"
            )).fetchall()
            test_dbs = [row[0] for row in rows]
        eng.dispose()
        r["test_dbs"] = test_dbs
        if test_dbs:
            warn(f"{len(test_dbs)} base(s) de prueba encontrada(s):")
            for d in test_dbs:
                info(f"• {d}")
        else:
            ok("Sin bases de datos de prueba")
    except Exception as e:
        err(f"No se pudo consultar bases de datos: {e}")
        r["test_dbs"] = []

    return r

# ════════════════════════════════════════════════════════════════════════════
# LIMPIEZA
# ════════════════════════════════════════════════════════════════════════════
def limpiar(r):
    from sqlalchemy import text

    titulo("EJECUTANDO LIMPIEZA")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = [f"Limpieza ejecutada: {datetime.now().isoformat()}"]
    errores = []

    # PASO 1: Desactivar y eliminar registros en BD (elimina primero las programaciones para detener el scheduler)
    sec("Paso 1/4  Registros en base de datos")
    if "db_error" not in r:
        try:
            eng = engine_prod()
            with eng.connect() as conn:
                # 1. Programaciones primero para que uvicorn scheduler deje de disparar backups
                conn.execute(text("UPDATE backup_schedules SET enabled = false"))
                n_sch = conn.execute(text("DELETE FROM backup_schedules")).rowcount
                ok(f"backup_schedules: {n_sch} programaciones eliminadas (scheduler detenido)")
                log.append(f"  BD: backup_schedules {n_sch} filas")

                # 2. Historial de restauraciones
                n_rh = conn.execute(text("DELETE FROM restore_history")).rowcount
                ok(f"restore_history:  {n_rh} filas eliminadas")
                log.append(f"  BD: restore_history {n_rh} filas")

                # 3. Historial de backups
                n_bh = conn.execute(text("DELETE FROM backup_history")).rowcount
                ok(f"backup_history:   {n_bh} filas eliminadas")
                log.append(f"  BD: backup_history {n_bh} filas")

                # 4. Archivos registrados
                n_bf = conn.execute(text("DELETE FROM backup_files")).rowcount
                ok(f"backup_files:     {n_bf} filas eliminadas")
                log.append(f"  BD: backup_files {n_bf} filas")
            eng.dispose()
        except Exception as e:
            err(f"Error en limpieza de BD: {e}")
            errores.append(f"BD: {e}")
    else:
        warn("BD omitida (sin conexion durante auditoria)")

    # PASO 2: Archivos en disco (escaneo fresco para incluir cualquier backup generado recién)
    sec("Paso 2/4  Archivos .backup en disco")
    archivos_actuales = sorted(BACKUP_PATH.glob("*.backup"), reverse=True) if BACKUP_PATH.exists() else []
    n_elim, tam_lib = 0, 0
    for f in archivos_actuales:
        try:
            t = f.stat().st_size
            f.unlink()
            n_elim += 1
            tam_lib += t
            log.append(f"  DISCO: {f.name} ({fmt(t)})")
        except Exception as e:
            err(f"No se pudo eliminar {f.name}: {e}")
            errores.append(f"Disco {f.name}: {e}")
    ok(f"{n_elim}/{len(archivos_actuales)} archivos eliminados — {fmt(tam_lib)} liberados")

    # PASO 3: Bases de datos de prueba
    sec("Paso 3/4  Bases de datos PostgreSQL de prueba")
    test_dbs = r.get("test_dbs", [])
    PROTEGIDAS = {"portal_academico", "postgres", "template0", "template1", "db_empleabilidad"}
    if test_dbs:
        try:
            eng = engine_postgres()
            with eng.connect() as conn:
                for db in test_dbs:
                    if db in PROTEGIDAS:
                        warn(f"OMITIDA (protegida): {db}")
                        continue
                    try:
                        conn.execute(text(f'DROP DATABASE IF EXISTS "{db}" WITH (FORCE)'))
                        ok(f"Eliminada: {db}")
                        log.append(f"  PSQL: DROP DATABASE {db}")
                    except Exception as e:
                        err(f"No se pudo eliminar {db}: {e}")
                        errores.append(f"DB {db}: {e}")
            eng.dispose()
        except Exception as e:
            err(f"No se pudo conectar: {e}")
            errores.append(f"Conexion postgres: {e}")
    else:
        ok("No habia bases de prueba")

    # PASO 4: Resetear secuencias
    sec("Paso 4/4  Reseteando secuencias de auto-incremento")
    if "db_error" not in r:
        try:
            eng = engine_prod()
            with eng.connect() as conn:
                seqs = [
                    "backup_files_id_seq",
                    "backup_history_id_seq",
                    "restore_history_id_seq",
                    "backup_schedules_id_seq",
                ]
                for seq in seqs:
                    try:
                        conn.execute(text(f"ALTER SEQUENCE {seq} RESTART WITH 1"))
                        ok(f"{seq} -> reiniciada en 1")
                    except Exception as e:
                        warn(f"No se pudo resetear {seq}: {e}")
            eng.dispose()
        except Exception as e:
            warn(f"No se pudieron resetear secuencias: {e}")
    else:
        warn("Secuencias omitidas (sin conexion)")

    # RESUMEN FINAL
    titulo("RESUMEN FINAL")
    print(f"  Archivos eliminados del disco : {n_elim}")
    print(f"  Espacio liberado              : {fmt(tam_lib)}")
    print(f"  Bases de datos de prueba      : {len([d for d in test_dbs if d not in PROTEGIDAS])} eliminada(s)")

    if errores:
        print(f"\n  {C.YELLOW}Errores ({len(errores)}):{C.RESET}")
        for e in errores:
            warn(e)
    else:
        print(f"\n  {C.GREEN}{C.BOLD}Limpieza completada sin errores.{C.RESET}")

    print(f"\n  {C.CYAN}El sistema esta listo para el primer backup oficial.{C.RESET}")
    print(f"  Siguiente paso: Administrador -> Copias de Seguridad -> Crear Backup\n")

    # Guardar log
    log_path = Path(__file__).parent / f"limpieza_{ts}.log"
    try:
        log_path.write_text("\n".join(log), encoding="utf-8")
        info(f"Log guardado en: {log_path.name}")
    except Exception:
        pass


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    solo_audit  = "--audit" in sys.argv
    forzado     = "--force" in sys.argv

    print(f"\n{C.BOLD}{C.CYAN}")
    print("  +---------------------------------------------------------+")
    print("  |   PORTAL ACADEMICO  --  LIMPIADOR DE DATOS DE PRUEBA   |")
    print("  +---------------------------------------------------------+")
    print(f"{C.RESET}")
    db_display = DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL
    print(f"  BD activa     : {db_display}")
    print(f"  BACKUP_DIR    : {BACKUP_PATH}")
    print(f"  Modo          : {'SOLO AUDITORIA' if solo_audit else ('FORZADO' if forzado else 'INTERACTIVO')}")

    # Verificar SQLAlchemy
    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        err("SQLAlchemy no encontrado. Ejecute: pip install sqlalchemy")
        sys.exit(1)

    # Auditar
    datos = auditar()

    total_reg = datos.get("bf",0) + datos.get("bh",0) + datos.get("rh",0) + datos.get("sch",0)
    total_arch = len(datos.get("archivos", []))
    total_dbs  = len(datos.get("test_dbs", []))

    if solo_audit:
        print(f"\n  {C.YELLOW}Modo --audit: revision completada. No se elimino nada.{C.RESET}")
        print(f"  Para limpiar ejecute: python limpiar_pruebas.py\n")
        sys.exit(0)

    if total_reg == 0 and total_arch == 0 and total_dbs == 0:
        print(f"\n  {C.GREEN}El sistema ya esta limpio. No hay datos de prueba.{C.RESET}\n")
        sys.exit(0)

    print(f"\n{C.BOLD}  == Que se ELIMINARA =={C.RESET}")
    print(f"  * {total_arch} archivos .backup del disco ({fmt(datos.get('tam_total',0))})")
    print(f"  * {datos.get('bf',0)} registros de backup_files")
    print(f"  * {datos.get('bh',0)} registros de backup_history")
    print(f"  * {datos.get('rh',0)} registros de restore_history")
    print(f"  * {datos.get('sch',0)} programaciones automaticas")
    print(f"  * {total_dbs} base(s) de prueba: {datos.get('test_dbs', [])}")

    print(f"\n{C.BOLD}  == Que se PRESERVA =={C.RESET}")
    print(f"  + Estructura de tablas y migraciones")
    print(f"  + Cuenta ADMIN y todos los usuarios")
    print(f"  + Estudiantes, cursos, matriculas y notas")
    print(f"  + Base de datos portal_academico (produccion)")
    print(f"  + Todo el codigo fuente y configuracion")

    if not forzado:
        print(f"\n{C.YELLOW}{C.BOLD}  ATENCION: Esta accion NO se puede deshacer.{C.RESET}")
        resp = input("  Escriba 'LIMPIAR' para confirmar: ").strip()
        if resp != "LIMPIAR":
            print(f"\n  {C.YELLOW}Cancelado. No se elimino nada.{C.RESET}\n")
            sys.exit(0)

    limpiar(datos)
