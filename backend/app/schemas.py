from datetime import date, datetime
from pydantic import BaseModel, EmailStr, ConfigDict

class LoginIn(BaseModel):
    correo: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    nombre: str
    rol: str

class ChangePasswordIn(BaseModel):
    password_actual: str
    password_nueva: str

class PerfilUpdateIn(BaseModel):
    telefono: str | None = None
    direccion: str | None = None

class PeriodoOut(BaseModel):
    id: int
    codigo: str
    nombre: str
    activo: bool
    model_config = ConfigDict(from_attributes=True)

class EstudianteMeOut(BaseModel):
    id: int
    codigo: str
    nombres: str
    apellidos: str
    nombre_completo: str
    carrera: str
    ciclo: int
    correo: EmailStr
    dni: str
    telefono: str | None = None
    direccion: str | None = None
    estado: str = "ACTIVO"

class CursoMatriculadoOut(BaseModel):
    matricula_id: int
    curso_id: int
    codigo: str
    curso: str
    creditos: int
    seccion: str
    docente: str
    horario: str | None = None
    aula: str | None = None
    estado: str
    tiene_silabo: bool

class EvaluacionDetalleOut(BaseModel):
    evaluacion_id: int
    evaluacion: str
    tipo: str
    peso: float
    nota: float | None = None
    estado: str

class NotasCursoOut(BaseModel):
    matricula_id: int
    curso: str
    codigo: str
    docente: str
    periodo: str
    seccion: str
    evaluaciones: list[EvaluacionDetalleOut]
    promedio_actual: float | None = None
    promedio_final: float | None = None
    estado_curso: str

class TramiteCreateIn(BaseModel):
    tipo: str
    motivo: str
    descripcion: str | None = None
    archivo: str | None = None

class BienestarUpdateIn(BaseModel):
    contacto_emergencia: str | None = None
    telefono_emergencia: str | None = None
    parentesco_contacto: str | None = None
    direccion_actual: str | None = None
    ocupacion_padres: str | None = None
    ingreso_familiar: float | None = None
    condicion_vivienda: str | None = None
    seguro_salud: str | None = None
    alergias_condiciones: str | None = None

class RecuperacionCreateIn(BaseModel):
    matricula_id: int
    motivo: str | None = None

class ReprogramacionCreateIn(BaseModel):
    evaluacion_id: int
    matricula_id: int
    motivo: str
    fecha_solicitada: date | None = None
    sustento: str | None = None

class EncuestaSubmitIn(BaseModel):
    seccion_id: int | None = None
    calificacion: int
    comentarios: str | None = None

class EstudianteBase(BaseModel):
    codigo: str
    nombres: str
    apellidos: str
    dni: str
    correo: EmailStr
    carrera: str
    ciclo: int
    fecha_ingreso: date
    estado: str = "ACTIVO"

class EstudianteCreate(EstudianteBase): pass
class EstudianteUpdate(EstudianteBase): pass
class EstudianteOut(EstudianteBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class CursoBase(BaseModel):
    codigo: str
    nombre: str
    creditos: int
    docente: str
    ciclo: int

class CursoCreate(CursoBase): pass
class CursoUpdate(CursoBase): pass
class CursoOut(CursoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class MatriculaBase(BaseModel):
    estudiante_id: int
    curso_id: int
    periodo: str
    nota: float | None = None
    estado: str = "MATRICULADO"

class MatriculaCreate(MatriculaBase): pass
class MatriculaUpdate(MatriculaBase): pass
class MatriculaOut(MatriculaBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
