# test-e2e.ps1 - Script completo de test E2E para ICFES Leveling
# Ejecutar como administrador en PowerShell

Write-Host "INICIANDO TEST E2E COMPLETO - ICFES LEVELING" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# 1. VERIFICACIÓN DE PUERTOS
Write-Host "`nPASO 1: Verificando puertos del sistema..." -ForegroundColor Yellow
$ports = @(
    @{Port=4001; Service="Frontend"; URL="http://localhost:4001"},
    @{Port=4000; Service="Backend"; URL="http://localhost:4000/health"},
    @{Port=4002; Service="WebSocket"; URL="http://localhost:4002/health"},
    @{Port=8002; Service="AI Service"; URL="http://localhost:8002/health"},
    @{Port=5433; Service="PostgreSQL"; URL="N/A"},
    @{Port=6379; Service="Redis"; URL="N/A"},
    @{Port=9000; Service="ClickHouse"; URL="N/A"},
    @{Port=8123; Service="ClickHouse HTTP"; URL="N/A"}
)

$portStatus = @{}
foreach ($portInfo in $ports) {
    $port = $portInfo.Port
    $service = $portInfo.Service
    $url = $portInfo.URL
    
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connection) {
        $portStatus[$port] = $true
        Write-Host "OK Puerto $port ($service) - ACTIVO" -ForegroundColor Green
    } else {
        $portStatus[$port] = $false
        Write-Host "ERROR Puerto $port ($service) - INACTIVO" -ForegroundColor Red
    }
}

# 2. VERIFICACIÓN DE SERVICIOS DOCKER
Write-Host "`nPASO 2: Verificando servicios Docker..." -ForegroundColor Yellow
try {
    $dockerServices = docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    Write-Host "OK Servicios Docker:" -ForegroundColor Green
    Write-Host $dockerServices -ForegroundColor White
} catch {
    Write-Host "ERROR Error verificando Docker: $_" -ForegroundColor Red
}

# 3. TEST DE CONECTIVIDAD HTTP
Write-Host "`nPASO 3: Test de conectividad HTTP..." -ForegroundColor Yellow
$httpTests = @(
    @{URL="http://localhost:4000/health"; Service="Backend API"},
    @{URL="http://localhost:4002/health"; Service="WebSocket Service (expect 426)"},
    @{URL="http://localhost:8002/health"; Service="AI Service"}
)

foreach ($test in $httpTests) {
    try {
        $response = Invoke-WebRequest -Uri $test.URL -TimeoutSec 10 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "OK $($test.Service): $($test.URL) - OK ($($response.StatusCode))" -ForegroundColor Green
        } else {
            Write-Host "WARNING $($test.Service): $($test.URL) - Status: $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        # WebSocket health endpoint over HTTP often returns 426 Upgrade Required which is acceptable
        if ($test.URL -like "http://localhost:4002/*" -and $_.Exception.Response.StatusCode.value__ -eq 426) {
            Write-Host "OK $($test.Service): $($test.URL) - 426 Upgrade Required (esperado)" -ForegroundColor Green
        } else {
            Write-Host "ERROR $($test.Service): $($test.URL) - ERROR: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# 4. VERIFICACIÓN DE ARCHIVOS DE CONFIGURACIÓN
Write-Host "`nPASO 4: Verificando archivos de configuración..." -ForegroundColor Yellow

# Frontend .env.local
    $frontendEnv = "apps/frontend/.env.local"
if (Test-Path $frontendEnv) {
    Write-Host "OK Archivo de configuracion frontend encontrado" -ForegroundColor Green
    $envContent = Get-Content $frontendEnv
    Write-Host "   Contenido:" -ForegroundColor White
    $envContent | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
} else {
    Write-Host "ERROR Archivo de configuracion frontend NO encontrado" -ForegroundColor Red
}

# Backend config.py
$backendConfig = "apps/backend/app/core/config.py"
if (Test-Path $backendConfig) {
    Write-Host "OK Archivo de configuracion backend encontrado" -ForegroundColor Green
} else {
    Write-Host "ERROR Archivo de configuracion backend NO encontrado" -ForegroundColor Red
}

# 5. VERIFICACIÓN DE BASE DE DATOS
Write-Host "`n[DB] PASO 5: Verificando base de datos..." -ForegroundColor Yellow
try {
    $dbTest = docker exec icfes_postgres psql -U gameplay -d gameplay_db -c "SELECT version();" 2>$null
    if ($dbTest) {
        Write-Host "OK Conexion a PostgreSQL exitosa" -ForegroundColor Green
    } else {
        Write-Host "ERROR Error conectando a PostgreSQL" -ForegroundColor Red
    }
} catch {
    Write-Host "ERROR Error verificando base de datos: $_" -ForegroundColor Red
}

# 6. TEST DE FRONTEND
Write-Host "`nPASO 6: Test del frontend..." -ForegroundColor Yellow
try {
    $frontendResponse = Invoke-WebRequest -Uri "http://localhost:4001" -TimeoutSec 10 -ErrorAction Stop
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Host "OK Frontend accesible en http://localhost:4001" -ForegroundColor Green
        Write-Host "   Titulo: $($frontendResponse.ParsedHtml.title)" -ForegroundColor White
    } else {
        Write-Host "WARNING Frontend responde con status: $($frontendResponse.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "ERROR Frontend no accesible: $($_.Exception.Message)" -ForegroundColor Red
}

# 7. VERIFICACIÓN DE LOGS
Write-Host "`nPASO 7: Verificando logs del sistema..." -ForegroundColor Yellow
$logFiles = @(
    "logs/app.log",
    "apps/backend/logs/app.log"
)

foreach ($logFile in $logFiles) {
    if (Test-Path $logFile) {
        $logSize = (Get-Item $logFile).Length
        Write-Host "OK Log $logFile encontrado (Tamano: $logSize bytes)" -ForegroundColor Green
    } else {
        Write-Host "WARNING Log $logFile NO encontrado" -ForegroundColor Yellow
    }
}

# 8. RESUMEN FINAL
Write-Host "`nRESUMEN DEL TEST E2E" -ForegroundColor Cyan
Write-Host "=======================" -ForegroundColor Cyan

$activePorts = ($portStatus.Values | Where-Object { $_ -eq $true }).Count
$totalPorts = $portStatus.Count

Write-Host "Puertos activos: $activePorts/$totalPorts" -ForegroundColor White

if ($activePorts -eq $totalPorts) {
    Write-Host "TODOS LOS SERVICIOS ESTAN FUNCIONANDO!" -ForegroundColor Green
} else {
    Write-Host "Algunos servicios no estan funcionando" -ForegroundColor Yellow
}

Write-Host "`nProximos pasos:" -ForegroundColor Cyan
Write-Host "   1. Si hay errores, revisa los logs de Docker" -ForegroundColor White
Write-Host "   2. Verifica que todos los servicios esten corriendo" -ForegroundColor White
Write-Host "   3. Accede a http://localhost:4001 para probar la aplicacion" -ForegroundColor White
Write-Host "   4. Revisa la documentacion en http://localhost:4000/docs" -ForegroundColor White

Write-Host "`nTest E2E completado!" -ForegroundColor Green
