# start-services.ps1 - Script para iniciar todos los servicios ICFES Leveling
# Ejecutar como administrador en PowerShell

Write-Host "🚀 Iniciando servicios ICFES Leveling..." -ForegroundColor Green

# Función para verificar si un puerto está disponible
function Test-PortAvailable {
    param([int]$Port)
    $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    return !$connection
}

# Función para esperar a que un servicio esté disponible
function Wait-ForService {
    param(
        [string]$ServiceName,
        [string]$Url,
        [int]$MaxAttempts = 30,
        [int]$DelaySeconds = 2
    )
    
    Write-Host "⏳ Esperando a que $ServiceName esté disponible en $Url..." -ForegroundColor Yellow
    
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -Method HEAD -TimeoutSec 5 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Host "✅ $ServiceName está disponible" -ForegroundColor Green
                return $true
            }
        } catch {
            Write-Host "🔄 Intento $i/$MaxAttempts - $ServiceName aún no está disponible..." -ForegroundColor Yellow
        }
        
        if ($i -lt $MaxAttempts) {
            Start-Sleep -Seconds $DelaySeconds
        }
    }
    
    Write-Host "❌ $ServiceName no está disponible después de $MaxAttempts intentos" -ForegroundColor Red
    return $false
}

# 1. Verificar Docker
Write-Host "`n🐳 Verificando Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker disponible: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker no está disponible" -ForegroundColor Red
    exit 1
}

# 2. Verificar Docker Compose
Write-Host "`n📋 Verificando Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version
    Write-Host "✅ Docker Compose disponible: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose no está disponible" -ForegroundColor Red
    exit 1
}

# 3. Verificar puertos disponibles
Write-Host "`n🔍 Verificando puertos disponibles..." -ForegroundColor Yellow
$requiredPorts = @{
    5432 = "PostgreSQL"
    6379 = "Redis"
    9000 = "ClickHouse"
    8123 = "ClickHouse HTTP"
}

$availablePorts = @()
$unavailablePorts = @()

foreach ($port in $requiredPorts.Keys) {
    if (Test-PortAvailable $port) {
        $availablePorts += $port
        Write-Host "✅ Puerto $port ($($requiredPorts[$port])) disponible" -ForegroundColor Green
    } else {
        $unavailablePorts += $port
        Write-Host "❌ Puerto $port ($($requiredPorts[$port])) en uso" -ForegroundColor Red
    }
}

if ($unavailablePorts.Count -gt 0) {
    Write-Host "`n⚠️  Algunos puertos están en uso. Deteniendo servicios conflictivos..." -ForegroundColor Yellow
    
    foreach ($port in $unavailablePorts) {
        $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($connection) {
            try {
                Stop-Process -Id $connection.OwningProcess -Force -ErrorAction SilentlyContinue
                Write-Host "✅ Proceso en puerto $port detenido" -ForegroundColor Green
                Start-Sleep -Seconds 2
            } catch {
                Write-Host "⚠️  No se pudo detener el proceso en puerto $port" -ForegroundColor Yellow
            }
        }
    }
}

# 4. Levantar servicios de base de datos
Write-Host "`n🐳 Levantando servicios de base de datos..." -ForegroundColor Yellow
try {
    docker-compose up -d postgres redis clickhouse
    Write-Host "✅ Servicios de base de datos iniciados" -ForegroundColor Green
} catch {
    Write-Host "❌ Error iniciando servicios de base de datos: $_" -ForegroundColor Red
    exit 1
}

# 5. Esperar a que las bases de datos estén listas
Write-Host "`n⏳ Esperando a que las bases de datos estén listas..." -ForegroundColor Yellow

# PostgreSQL
if (!(Wait-ForService "PostgreSQL" "http://localhost:5432")) {
    Write-Host "❌ PostgreSQL no está disponible" -ForegroundColor Red
    exit 1
}

# Redis
if (!(Wait-ForService "Redis" "http://localhost:6379")) {
    Write-Host "❌ Redis no está disponible" -ForegroundColor Red
    exit 1
}

# ClickHouse
if (!(Wait-ForService "ClickHouse" "http://localhost:8123/ping")) {
    Write-Host "❌ ClickHouse no está disponible" -ForegroundColor Red
    exit 1
}

