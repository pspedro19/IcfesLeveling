#!/bin/bash

# =====================================================
# ICFES LEVELING - Script de Inicio
# =====================================================

set -e

echo "====================================================="
echo "   ICFES LEVELING - Iniciando Sistema"
echo "====================================================="

# Verificar si Docker está disponible
if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
    echo "🐳 Iniciando con Docker..."

    # Verificar si ya están corriendo
    if docker ps | grep -q icfes_postgres; then
        echo "✅ Servicios ya están corriendo"
        docker-compose ps
    else
        echo "🚀 Iniciando servicios..."
        docker-compose up -d

        echo "⏳ Esperando a que los servicios inicien..."
        sleep 10

        echo ""
        echo "✅ Servicios iniciados:"
        docker-compose ps
    fi

    echo ""
    echo "====================================================="
    echo "   URLs de Acceso:"
    echo "====================================================="
    echo "🌐 Frontend:   http://localhost:3002"
    echo "🔧 Backend:    http://localhost:4000"
    echo "📚 API Docs:   http://localhost:4000/docs"
    echo "🗄️  PgAdmin:    http://localhost:5050"
    echo ""
    echo "Ver logs: docker-compose logs -f"
    echo "Detener:  docker-compose down"
    echo "====================================================="

else
    echo "⚠️  Docker no encontrado. Iniciando en modo local..."

    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 no está instalado"
        exit 1
    fi

    # Iniciar Backend
    echo "🔧 Iniciando Backend..."
    cd apps/backend
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    else
        source venv/bin/activate
    fi
    python -m uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload &
    BACKEND_PID=$!
    cd ../..

    # Iniciar Frontend
    echo "🌐 Iniciando Frontend..."
    cd apps/frontend
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    npm run dev &
    FRONTEND_PID=$!
    cd ../..

    echo ""
    echo "✅ Servicios iniciados en modo local"
    echo "Backend PID: $BACKEND_PID"
    echo "Frontend PID: $FRONTEND_PID"
    echo ""
    echo "Para detener: kill $BACKEND_PID $FRONTEND_PID"

    # Mantener el script corriendo
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
    wait
fi
