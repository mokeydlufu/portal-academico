# Portal Académico - PHP + FastAPI + PostgreSQL

Sistema web de gestión académica e intranet institucional con diseño unificado **Student Intranet / Admin Dashboard SPA**.

---

## 🚀 Arquitectura y Tecnologías
- **Frontend**: PHP 8.2+, Tailwind CSS (diseño unificado azul pizarra `#0f172a`, acentos en `#f4511e` y rose, acordeones interactivos `+` / `-`, arquitectura SPA), Font Awesome 6.5.2, JavaScript nativo con Fetch API.
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0+, Pydantic v2, Uvicorn con worker asíncrono en segundo plano.
- **Base de Datos**: PostgreSQL 14+ (27 tablas académicas e índices optimizados).
- **Herramientas de Respaldo**: PostgreSQL `pg_dump` y `pg_restore` nativos (formato binario Custom comprimido `-F c`).

---

## 🔐 Credenciales de Acceso

| Rol | Correo | Contraseña | Portal Asignado |
| :--- | :--- | :--- | :--- |
| **Administrador** | `admin@portal.edu.pe` | `Admin123*` | `/dashboard.php` (Acceso Total + Módulo de Backups) |
| **Estudiante** | `carlos@portal.edu.pe` | `Estudiante123*` | `/notas.php` (Intranet Académica Estudiantil) |

> **Aislamiento de Seguridad**: Los estudiantes tienen acceso exclusivo a sus notas y trámites. El módulo de Copias de Seguridad está estrictamente restringido a administradores (retorna `403 Forbidden` en API y no aparece en la interfaz estudiantil).

---

## 💾 Módulo Profesional de Copias de Seguridad (Backups)

El sistema cuenta con un motor de respaldos y restauraciones de base de datos PostgreSQL:

### 1. Características Principales
- **Copias Binarias Reales**: Ejecuta `pg_dump -F c` comprimido de la base `portal_academico` sin simulaciones.
- **Validación de Integridad**: Verifica tamaño físico en disco y consistencia mediante `pg_restore --list`.
- **Descarga Segura**: Descarga autenticada mediante Blob HTTP o token firmado con protección contra Path Traversal.
- **Restauración Segura en Base de Prueba**: Permite restaurar cualquier dump en una base de datos aislada (ej. `portal_academico_restaurado_prueba`) para certificar la integridad de las 27 tablas sin alterar la base productiva.
- **Protección Anti-Colisión**: Dos candados consultivos PostgreSQL (`pg_try_advisory_lock` con IDs `88812345` y `88812346`) garantizan que nunca se ejecuten 2 copias de seguridad de forma simultánea, incluso en entornos con múltiples réplicas o workers de Uvicorn.
- **Auditoría Exhaustiva**: Registro de fecha/hora de inicio, fin, duración exacta, archivo generado, usuario responsable, disparador y estado (`CORRECTO` / `ERROR`).

### 2. Programación Automática de Backups
Permite programar copias desatendidas que se ejecutan automáticamente en el backend (aunque el navegador del administrador esté cerrado):
- **Precisión Horaria**: Formato `HH:MM:SS` (horas, minutos y segundos).
- **Frecuencias Disponibles**:
  - **Diaria**: Se ejecuta todos los días a la hora fijada `HH:MM:SS`.
  - **Semanal**: Se ejecuta el día de la semana configurado (Lunes a Domingo) a la hora fijada.
  - **Cada N Horas**: Intervalo recurrente en horas (mínimo 1 hora).
  - **Cada N Minutos**: Intervalo recurrente en minutos (mínimo 1 minuto).
  - **Cada N Segundos (Modo Pruebas)**: Permite programar intervalos a partir de 10 segundos para demostraciones y laboratorios inmediatos.
- **Cálculo de Próxima Ejecución**: Fecha y hora exacta (`DD/MM/YYYY HH:MM:SS`) calculada en la zona horaria `America/Lima`.
- **Botón "Ejecutar ahora"**: Permite forzar la ejecución de cualquier tarea programada de manera instantánea bajo demanda.
- **Política de Retención Automática**: Los respaldos antiguos que superen los días de retención configurados se eliminan físicamente del disco, preservando su traza histórica con estado `ELIMINADO_RETENCION`.

---

## ⚙️ Variables de Entorno (`backend/.env`)

```ini
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/portal_academico
SECRET_KEY=clave_secreta_super_segura_portal_academico_2026
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Configuración de Copias de Seguridad
BACKUP_DIR=storage/backups
BACKUP_TIMEZONE=America/Lima

# Rutas de ejecutables de PostgreSQL (Windows / Linux)
PG_DUMP_PATH=D:\Program Files\PostgreSQL\17\bin\pg_dump.exe
PG_RESTORE_PATH=D:\Program Files\PostgreSQL\17\bin\pg_restore.exe
```

> **Persistencia en Docker / Producción**: En entornos contenedorizados, se debe montar un volumen persistente para la carpeta de almacenamiento de backups (ej: `-v /var/data/portal_backups:/app/storage/backups`).

---

## 📦 Puesta en Marcha Local

### 1. Base de Datos
```bash
# Crear base de datos en PostgreSQL
createdb -U postgres portal_academico

# Ejecutar esquema académico y migración de backups
psql -U postgres -d portal_academico -f database/schema.sql
python database/run_migration_backups.py
```

### 2. Backend (FastAPI)
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
- Swagger API Docs: `http://127.0.0.1:8000/docs`

### 3. Frontend (PHP)
Desde la raíz del proyecto:
```bash
php -S localhost:8080 -t frontend
```
- Portal Web: `http://localhost:8080`

---

## 🧪 Pruebas Automatizadas

El proyecto incluye dos suites completas de pruebas automatizadas:

```bash
# 1. Pruebas base del módulo de copias de seguridad (10 pruebas)
python backend/test_backups_module.py

# 2. Pruebas exhaustivas de todas las opciones de programación automática (9 pruebas)
python backend/test_scheduling_options.py
```

---

## ⚠️ Empaquetado y Distribución
Al generar archivos comprimidos (`.zip` o `.tar.gz`) para entrega o despliegue, **NUNCA** incluir la carpeta del entorno virtual `backend/.venv` (ya excluida en el `.gitignore` raíz).
