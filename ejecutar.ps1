Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "      INICIANDO PORTAL ACADEMICO                   " -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

$root = $PSScriptRoot

# 1. Iniciar Backend
Write-Host "[1/2] Iniciando Backend FastAPI (Puerto 8000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000"

Start-Sleep -Seconds 3

# 2. Iniciar Frontend PHP
Write-Host "[2/2] Iniciando Frontend PHP (Puerto 8080)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; php -S localhost:8080 -t frontend"

Start-Sleep -Seconds 2

# 3. Abrir en navegador
Write-Host "Abriendo el navegador..." -ForegroundColor Yellow
Start-Process "http://localhost:8080"

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host " Portal Academico listo:" -ForegroundColor Green
Write-Host " - Frontend:  http://localhost:8080" -ForegroundColor White
Write-Host " - Backend:   http://127.0.0.1:8000" -ForegroundColor White
Write-Host " - Swagger:   http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host " Credenciales de acceso:" -ForegroundColor Yellow
Write-Host " - Correo:      admin@portal.edu.pe" -ForegroundColor White
Write-Host " - Contrasena:  Admin123*" -ForegroundColor White
Write-Host "===================================================" -ForegroundColor Cyan
