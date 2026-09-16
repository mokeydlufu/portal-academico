#!/bin/bash
set -e

export PORT=${PORT:-80}

echo "======================================================"
echo "    INICIANDO PORTAL ACADÉMICO UNIFICADO (PRODUCCIÓN)  "
echo "======================================================"
echo "==> Puerto público asignado: $PORT"

# 1. Configurar Nginx con el puerto dinámico de Render
echo "==> Configurando proxy inverso Nginx..."
envsubst '${PORT}' < /app/nginx.conf.template > /etc/nginx/conf.d/default.conf
rm -f /etc/nginx/sites-enabled/default

# 1.5 Ejecutar migración y seed inicial (idempotente)
echo "==> Ejecutando migraciones y seed de base de datos..."
python /app/database/run_migration_and_seed.py || echo "[WARN] Seed ejecutado previamente o no crítico."

# 2. Iniciar Backend FastAPI en background (127.0.0.1:8000)
echo "==> Iniciando Backend FastAPI (Python)..."
cd /app/backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 &

# 3. Iniciar Frontend PHP en background (127.0.0.1:8080)
echo "==> Iniciando Frontend PHP..."
cd /app
php -S 127.0.0.1:8080 -t frontend &

# 4. Esperar un instante para que ambos servicios inicialicen
sleep 3

# 5. Iniciar Nginx en primer plano (recibe el tráfico público de Render)
echo "==> Sistema listo. Nginx escuchando en el puerto $PORT."
exec nginx -g "daemon off;"
