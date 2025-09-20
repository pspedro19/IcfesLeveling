#!/bin/bash
# Script para configurar automáticamente la IP del host

# Detectar la IP del servidor
HOST_IP=$(hostname -I | awk '{print $1}')

if [ -z "$HOST_IP" ]; then
    echo "❌ No se pudo detectar la IP del host"
    exit 1
fi

echo "🔍 IP detectada: $HOST_IP"

# Actualizar archivo .env
if [ -f ".env" ]; then
    # Crear backup
    cp .env .env.backup

    # Actualizar HOST_IP en .env
    sed -i "s/HOST_IP=.*/HOST_IP=$HOST_IP/" .env

    echo "✅ Archivo .env actualizado con HOST_IP=$HOST_IP"
else
    echo "⚠️  Archivo .env no encontrado, creando uno nuevo..."
    cat > .env << EOF
# Environment Configuration
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql://gameplay:gameplay123@postgres:5432/gameplay_db

# JWT
JWT_SECRET=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# App URLs (dinámicas) - Se configuran automáticamente por el host
HOST_IP=$HOST_IP
APP_URL=http://\${HOST_IP}:4001
API_URL=http://\${HOST_IP}:4000
FRONTEND_URL=http://\${HOST_IP}:4001
WS_URL=ws://\${HOST_IP}:4002

# Server configuration
HOST=0.0.0.0
PORT=4000

# OpenAI - opcional
OPENAI_API_KEY=
EOF
    echo "✅ Archivo .env creado con HOST_IP=$HOST_IP"
fi

# Exportar la variable para docker-compose
export HOST_IP

echo "🚀 Configuración completada. La aplicación usará:"
echo "   - Frontend: http://$HOST_IP:4001"
echo "   - Backend:  http://$HOST_IP:4000"
echo "   - WebSocket: ws://$HOST_IP:4002"
echo ""
echo "💡 Para aplicar los cambios, reinicia los servicios:"
echo "   docker-compose down && docker-compose up -d"