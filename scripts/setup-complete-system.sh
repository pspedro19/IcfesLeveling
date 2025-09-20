#!/bin/bash

# =============================================================================
# ICFES LEVELING - Sistema de Configuración Completa
# Este script configura completamente el sistema para que funcione en cualquier servidor
# =============================================================================

set -e  # Exit on any error

echo "🚀 Iniciando configuración completa del sistema ICFES LEVELING..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables de configuración
POSTGRES_CONTAINER="icfes_postgres"
BACKEND_CONTAINER="icfes_backend"
DB_USER="gameplay"
DB_NAME="gameplay_db"

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# 1. Verificar que Docker esté funcionando
log "🔍 Verificando Docker..."
if ! docker --version > /dev/null 2>&1; then
    error "Docker no está instalado o no está funcionando"
fi

# 2. Verificar que los contenedores estén corriendo
log "📦 Verificando contenedores..."
if ! docker ps | grep -q "$POSTGRES_CONTAINER"; then
    error "Contenedor PostgreSQL no está corriendo: $POSTGRES_CONTAINER"
fi

if ! docker ps | grep -q "$BACKEND_CONTAINER"; then
    error "Contenedor Backend no está corriendo: $BACKEND_CONTAINER"
fi

# 3. Esperar a que PostgreSQL esté listo
log "⏳ Esperando a que PostgreSQL esté listo..."
for i in {1..30}; do
    if docker exec $POSTGRES_CONTAINER pg_isready -U $DB_USER -d $DB_NAME > /dev/null 2>&1; then
        log "✅ PostgreSQL está listo"
        break
    fi
    if [ $i -eq 30 ]; then
        error "PostgreSQL no respondió después de 30 intentos"
    fi
    sleep 2
done

# 4. Ejecutar scripts de inicialización de base de datos
log "🗄️ Inicializando estructura de base de datos..."

# Ejecutar scripts en orden específico
INIT_SCRIPTS=(
    "01-init.sql"
    "02-seed-data.sql"
    "03-boss-tables.sql"
    "04-monthly-reassessment.sql"
    "05-premium-system.sql"
    "06-guild-system.sql"
    "07-achievement-system.sql"
    "08-virtual-economy.sql"
    "11-diagnostic-analytics.sql"
    "14-multimedia-questions.sql"
    "15-expanded-achievements.sql"
    "16-gamification-complete.sql"
)

for script in "${INIT_SCRIPTS[@]}"; do
    script_path="/docker-entrypoint-initdb.d/$script"
    if docker exec $POSTGRES_CONTAINER test -f "$script_path"; then
        log "📝 Ejecutando script: $script"
        if docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -f "$script_path" > /dev/null 2>&1; then
            info "✅ Script ejecutado exitosamente: $script"
        else
            warning "⚠️ Error en script (continuando): $script"
        fi
    else
        warning "⚠️ Script no encontrado: $script"
    fi
done

# 5. Crear usuario administrador si no existe
log "👤 Creando usuario administrador..."
docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -c "
INSERT INTO users (username, email, hashed_password)
VALUES ('admin', 'admin@icfes.com', '\$2b\$12\$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW')
ON CONFLICT (username) DO NOTHING;
" > /dev/null 2>&1