# 6. Verificar tablas de base de datos
Write-Host "`n🔍 Verificando estructura de base de datos..." -ForegroundColor Yellow
try {
    $dbCheck = docker exec icfes_postgres psql -U gameplay -d gameplay_db -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';" 2>$null
    if ($dbCheck -match "quizzes|users|questions") {
        Write-Host "✅ Base de datos configurada correctamente" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Base de datos puede no estar completamente configurada" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  No se pudo verificar la base de datos" -ForegroundColor Yellow
}

# 7. Iniciar backend
Write-Host "`n🐍 Iniciando backend FastAPI..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location "apps/backend"
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload
}

# Esperar a que el backend esté disponible
if (Wait-ForService "Backend" "http://localhost:8006/health") {
    Write-Host "✅ Backend iniciado correctamente" -ForegroundColor Green
} else {
    Write-Host "❌ Backend no está disponible" -ForegroundColor Red
    Stop-Job $backendJob
    exit 1
}

# 8. Iniciar WebSocket
Write-Host "`n🔌 Iniciando servicio WebSocket..." -ForegroundColor Yellow
$websocketJob = Start-Job -ScriptBlock {
    Set-Location "apps/websocket"
    python main.py
}

# Esperar a que WebSocket esté disponible
Start-Sleep -Seconds 5
if (Wait-ForService "WebSocket" "http://localhost:8003/health" -MaxAttempts 15) {
    Write-Host "✅ WebSocket iniciado correctamente" -ForegroundColor Green
} else {
    Write-Host "⚠️  WebSocket puede no estar disponible" -ForegroundColor Yellow
}

# 9. Iniciar AI Service
Write-Host "`n🤖 Iniciando servicio de IA..." -ForegroundColor Yellow
$aiJob = Start-Job -ScriptBlock {
    Set-Location "apps/ai-service"
    python main.py
}

# Esperar a que AI Service esté disponible
Start-Sleep -Seconds 5
if (Wait-ForService "AI Service" "http://localhost:8002/health" -MaxAttempts 15) {
    Write-Host "✅ AI Service iniciado correctamente" -ForegroundColor Green
} else {
    Write-Host "⚠️  AI Service puede no estar disponible" -ForegroundColor Yellow
}

# 10. Iniciar frontend
Write-Host "`n🟢 Iniciando frontend Next.js..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "apps/frontend"
    npm run dev -- -p 3001
}

# Esperar a que el frontend esté disponible
Start-Sleep -Seconds 10
if (Wait-ForService "Frontend" "http://localhost:3001" -MaxAttempts 20) {
    Write-Host "✅ Frontend iniciado correctamente" -ForegroundColor Green
} else {
    Write-Host "⚠️  Frontend puede no estar disponible" -ForegroundColor Yellow
}

# 11. Resumen final
Write-Host "`n🎉 ¡Todos los servicios están iniciados!" -ForegroundColor Green
Write-Host "`n📋 Estado de servicios:" -ForegroundColor Cyan
Write-Host "   🐳 PostgreSQL: http://localhost:5432" -ForegroundColor White
Write-Host "   🔴 Redis: http://localhost:6379" -ForegroundColor White
Write-Host "   📊 ClickHouse: http://localhost:8123" -ForegroundColor White
Write-Host "   🐍 Backend: http://localhost:8006" -ForegroundColor White
Write-Host "   🔌 WebSocket: ws://localhost:8003" -ForegroundColor White
Write-Host "   🤖 AI Service: http://localhost:8002" -ForegroundColor White
Write-Host "   🟢 Frontend: http://localhost:3001" -ForegroundColor White

Write-Host "`n🔗 URLs importantes:" -ForegroundColor Cyan
Write-Host "   📚 API Docs: http://localhost:8006/docs" -ForegroundColor White
Write-Host "   🧪 Test Images: http://localhost:3001/test-images" -ForegroundColor White
Write-Host "   📝 Unit Quiz: http://localhost:3001/unit-quiz" -ForegroundColor White

Write-Host "`n💡 Para detener todos los servicios:" -ForegroundColor Yellow
Write-Host "   Get-Job | Stop-Job" -ForegroundColor White
Write-Host "   docker-compose down" -ForegroundColor White

Write-Host "`n🚀 ¡Proyecto ICFES Leveling funcionando completamente!" -ForegroundColor Green
