from datetime import date, datetime
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, Numeric, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    correo: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[str] = mapped_column(String(30), default="ADMIN")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    estudiante: Mapped["Estudiante"] = relationship(back_populates="usuario", uselist=False)

class Carrera(Base):
    __tablename__ = "carreras"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(150))
    estudiantes: Mapped[list["Estudiante"]] = relationship(back_populates="carrera_rel")

class Periodo(Base):
    __tablename__ = "periodos"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(100))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    secciones: Mapped[list["Seccion"]] = relationship(back_populates="periodo")
    matriculas: Mapped[list["Matricula"]] = relationship(back_populates="periodo_rel")
    pagos: Mapped[list["Pago"]] = relationship(back_populates="periodo_rel")

class Docente(Base):
    __tablename__ = "docentes"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    nombres: Mapped[str] = mapped_column(String(100))
    apellidos: Mapped[str] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    secciones: Mapped[list["Seccion"]] = relationship(back_populates="docente")

class Curso(Base):
    __tablename__ = "cursos"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    creditos: Mapped[int] = mapped_column(Integer)
    docente: Mapped[str] = mapped_column(String(120))
    ciclo: Mapped[int] = mapped_column(Integer)
    matriculas: Mapped[list["Matricula"]] = relationship(back_populates="curso", cascade="all, delete-orphan")
    secciones: Mapped[list["Seccion"]] = relationship(back_populates="curso", cascade="all, delete-orphan")
    silabo: Mapped["Silabo"] = relationship(back_populates="curso", uselist=False)

class Seccion(Base):
    __tablename__ = "secciones"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30))
    curso_id: Mapped[int] = mapped_column(ForeignKey("cursos.id", ondelete="CASCADE"))
    docente_id: Mapped[int | None] = mapped_column(ForeignKey("docentes.id", ondelete="SET NULL"), nullable=True)
    periodo_id: Mapped[int] = mapped_column(ForeignKey("periodos.id", ondelete="CASCADE"))
    curso: Mapped[Curso] = relationship(back_populates="secciones")
    docente: Mapped[Docente | None] = relationship(back_populates="secciones")
    periodo: Mapped[Periodo] = relationship(back_populates="secciones")
    evaluaciones: Mapped[list["Evaluacion"]] = relationship(back_populates="seccion", cascade="all, delete-orphan", order_by="Evaluacion.orden")
    matriculas: Mapped[list["Matricula"]] = relationship(back_populates="seccion")
    horarios: Mapped[list["Horario"]] = relationship(back_populates="seccion", cascade="all, delete-orphan")

class Horario(Base):
    __tablename__ = "horarios"
    id: Mapped[int] = mapped_column(primary_key=True)
    seccion_id: Mapped[int] = mapped_column(ForeignKey("secciones.id", ondelete="CASCADE"))
    dia: Mapped[str] = mapped_column(String(20))
    hora_inicio: Mapped[str] = mapped_column(String(10))
    hora_fin: Mapped[str] = mapped_column(String(10))
    aula: Mapped[str] = mapped_column(String(50))
    modalidad: Mapped[str] = mapped_column(String(30), default="PRESENCIAL")
    seccion: Mapped[Seccion] = relationship(back_populates="horarios")

class TipoEvaluacion(Base):
    __tablename__ = "tipos_evaluacion"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(10), unique=True)
    nombre: Mapped[str] = mapped_column(String(100))
    evaluaciones: Mapped[list["Evaluacion"]] = relationship(back_populates="tipo")

class Evaluacion(Base):
    __tablename__ = "evaluaciones"
    id: Mapped[int] = mapped_column(primary_key=True)
    seccion_id: Mapped[int] = mapped_column(ForeignKey("secciones.id", ondelete="CASCADE"))
    tipo_id: Mapped[int] = mapped_column(ForeignKey("tipos_evaluacion.id", ondelete="CASCADE"))
    nombre: Mapped[str] = mapped_column(String(100))
    peso: Mapped[float] = mapped_column(Numeric(5, 2))
    orden: Mapped[int] = mapped_column(Integer, default=1)
    seccion: Mapped[Seccion] = relationship(back_populates="evaluaciones")
    tipo: Mapped[TipoEvaluacion] = relationship(back_populates="evaluaciones")
    notas: Mapped[list["Nota"]] = relationship(back_populates="evaluacion", cascade="all, delete-orphan")

