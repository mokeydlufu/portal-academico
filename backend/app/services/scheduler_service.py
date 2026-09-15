import os
import asyncio
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import SessionLocal, engine
from ..models import BackupSchedule
from .backup_service import crear_backup, get_timezone

# Identificador constante para PostgreSQL Advisory Lock (anti-colisión en producción)
SCHEDULER_ADVISORY_LOCK_ID = 88812345

DIAS_SEMANA_MAP = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo"
}
DIAS_SEMANA_INV = {v.lower(): k for k, v in DIAS_SEMANA_MAP.items()}
DIAS_SEMANA_INV["miercoles"] = 2
DIAS_SEMANA_INV["sabado"] = 5

def to_local_tz(dt: datetime | None, tz: ZoneInfo) -> datetime | None:
    if not dt:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(tz)
    from datetime import timezone
    return dt.replace(tzinfo=timezone.utc).astimezone(tz)

def parse_run_time(time_str: str | None) -> tuple[int, int, int]:
    """
    Parsea una cadena de hora en formato HH:MM:SS o HH:MM.
    Retorna (hh, mm, ss).
    """
    if not time_str:
        return (6, 0, 0)
    try:
        parts = [int(p) for p in time_str.split(":")]
        hh = parts[0]
        mm = parts[1] if len(parts) > 1 else 0
        ss = parts[2] if len(parts) > 2 else 0
        return (hh, mm, ss)
    except Exception:
        return (6, 0, 0)

def calcular_proxima_ejecucion(schedule: BackupSchedule) -> datetime | None:
    """
    Calcula la próxima fecha/hora de ejecución para una programación
    en la zona horaria configurada (ej. America/Lima) con precisión de segundos.
    Soporta:
      - DIARIA: a la hora HH:MM:SS de cada día
      - SEMANAL: al día indicado de la semana a la hora HH:MM:SS
      - INTERVALO_HORAS: cada N horas
      - INTERVALO_MINUTOS: cada N minutos
      - INTERVALO_SEGUNDOS: cada N segundos (mínimo 10 segundos para pruebas)
    """
    if not schedule.enabled:
        return None

    tz = get_timezone()
    now_local = datetime.now(tz)
    freq = (schedule.frequency or "DIARIA").upper()
    hh, mm, ss = parse_run_time(schedule.run_time)

    last_run_local = to_local_tz(schedule.last_run_at, tz)
    created_local = to_local_tz(schedule.created_at, tz) or now_local

    if freq in ["DIARIA", "DIARIO"]:
        target_today = now_local.replace(hour=hh, minute=mm, second=ss, microsecond=0)
        if target_today > now_local:
            return target_today
        else:
            return target_today + timedelta(days=1)

    elif freq == "SEMANAL":
        dow_str = (schedule.day_of_week or "Lunes").lower().strip()
        target_dow = DIAS_SEMANA_INV.get(dow_str, 0) # 0 = Lunes

        current_dow = now_local.weekday()
        days_ahead = (target_dow - current_dow) % 7
        target_date = (now_local + timedelta(days=days_ahead)).replace(hour=hh, minute=mm, second=ss, microsecond=0)

        if days_ahead == 0 and target_date <= now_local:
            target_date += timedelta(days=7)

        return target_date

    elif freq in ["INTERVALO_HORAS", "CADA_HORAS", "HORAS"]:
        hours = max(1, schedule.interval_value or 1)
        base = last_run_local or created_local
        nxt = base + timedelta(hours=hours)
        return nxt if nxt > now_local else now_local

    elif freq in ["INTERVALO_MINUTOS", "CADA_MINUTOS", "MINUTOS"]:
        minutes = max(1, schedule.interval_value or 1)
        base = last_run_local or created_local
        nxt = base + timedelta(minutes=minutes)
        return nxt if nxt > now_local else now_local

    elif freq in ["INTERVALO_SEGUNDOS", "CADA_SEGUNDOS", "SEGUNDOS"]:
        seconds = max(10, schedule.interval_value or 10)
        base = last_run_local or created_local
        nxt = base + timedelta(seconds=seconds)
        return nxt if nxt > now_local else now_local

    return None

