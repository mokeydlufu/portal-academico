FROM python:3.11-slim

# Instalar dependencias del sistema y el cliente oficial de PostgreSQL 18 para coincidir con Render (v18.6)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    lsb-release \
    ca-certificates \
    postgresql-common \
    && (/usr/share/postgresql-common/pgdg/apt.postgresql.org.sh -y || \
        (curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg && \
         echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list)) \
    && apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client-18 \
    php-cli \
    php-curl \
    php-pgsql \
    php-mbstring \
    nginx \
    gettext-base \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias de Python del Backend
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copiar el código fuente completo del proyecto
COPY . .

# Asegurar permisos y directorio de respaldos
RUN mkdir -p backend/storage/backups && \
    chmod +x /app/entrypoint.sh

EXPOSE 80 8080 10000

CMD ["/app/entrypoint.sh"]
