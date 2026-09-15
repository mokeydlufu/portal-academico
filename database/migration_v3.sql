-- Migración v3: Tablas complementarias para todos los módulos de la Intranet Estudiantil

-- 1. Ampliación de campos en estudiantes
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='estudiantes' AND column_name='telefono') THEN
        ALTER TABLE estudiantes ADD COLUMN telefono VARCHAR(20) DEFAULT '987654321';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='estudiantes' AND column_name='direccion') THEN
        ALTER TABLE estudiantes ADD COLUMN direccion VARCHAR(200) DEFAULT 'Av. Universitaria 1450, Lima';
    END IF;
END $$;

-- 2. Horarios de Secciones
CREATE TABLE IF NOT EXISTS horarios (
    id SERIAL PRIMARY KEY,
    seccion_id INT NOT NULL REFERENCES secciones(id) ON DELETE CASCADE,
    dia VARCHAR(20) NOT NULL, -- Lunes, Martes, etc.
    hora_inicio VARCHAR(10) NOT NULL, -- 08:00
    hora_fin VARCHAR(10) NOT NULL,    -- 10:15
    aula VARCHAR(50) NOT NULL,        -- Lab 402, Aula B-201
    modalidad VARCHAR(30) NOT NULL DEFAULT 'PRESENCIAL'
);

-- 3. Asistencias detalladas por sesión
CREATE TABLE IF NOT EXISTS asistencias (
    id SERIAL PRIMARY KEY,
    matricula_id INT NOT NULL REFERENCES matriculas(id) ON DELETE CASCADE,
    fecha DATE NOT NULL,
    hora VARCHAR(10) NOT NULL,
    estado VARCHAR(20) NOT NULL, -- PRESENTE, FALTA, TARDANZA, JUSTIFICADO
    observacion VARCHAR(255)
);

-- 4. Trámites Académicos
CREATE TABLE IF NOT EXISTS tramites (
    id SERIAL PRIMARY KEY,
    estudiante_id INT NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
    codigo VARCHAR(30) UNIQUE NOT NULL,
    tipo VARCHAR(100) NOT NULL,
    motivo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    estado VARCHAR(30) NOT NULL DEFAULT 'PENDIENTE', -- PENDIENTE, EN REVISION, APROBADO, RECHAZADO
    fecha_solicitud TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_respuesta TIMESTAMP,
    respuesta TEXT
);

-- 5. Pagos y Obligaciones Financieras
CREATE TABLE IF NOT EXISTS pagos (
    id SERIAL PRIMARY KEY,
    estudiante_id INT NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
    periodo_id INT REFERENCES periodos(id) ON DELETE SET NULL,
    concepto VARCHAR(150) NOT NULL,
    monto NUMERIC(8,2) NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    fecha_pago DATE,
    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE', -- CANCELADO, PENDIENTE, VENCIDO
    nro_operacion VARCHAR(50)
);

-- 6. Fichas de Bienestar Universitario
CREATE TABLE IF NOT EXISTS fichas_bienestar (
    id SERIAL PRIMARY KEY,
    estudiante_id INT UNIQUE NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
    contacto_emergencia VARCHAR(150),
    telefono_emergencia VARCHAR(20),
    parentesco_contacto VARCHAR(50),
    direccion_actual VARCHAR(200),
    ocupacion_padres VARCHAR(150),
    ingreso_familiar NUMERIC(8,2),
    condicion_vivienda VARCHAR(100),
    seguro_salud VARCHAR(100) DEFAULT 'Seguro Estudiantil Universitario',
    alergias_condiciones TEXT,
    fecha_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 7. Solicitudes de Examen de Recuperación
CREATE TABLE IF NOT EXISTS solicitudes_recuperacion (
    id SERIAL PRIMARY KEY,
    estudiante_id INT NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
    matricula_id INT NOT NULL REFERENCES matriculas(id) ON DELETE CASCADE,
    motivo VARCHAR(255),
    estado VARCHAR(30) NOT NULL DEFAULT 'PENDIENTE', -- PENDIENTE, APROBADO, RECHAZADO
    fecha_solicitud TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_examen DATE
);

-- 8. Solicitudes de Reprogramación de Evaluaciones
CREATE TABLE IF NOT EXISTS solicitudes_reprogramacion (
    id SERIAL PRIMARY KEY,
    estudiante_id INT NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
    evaluacion_id INT NOT NULL REFERENCES evaluaciones(id) ON DELETE CASCADE,
    matricula_id INT NOT NULL REFERENCES matriculas(id) ON DELETE CASCADE,
    motivo VARCHAR(255) NOT NULL,
    fecha_solicitada DATE,
    sustento TEXT,
    estado VARCHAR(30) NOT NULL DEFAULT 'PENDIENTE', -- PENDIENTE, APROBADO, RECHAZADO
    fecha_solicitud TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 9. Catálogo de Empleos y Prácticas
CREATE TABLE IF NOT EXISTS empleos (
    id SERIAL PRIMARY KEY,
    empresa VARCHAR(150) NOT NULL,
    puesto VARCHAR(150) NOT NULL,
    modalidad VARCHAR(50) NOT NULL, -- Presencial, Remoto, Híbrido
    ubicacion VARCHAR(100) NOT NULL,
    descripcion TEXT NOT NULL,
    requisitos TEXT NOT NULL,
    funciones TEXT,
    remuneracion VARCHAR(50),
    fecha_publicacion DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_limite DATE,
    carrera_afin VARCHAR(150)
);

-- 10. Postulaciones del Estudiante
CREATE TABLE IF NOT EXISTS postulaciones (
    id SERIAL PRIMARY KEY,
    estudiante_id INT NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
    empleo_id INT NOT NULL REFERENCES empleos(id) ON DELETE CASCADE,
    fecha_postulacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(30) NOT NULL DEFAULT 'ENVIADA', -- ENVIADA, EN REVISION, PRESELECCIONADO, FINALIZADO
    CONSTRAINT unq_estudiante_empleo UNIQUE (estudiante_id, empleo_id)
);

-- 11. Encuestas de Desempeño Docente
CREATE TABLE IF NOT EXISTS encuestas_docente (
    id SERIAL PRIMARY KEY,
    estudiante_id INT NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
    seccion_id INT NOT NULL REFERENCES secciones(id) ON DELETE CASCADE,
    calificacion INT NOT NULL CHECK(calificacion BETWEEN 1 AND 5),
    comentarios TEXT,
    estado VARCHAR(20) NOT NULL DEFAULT 'COMPLETADA',
    fecha_respuesta TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unq_estudiante_seccion_encuesta UNIQUE (estudiante_id, seccion_id)
);

-- 12. Avisos Académicos
CREATE TABLE IF NOT EXISTS avisos_academicos (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    contenido TEXT NOT NULL,
    fecha DATE NOT NULL DEFAULT CURRENT_DATE,
    tipo VARCHAR(30) NOT NULL DEFAULT 'INFORMATIVO' -- URGENTE, INFORMATIVO, ACADEMICO
);
