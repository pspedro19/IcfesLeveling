#!/bin/bash

# =====================================================
# SCRIPT DE INICIO LOCAL - ICFES LEVELING
# =====================================================
# Este script inicia todos los servicios localmente
# sin Docker para desarrollo rápido
# =====================================================

set -e

echo "====================================================="
echo "   INICIANDO ICFES LEVELING - MODO LOCAL"
echo "====================================================="
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para verificar comandos
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1 no está instalado${NC}"
        echo "Instala $1 primero"
        exit 1
    else
        echo -e "${GREEN}✅ $1 encontrado${NC}"
    fi
}

# Verificar requisitos
echo -e "${YELLOW}[1/7] Verificando requisitos...${NC}"
check_command python3
check_command node
check_command npm

# Navegar al directorio del proyecto
cd /c/Users/HOME/Documents/icfes/IcfesLeveling

# Crear entorno virtual si no existe
echo -e "${YELLOW}[2/7] Configurando entorno Python...${NC}"
cd apps/backend
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
    echo -e "${GREEN}✅ Entorno virtual ya existe${NC}"
fi

# Instalar dependencias del frontend
echo -e "${YELLOW}[3/7] Configurando frontend...${NC}"
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "Instalando dependencias del frontend..."
    npm install
else
    echo -e "${GREEN}✅ Dependencias del frontend ya instaladas${NC}"
fi

# Crear archivo .env si no existe
cd ../..
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[4/7] Creando archivo .env...${NC}"
    cat > .env << EOF
# Environment Configuration
ENVIRONMENT=development
DEBUG=true

# Database - SQLite para desarrollo local
DATABASE_URL=sqlite:///./icfes_local.db

# Redis - Opcional para desarrollo local
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API URLs
NEXT_PUBLIC_API_URL=http://localhost:4000
NEXT_PUBLIC_WS_URL=ws://localhost:4002

# Frontend
NEXT_PUBLIC_APP_URL=http://localhost:4001
EOF
    echo -e "${GREEN}✅ Archivo .env creado${NC}"
else
    echo -e "${GREEN}✅ Archivo .env ya existe${NC}"
fi

# Inicializar base de datos SQLite
echo -e "${YELLOW}[5/7] Inicializando base de datos...${NC}"
cd apps/backend
python << EOF
import sys
sys.path.append('.')
from app.core.database import engine
from app.models import Base
Base.metadata.create_all(bind=engine)
print("✅ Base de datos inicializada")
EOF

echo ""
echo -e "${BLUE}[6/7] Iniciando servicios...${NC}"
echo ""

# Función para matar procesos en los puertos
kill_port() {
    port=$1
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}Deteniendo proceso en puerto $port...${NC}"
        kill -9 $pid 2>/dev/null || true
    fi
}

# Limpiar puertos
kill_port 4000
kill_port 4001
kill_port 4002

# Iniciar Backend
echo -e "${BLUE}Iniciando Backend (FastAPI) en puerto 4000...${NC}"
cd /c/Users/HOME/Documents/icfes/IcfesLeveling/apps/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload &
BACKEND_PID=$!

# Esperar a que el backend inicie
sleep 3

# Iniciar Frontend
echo -e "${BLUE}Iniciando Frontend (Next.js) en puerto 4001...${NC}"
cd /c/Users/HOME/Documents/icfes/IcfesLeveling/apps/frontend
npm run dev &
FRONTEND_PID=$!

# Iniciar WebSocket (si existe)
if [ -f "/c/Users/HOME/Documents/icfes/IcfesLeveling/apps/websocket/main.py" ]; then
    echo -e "${BLUE}Iniciando WebSocket Server en puerto 4002...${NC}"
    cd /c/Users/HOME/Documents/icfes/IcfesLeveling/apps/websocket
    python main.py &
    WEBSOCKET_PID=$!
fi

# Esperar a que los servicios inicien
echo -e "${YELLOW}[7/7] Esperando que los servicios inicien...${NC}"
sleep 5

# Verificar servicios
check_service() {
    port=$1
    name=$2
    if curl -s http://localhost:$port > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name funcionando en puerto $port${NC}"
    else
        echo -e "${YELLOW}⚠️  $name iniciando en puerto $port...${NC}"
    fi
}

check_service 4000 "Backend API"
check_service 4001 "Frontend"

echo ""
echo -e "${GREEN}====================================================="
echo -e "   🚀 ICFES LEVELING INICIADO EXITOSAMENTE"
echo -e "=====================================================${NC}"
echo ""
echo "Servicios disponibles:"
echo -e "  ${BLUE}Frontend:${NC}  http://localhost:4001"
echo -e "  ${BLUE}Backend:${NC}   http://localhost:4000"
echo -e "  ${BLUE}API Docs:${NC}  http://localhost:4000/docs"
echo -e "  ${BLUE}WebSocket:${NC} ws://localhost:4002"
echo ""
echo -e "${YELLOW}Para detener los servicios, presiona Ctrl+C${NC}"
echo ""

# Abrir navegador
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:4001
elif command -v open &> /dev/null; then
    open http://localhost:4001
fi

# Mantener el script corriendo
trap "kill $BACKEND_PID $FRONTEND_PID $WEBSOCKET_PID 2>/dev/null; exit" INT
wait