def is_schedule_due(schedule: BackupSchedule, now_local: datetime, tz: ZoneInfo) -> bool:
    """
    Determina con exactitud si una programación debe dispararse en el instante actual.
    """
    freq = (schedule.frequency or "DIARIA").upper()
    hh, mm, ss = parse_run_time(schedule.run_time)

    last_run_local = to_local_tz(schedule.last_run_at, tz)
    created_local = to_local_tz(schedule.created_at, tz) or now_local

    if freq in ["DIARIA", "DIARIO"]:
        target_today = now_local.replace(hour=hh, minute=mm, second=ss, microsecond=0)
        if now_local >= target_today:
            if not last_run_local or last_run_local < target_today:
                if (now_local - target_today).total_seconds() <= 120:
                    return True

    elif freq == "SEMANAL":
        dow_str = (schedule.day_of_week or "Lunes").lower().strip()
        target_dow = DIAS_SEMANA_INV.get(dow_str, 0)
        if now_local.weekday() == target_dow:
            target_time = now_local.replace(hour=hh, minute=mm, second=ss, microsecond=0)
            if now_local >= target_time:
                if not last_run_local or last_run_local < target_time:
                    if (now_local - target_time).total_seconds() <= 120:
                        return True

    elif freq in ["INTERVALO_HORAS", "CADA_HORAS", "HORAS"]:
        hours = max(1, schedule.interval_value or 1)
        base = last_run_local or created_local
        if (now_local - base).total_seconds() >= hours * 3600:
            return True

    elif freq in ["INTERVALO_MINUTOS", "CADA_MINUTOS", "MINUTOS"]:
        minutes = max(1, schedule.interval_value or 1)
        base = last_run_local or created_local
        if (now_local - base).total_seconds() >= minutes * 60:
            return True

    elif freq in ["INTERVALO_SEGUNDOS", "CADA_SEGUNDOS", "SEGUNDOS"]:
        seconds = max(10, schedule.interval_value or 10)
        base = last_run_local or created_local
        if (now_local - base).total_seconds() >= seconds:
            return True

    return False

def calcular_proximo_backup_global(db: Session) -> tuple[str | None, str | None]:
    """
    Calcula la fecha más próxima de respaldo entre todas las programaciones habilitadas,
    en formato con segundos 'DD/MM/YYYY HH:MM:SS'.
    """
    schedules = db.query(BackupSchedule).filter(BackupSchedule.enabled == True).all()
    if not schedules:
        return None, None

    proximas = []
    for s in schedules:
        nxt = calcular_proxima_ejecucion(s)
        if nxt:
            proximas.append((nxt, s.name))

    if not proximas:
        return None, None

    proximas.sort(key=lambda x: x[0])
    next_dt, sch_name = proximas[0]
    return next_dt.strftime("%d/%m/%Y %H:%M:%S"), sch_name

def ejecutar_programacion_inmediata(schedule_id: int, user_id: int | None = None) -> dict:
    """
    Ejecuta una programación bajo demanda inmediatamente para pruebas de verificación.
    """
    with SessionLocal() as db:
        schedule = db.get(BackupSchedule, schedule_id)
        if not schedule:
            raise ValueError("Programación no encontrada")

        backup_file = crear_backup(
            db=db,
            user_id=user_id or schedule.created_by,
            trigger="MANUAL",
            schedule_id=schedule.id
        )
        schedule.last_run_at = datetime.utcnow()
        db.commit()

        return {
            "ok": True,
            "message": f"Programación '{schedule.name}' ejecutada con éxito de forma manual.",
            "backup_id": backup_file.id,
            "filename": backup_file.filename,
            "size": backup_file.size_bytes
        }

async def scheduler_worker_loop():
    """
    Worker en segundo plano asíncrono para FastAPI.
    Usa PostgreSQL Advisory Locks para garantizar que en arquitecturas con múltiples
    workers solo UNA instancia ejecute los backups.
    Comprueba periódicamente con intervalo de 2 segundos para permitir frecuencias
    de segundos (mínimo 10s para pruebas) y exactitud HH:MM:SS.
    """
    tz = get_timezone()
    print(f"[BACKUP-SCHEDULER] Servicio de programación iniciado con zona horaria: {tz}")

    while True:
        try:
            await asyncio.sleep(2)
            now_local = datetime.now(tz)
            now_utc = datetime.utcnow()

            # 1. Intentar adquirir el candado consultivo en PostgreSQL
            with engine.connect() as conn:
                got_lock = conn.execute(
                    text("SELECT pg_try_advisory_lock(:lock_id)"),
                    {"lock_id": SCHEDULER_ADVISORY_LOCK_ID}
                ).scalar()

                if not got_lock:
                    continue

                try:
                    # 2. Revisar programaciones habilitadas
                    with SessionLocal() as db:
                        schedules = db.query(BackupSchedule).filter(BackupSchedule.enabled == True).all()

                        for s in schedules:
                            if is_schedule_due(s, now_local, tz):
                                print(f"[BACKUP-SCHEDULER] Disparando respaldo automático: '{s.name}' (Frecuencia: {s.frequency})")
                                try:
                                    # Marcar last_run_at de inmediato para evitar reentrancia
                                    s.last_run_at = now_utc
                                    db.commit()

                                    crear_backup(
                                        db=db,
                                        user_id=s.created_by,
                                        trigger="PROGRAMADO",
                                        schedule_id=s.id
                                    )
                                    print(f"[BACKUP-SCHEDULER] Respaldo automático '{s.name}' completado correctamente.")
                                except Exception as e:
                                    print(f"[BACKUP-SCHEDULER] Advertencia al ejecutar respaldo '{s.name}': {e}")
                finally:
                    conn.execute(
                        text("SELECT pg_advisory_unlock(:lock_id)"),
                        {"lock_id": SCHEDULER_ADVISORY_LOCK_ID}
                    )

        except asyncio.CancelledError:
            print("[BACKUP-SCHEDULER] Tarea de programación detenida.")
            break
        except Exception as ex:
            print("[BACKUP-SCHEDULER] Error inesperado en el ciclo del scheduler:", ex)
