#!/bin/bash
# Script para iniciar el backend simple sin dependencias complejas

cd /root/IcfesLeveling/apps/backend

# Configurar variables de entorno
export HOST_IP=$(hostname -I | awk '{print $1}')
export ALLOWED_ORIGINS="http://localhost:4001,http://127.0.0.1:4001,http://$HOST_IP:4001,http://$HOST_IP:4000"

echo "🚀 Iniciando backend simple en puerto 4000"
echo "📡 IP del host: $HOST_IP"
echo "🔒 CORS origins: $ALLOWED_ORIGINS"

# Matar procesos existentes en puerto 4000
sudo fuser -k 4000/tcp 2>/dev/null || true

# Iniciar el backend simple
python3 simple_app.py