# setup-dev.ps1 - Script para configurar el entorno de desarrollo ICFES Leveling
# Ejecutar como administrador en PowerShell

Write-Host "🚀 Configurando entorno de desarrollo ICFES Leveling..." -ForegroundColor Green

# 1. Verificar puertos disponibles
Write-Host "`n🔍 Verificando puertos disponibles..." -ForegroundColor Yellow
$ports = @(4001, 4000, 4002, 8002, 5433, 6379, 9000, 8123)
$usedPorts = @()

foreach ($port in $ports) {
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connection) {
        $usedPorts += $port
        Write-Host "⚠️  Puerto $port está en uso por PID: $($connection.OwningProcess)" -ForegroundColor Red
    } else {
        Write-Host "✅ Puerto $port disponible" -ForegroundColor Green
    }
}

if ($usedPorts.Count -gt 0) {
    Write-Host "`n❌ Los siguientes puertos están en uso:" -ForegroundColor Red
    $usedPorts | ForEach-Object { Write-Host "   - Puerto $_" -ForegroundColor Red }
    Write-Host "`n💡 Cierra las aplicaciones que usen estos puertos o cambia la configuracion" -ForegroundColor Yellow
    Read-Host "Presiona Enter para continuar o Ctrl+C para cancelar"
}

# 2. Crear archivo .env.local
Write-Host "`n📝 Creando archivo .env.local..." -ForegroundColor Yellow
$envContent = @"
# Frontend URLs (desarrollo local)
NEXT_PUBLIC_API_URL=http://localhost:4000
NEXT_PUBLIC_WS_URL=ws://localhost:4002

# Configuracion de desarrollo
NODE_ENV=development
PORT=4001

# Opcional - descomenta si tienes las keys
# NEXT_PUBLIC_SENTRY_DSN=
# NEXT_PUBLIC_GA_MEASUREMENT_ID=
# NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=
"@

$envPath = "apps/frontend/.env.local"
if (!(Test-Path $envPath)) {
    $envContent | Out-File -FilePath $envPath -Encoding UTF8
    Write-Host "✅ Archivo .env.local creado" -ForegroundColor Green
} else {
    Write-Host "⏭️  Archivo .env.local ya existe" -ForegroundColor Yellow
}

# 3. Crear directorios necesarios
Write-Host "`n📁 Creando directorios necesarios..." -ForegroundColor Yellow
$directories = @(
    "apps/frontend/public/mathimg",
    "logs",
    "apps/backend/logs"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Host "✅ Directorio creado: $dir" -ForegroundColor Green
    } else {
        Write-Host "⏭️  Directorio ya existe: $dir" -ForegroundColor Yellow
    }
}

# 4. Migrar imágenes
Write-Host "`n🖼️  Migrando imágenes..." -ForegroundColor Yellow
if (Test-Path "scripts/migrate-images.js") {
    try {
        node scripts/migrate-images.js
        Write-Host "✅ Migración de imágenes completada" -ForegroundColor Green
    } catch {
        Write-Host "❌ Error en migración de imágenes: $_" -ForegroundColor Red
    }
} else {
    Write-Host "⚠️  Script de migración no encontrado" -ForegroundColor Yellow
}

# 5. Verificar componente separator
Write-Host "`n🔍 Verificando componente separator..." -ForegroundColor Yellow
$separatorPath = "apps/frontend/app/components/ui/separator.tsx"
if (!(Test-Path $separatorPath)) {
    Write-Host "⚠️  Componente separator.tsx faltante. Creando..." -ForegroundColor Yellow
    
    $separatorContent = @"
import * as React from "react"

export interface SeparatorProps extends React.HTMLAttributes<HTMLDivElement> {
  orientation?: "horizontal" | "vertical"
  decorative?: boolean
}

const Separator = React.forwardRef<HTMLDivElement, SeparatorProps>(
  ({ className = "", orientation = "horizontal", decorative = true, ...props }, ref) => (
    <div
      ref={ref}
      role={decorative ? "none" : "separator"}
      aria-orientation={decorative ? undefined : orientation}
      className={`shrink-0 bg-border ${
        orientation === "horizontal" ? "h-[1px] w-full" : "h-full w-[1px]"
      } ${className}`}
      {...props}
    />
  )
)
Separator.displayName = "Separator"

export { Separator }
"@

    $separatorContent | Out-File -FilePath $separatorPath -Encoding UTF8
    Write-Host "✅ Componente separator.tsx creado" -ForegroundColor Green
} else {
    Write-Host "✅ Componente separator.tsx ya existe" -ForegroundColor Green
}

# 6. Instalar dependencias del frontend
Write-Host "`n📦 Instalando dependencias del frontend..." -ForegroundColor Yellow
Set-Location "apps/frontend"
try {
    npm install --legacy-peer-deps
    Write-Host "✅ Dependencias instaladas" -ForegroundColor Green
} catch {
    Write-Host "❌ Error instalando dependencias: $_" -ForegroundColor Red
}

# 7. Verificar Docker
Write-Host "`n🐳 Verificando Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker disponible: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker no está disponible. Instálalo desde https://docker.com" -ForegroundColor Red
    exit 1
}

# 8. Verificar Docker Compose
Write-Host "`n📋 Verificando Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version
    Write-Host "✅ Docker Compose disponible: $composeVersion" -ForegroundColor Green
} else {
    Write-Host "❌ Docker Compose no está disponible" -ForegroundColor Red
    exit 1
}

# 9. Verificar Python
Write-Host "`n🐍 Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✅ Python disponible: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python no está disponible. Instálalo desde https://python.org" -ForegroundColor Red
    exit 1
}

# 10. Verificar Node.js
Write-Host "`n🟢 Verificando Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js disponible: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js no está disponible. Instálalo desde https://nodejs.org" -ForegroundColor Red
    exit 1
}

# Volver al directorio raíz
Set-Location "../.."

Write-Host "`n✨ Configuración completada!" -ForegroundColor Green
Write-Host "`n📌 Próximos pasos:" -ForegroundColor Cyan
Write-Host "   1. Levantar servicios: docker-compose up -d" -ForegroundColor White
Write-Host "   2. Iniciar backend: cd apps/backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor White
Write-Host "   3. Iniciar frontend: cd apps/frontend && npm run dev -- -p 4001" -ForegroundColor White
Write-Host "   4. Probar: http://localhost:4001" -ForegroundColor White

Write-Host "`n🚀 ¡Todo listo para el desarrollo!" -ForegroundColor Green
