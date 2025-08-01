# ICFES LEVELING - Quick Start Script for Windows
# Este script levanta todo el sistema de microservicios

Write-Host "🎮 ICFES LEVELING - Iniciando sistema completo..." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Verificar que Docker esté corriendo
try {
    docker info | Out-Null
    Write-Host "✅ Docker verificado" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Docker no está corriendo. Por favor inicia Docker Desktop primero." -ForegroundColor Red
    exit 1
}

# Verificar que Docker Compose esté disponible
try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker Compose verificado" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Docker Compose no está disponible." -ForegroundColor Red
    exit 1
}

# Crear archivo .env si no existe
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creando archivo .env desde env.example..." -ForegroundColor Yellow
    Copy-Item "env.example" ".env"
    Write-Host "✅ Archivo .env creado. Puedes editarlo si necesitas configurar OpenAI API." -ForegroundColor Green
}

# Detener contenedores existentes
Write-Host "🛑 Deteniendo contenedores existentes..." -ForegroundColor Yellow
docker-compose down

# Limpiar recursos no utilizados
Write-Host "🧹 Limpiando recursos no utilizados..." -ForegroundColor Yellow
docker system prune -f

# Construir y levantar servicios
Write-Host "🔨 Construyendo y levantando servicios..." -ForegroundColor Yellow
docker-compose up --build -d

# Esperar a que los servicios estén listos
Write-Host "⏳ Esperando a que los servicios estén listos..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Verificar estado de los servicios
Write-Host "🔍 Verificando estado de los servicios..." -ForegroundColor Yellow
docker-compose ps

# Verificar endpoints
Write-Host "🌐 Verificando endpoints..." -ForegroundColor Yellow
Write-Host ""

# Backend API
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ Backend API: http://localhost:8000" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend API: No responde" -ForegroundColor Red
}

# AI Service
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8002/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ AI Service: http://localhost:8002" -ForegroundColor Green
} catch {
    Write-Host "❌ AI Service: No responde" -ForegroundColor Red
}

# Frontend
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ Frontend: http://localhost:3000" -ForegroundColor Green
} catch {
    Write-Host "❌ Frontend: No responde (puede tardar más en cargar)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 ¡Sistema iniciado exitosamente!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "📱 Acceso a los servicios:" -ForegroundColor Cyan
Write-Host "   • Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "   • Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "   • AI Service: http://localhost:8002" -ForegroundColor White
Write-Host "   • WebSocket: ws://localhost:8001" -ForegroundColor White
Write-Host ""
Write-Host "📊 Base de datos:" -ForegroundColor Cyan
Write-Host "   • PostgreSQL: localhost:5432" -ForegroundColor White
Write-Host "   • Redis: localhost:6379" -ForegroundColor White
Write-Host "   • ClickHouse: localhost:8123" -ForegroundColor White
Write-Host ""
Write-Host "👥 Usuarios de prueba:" -ForegroundColor Cyan
Write-Host "   • shadow_hunter / password123 (Level 25, Rank B)" -ForegroundColor White
Write-Host "   • math_master / password123 (Level 18, Rank C)" -ForegroundColor White
Write-Host "   • newbie_student / password123 (Level 1, Rank E)" -ForegroundColor White
Write-Host ""
Write-Host "📋 Comandos útiles:" -ForegroundColor Cyan
Write-Host "   • Ver logs: docker-compose logs -f" -ForegroundColor White
Write-Host "   • Ver logs de un servicio: docker-compose logs -f frontend" -ForegroundColor White
Write-Host "   • Reiniciar un servicio: docker-compose restart backend" -ForegroundColor White
Write-Host "   • Detener todo: docker-compose down" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Para desarrollo:" -ForegroundColor Cyan
Write-Host "   • Edita .env para configurar OpenAI API" -ForegroundColor White
Write-Host "   • Los cambios en el código se reflejan automáticamente" -ForegroundColor White
Write-Host "   • Usa docker-compose exec para ejecutar comandos dentro de contenedores" -ForegroundColor White
Write-Host ""
Write-Host "🎮 ¡Disfruta aprendiendo mientras combates enemigos académicos!" -ForegroundColor Green 