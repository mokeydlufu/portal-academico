<#
.SYNOPSIS
    Script de exportación y empaquetado limpio para despliegue del Portal Académico.
.DESCRIPTION
    Genera un archivo comprimido .zip listo para distribución o despliegue excluyendo:
    - Entornos virtuales (backend/.venv)
    - Archivos de secretos y variables de entorno reales (backend/.env, .env)
    - Caches de Python (__pycache__, *.pyc)
    - Copias de seguridad de prueba y reales (*.backup, *.dump)
    - Enlace simbólico o junction raíz (/app)
    - Logs y archivos temporales
#>

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$destZip = Join-Path $root "portal_academico_dist.zip"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  EMPAQUETADO LIMPIO DEL PORTAL ACADÉMICO PARA DESPLIEGUE  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Eliminar zip anterior si existe
if (Test-Path $destZip) {
    Remove-Item -Force $destZip
    Write-Host "[-] Archivo zip anterior eliminado." -ForegroundColor Gray
}

# Crear directorio temporal para el staging limpio
$tempDir = Join-Path $env:TEMP ("portal_academico_export_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Path $tempDir | Out-Null
Write-Host "[+] Directorio temporal de staging: $tempDir" -ForegroundColor Gray

# Patrones y nombres a excluir
$excludeNames = @(
    ".venv",
    ".env",
    "__pycache__",
    ".pytest_cache",
    ".git",
    "app", # Junction de la raíz (el backend real es backend/app)
    "portal_academico_dist.zip"
)

$excludeExtensions = @(
    ".backup",
    ".dump",
    ".pyc",
    ".pyo",
    ".log",
    ".tmp"
)

Write-Host "[*] Copiando archivos del proyecto con exclusión de artefactos..." -ForegroundColor Yellow

Get-ChildItem -Path $root -Force | ForEach-Object {
    $item = $_
    $itemName = $item.Name

    # Omitir elementos raíz en lista de exclusión
    if ($excludeNames -contains $itemName) {
        Write-Host "  [OMITIDO RAÍZ] $itemName" -ForegroundColor DarkGray
        return
    }

    if ($item.PSIsContainer) {
        # Copiar recursivamente omitiendo patrones
        $targetSub = Join-Path $tempDir $itemName
        New-Item -ItemType Directory -Path $targetSub -Force | Out-Null

        Get-ChildItem -Path $item.FullName -Recurse -Force | ForEach-Object {
            $subItem = $_
            $relPath = $subItem.FullName.Substring($item.FullName.Length + 1)
            $destSubItem = Join-Path $targetSub $relPath

            # Verificar exclusión por nombre de carpeta
            $parts = $relPath.Split([System.IO.Path]::DirectorySeparatorChar)
            foreach ($p in $parts) {
                if ($excludeNames -contains $p) {
                    return
                }
            }

            # Verificar exclusión por extensión
            if ($excludeExtensions -contains $subItem.Extension.ToLower()) {
                return
            }

            # Si es el archivo .env real, omitir
            if ($subItem.Name -eq ".env") {
                return
            }

            if ($subItem.PSIsContainer) {
                if (-not (Test-Path $destSubItem)) {
                    New-Item -ItemType Directory -Path $destSubItem -Force | Out-Null
                }
            } else {
                $destParent = Split-Path $destSubItem -Parent
                if (-not (Test-Path $destParent)) {
                    New-Item -ItemType Directory -Path $destParent -Force | Out-Null
                }
                Copy-Item -Path $subItem.FullName -Destination $destSubItem -Force
            }
        }
    } else {
        if (-not ($excludeExtensions -contains $item.Extension.ToLower()) -and $item.Name -ne ".env") {
            Copy-Item -Path $item.FullName -Destination (Join-Path $tempDir $item.Name) -Force
        }
    }
}

# Asegurar .gitkeep en carpetas de almacenamiento para que existan vacías
$bkDirs = @(
    (Join-Path $tempDir "backend\storage\backups"),
    (Join-Path $tempDir "storage\backups")
)
foreach ($d in $bkDirs) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Path $d -Force | Out-Null
    }
    $gk = Join-Path $d ".gitkeep"
    if (-not (Test-Path $gk)) {
        Set-Content -Path $gk -Value ""
    }
}

Write-Host "[*] Comprimiendo paquete limpio a: $destZip ..." -ForegroundColor Yellow
Compress-Archive -Path "$tempDir\*" -DestinationPath $destZip -Force

# Limpiar temporal
Remove-Item -Recurse -Force $tempDir

$zipSize = (Get-Item $destZip).Length / 1MB
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ("  PAQUETE LIMPIO CREADO EXITOSAMENTE: {0:N2} MB" -f $zipSize) -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Ruta: $destZip" -ForegroundColor White
Write-Host "  Excluidos: backend/.venv, backend/.env, __pycache__, *.backup, /app" -ForegroundColor Cyan
