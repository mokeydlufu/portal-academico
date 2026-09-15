-- =========================================================================
-- MIGRACIÓN: MÓDULO DE COPIAS DE SEGURIDAD (BACKUPS)
-- Portal Académico - PostgreSQL 14+
-- =========================================================================

-- 1. Tabla de archivos de respaldos generados
CREATE TABLE IF NOT EXISTS backup_files (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL UNIQUE,
    path VARCHAR(500) NOT NULL,
    size_bytes BIGINT NOT NULL DEFAULT 0,
    backup_type VARCHAR(50) NOT NULL DEFAULT 'MANUAL', -- 'MANUAL', 'PROGRAMADO'
    status VARCHAR(50) NOT NULL DEFAULT 'CORRECTO',     -- 'CORRECTO', 'ERROR', 'ELIMINADO_RETENCION', 'INVALIDO'
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    created_by INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    retention_deleted_at TIMESTAMP WITHOUT TIME ZONE NULL,
    retention_reason TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_backup_files_created_at ON backup_files(created_at);
CREATE INDEX IF NOT EXISTS idx_backup_files_status ON backup_files(status);

-- 2. Tabla de programaciones automáticas
CREATE TABLE IF NOT EXISTS backup_schedules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    frequency VARCHAR(50) NOT NULL DEFAULT 'DIARIA',   -- 'DIARIA', 'SEMANAL', 'INTERVALO_HORAS', 'INTERVALO_MINUTOS', 'INTERVALO_SEGUNDOS'
    run_time VARCHAR(20) NOT NULL DEFAULT '06:00:00',   -- Formato HH:MM:SS (24h)
    day_of_week VARCHAR(20) NULL,                      -- 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'
    interval_value INTEGER NULL,                       -- Para intervalos en horas, minutos o segundos
    retention_days INTEGER NOT NULL DEFAULT 7,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_run_at TIMESTAMP WITHOUT TIME ZONE NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    created_by INTEGER REFERENCES usuarios(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_backup_schedules_enabled ON backup_schedules(enabled);

-- 3. Tabla de historial de ejecuciones de backup (bitácora de auditoría)
CREATE TABLE IF NOT EXISTS backup_history (
    id SERIAL PRIMARY KEY,
    backup_file_id INTEGER REFERENCES backup_files(id) ON DELETE SET NULL,
    schedule_id INTEGER REFERENCES backup_schedules(id) ON DELETE SET NULL,
    started_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMP WITHOUT TIME ZONE NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'EN_PROCESO',   -- 'EN_PROCESO', 'CORRECTO', 'ERROR'
    trigger VARCHAR(50) NOT NULL DEFAULT 'MANUAL',      -- 'MANUAL', 'PROGRAMADO'
    message TEXT NULL,
    created_by INTEGER REFERENCES usuarios(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_backup_history_started_at ON backup_history(started_at);
CREATE INDEX IF NOT EXISTS idx_backup_history_status ON backup_history(status);

-- 4. Tabla de historial de restauraciones a bases de prueba
CREATE TABLE IF NOT EXISTS restore_history (
    id SERIAL PRIMARY KEY,
    backup_file_id INTEGER REFERENCES backup_files(id) ON DELETE SET NULL,
    target_database VARCHAR(100) NOT NULL,
    started_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMP WITHOUT TIME ZONE NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'EN_PROCESO',   -- 'EN_PROCESO', 'CORRECTO', 'ERROR'
    message TEXT NULL,
    created_by INTEGER REFERENCES usuarios(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_restore_history_started_at ON restore_history(started_at);
