CREATE TABLE IF NOT EXISTS usuarios (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(120) NOT NULL,
  correo VARCHAR(150) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  rol VARCHAR(30) NOT NULL DEFAULT 'ADMIN',
  activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS estudiantes (
  id SERIAL PRIMARY KEY,
  codigo VARCHAR(20) UNIQUE NOT NULL,
  nombres VARCHAR(100) NOT NULL,
  apellidos VARCHAR(100) NOT NULL,
  dni VARCHAR(8) UNIQUE NOT NULL,
  correo VARCHAR(150) UNIQUE NOT NULL,
  carrera VARCHAR(120) NOT NULL,
  ciclo INT NOT NULL CHECK(ciclo BETWEEN 1 AND 12),
  fecha_ingreso DATE NOT NULL,
  estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO'
);

CREATE TABLE IF NOT EXISTS cursos (
  id SERIAL PRIMARY KEY,
  codigo VARCHAR(20) UNIQUE NOT NULL,
  nombre VARCHAR(120) NOT NULL,
  creditos INT NOT NULL,
  docente VARCHAR(120) NOT NULL,
  ciclo INT NOT NULL
);

CREATE TABLE IF NOT EXISTS matriculas (
  id SERIAL PRIMARY KEY,
  estudiante_id INT NOT NULL REFERENCES estudiantes(id) ON DELETE CASCADE,
  curso_id INT NOT NULL REFERENCES cursos(id) ON DELETE CASCADE,
  periodo VARCHAR(20) NOT NULL,
  nota NUMERIC(5,2),
  estado VARCHAR(20) NOT NULL DEFAULT 'MATRICULADO'
);

-- El usuario administrador inicial se crea automáticamente al iniciar FastAPI.

INSERT INTO estudiantes (codigo,nombres,apellidos,dni,correo,carrera,ciclo,fecha_ingreso,estado) VALUES
('2026001','Carlos','Quispe','76543210','carlos@portal.edu.pe','Ingeniería de Sistemas de Información',8,'2026-03-15','ACTIVO'),
('2026002','Ana','Huamán','71234567','ana@portal.edu.pe','Ingeniería de Sistemas de Información',6,'2026-03-15','ACTIVO')
ON CONFLICT DO NOTHING;

INSERT INTO cursos (codigo,nombre,creditos,docente,ciclo) VALUES
('BD-801','Gestión de Base de Datos',4,'Ing. Erick Palomino',8),
('SW-802','Ingeniería de Software',4,'Ing. María Torres',8)
ON CONFLICT DO NOTHING;