class Estudiante(Base):
    __tablename__ = "estudiantes"
    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    nombres: Mapped[str] = mapped_column(String(100))
    apellidos: Mapped[str] = mapped_column(String(100))
    dni: Mapped[str] = mapped_column(String(8), unique=True)
    correo: Mapped[str] = mapped_column(String(150), unique=True)
    carrera: Mapped[str] = mapped_column(String(120))
    ciclo: Mapped[int] = mapped_column(Integer)
    fecha_ingreso: Mapped[date] = mapped_column(Date)
    estado: Mapped[str] = mapped_column(String(20), default="ACTIVO")
    telefono: Mapped[str | None] = mapped_column(String(20), nullable=True)
    direccion: Mapped[str | None] = mapped_column(String(200), nullable=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True, unique=True)
    carrera_id: Mapped[int | None] = mapped_column(ForeignKey("carreras.id", ondelete="SET NULL"), nullable=True)
    usuario: Mapped[Usuario | None] = relationship(back_populates="estudiante")
    carrera_rel: Mapped[Carrera | None] = relationship(back_populates="estudiantes")
    matriculas: Mapped[list["Matricula"]] = relationship(back_populates="estudiante", cascade="all, delete-orphan")
    tramites: Mapped[list["Tramite"]] = relationship(back_populates="estudiante", cascade="all, delete-orphan")
    pagos: Mapped[list["Pago"]] = relationship(back_populates="estudiante", cascade="all, delete-orphan")
    ficha_bienestar: Mapped["FichaBienestar"] = relationship(back_populates="estudiante", uselist=False)
    postulaciones: Mapped[list["Postulacion"]] = relationship(back_populates="estudiante", cascade="all, delete-orphan")

class Matricula(Base):
    __tablename__ = "matriculas"
    id: Mapped[int] = mapped_column(primary_key=True)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("estudiantes.id", ondelete="CASCADE"))
    curso_id: Mapped[int] = mapped_column(ForeignKey("cursos.id", ondelete="CASCADE"))
    periodo: Mapped[str] = mapped_column(String(20))
    nota: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="MATRICULADO")
    seccion_id: Mapped[int | None] = mapped_column(ForeignKey("secciones.id", ondelete="CASCADE"), nullable=True)
    periodo_id: Mapped[int | None] = mapped_column(ForeignKey("periodos.id", ondelete="CASCADE"), nullable=True)
    estudiante: Mapped[Estudiante] = relationship(back_populates="matriculas")
    curso: Mapped[Curso] = relationship(back_populates="matriculas")
    seccion: Mapped[Seccion | None] = relationship(back_populates="matriculas")
    periodo_rel: Mapped[Periodo | None] = relationship(back_populates="matriculas")
    notas: Mapped[list["Nota"]] = relationship(back_populates="matricula", cascade="all, delete-orphan")
    asistencias: Mapped[list["Asistencia"]] = relationship(back_populates="matricula", cascade="all, delete-orphan")

class Nota(Base):
    __tablename__ = "notas"
    id: Mapped[int] = mapped_column(primary_key=True)
    evaluacion_id: Mapped[int] = mapped_column(ForeignKey("evaluaciones.id", ondelete="CASCADE"))
    matricula_id: Mapped[int] = mapped_column(ForeignKey("matriculas.id", ondelete="CASCADE"))
    valor: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evaluacion: Mapped[Evaluacion] = relationship(back_populates="notas")
    matricula: Mapped[Matricula] = relationship(back_populates="notas")

class Silabo(Base):
    __tablename__ = "silabos"
    id: Mapped[int] = mapped_column(primary_key=True)
    curso_id: Mapped[int] = mapped_column(ForeignKey("cursos.id", ondelete="CASCADE"))
    nombre_archivo: Mapped[str] = mapped_column(String(255))
    ruta_archivo: Mapped[str] = mapped_column(String(500))
    fecha_subida: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    curso: Mapped[Curso] = relationship(back_populates="silabo")

class Asistencia(Base):
    __tablename__ = "asistencias"
    id: Mapped[int] = mapped_column(primary_key=True)
    matricula_id: Mapped[int] = mapped_column(ForeignKey("matriculas.id", ondelete="CASCADE"))
    fecha: Mapped[date] = mapped_column(Date)
    hora: Mapped[str] = mapped_column(String(10))
    estado: Mapped[str] = mapped_column(String(20)) # PRESENTE, FALTA, TARDANZA, JUSTIFICADO
    observacion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    matricula: Mapped[Matricula] = relationship(back_populates="asistencias")

