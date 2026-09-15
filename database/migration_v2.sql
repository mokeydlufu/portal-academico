-- Migración v2: Tablas académicas completas para Portal Académico

-- 1. Carreras
CREATE TABLE IF NOT EXISTS carreras (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(150) NOT NULL
);

-- 2. Periodos
CREATE TABLE IF NOT EXISTS periodos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- 3. Docentes
CREATE TABLE IF NOT EXISTS docentes (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    email VARCHAR(150)
);

-- 4. Ampliación de Estudiantes (FKs opcionales para usuario_id y carrera_id)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='estudiantes' AND column_name='usuario_id') THEN
        ALTER TABLE estudiantes ADD COLUMN usuario_id INT UNIQUE REFERENCES usuarios(id) ON DELETE SET NULL;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='estudiantes' AND column_name='carrera_id') THEN
        ALTER TABLE estudiantes ADD COLUMN carrera_id INT REFERENCES carreras(id) ON DELETE SET NULL;
    END IF;
END $$;

-- 5. Secciones
CREATE TABLE IF NOT EXISTS secciones (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(30) NOT NULL,
    curso_id INT NOT NULL REFERENCES cursos(id) ON DELETE CASCADE,
    docente_id INT REFERENCES docentes(id) ON DELETE SET NULL,
    periodo_id INT NOT NULL REFERENCES periodos(id) ON DELETE CASCADE
);

-- 6. Tipos de Evaluación
CREATE TABLE IF NOT EXISTS tipos_evaluacion (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(10) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL
);

-- 7. Evaluaciones
CREATE TABLE IF NOT EXISTS evaluaciones (
    id SERIAL PRIMARY KEY,
    seccion_id INT NOT NULL REFERENCES secciones(id) ON DELETE CASCADE,
    tipo_id INT NOT NULL REFERENCES tipos_evaluacion(id) ON DELETE CASCADE,
    nombre VARCHAR(100) NOT NULL,
    peso NUMERIC(5,2) NOT NULL,
    orden INT NOT NULL DEFAULT 1
);

-- 8. Ampliación de Matrículas
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='matriculas' AND column_name='seccion_id') THEN
        ALTER TABLE matriculas ADD COLUMN seccion_id INT REFERENCES secciones(id) ON DELETE CASCADE;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='matriculas' AND column_name='periodo_id') THEN
        ALTER TABLE matriculas ADD COLUMN periodo_id INT REFERENCES periodos(id) ON DELETE CASCADE;
    END IF;
END $$;

-- 9. Notas por Evaluación
CREATE TABLE IF NOT EXISTS notas (
    id SERIAL PRIMARY KEY,
    evaluacion_id INT NOT NULL REFERENCES evaluaciones(id) ON DELETE CASCADE,
    matricula_id INT NOT NULL REFERENCES matriculas(id) ON DELETE CASCADE,
    valor NUMERIC(4,2),
    observaciones VARCHAR(255),
    CONSTRAINT unq_matricula_evaluacion UNIQUE (matricula_id, evaluacion_id)
);

-- 10. Sílabos
CREATE TABLE IF NOT EXISTS silabos (
    id SERIAL PRIMARY KEY,
    curso_id INT NOT NULL REFERENCES cursos(id) ON DELETE CASCADE,
    nombre_archivo VARCHAR(255) NOT NULL,
    ruta_archivo VARCHAR(500) NOT NULL,
    fecha_subida TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
