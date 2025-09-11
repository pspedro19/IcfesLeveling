# Sistema de Actualización Masiva de Base de Datos - ICFES Leveling

## DÍA 3 - PASO 7: Actualización Completa con Rutas Normalizadas

Este directorio contiene el sistema completo de actualización masiva de la base de datos PostgreSQL para el proyecto ICFES Leveling, implementando la normalización de rutas de imágenes y optimizaciones de rendimiento.

## 📁 Estructura del Directorio

```
database/
├── scripts/                          # Scripts de actualización y mantenimiento
│   ├── mass_image_update.py         # Script principal de actualización masiva
│   ├── integrity_checker.py         # Verificador de integridad referencial
│   ├── index_optimizer.py           # Optimizador de índices de BD
│   ├── rollback_manager.py          # Manejador de validación y rollback
│   ├── cache_manager.py             # Gestor de cache Redis
│   ├── migration_manager.py         # Manejador de migraciones Alembic
│   └── master_update_script.py      # Script maestro orquestador
├── migrations/                       # Migraciones Alembic
│   ├── alembic.ini                  # Configuración de Alembic
│   ├── env.py                       # Entorno de migraciones
│   ├── script.py.mako               # Template de migraciones
│   └── versions/                    # Archivos de migración
│       ├── 20241209_120000_add_image_path_indexes.py
│       ├── 20241209_120100_add_requiere_imagen_field.py
│       └── 20241209_120200_normalize_image_paths.py
├── backups/                         # Backups automáticos (se crea dinámicamente)
├── reports/                         # Reportes de actualización (se crea dinámicamente)
└── README.md                        # Esta documentación
```

## 🚀 Características Principales

### ✅ Sistema de Actualización Masiva
- **Mapeo de rutas**: Utiliza tabla de correspondencia CSV para mapear rutas originales a rutas físicas reales
- **Actualización batch**: Procesa miles de registros de forma eficiente
- **Validación de archivos**: Verifica existencia y tamaño de archivos de imagen
- **Campo automático**: Actualiza campo `Requiere_Imagen` basado en presencia real de imágenes

### ✅ Verificación de Integridad Referencial
- **Foreign Keys**: Verifica integridad de relaciones con `topics` y `subjects`
- **Constraints**: Valida reglas de negocio y consistencia de datos
- **Unicidad**: Comprueba campos únicos como `natural_key`
- **Reportes detallados**: Genera reportes de errores críticos y advertencias

### ✅ Optimización de Índices
- **Índices de imagen**: Optimiza búsquedas en campos de imagen
- **Índices compuestos**: Para consultas complejas (`área_evaluada`, `requiere_imagen`)
- **Índices GIN**: Búsqueda full-text en texto de preguntas
- **Análisis de rendimiento**: Benchmarks antes y después de optimización

### ✅ Sistema de Rollback y Validación
- **Backups automáticos**: Crea backups antes de modificaciones
- **Scripts de rollback**: Genera scripts SQL para reversión
- **Validaciones multi-nivel**: Críticas, advertencias e informativas
- **Cleanup automático**: Limpia backups antiguos automáticamente

### ✅ Gestión de Cache Redis
- **Invalidación masiva**: Limpia cache después de actualizaciones de BD
- **Pre-carga inteligente**: Carga imágenes importantes con alta prioridad
- **Métricas de rendimiento**: Monitorea hit rate, uso de memoria, etc.
- **Optimización automática**: Configura políticas de expiración

### ✅ Migraciones de Esquema
- **Alembic integrado**: Sistema completo de migraciones
- **Versionado**: Control de versiones de esquema de BD
- **Reversibilidad**: Todas las migraciones son reversibles
- **Validación**: Verifica integridad después de migraciones

## 🔧 Configuración

### Variables de Entorno

```bash
# Base de datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gameplay_db
DB_USER=gameplay
DB_PASSWORD=gameplay123

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Archivos de entrada
CORRESPONDENCE_TABLE=C:\Users\PEDRO_PEREZ\tabla_correspondencia_imagenes.csv
```

### Dependencias Python

```bash
pip install psycopg2-binary redis alembic sqlalchemy aioredis
```

## 📋 Uso del Sistema

### 1. Script Maestro (Recomendado)

Ejecuta todo el proceso de actualización de forma automática:

```bash
cd C:\Users\PEDRO_PEREZ\Documents\IcfesLeveling\database\scripts
python master_update_script.py
```

**Fases ejecutadas automáticamente:**
- 🔧 Inicialización del sistema
- 🔍 Validaciones previas
- 💾 Backup y preparación
- 🔄 Migraciones de esquema
- 📋 Actualización masiva de datos
- 📊 Optimización de índices
- 🔗 Validación de integridad
- 🧹 Gestión de cache
- ✅ Validación final

### 2. Scripts Individuales

#### Actualización Masiva de Imágenes
```bash
python mass_image_update.py
```

#### Verificación de Integridad
```bash
python integrity_checker.py
```

#### Optimización de Índices
```bash
python index_optimizer.py
```

#### Gestión de Cache
```bash
# Invalidar cache después de actualización
python cache_manager.py invalidate

# Monitorear salud del cache
python cache_manager.py health

# Pre-cargar imágenes importantes
python cache_manager.py preload
```

#### Migraciones Alembic
```bash
# Ver estado de migraciones
python migration_manager.py status

# Aplicar migraciones
python migration_manager.py upgrade

# Crear nueva migración
python migration_manager.py create "Descripción de la migración"
```

