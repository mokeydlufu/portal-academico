import sys
from pathlib import Path
from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.database import engine

def run():
    print("Iniciando migración de tablas para el módulo de Copias de Seguridad...")
    sql_file = BASE_DIR / "database" / "migration_backups.sql"
    sql_content = sql_file.read_text(encoding="utf-8")
    
    with engine.begin() as conn:
        conn.execute(text(sql_content))
        print("Tablas creadas exitosamente: backup_files, backup_schedules, backup_history, restore_history.")
        
        # Insertar una programación por defecto si no existe ninguna
        count = conn.execute(text("SELECT COUNT(*) FROM backup_schedules")).scalar()
        if count == 0:
            conn.execute(text("""
                INSERT INTO backup_schedules (name, frequency, run_time, day_of_week, retention_days, enabled)
                VALUES ('Copia de Seguridad Diaria', 'DIARIA', '06:00', NULL, 7, TRUE)
            """))
            print("Programación inicial agregada: 'Copia de Seguridad Diaria' (06:00, retención 7 días).")

if __name__ == "__main__":
    run()
