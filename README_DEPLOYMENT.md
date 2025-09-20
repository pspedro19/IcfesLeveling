# 🚀 ICFES Leveling - Deployment Universal

## 📋 Resumen

Sistema educativo adaptativo con configuración automática que funciona en cualquier servidor sin hardcodear IPs.

## ⚡ Inicio Rápido

### Opción 1: Script Universal (Recomendado)
```bash
# Configurar e iniciar todo automáticamente
./start-services.sh
```

### Opción 2: Manual
```bash
# 1. Configurar entorno automáticamente
./configure-environment.sh

# 2. Iniciar servicios
cd apps/backend && source venv/bin/activate && python simple_app.py &
cd apps/frontend && npm run dev &
```

## 🔧 Configuración Automática

El sistema detecta automáticamente:

### Desarrollo Local
- **IP detectada**: `localhost`, `192.168.x.x`, `10.x.x.x`, `172.16-31.x.x`
- **URLs configuradas**: `http://localhost:4000/4001`

### Servidor Público
- **IP detectada**: Cualquier IP pública
- **URLs configuradas**: `http://[IP_EXTERNA]:4000/4001`

## 📂 Archivos de Configuración

### `/configure-environment.sh`
- ✅ Detecta IP automáticamente
- ✅ Configura `.env.local` del frontend
- ✅ Configura `.env` del backend
- ✅ Actualiza CORS dinámicamente

### `/start-services.sh`
- ✅ Ejecuta configuración automática
- ✅ Inicia backend y frontend
- ✅ Verifica que los servicios funcionen
- ✅ Monitorea servicios en tiempo real

## 🌐 URLs de Acceso

El script muestra automáticamente las URLs correctas:

```
🌐 URLs de acceso:
   Frontend:  http://[IP]:4001
   Backend:   http://[IP]:4000
   API Docs:  http://[IP]:4000/docs
```

## 👤 Credenciales de Prueba

```
Email:     estudiante@icfes.com
Password:  123456
```

## 🔄 Gestión de Servicios

### Detener servicios
```bash
pkill -f 'python simple_app.py'
pkill -f 'next dev'
```

### Reiniciar servicios
```bash
./start-services.sh
```

### Verificar estado
```bash
curl http://localhost:4000/health          # Backend
curl http://localhost:4001/api/health      # Frontend
```

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │
│   Next.js       │◄──►│   FastAPI       │
│   Port: 4001    │    │   Port: 4000    │
└─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────────────────────────────┐
│        Configuración Automática         │
│   • Detección de IP                    │
│   • CORS dinámico                      │
│   • URLs deterministas                 │
└─────────────────────────────────────────┘
```

## ✅ Ventajas del Sistema

1. **Determinista**: Funciona igual en cualquier servidor
2. **Automático**: Sin configuración manual de IPs
3. **Inteligente**: Detecta el entorno automáticamente
4. **Robusto**: Manejo de errores y verificación
5. **Universal**: Compatible con desarrollo y producción

## 🔧 Variables de Entorno Generadas

### Frontend (`.env.local`)
```env
NEXT_PUBLIC_API_URL=http://[IP]:4000
NEXT_PUBLIC_WS_URL=ws://[IP]:4002
NEXT_PUBLIC_APP_URL=http://[IP]:4001
```

### Backend (`.env`)
```env
APP_URL=http://[IP]:4001
API_URL=http://[IP]:4000
FRONTEND_URL=http://[IP]:4001
```

## 📊 Sistema de Recomendaciones Incluido

- ✅ Motor de recomendaciones con IA
- ✅ Análisis de debilidades estudiantiles
- ✅ Planes de estudio adaptativos
- ✅ APIs RESTful completas
- ✅ Autenticación mock funcional

## 🚀 Para Desarrolladores

```bash
# Desarrollo local
EXTERNAL_IP=localhost ./configure-environment.sh

# Servidor específico
EXTERNAL_IP=192.168.1.100 ./configure-environment.sh

# Producción (auto-detección)
./configure-environment.sh
```

## 📝 Logs y Monitoreo

El script de inicio muestra:
- ✅ Estado de configuración
- ✅ Estado de servicios
- ✅ URLs de acceso
- ✅ Monitoreo en tiempo real

---

**🎯 Resultado**: Sistema completamente portátil que funciona en cualquier servidor sin hardcodear IPs ni configuración manual.