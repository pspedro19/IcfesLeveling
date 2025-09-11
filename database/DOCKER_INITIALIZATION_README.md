# ICFES Docker Database Initialization

Este README documenta la configuración automática de la base de datos con los 81 campos ICFES y carga automática de datos desde Excel.

## 🚀 Configuración Automática

### Archivos de Inicialización

Los siguientes archivos se ejecutan automáticamente cuando Docker inicia el contenedor PostgreSQL:

1. **`01-init.sql`** - Creación de tablas básicas
2. **`02-seed-data.sql`** - Datos iniciales (usuarios, subjects, etc.)
3. **`03-import-icfes-data.sql`** - ✅ **NUEVO**: Estructura completa con 81 campos ICFES
4. **`99-load-icfes-data.sh`** - ✅ **NUEVO**: Carga automática de datos desde Excel

### Estructura de 81 Campos ICFES

El script `03-import-icfes-data.sql` agrega automáticamente todos los campos necesarios:

#### Campos Básicos
- `id_pregunta_original`
- `area_evaluada`
- `tema_especifico`
- `grado_escolar`
- `periodo_aplicacion`

#### Campos de Imágenes
- `requiere_imagen`
- `imagen_pregunta_url`
- `imagen_opcion_a_url`
- `imagen_opcion_b_url`
- `imagen_opcion_c_url`
- `imagen_opcion_d_url`
- `imagen_contexto_comp`

#### Campos de Contexto
- `pregunta_con_contexto`
- `pregunta_libro`
- `orden_en_contexto`
- `contexto_requerido`
- `texto_contexto_completo`
- `id_contexto_compartido`

#### Campos de Categorización (67 campos adicionales)
- Análisis textual (tipo_texto, genero_textual, funcion_comunicativa, etc.)
- Campos matemáticos (pensamiento_matematico, tipo_problema, estrategia_solucion, etc.)
- Campos científicos (disciplina_predominante, concepto_cientifico, proceso_cientifico, etc.)
- Campos sociales (periodo_historico, ambito_analisis, escala_espacial, etc.)
- Campos de comunicación y lenguaje (40+ campos específicos)
- Campos de análisis y evaluación
- Campos de argumentación

## 📊 Carga Automática de Datos

### Archivo Excel Esperado

- **Ruta**: `database/allquestions/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx`
- **Formato**: Excel con columnas que coincidan con los 81 campos
- **Contenido**: ~480 preguntas con todos los campos ICFES

### Proceso de Carga

El script `99-load-icfes-data.sh`:

1. ✅ Instala Python3 y dependencias (pandas, psycopg2, openpyxl)
2. ✅ Espera a que PostgreSQL esté listo
3. ✅ Verifica que el archivo Excel existe
4. ✅ Carga datos desde Excel
5. ✅ Mapea áreas a subject_id UUIDs:
   - Matemáticas → `550e8400-e29b-41d4-a716-446655440001`
   - Lectura Crítica → `550e8400-e29b-41d4-a716-446655440002`
   - Ciencias Naturales → `550e8400-e29b-41d4-a716-446655440003`
   - Ciencias Sociales → `550e8400-e29b-41d4-a716-446655440004`
   - Inglés → `550e8400-e29b-41d4-a716-446655440005`
6. ✅ Inserta todas las preguntas con campos completos
7. ✅ Reporta estadísticas finales

## 🔧 Uso

### Primera Instalación

```bash
# Detener contenedores existentes
docker-compose down

# Limpiar volúmenes (esto reinicia la DB)
docker volume rm icfesleveling_postgres_data

# Iniciar con configuración automática
docker-compose up -d postgres
```

### Verificar Carga

```bash
# Conectar a PostgreSQL
docker exec -it icfes_postgres psql -U gameplay -d gameplay_db

# Verificar estructura de tabla (debe tener ~100 columnas)
\d questions

# Verificar datos cargados
SELECT COUNT(*) as total_questions FROM questions;
SELECT area_evaluada, COUNT(*) FROM questions GROUP BY area_evaluada;

# Verificar campos ICFES específicos
SELECT id, area_evaluada, tema_especifico, competencia, componente 
FROM questions 
LIMIT 5;
```

### Logs de Inicialización

```bash
# Ver logs del contenedor PostgreSQL durante inicialización
docker logs icfes_postgres

# Buscar específicamente los logs de ICFES
docker logs icfes_postgres 2>&1 | grep -i icfes
```

## 📁 Estructura de Archivos

```
database/
├── init/
│   ├── 01-init.sql                    # Tablas básicas
│   ├── 02-seed-data.sql               # Datos iniciales
│   ├── 03-import-icfes-data.sql       # ✅ 81 campos ICFES
│   ├── 99-load-icfes-data.sh          # ✅ Carga automática Excel
│   └── load_icfes_data.py             # ✅ Script Python auxiliar
├── allquestions/
│   └── ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx
└── DOCKER_INITIALIZATION_README.md    # Este archivo
```

## ✅ Validación

Después de la inicialización automática, el sistema debe tener:

- ✅ Tabla `questions` con ~100 columnas (81 campos ICFES + campos originales)
- ✅ ~480 preguntas cargadas desde Excel
- ✅ Distribución por materias:
  - Ciencias Naturales: ~258 preguntas
  - Ciencias Sociales: ~153 preguntas  
  - Matemáticas: ~1+ preguntas
  - Lectura Crítica: ~50+ preguntas
  - Inglés: ~20+ preguntas
- ✅ Todos los campos ICFES poblados con datos del Excel
- ✅ Frontend conectado correctamente a la base de datos

## 🔄 Actualización de Datos

Para actualizar con nuevos datos ICFES:

1. Reemplazar el archivo Excel en `database/allquestions/`
2. Reiniciar el contenedor PostgreSQL:
   ```bash
   docker-compose restart postgres
   ```
3. O ejecutar manualmente el script de carga:
   ```bash
   docker exec -it icfes_postgres bash /docker-entrypoint-initdb.d/99-load-icfes-data.sh
   ```

## ⚠️ Notas Importantes

- La carga automática solo ocurre durante la primera inicialización del contenedor
- Si el archivo Excel no existe, se omite la carga (sin errores)
- Los datos existentes se limpian antes de cargar nuevos datos
- La estructura de 81 campos se agrega siempre (usando `ADD COLUMN IF NOT EXISTS`)
- Todos los scripts son idempotentes (se pueden ejecutar múltiples veces sin problemas)

## 🐛 Solución de Problemas

### El Excel no se carga
- Verificar que existe: `database/allquestions/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx`
- Verificar logs: `docker logs icfes_postgres | grep -i excel`
- Ejecutar manualmente: `docker exec -it icfes_postgres bash /docker-entrypoint-initdb.d/99-load-icfes-data.sh`

### La estructura no se actualiza
- Verificar logs: `docker logs icfes_postgres | grep -i "estructura"`
- Conectar y verificar: `docker exec -it icfes_postgres psql -U gameplay -d gameplay_db -c "\d questions"`

### Frontend no carga preguntas
- Verificar datos: `SELECT COUNT(*) FROM questions;`
- Verificar subject_ids: `SELECT DISTINCT subject_id FROM questions;`
- Verificar que los UUIDs coinciden con los esperados por el frontend