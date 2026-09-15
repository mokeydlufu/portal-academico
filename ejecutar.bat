@echo off
title Portal Academico - Iniciador
echo ===================================================
echo       INICIANDO PORTAL ACADEMICO
echo ===================================================
echo.

REM Iniciar Backend FastAPI en segundo plano / nueva ventana
echo [1/2] Iniciando Backend FastAPI (Puerto 8000)...
start "Backend - FastAPI" cmd /k "cd /d %~dp0backend && .venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

REM Esperar 3 segundos
timeout /t 3 /nobreak >nul

REM Iniciar Frontend PHP en segundo plano / nueva ventana
echo [2/2] Iniciando Frontend PHP (Puerto 8080)...
start "Frontend - PHP" cmd /k "cd /d %~dp0 && php -S localhost:8080 -t frontend"

REM Esperar 2 segundos
timeout /t 2 /nobreak >nul

REM Abrir navegador
echo Abriendo el navegador en http://localhost:8080 ...
start http://localhost:8080

echo.
echo ===================================================
echo  Portal Academico listo:
echo  - Frontend:  http://localhost:8080
echo  - Backend:   http://127.0.0.1:8000
echo  - Swagger:   http://127.0.0.1:8000/docs
echo.
echo  Credenciales de acceso:
echo  - Estudiante:  carlos@portal.edu.pe / Estudiante123*
echo  - Admin:       admin@portal.edu.pe / Admin123*
echo ===================================================
pause
