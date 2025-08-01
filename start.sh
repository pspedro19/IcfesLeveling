#!/bin/bash

# ICFES LEVELING - Quick Start Script
# Este script levanta todo el sistema de microservicios

echo "🎮 ICFES LEVELING - Iniciando sistema completo..."
echo "=================================================="

# Verificar que Docker esté corriendo
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker no está corriendo. Por favor inicia Docker primero."
    exit 1
fi

# Verificar que Docker Compose esté disponible
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose no está instalado."
    exit 1
fi

echo "✅ Docker y Docker Compose verificados"

# Crear archivo .env si no existe
if [ ! -f .env ]; then
    echo "📝 Creando archivo .env desde env.example..."
    cp env.example .env
    echo "✅ Archivo .env creado. Puedes editarlo si necesitas configurar OpenAI API."
fi

# Detener contenedores existentes
echo "🛑 Deteniendo contenedores existentes..."
docker-compose down

# Limpiar recursos no utilizados
echo "🧹 Limpiando recursos no utilizados..."
docker system prune -f

# Construir y levantar servicios
echo "🔨 Construyendo y levantando servicios..."
docker-compose up --build -d

# Esperar a que los servicios estén listos
echo "⏳ Esperando a que los servicios estén listos..."
sleep 30

# Verificar estado de los servicios
echo "🔍 Verificando estado de los servicios..."
docker-compose ps

# Verificar endpoints
echo "🌐 Verificando endpoints..."
echo ""

# Backend API
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend API: http://localhost:8000"
else
    echo "❌ Backend API: No responde"
fi

# AI Service
if curl -s http://localhost:8002/health > /dev/null; then
    echo "✅ AI Service: http://localhost:8002"
else
    echo "❌ AI Service: No responde"
fi

# Frontend
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend: http://localhost:3000"
else
    echo "❌ Frontend: No responde (puede tardar más en cargar)"
fi

echo ""
echo "🎉 ¡Sistema iniciado exitosamente!"
echo "=================================================="
echo ""
echo "📱 Acceso a los servicios:"
echo "   • Frontend: http://localhost:3000"
echo "   • Backend API: http://localhost:8000"
echo "   • AI Service: http://localhost:8002"
echo "   • WebSocket: ws://localhost:8001"
echo ""
echo "📊 Base de datos:"
echo "   • PostgreSQL: localhost:5432"
echo "   • Redis: localhost:6379"
echo "   • ClickHouse: localhost:8123"
echo ""
echo "👥 Usuarios de prueba:"
echo "   • shadow_hunter / password123 (Level 25, Rank B)"
echo "   • math_master / password123 (Level 18, Rank C)"
echo "   • newbie_student / password123 (Level 1, Rank E)"
echo ""
echo "📋 Comandos útiles:"
echo "   • Ver logs: docker-compose logs -f"
echo "   • Ver logs de un servicio: docker-compose logs -f frontend"
echo "   • Reiniciar un servicio: docker-compose restart backend"
echo "   • Detener todo: docker-compose down"
echo ""
echo "🔧 Para desarrollo:"
echo "   • Edita .env para configurar OpenAI API"
echo "   • Los cambios en el código se reflejan automáticamente"
echo "   • Usa docker-compose exec para ejecutar comandos dentro de contenedores"
echo ""
echo "🎮 ¡Disfruta aprendiendo mientras combates enemigos académicos!" 