FROM python:3.11-slim

# Instalar dependencias del sistema: PHP, Nginx, PostgreSQL Client (para pg_dump/pg_restore) y utilidades
RUN apt-get update && apt-get install -y --no-install-recommends \
    php-cli \
    php-curl \
    php-pgsql \
    php-mbstring \
    postgresql-client \
    nginx \
    gettext-base \
    curl \
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
