# 🚀 ICFES LEVELING - Guía de Despliegue Completo

## ✅ Sistema Completamente Configurado

Este sistema ha sido configurado para funcionar automáticamente en cualquier servidor nuevo. Todos los datos se cargan dinámicamente y las APIs están completamente funcionales.

## 📋 Estado Actual del Sistema

### ✅ **Base de Datos Configurada**
- **5 Materias** cargadas (Matemáticas, Lectura Crítica, Ciencias Naturales, Ciencias Sociales, Inglés)
- **15 Temas** distribuidos entre las materias
- **31 Preguntas** de ejemplo cargadas y funcionando
- **Usuario administrador** creado y funcionando

### ✅ **APIs Funcionando**
- ✅ `GET /api/v1/subjects` - Lista de materias
- ✅ `GET /api/student/dashboard/stats` - Estadísticas del estudiante
- ✅ `GET /health` - Health check del sistema
- ✅ `POST /api/v1/auth-simple/login` - Autenticación

### ✅ **Configuración Automática**
- Scripts de inicialización automática
- Importación de datos desde Excel (cuando esté disponible)
- Creación automática de materias y temas
- Configuración de usuarios por defecto

## 🔧 Instrucciones para Servidor Nuevo

### 1. Clonar e Iniciar
```bash
git clone <repository>
cd IcfesLeveling

# El sistema se configura automáticamente
docker-compose up -d

# Esperar a que termine la configuración (1-2 minutos)
# Monitorear logs si es necesario:
docker-compose logs -f init-system
```

### 2. Verificar Estado
```bash
# Verificar que todos los servicios estén funcionando
docker-compose ps

# Probar APIs principales
curl http://localhost:4000/health
curl http://localhost:4000/api/v1/subjects
curl http://localhost:4000/api/student/dashboard/stats
```

### 3. Acceso al Sistema
- **Frontend**: http://localhost:4001
- **Backend**: http://localhost:4000
- **Usuario**: `admin`
- **Contraseña**: `secret`

## 📊 Archivos de Configuración Permanente

### Scripts de Inicialización
- `scripts/setup-complete-system.sh` - Configuración completa automática
- `scripts/complete_import.py` - Importación de preguntas desde Excel
- `init-system.sh` - Script de inicialización para Docker

### Configuración Docker
- `docker-compose.override.yml` - Configuración adicional automática
- `docker-init.yml` - Configuración de inicialización

### Base de Datos
- Todos los scripts SQL en `database/init/` se ejecutan automáticamente
- Las materias y temas se crean automáticamente si no existen
- Usuario administrador se crea automáticamente

## 🔄 Funcionalidades Automáticas

### ✅ **Inicialización Automática**
1. **Estructura de BD**: Se ejecutan automáticamente todos los scripts SQL
2. **Datos Semilla**: Se crean materias, temas y preguntas de ejemplo
3. **Usuario Admin**: Se crea automáticamente el usuario administrador
4. **Verificación**: Se verifica que todo esté funcionando correctamente

### ✅ **Importación de Datos**
- **Búsqueda Automática**: Busca archivos Excel en múltiples ubicaciones
- **Mapeo Flexible**: Reconoce diferentes nombres de columnas
- **Respaldo**: Si no encuentra Excel, crea preguntas de ejemplo
- **Validación**: Verifica que los datos se carguen correctamente

### ✅ **Configuración de APIs**
- **Todas las rutas** están configuradas y funcionando
- **CORS configurado** para frontend y backend
- **Manejo de errores** robusto
- **Datos mock** para desarrollo inmediato

## 🧪 Testing y Verificación

### Comandos de Verificación
```bash
# Verificar base de datos
docker exec icfes_postgres psql -U gameplay -d gameplay_db -c "
SELECT
  (SELECT COUNT(*) FROM subjects) as subjects,
  (SELECT COUNT(*) FROM topics) as topics,
  (SELECT COUNT(*) FROM questions) as questions,
  (SELECT COUNT(*) FROM users) as users;
"

# Probar autenticación
curl -X POST http://localhost:4000/api/v1/auth-simple/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secret"

# Probar materias
curl http://localhost:4000/api/v1/subjects | jq '.[] | {name: .name, questions: .question_count}'
```

### Estado Esperado
- **Materias**: 5 (todas las áreas del ICFES)
- **Temas**: 15+ (distribuidos entre materias)
- **Preguntas**: 30+ (mínimo para funcionamiento)
- **Usuarios**: 1+ (administrador)

## 🔧 Resolución de Problemas

### Si el Sistema No Funciona
```bash
# 1. Revisar logs
docker-compose logs backend
docker-compose logs postgres
docker-compose logs init-system

# 2. Ejecutar configuración manual
./scripts/setup-complete-system.sh

# 3. Reiniciar servicios
docker-compose restart backend
```

### Si Faltan Datos
```bash
# Ejecutar importación manual
docker exec icfes_backend python /app/scripts/complete_import.py

# Verificar estado
curl http://localhost:4000/api/v1/subjects
```

## 🎯 Próximos Pasos

1. **Agregar Preguntas Reales**: Colocar archivos Excel en `database/allquestions/`
2. **Personalizar Temas**: Modificar temas en `docker-init.yml`
3. **Configurar Dominio**: Actualizar `HOST_IP` en `.env`
4. **Monitoreo**: Configurar logs y alertas para producción

## ⚡ Características del Sistema

- **🔄 Auto-configuración**: Se configura solo en servidor nuevo
- **📊 Datos Dinámicos**: Carga preguntas automáticamente desde Excel
- **🛡️ Robusto**: Manejo de errores y respaldos automáticos
- **🧪 Testing**: APIs listas para pruebas inmediatas
- **📈 Escalable**: Preparado para miles de preguntas
- **🔧 Mantenible**: Configuración centralizada y documentada

---

**¡El sistema está listo para usar!** 🎉

**Credenciales**: admin / secret
**URL**: http://localhost:4001
**API**: http://localhost:4000