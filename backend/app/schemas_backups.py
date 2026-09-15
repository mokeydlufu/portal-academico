from datetime import datetime
from pydantic import BaseModel, Field, model_validator

class BackupCreateIn(BaseModel):
    description: str | None = Field(default=None, max_length=255, description="Nombre descriptivo de la copia de seguridad")

class BackupFileOut(BaseModel):
    id: int
    filename: str
    description: str | None = None
    size_bytes: int
    size_formatted: str
    backup_type: str
    status: str
    created_at: str
    created_by_name: str | None = None
    retention_deleted_at: str | None = None
    retention_reason: str | None = None

    class Config:
        from_attributes = True

class BackupScheduleCreateIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    frequency: str = Field(default="DIARIA") # DIARIA, SEMANAL, INTERVALO_HORAS, INTERVALO_MINUTOS, INTERVALO_SEGUNDOS
    run_time: str = Field(default="06:00:00", pattern=r"^\d{2}:\d{2}(:\d{2})?$")
    day_of_week: str | None = None # 'Lunes', 'Martes', etc.
    interval_value: int | None = None # Cantidad N para horas, minutos o segundos
    retention_days: int = Field(default=7, ge=0, le=365)
    enabled: bool = True

    @model_validator(mode="after")
    def validate_frequency_and_intervals(self):
        freq = self.frequency.upper()
        # Normalizar run_time a HH:MM:SS si viene como HH:MM
        if self.run_time and len(self.run_time.split(":")) == 2:
            self.run_time = f"{self.run_time}:00"

        if freq in ["INTERVALO_SEGUNDOS", "CADA_SEGUNDOS", "SEGUNDOS"]:
            if self.interval_value is None or self.interval_value < 10:
                raise ValueError("El intervalo mínimo en segundos para pruebas es de 10 segundos.")
        elif freq in ["INTERVALO_MINUTOS", "CADA_MINUTOS", "MINUTOS"]:
            if self.interval_value is None or self.interval_value < 1:
                raise ValueError("El intervalo en minutos debe ser mayor o igual a 1.")
        elif freq in ["INTERVALO_HORAS", "CADA_HORAS", "HORAS"]:
            if self.interval_value is None or self.interval_value < 1:
                raise ValueError("El intervalo en horas debe ser mayor o igual a 1.")
        return self

class BackupScheduleUpdateIn(BaseModel):
    name: str | None = None
    frequency: str | None = None
    run_time: str | None = None
    day_of_week: str | None = None
    interval_value: int | None = None
    retention_days: int | None = Field(default=None, ge=0, le=365)
    enabled: bool | None = None

    @model_validator(mode="after")
    def normalize_update(self):
        if self.run_time and len(self.run_time.split(":")) == 2:
            self.run_time = f"{self.run_time}:00"
        if self.frequency and self.frequency.upper() in ["INTERVALO_SEGUNDOS", "CADA_SEGUNDOS", "SEGUNDOS"]:
            if self.interval_value is not None and self.interval_value < 10:
                raise ValueError("El intervalo mínimo en segundos para pruebas es de 10 segundos.")
        return self

class BackupScheduleOut(BaseModel):
    id: int
    name: str
    frequency: str
    run_time: str
    day_of_week: str | None = None
    interval_value: int | None = None
    retention_days: int
    enabled: bool
    last_run_at: str | None = None
    next_run_at: str | None = None
    created_at: str

    class Config:
        from_attributes = True

class BackupHistoryOut(BaseModel):
    id: int
    backup_file_id: int | None = None
    filename: str | None = None
    description: str | None = None
    schedule_id: int | None = None
    schedule_name: str | None = None
    started_at: str
    finished_at: str | None = None
    duration_str: str | None = None
    status: str
    trigger: str
    message: str | None = None
    user_name: str | None = None

    class Config:
        from_attributes = True

class RestoreCreateIn(BaseModel):
    target_database: str = Field(
        ...,
        pattern=r"^[a-zA-Z0-9_]+$",
        min_length=3,
        max_length=60,
        description="Nombre de la base de datos de prueba destino (solo letras, números y guión bajo)"
    )
    description: str | None = Field(default=None, max_length=255, description="Nombre descriptivo de la restauración")

class RestoreHistoryOut(BaseModel):
    id: int
    backup_file_id: int | None = None
    filename: str | None = None
    target_database: str
    description: str | None = None
    backup_description: str | None = None
    started_at: str
    finished_at: str | None = None
    duration_str: str | None = None
    status: str
    message: str | None = None
    user_name: str | None = None

    class Config:
        from_attributes = True

class HealthCheckOut(BaseModel):
    pg_dump_found: bool
    pg_dump_path: str | None = None
    pg_restore_found: bool
    pg_restore_path: str | None = None
    backup_dir_writable: bool
    backup_dir_path: str
    database_connected: bool
    is_operational: bool
    message: str

class BackupSummaryOut(BaseModel):
    last_backup_date: str | None = None
    last_backup_file: str | None = None
    last_backup_description: str | None = None
    last_backup_status: str | None = None
    next_backup_date: str | None = None
    next_backup_schedule: str | None = None
    backup_count: int
    status: str # 'Correcto', 'Error', 'Sin configuración'
    health: HealthCheckOut

class BackupFileOnDiskOut(BaseModel):
    """Representa un archivo .backup real encontrado en el BACKUP_DIR del servidor."""
    filename: str
    size_bytes: int
    size_formatted: str
    modified_at: str          # Fecha de modificación del archivo en disco
    db_id: int | None = None  # ID en backup_files (None = huérfano, no está en BD)
    db_description: str | None = None # Nombre descriptivo en BD
    db_status: str | None = None   # Estado en BD (CORRECTO / ELIMINADO_RETENCION / None)
    db_type: str | None = None     # Tipo de backup según BD (MANUAL / PROGRAMADO / None)
    db_created_by: str | None = None  # Usuario que lo generó según BD
    is_orphan: bool = False       # True si existe en disco pero no tiene registro en BD