class Tramite(Base):
    __tablename__ = "tramites"
    id: Mapped[int] = mapped_column(primary_key=True)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("estudiantes.id", ondelete="CASCADE"))
    codigo: Mapped[str] = mapped_column(String(30), unique=True)
    tipo: Mapped[str] = mapped_column(String(100))
    motivo: Mapped[str] = mapped_column(String(255))
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(30), default="PENDIENTE")
    fecha_solicitud: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    fecha_respuesta: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    respuesta: Mapped[str | None] = mapped_column(Text, nullable=True)
    estudiante: Mapped[Estudiante] = relationship(back_populates="tramites")

class Pago(Base):
    __tablename__ = "pagos"
    id: Mapped[int] = mapped_column(primary_key=True)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("estudiantes.id", ondelete="CASCADE"))
    periodo_id: Mapped[int | None] = mapped_column(ForeignKey("periodos.id", ondelete="SET NULL"), nullable=True)
    concepto: Mapped[str] = mapped_column(String(150))
    monto: Mapped[float] = mapped_column(Numeric(8, 2))
    fecha_vencimiento: Mapped[date] = mapped_column(Date)
    fecha_pago: Mapped[date | None] = mapped_column(Date, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="PENDIENTE")
    nro_operacion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    estudiante: Mapped[Estudiante] = relationship(back_populates="pagos")
    periodo_rel: Mapped[Periodo | None] = relationship(back_populates="pagos")

class FichaBienestar(Base):
    __tablename__ = "fichas_bienestar"
    id: Mapped[int] = mapped_column(primary_key=True)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("estudiantes.id", ondelete="CASCADE"), unique=True)
    contacto_emergencia: Mapped[str | None] = mapped_column(String(150), nullable=True)
    telefono_emergencia: Mapped[str | None] = mapped_column(String(20), nullable=True)
    parentesco_contacto: Mapped[str | None] = mapped_column(String(50), nullable=True)
    direccion_actual: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ocupacion_padres: Mapped[str | None] = mapped_column(String(150), nullable=True)
    ingreso_familiar: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    condicion_vivienda: Mapped[str | None] = mapped_column(String(100), nullable=True)
    seguro_salud: Mapped[str | None] = mapped_column(String(100), default="Seguro Estudiantil")
    alergias_condiciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_actualizacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    estudiante: Mapped[Estudiante] = relationship(back_populates="ficha_bienestar")

class SolicitudRecuperacion(Base):
    __tablename__ = "solicitudes_recuperacion"
    id: Mapped[int] = mapped_column(primary_key=True)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("estudiantes.id", ondelete="CASCADE"))
    matricula_id: Mapped[int] = mapped_column(ForeignKey("matriculas.id", ondelete="CASCADE"))
    motivo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    estado: Mapped[str] = mapped_column(String(30), default="PENDIENTE")
    fecha_solicitud: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    fecha_examen: Mapped[date | None] = mapped_column(Date, nullable=True)

class SolicitudReprogramacion(Base):
    __tablename__ = "solicitudes_reprogramacion"
    id: Mapped[int] = mapped_column(primary_key=True)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("estudiantes.id", ondelete="CASCADE"))
    evaluacion_id: Mapped[int] = mapped_column(ForeignKey("evaluaciones.id", ondelete="CASCADE"))
    matricula_id: Mapped[int] = mapped_column(ForeignKey("matriculas.id", ondelete="CASCADE"))
    motivo: Mapped[str] = mapped_column(String(255))
    fecha_solicitada: Mapped[date | None] = mapped_column(Date, nullable=True)
    sustento: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(30), default="PENDIENTE")
    fecha_solicitud: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Empleo(Base):
    __tablename__ = "empleos"
    id: Mapped[int] = mapped_column(primary_key=True)
    empresa: Mapped[str] = mapped_column(String(150))
    puesto: Mapped[str] = mapped_column(String(150))
    modalidad: Mapped[str] = mapped_column(String(50))
    ubicacion: Mapped[str] = mapped_column(String(100))
    descripcion: Mapped[str] = mapped_column(Text)
    requisitos: Mapped[str] = mapped_column(Text)
    funciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    remuneracion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fecha_publicacion: Mapped[date] = mapped_column(Date, default=date.today)
    fecha_limite: Mapped[date | None] = mapped_column(Date, nullable=True)
    carrera_afin: Mapped[str | None] = mapped_column(String(150), nullable=True)
    postulaciones: Mapped[list["Postulacion"]] = relationship(back_populates="empleo", cascade="all, delete-orphan")

