# ============================================
# ICFES Leveling - Script de Inicio de Desarrollo
# ============================================

Write-Host @"

  ___  ____ _____ _____ ____    _                    _ _
 |_ _|/ ___|  ___| ____/ ___|  | |    _____   _____| (_)_ __   __ _
  | || |   | |_  |  _| \___ \  | |   / _ \ \ / / _ \ | | '_ \ / _` |
  | || |___|  _| | |___ ___) | | |__|  __/\ V /  __/ | | | | | (_| |
 |___|\____|_|   |_____|____/  |_____\___| \_/ \___|_|_|_| |_|\__, |
                                                              |___/
"@ -ForegroundColor Cyan

# Configurar variables de entorno
Write-Host "`n[1/6] Configurando variables de entorno..." -ForegroundColor Yellow
$env:JAVA_HOME = "C:\Program Files\Microsoft\jdk-17.0.9.8-hotspot"
$env:ANDROID_HOME = "C:\android_sdk"
$env:ANDROID_SDK_ROOT = "C:\android_sdk"
$env:PATH = "C:\flutter\bin;$env:JAVA_HOME\bin;$env:ANDROID_HOME\cmdline-tools\latest\bin;$env:ANDROID_HOME\platform-tools;$env:PATH"
Write-Host "   JAVA_HOME = $env:JAVA_HOME" -ForegroundColor Gray
Write-Host "   ANDROID_HOME = $env:ANDROID_HOME" -ForegroundColor Gray

# Ir al proyecto
Set-Location "C:\Users\pedro\OneDrive\Documents\ICFESLEVELING\IcfesLeveling"

# Verificar Docker
Write-Host "`n[2/6] Verificando Docker..." -ForegroundColor Yellow
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   ERROR: Docker no esta corriendo. Inicia Docker Desktop primero." -ForegroundColor Red
        exit 1
    }
    Write-Host "   Docker OK" -ForegroundColor Green
} catch {
    Write-Host "   ERROR: Docker no encontrado" -ForegroundColor Red
    exit 1
}

# Iniciar servicios Docker
Write-Host "`n[3/6] Iniciando servicios Docker..." -ForegroundColor Yellow
docker-compose up -d postgres redis clickhouse backend
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERROR al iniciar Docker Compose" -ForegroundColor Red
    exit 1
}

# Esperar a que inicien
Write-Host "`n[4/6] Esperando que los servicios inicien (60s)..." -ForegroundColor Yellow
$totalSeconds = 60
for ($i = 0; $i -lt $totalSeconds; $i += 5) {
    $percent = [math]::Round(($i / $totalSeconds) * 100)
    Write-Progress -Activity "Esperando servicios" -Status "$percent% completado" -PercentComplete $percent
    Start-Sleep -Seconds 5
}
Write-Progress -Activity "Esperando servicios" -Completed

# Verificar backend
Write-Host "`n[5/6] Verificando Backend..." -ForegroundColor Yellow
$maxRetries = 5
$retryCount = 0
$backendOk = $false

while ($retryCount -lt $maxRetries -and -not $backendOk) {
    try {
        $health = Invoke-RestMethod -Uri "http://localhost:4000/health" -TimeoutSec 10
        Write-Host "   Backend OK!" -ForegroundColor Green
        $backendOk = $true
    } catch {
        $retryCount++
        if ($retryCount -lt $maxRetries) {
            Write-Host "   Reintentando... ($retryCount/$maxRetries)" -ForegroundColor Gray
            Start-Sleep -Seconds 10
        }
    }
}

if (-not $backendOk) {
    Write-Host "   Backend no responde. Verificar logs:" -ForegroundColor Red
    Write-Host "   docker logs icfes_backend --tail 50" -ForegroundColor Gray
}

# Flutter check
Write-Host "`n[6/6] Verificando Flutter..." -ForegroundColor Yellow
$flutterVersion = flutter --version 2>&1 | Select-String "Flutter"
if ($flutterVersion) {
    Write-Host "   $flutterVersion" -ForegroundColor Green
} else {
    Write-Host "   Flutter no encontrado en PATH" -ForegroundColor Red
}

# Resumen
Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host " DESARROLLO LISTO " -ForegroundColor Green -BackgroundColor Black
Write-Host "="*60 -ForegroundColor Cyan

Write-Host @"

URLs Disponibles:
  - Swagger API:  http://localhost:4000/docs
  - Health Check: http://localhost:4000/health
  - pgAdmin:      http://localhost:5050 (admin@icfes.com / admin123)

Comandos rapidos:
  - Ver logs backend:    docker logs icfes_backend -f
  - Correr app Flutter:  cd apps/mobile; flutter run -d chrome
  - Parar Docker:        docker-compose down

"@ -ForegroundColor White

# Mantener terminal abierta
Write-Host "Presiona Enter para abrir la carpeta mobile..." -ForegroundColor Yellow
Read-Host
Set-Location "apps/mobile"
Write-Host "`nAhora puedes ejecutar: flutter run -d chrome" -ForegroundColor Cyan
