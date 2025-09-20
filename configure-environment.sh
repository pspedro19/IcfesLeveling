#!/bin/bash

# =====================================================
# SCRIPT DE CONFIGURACIÓN AUTOMÁTICA - ICFES LEVELING
# =====================================================
# Este script configura automáticamente las URLs basadas
# en el entorno donde se ejecuta
# =====================================================

set -e

echo "====================================================="
echo "   CONFIGURANDO ENTORNO - ICFES LEVELING"
echo "====================================================="

# Detectar IP externa del servidor
EXTERNAL_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || echo "localhost")
echo "IP externa detectada: $EXTERNAL_IP"

# Detectar si estamos en desarrollo local o servidor
if [[ "$EXTERNAL_IP" == "localhost" ]] || [[ "$EXTERNAL_IP" =~ ^192\.168\. ]] || [[ "$EXTERNAL_IP" =~ ^10\. ]] || [[ "$EXTERNAL_IP" =~ ^172\.(1[6-9]|2[0-9]|3[0-1])\. ]]; then
    echo "Entorno detectado: DESARROLLO LOCAL"
    API_URL="http://localhost:4000"
    WS_URL="ws://localhost:4002"
    APP_URL="http://localhost:4001"
else
    echo "Entorno detectado: SERVIDOR PÚBLICO"
    API_URL="http://$EXTERNAL_IP:4000"
    WS_URL="ws://$EXTERNAL_IP:4002"
    APP_URL="http://$EXTERNAL_IP:4001"
fi

echo "Configurando URLs:"
echo "  API URL: $API_URL"
echo "  WebSocket URL: $WS_URL"
echo "  App URL: $APP_URL"

# Crear archivo .env.local para el frontend
cat > apps/frontend/.env.local << EOF
NEXT_PUBLIC_API_URL=$API_URL
NEXT_PUBLIC_WS_URL=$WS_URL
NEXT_PUBLIC_APP_URL=$APP_URL
NODE_ENV=development
PORT=4001
HOSTNAME=0.0.0.0
NEXT_TELEMETRY_DISABLED=1
EOF

# Crear archivo .env para el backend
cat > .env << EOF
# Environment Configuration
ENVIRONMENT=development
DEBUG=true

# Database - SQLite para desarrollo
DATABASE_URL=sqlite:///./icfes_local.db

# JWT
JWT_SECRET=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# App URLs (dinámicas)
APP_URL=$APP_URL
API_URL=$API_URL
FRONTEND_URL=$APP_URL

# Server configuration
HOST=0.0.0.0
PORT=4000

# OpenAI - opcional
OPENAI_API_KEY=
EOF

# Actualizar CORS en el backend para incluir las URLs dinámicas
python3 << EOF
import re

# Leer el archivo del backend
with open('apps/backend/simple_app.py', 'r') as f:
    content = f.read()

# Reemplazar la configuración CORS
cors_config = '''# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4001",
        "http://127.0.0.1:4001",
        "$API_URL",
        "$APP_URL"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)'''.replace('$API_URL', '$API_URL').replace('$APP_URL', '$APP_URL')

# Encontrar y reemplazar la sección CORS
pattern = r'# Add CORS middleware\napp\.add_middleware\(\s*CORSMiddleware,.*?\)'
replacement = cors_config

# Hacer el reemplazo
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Escribir el archivo actualizado
with open('apps/backend/simple_app.py', 'w') as f:
    f.write(new_content)

print("✅ Configuración CORS actualizada")
EOF

echo ""
echo "✅ Configuración completada!"
echo ""
echo "URLs de acceso:"
echo "  🌐 Frontend: $APP_URL"
echo "  🔧 Backend:  $API_URL"
echo "  📚 API Docs: $API_URL/docs"
echo ""
echo "Para iniciar los servicios:"
echo "  cd apps/backend && source venv/bin/activate && python simple_app.py &"
echo "  cd apps/frontend && npm run dev &"
echo ""