# ====================================================================
#   PORTAL ACADÉMICO - SCRIPT DE LIMPIEZA DE DATOS DE PRUEBA (PowerShell)
#   Versión: 1.0  |  Fecha: 2026-09-15
# ====================================================================
# Uso:
#   .\limpiar_pruebas.ps1            # Modo interactivo con confirmación
#   .\limpiar_pruebas.ps1 --audit    # Solo auditar sin borrar nada
#   .\limpiar_pruebas.ps1 --force    # Ejecutar sin confirmación manual
# ====================================================================

[CmdletBinding()]
param (
    [switch]$audit,
    [switch]$force
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$venvPython = Join-Path $scriptDir "backend\.venv\Scripts\python.exe"
$pyScript = Join-Path $scriptDir "limpiar_pruebas.py"

if (Test-Path $venvPython) {
    $pythonExe = $venvPython
} else {
    $pythonExe = "python"
}

$argsList = @($pyScript)
if ($audit) { $argsList += "--audit" }
if ($force) { $argsList += "--force" }

# Pasar cualquier argumento adicional
$argsList += $args

& $pythonExe $argsList