class Postulacion(Base):
    __tablename__ = "postulaciones"
    id: Mapped[int] = mapped_column(primary_key=True)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("estudiantes.id", ondelete="CASCADE"))
    empleo_id: Mapped[int] = mapped_column(ForeignKey("empleos.id", ondelete="CASCADE"))
    fecha_postulacion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    estado: Mapped[str] = mapped_column(String(30), default="ENVIADA")
    estudiante: Mapped[Estudiante] = relationship(back_populates="postulaciones")
    empleo: Mapped[Empleo] = relationship(back_populates="postulaciones")

class EncuestaDocente(Base):
    __tablename__ = "encuestas_docente"
    id: Mapped[int] = mapped_column(primary_key=True)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("estudiantes.id", ondelete="CASCADE"))
    seccion_id: Mapped[int] = mapped_column(ForeignKey("secciones.id", ondelete="CASCADE"))
    calificacion: Mapped[int] = mapped_column(Integer)
    comentarios: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="COMPLETADA")
    fecha_respuesta: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class AvisoAcademico(Base):
    __tablename__ = "avisos_academicos"
    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(150))
    contenido: Mapped[str] = mapped_column(Text)
    fecha: Mapped[date] = mapped_column(Date, default=date.today)
    tipo: Mapped[str] = mapped_column(String(30), default="INFORMATIVO")

# ==================== MÓDULO DE COPIAS DE SEGURIDAD ====================

class BackupFile(Base):
    __tablename__ = "backup_files"
    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    path: Mapped[str] = mapped_column(String(500))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    backup_type: Mapped[str] = mapped_column(String(50), default="MANUAL") # MANUAL, PROGRAMADO
    status: Mapped[str] = mapped_column(String(50), default="CORRECTO", index=True) # CORRECTO, ERROR, ELIMINADO_RETENCION, INVALIDO
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    retention_deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    retention_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    usuario: Mapped["Usuario"] = relationship(foreign_keys=[created_by])
    history: Mapped[list["BackupHistory"]] = relationship(back_populates="backup_file", cascade="all, delete-orphan")
    restores: Mapped[list["RestoreHistory"]] = relationship(back_populates="backup_file", cascade="all, delete-orphan")

class BackupSchedule(Base):
    __tablename__ = "backup_schedules"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    frequency: Mapped[str] = mapped_column(String(50), default="DIARIA") # DIARIA, SEMANAL, INTERVALO_HORAS, INTERVALO_MINUTOS, INTERVALO_SEGUNDOS
    run_time: Mapped[str] = mapped_column(String(20), default="06:00:00") # Formato HH:MM:SS
    day_of_week: Mapped[str | None] = mapped_column(String(20), nullable=True) # 'Lunes', etc.
    interval_value: Mapped[int | None] = mapped_column(Integer, nullable=True) # Valor N para intervalos
    retention_days: Mapped[int] = mapped_column(Integer, default=7)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)

    usuario: Mapped["Usuario"] = relationship(foreign_keys=[created_by])
    history: Mapped[list["BackupHistory"]] = relationship(back_populates="schedule")

class BackupHistory(Base):
    __tablename__ = "backup_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    backup_file_id: Mapped[int | None] = mapped_column(ForeignKey("backup_files.id", ondelete="SET NULL"), nullable=True)
    schedule_id: Mapped[int | None] = mapped_column(ForeignKey("backup_schedules.id", ondelete="SET NULL"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="EN_PROCESO", index=True) # EN_PROCESO, CORRECTO, ERROR
    trigger: Mapped[str] = mapped_column(String(50), default="MANUAL") # MANUAL, PROGRAMADO
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)

    backup_file: Mapped["BackupFile"] = relationship(back_populates="history", foreign_keys=[backup_file_id])
    schedule: Mapped["BackupSchedule"] = relationship(back_populates="history", foreign_keys=[schedule_id])
    usuario: Mapped["Usuario"] = relationship(foreign_keys=[created_by])

class RestoreHistory(Base):
    __tablename__ = "restore_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    backup_file_id: Mapped[int | None] = mapped_column(ForeignKey("backup_files.id", ondelete="SET NULL"), nullable=True)
    target_database: Mapped[str] = mapped_column(String(100))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="EN_PROCESO") # EN_PROCESO, CORRECTO, ERROR
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)

    backup_file: Mapped["BackupFile"] = relationship(back_populates="restores", foreign_keys=[backup_file_id])
    usuario: Mapped["Usuario"] = relationship(foreign_keys=[created_by])

