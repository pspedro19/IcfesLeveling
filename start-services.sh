#!/bin/bash

# =====================================================
# SCRIPT DE INICIO UNIVERSAL - ICFES LEVELING
# =====================================================
# Este script configura e inicia automáticamente todos
# los servicios independientemente del servidor
# =====================================================

set -e

echo "====================================================="
echo "   INICIANDO ICFES LEVELING - MODO UNIVERSAL"
echo "====================================================="

# Configurar entorno automáticamente
echo "🔧 Configurando entorno..."
./configure-environment.sh > /dev/null 2>&1

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${YELLOW}🚀 Iniciando servicios...${NC}"

# Detener procesos existentes en los puertos
echo "🔄 Deteniendo servicios existentes..."
pkill -f "python simple_app.py" 2>/dev/null || true
pkill -f "python -m uvicorn app.main:app" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
sleep 2

# Iniciar Backend HÍBRIDO con datos ICFES reales
echo -e "${BLUE}🔧 Iniciando Backend HÍBRIDO con datos ICFES reales (Puerto 4000)...${NC}"
cd apps/backend
source venv/bin/activate

# Usar simple_app.py modificado con datos reales
echo "📊 Iniciando aplicación simple con datos reales desde Excel..."
python simple_app.py &
BACKEND_PID=$!
cd ../..

# Esperar a que el backend inicie
sleep 3

# Iniciar Frontend
echo -e "${BLUE}🌐 Iniciando Frontend (Puerto 4001)...${NC}"
cd apps/frontend
npm run dev &
FRONTEND_PID=$!
cd ../..

# Esperar a que los servicios inicien
echo "⏳ Esperando que los servicios inicien..."
sleep 8

# Verificar que los servicios estén funcionando
echo ""
echo "🔍 Verificando servicios..."

EXTERNAL_IP=$(curl -s ifconfig.me || echo "localhost")
if [[ "$EXTERNAL_IP" == "localhost" ]] || [[ "$EXTERNAL_IP" =~ ^192\.168\. ]]; then
    API_URL="http://localhost:4000"
    APP_URL="http://localhost:4001"
else
    API_URL="http://$EXTERNAL_IP:4000"
    APP_URL="http://$EXTERNAL_IP:4001"
fi

# Test backend
if curl -s "$API_URL/health" > /dev/null; then
    echo -e "${GREEN}✅ Backend funcionando${NC}"
else
    echo -e "❌ Backend no responde"
fi

# Test frontend
if curl -s "$APP_URL/api/health" > /dev/null; then
    echo -e "${GREEN}✅ Frontend funcionando${NC}"
else
    echo -e "❌ Frontend no responde"
fi

echo ""
echo -e "${GREEN}====================================================="
echo -e "   🚀 ICFES LEVELING INICIADO EXITOSAMENTE"
echo -e "=====================================================${NC}"
echo ""
echo "🌐 URLs de acceso:"
echo "   Frontend:  $APP_URL"
echo "   Backend:   $API_URL"
echo "   API Docs:  $API_URL/docs"
echo ""
echo "👤 Credenciales de prueba:"
echo "   Email:     estudiante@icfes.com"
echo "   Password:  123456"
echo ""
echo -e "${YELLOW}Para detener los servicios: pkill -f 'uvicorn app.main:app'; pkill -f 'next dev'${NC}"
echo ""

# Mantener el script corriendo y mostrar logs
echo "📊 Monitoreando servicios (Ctrl+C para detener)..."
trap "echo '🛑 Deteniendo servicios...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

# Mostrar el estado cada 30 segundos
while true; do
    sleep 30
    echo "$(date '+%H:%M:%S') - ✅ Servicios activos: Backend (PID: $BACKEND_PID), Frontend (PID: $FRONTEND_PID)"
done