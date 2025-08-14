# Script para iniciar el Backend ICFES Leveling
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Iniciando Backend ICFES Leveling" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si Python está instalado
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Python no está instalado o no está en el PATH" -ForegroundColor Red
    Write-Host "Por favor, instala Python desde https://python.org" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Verificar si estamos en el directorio correcto
if (-not (Test-Path "app")) {
    Write-Host "❌ ERROR: No se encontró el directorio 'app'" -ForegroundColor Red
    Write-Host "Asegúrate de ejecutar este script desde apps/backend/" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Verificar si existe el entorno virtual
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creando entorno virtual..." -ForegroundColor Yellow
    try {
        python -m venv venv
        Write-Host "✅ Entorno virtual creado exitosamente" -ForegroundColor Green
    } catch {
        Write-Host "❌ ERROR: No se pudo crear el entorno virtual" -ForegroundColor Red
        Read-Host "Presiona Enter para salir"
        exit 1
    }
}

# Activar entorno virtual
Write-Host "🔧 Activando entorno virtual..." -ForegroundColor Yellow
try {
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "✅ Entorno virtual activado" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: No se pudo activar el entorno virtual" -ForegroundColor Red
    Write-Host "Intenta ejecutar: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Verificar e instalar dependencias
Write-Host "📋 Verificando dependencias..." -ForegroundColor Yellow
try {
    $fastapiInstalled = pip show fastapi 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "📦 Instalando dependencias..." -ForegroundColor Yellow
        pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ ERROR: No se pudieron instalar las dependencias" -ForegroundColor Red
            Read-Host "Presiona Enter para salir"
            exit 1
        }
        Write-Host "✅ Dependencias instaladas exitosamente" -ForegroundColor Green
    } else {
        Write-Host "✅ Dependencias ya están instaladas" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ ERROR: Error al verificar dependencias" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    Configuración del Servidor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Host: 0.0.0.0" -ForegroundColor White
Write-Host "Puerto: 4000" -ForegroundColor White
Write-Host "URL: http://localhost:4000" -ForegroundColor White
Write-Host ""
Write-Host "Presiona Ctrl+C para detener el servidor" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Iniciar el servidor
try {
    Write-Host "🚀 Iniciando servidor..." -ForegroundColor Green
    python -m uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload
} catch {
    Write-Host "❌ ERROR: No se pudo iniciar el servidor" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "Servidor detenido." -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
} 