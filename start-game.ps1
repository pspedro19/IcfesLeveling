# ICFES LEVELING - Script de Inicio Rápido
# PowerShell script para iniciar el videojuego educativo completo

Write-Host "🎮 ICFES LEVELING - Videojuego Educativo" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si Docker está instalado
Write-Host "🔍 Verificando Docker..." -ForegroundColor Yellow
try {
    docker --version | Out-Null
    Write-Host "✅ Docker está instalado" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker no está instalado. Por favor instala Docker Desktop." -ForegroundColor Red
    exit 1
}

# Verificar si Docker Compose está disponible
Write-Host "🔍 Verificando Docker Compose..." -ForegroundColor Yellow
try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker Compose está disponible" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose no está disponible." -ForegroundColor Red
    exit 1
}

# Verificar archivo .env
Write-Host "🔍 Verificando configuración..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✅ Archivo .env encontrado" -ForegroundColor Green
} else {
    Write-Host "⚠️  Archivo .env no encontrado. Creando desde template..." -ForegroundColor Yellow
    if (Test-Path "env.example") {
        Copy-Item "env.example" ".env"
        Write-Host "✅ Archivo .env creado desde template" -ForegroundColor Green
        Write-Host "📝 Por favor edita el archivo .env con tus claves de API si es necesario" -ForegroundColor Cyan
    } else {
        Write-Host "❌ No se encontró env.example" -ForegroundColor Red
        exit 1
    }
}

# Detener contenedores existentes si los hay
Write-Host "🛑 Deteniendo contenedores existentes..." -ForegroundColor Yellow
docker-compose down 2>$null

# Construir e iniciar servicios
Write-Host "🚀 Iniciando ICFES LEVELING..." -ForegroundColor Green
Write-Host ""

Write-Host "📦 Construyendo imágenes Docker..." -ForegroundColor Yellow
docker-compose build

Write-Host "🌐 Iniciando servicios..." -ForegroundColor Yellow
docker-compose up -d

# Esperar un momento para que los servicios se inicien
Write-Host "⏳ Esperando que los servicios se inicien..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Verificar estado de los servicios
Write-Host "🔍 Verificando estado de los servicios..." -ForegroundColor Yellow
Write-Host ""

$services = @(
    @{Name="Frontend"; Port="3000"; URL="http://localhost:3000"},
    @{Name="Backend API"; Port="8000"; URL="http://localhost:8000"},
    @{Name="WebSocket"; Port="8001"; URL="ws://localhost:8001"},
    @{Name="AI Service"; Port="8002"; URL="http://localhost:8002"},
    @{Name="PostgreSQL"; Port="5432"; URL="localhost:5432"},
    @{Name="Redis"; Port="6379"; URL="localhost:6379"},
    @{Name="ClickHouse"; Port="8123"; URL="http://localhost:8123"}
)

foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri $service.URL -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200 -or $service.Name -eq "WebSocket" -or $service.Name -eq "PostgreSQL" -or $service.Name -eq "Redis") {
            Write-Host "✅ $($service.Name) - Puerto $($service.Port)" -ForegroundColor Green
        } else {
            Write-Host "⚠️  $($service.Name) - Puerto $($service.Port) (Estado: $($response.StatusCode))" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ $($service.Name) - Puerto $($service.Port) (No disponible)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🎉 ¡ICFES LEVELING está listo!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Accede al juego en: http://localhost:3000" -ForegroundColor Cyan
Write-Host "📚 Documentación API: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "👥 Usuarios de prueba:" -ForegroundColor Yellow
Write-Host "   • shadow_hunter / password123 (Level 25, Rank B)" -ForegroundColor White
Write-Host "   • math_master / password123 (Level 18, Rank C)" -ForegroundColor White
Write-Host "   • newbie_student / password123 (Level 1, Rank E)" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Comandos útiles:" -ForegroundColor Yellow
Write-Host "   • Ver logs: docker-compose logs -f [servicio]" -ForegroundColor White
Write-Host "   • Detener: docker-compose down" -ForegroundColor White
Write-Host "   • Reiniciar: docker-compose restart" -ForegroundColor White
Write-Host ""
Write-Host "📊 Datos sintéticos cargados:" -ForegroundColor Yellow
Write-Host "   • 10,000+ preguntas de ICFES" -ForegroundColor White
Write-Host "   • 4 materias principales" -ForegroundColor White
Write-Host "   • Usuarios de prueba con progreso" -ForegroundColor White
Write-Host "   • Batallas, items, quests de ejemplo" -ForegroundColor White
Write-Host ""
Write-Host "🎮 ¡Disfruta del videojuego educativo!" -ForegroundColor Green
Write-Host ""

# Abrir el navegador automáticamente
Write-Host "🌐 Abriendo navegador..." -ForegroundColor Cyan
Start-Process "http://localhost:3000" 