# 6. Verificar y crear materias (subjects)
log "📚 Verificando materias (subjects)..."
SUBJECTS_COUNT=$(docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM subjects;" | tr -d ' ')

if [ "$SUBJECTS_COUNT" -eq "0" ]; then
    log "📝 Creando materias principales..."
    docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -c "
    INSERT INTO subjects (id, name, description, icon_url, color) VALUES
    ('550e8400-e29b-41d4-a716-446655440001', 'Matemáticas', 'Razonamiento cuantitativo y matemático', '🔢', '#FF6B6B'),
    ('550e8400-e29b-41d4-a716-446655440002', 'Lectura Crítica', 'Comprensión y análisis de textos', '📖', '#4ECDC4'),
    ('550e8400-e29b-41d4-a716-446655440003', 'Ciencias Naturales', 'Biología, Física y Química', '🧪', '#45B7D1'),
    ('550e8400-e29b-41d4-a716-446655440004', 'Ciencias Sociales', 'Historia, Geografía y Ciudadanía', '🌍', '#96CEB4'),
    ('550e8400-e29b-41d4-a716-446655440005', 'Inglés', 'Comprensión lectora en inglés', '🌐', '#FECA57')
    ON CONFLICT (id) DO NOTHING;
    " > /dev/null 2>&1
    info "✅ Materias creadas exitosamente"
else
    info "✅ Materias ya existen ($SUBJECTS_COUNT encontradas)"
fi

# 7. Crear temas (topics) para cada materia
log "📝 Creando temas por materia..."
docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -c "
INSERT INTO topics (subject_id, name, description, difficulty_level) VALUES
-- Matemáticas
('550e8400-e29b-41d4-a716-446655440001', 'Álgebra', 'Ecuaciones y expresiones algebraicas', 2),
('550e8400-e29b-41d4-a716-446655440001', 'Geometría', 'Figuras geométricas y cálculo de áreas', 2),
('550e8400-e29b-41d4-a716-446655440001', 'Estadística', 'Análisis de datos y probabilidad', 3),
('550e8400-e29b-41d4-a716-446655440001', 'Trigonometría', 'Funciones trigonométricas', 3),
-- Lectura Crítica
('550e8400-e29b-41d4-a716-446655440002', 'Comprensión Lectora', 'Análisis y comprensión de textos', 2),
('550e8400-e29b-41d4-a716-446655440002', 'Argumentación', 'Estructura y validez de argumentos', 3),
('550e8400-e29b-41d4-a716-446655440002', 'Interpretación', 'Interpretación de textos complejos', 3),
-- Ciencias Naturales
('550e8400-e29b-41d4-a716-446655440003', 'Biología', 'Sistemas biológicos y ecosistemas', 2),
('550e8400-e29b-41d4-a716-446655440003', 'Física', 'Mecánica y ondas', 3),
('550e8400-e29b-41d4-a716-446655440003', 'Química', 'Estructura atómica y reacciones', 3),
-- Ciencias Sociales
('550e8400-e29b-41d4-a716-446655440004', 'Historia de Colombia', 'Períodos históricos colombianos', 2),
('550e8400-e29b-41d4-a716-446655440004', 'Geografía', 'Geografía física y humana', 2),
('550e8400-e29b-41d4-a716-446655440004', 'Constitución', 'Derechos y deberes ciudadanos', 2),
-- Inglés
('550e8400-e29b-41d4-a716-446655440005', 'Reading Comprehension', 'Comprensión de textos en inglés', 2),
('550e8400-e29b-41d4-a716-446655440005', 'Grammar', 'Estructuras gramaticales', 2),
('550e8400-e29b-41d4-a716-446655440005', 'Vocabulary', 'Vocabulario y expresiones', 1)
ON CONFLICT (subject_id, name) DO NOTHING;
" > /dev/null 2>&1

# 8. Ejecutar script de importación de preguntas
log "📊 Ejecutando importación de preguntas desde Excel..."
if docker exec $BACKEND_CONTAINER test -f "/app/ICFES_questions.xlsx" || \
   docker exec $BACKEND_CONTAINER test -f "/app/allquestions/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx"; then

    # Ejecutar script de importación Python
    docker exec $BACKEND_CONTAINER python3 -c "
import sys
sys.path.append('/app')
try:
    from scripts.complete_import import run_complete_import
    run_complete_import()
    print('✅ Importación completada exitosamente')
except Exception as e:
    print(f'⚠️ Error en importación: {e}')
" || warning "Error en importación de preguntas (continuando...)"
else
    warning "Archivos Excel no encontrados, creando preguntas de ejemplo..."
    # Crear preguntas de ejemplo como respaldo
    /root/IcfesLeveling/scripts/create-sample-questions.py
fi

# 9. Verificar estado final
log "🔍 Verificando estado final del sistema..."

# Contar registros importantes
SUBJECTS_COUNT=$(docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM subjects;" | tr -d ' ')
TOPICS_COUNT=$(docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM topics;" | tr -d ' ')
QUESTIONS_COUNT=$(docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM questions;" | tr -d ' ')
USERS_COUNT=$(docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM users;" | tr -d ' ')

echo "📊 ESTADO FINAL DEL SISTEMA:"
echo "   - Materias (Subjects): $SUBJECTS_COUNT"
echo "   - Temas (Topics): $TOPICS_COUNT"
echo "   - Preguntas (Questions): $QUESTIONS_COUNT"
echo "   - Usuarios (Users): $USERS_COUNT"

# 10. Reiniciar backend para aplicar cambios
log "🔄 Reiniciando backend..."
docker restart $BACKEND_CONTAINER > /dev/null 2>&1

# Esperar a que el backend esté listo
sleep 10
for i in {1..15}; do
    if curl -s http://localhost:4000/health > /dev/null 2>&1; then
        log "✅ Backend está funcionando correctamente"
        break
    fi
    if [ $i -eq 15 ]; then
        warning "Backend tardó más de lo esperado en responder"
    fi
    sleep 2
done

# 11. Mensaje final
echo ""
echo "🎉 ¡CONFIGURACIÓN COMPLETADA EXITOSAMENTE!"
echo ""
echo "📋 CREDENCIALES DE ACCESO:"
echo "   Usuario: admin"
echo "   Contraseña: secret"
echo ""
echo "🌐 URLS DE ACCESO:"
echo "   Frontend: http://localhost:4001"
echo "   Backend API: http://localhost:4000"
echo "   Health Check: http://localhost:4000/health"
echo ""
echo "📊 El sistema está listo para usar con $QUESTIONS_COUNT preguntas cargadas."
echo ""

exit 0