#### Rollback y Validación
```bash
# Crear backup
python rollback_manager.py backup questions

# Validar estado actual
python rollback_manager.py validate

# Ejecutar rollback (si es necesario)
python rollback_manager.py rollback backup_name questions

# Listar backups disponibles
python rollback_manager.py list
```

## 📊 Monitoreo y Reportes

### Tipos de Reportes Generados

1. **Reporte Maestro** (`master_update_report_YYYYMMDD_HHMMSS.json`)
   - Resumen completo de todas las fases
   - Métricas de tiempo y rendimiento
   - Recomendaciones de seguimiento

2. **Reporte de Integridad** (`integrity_report_YYYYMMDD_HHMMSS.json`)
   - Errores críticos y advertencias
   - Scripts de corrección SQL generados
   - Estado de foreign keys y constraints

3. **Reporte de Optimización** (`index_optimization_YYYYMMDD_HHMMSS.json`)
   - Índices creados y fallidos
   - Mejoras de rendimiento medidas
   - Estadísticas de base de datos

4. **Reporte de Cache** (`cache_health_YYYYMMDD_HHMMSS.json`)
   - Métricas de Redis
   - Hit rate y uso de memoria
   - Alertas de rendimiento

### Logs Detallados

Todos los scripts generan logs detallados:
- `master_update_YYYYMMDD_HHMMSS.log` - Log completo del proceso
- Console output en tiempo real
- Niveles: INFO, WARNING, ERROR, CRITICAL

## 🔍 Validaciones Implementadas

### Validaciones Críticas (Bloquean ejecución)
- ❌ Foreign keys rotas con `topics` y `subjects`
- ❌ Valores de `respuesta_correcta` inválidos
- ❌ Preguntas sin contenido (texto ni imagen)
- ❌ Campos obligatorios NULL

### Validaciones de Advertencia
- ⚠️ Inconsistencias en `requiere_imagen`
- ⚠️ Rutas de imagen con caracteres inválidos
- ⚠️ Duplicados en `natural_key`
- ⚠️ Dificultad fuera del rango 1-10

### Validaciones Informativas
- ℹ️ Conteo de preguntas con imágenes
- ℹ️ URLs vs rutas locales
- ℹ️ Distribución por dificultad

## ⚡ Optimizaciones de Rendimiento

### Índices Creados

1. **`idx_questions_pregunta_imagen`** - Búsquedas de imágenes de pregunta
2. **`idx_questions_area_imagen`** - Filtros por área con imágenes
3. **`idx_questions_natural_key`** - Unicidad y búsquedas por clave natural
4. **`idx_questions_topic_subject`** - Joins optimizados
5. **`idx_questions_difficulty`** - Filtros por dificultad
6. **`idx_questions_pregunta_texto_gin`** - Búsqueda full-text

### Optimizaciones de Cache

- **TTL dinámico**: Diferentes tiempos de vida según tipo de contenido
- **Compresión**: Compresión automática de contenido grande
- **Invalidación inteligente**: Patrones específicos por tipo de actualización
- **Pre-carga**: Algoritmo de prioridad para imágenes importantes

## 🚨 Recuperación en Caso de Error

### Backups Automáticos
- Se crea backup completo antes de cualquier modificación
- Backups incluyen metadata y validaciones
- Cleanup automático de backups antiguos (>30 días)

### Rollback Automático
```bash
# En caso de error crítico, ejecutar:
python rollback_manager.py rollback questions_backup_YYYYMMDD_HHMMSS questions --force
```

### Scripts de Corrección
- Se generan scripts SQL específicos para cada error encontrado
- Aplicación manual después de revisión
- Validación automática después de corrección

## 📈 Métricas de Éxito

### Indicadores Clave
- ✅ **0 errores críticos** de integridad
- ✅ **>95% de registros** actualizados exitosamente
- ✅ **<1% miss rate** en cache después de pre-carga
- ✅ **>50% mejora** en tiempo de respuesta de consultas de imágenes

### Benchmarks Típicos
- **Actualización masiva**: ~1000 registros/segundo
- **Creación de índices**: ~2-5 minutos para índices principales
- **Invalidación de cache**: ~10,000 keys/segundo
- **Validación de integridad**: ~30 segundos para BD completa

## 🛠️ Mantenimiento

### Tareas Programadas Recomendadas

1. **Semanal**: Ejecutar verificación de integridad
   ```bash
   python integrity_checker.py
   ```

2. **Mensual**: Optimizar índices y estadísticas
   ```bash
   python index_optimizer.py
   ```

3. **Trimestral**: Cleanup de backups antiguos
   ```bash
   python rollback_manager.py cleanup 90
   ```

### Monitoreo Continuo

- Configurar alertas en métricas de cache (hit rate < 50%)
- Monitorear crecimiento de logs y reportes
- Verificar espacio en disco para backups

## 🎯 Próximos Pasos

1. **Automatización**: Integrar con sistema de CI/CD
2. **Monitoring**: Dashboard de métricas en tiempo real
3. **Scaling**: Optimizaciones para BD de mayor tamaño
4. **Testing**: Suite de tests automatizados para validaciones

---

**Contacto**: Para dudas o problemas, revisar logs detallados y reportes JSON generados. Los scripts están diseñados para ser auto-explicativos y generar información diagnóstica completa.