#!/bin/bash

# =====================================================
# SCRIPT DE CARGA COMPLETA DE DATOS ICFES
# =====================================================
# Este script importa todos los datos desde los archivos Excel
# en el directorio dataimg hacia la base de datos
# =====================================================

set -e  # Salir si hay errores

echo "============================================="
echo "   CARGA COMPLETA DE DATOS ICFES"
echo "============================================="
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Directorio base
BASE_DIR="/c/Users/HOME/Documents/icfes"
BACKEND_DIR="$BASE_DIR/IcfesLeveling/apps/backend"
DATAIMG_DIR="$BASE_DIR/dataimg"

# Función para verificar archivos Excel
check_excel_files() {
    echo -e "${YELLOW}📁 Verificando archivos Excel en dataimg...${NC}"
    
    if [ ! -d "$DATAIMG_DIR" ]; then
        echo -e "${RED}❌ Directorio dataimg no encontrado${NC}"
        exit 1
    fi
    
    echo "Archivos Excel encontrados:"
    ls -la "$DATAIMG_DIR"/*.xlsx 2>/dev/null || echo "No se encontraron archivos Excel"
    echo ""
}

# Función para inicializar base de datos
init_database() {
    echo -e "${YELLOW}🗄️ Inicializando base de datos...${NC}"
    
    cd "$BACKEND_DIR"
    
    # Verificar conexión a PostgreSQL
    docker exec -it icfes_postgres psql -U gameplay -d gameplay_db -c "SELECT 1;" > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ No se puede conectar a PostgreSQL${NC}"
        echo "Iniciando servicios Docker..."
        docker-compose up -d postgres redis
        sleep 10
    fi
    
    echo -e "${GREEN}✅ Base de datos lista${NC}"
}

# Función para importar datos desde Excel principal
import_main_excel() {
    echo -e "${YELLOW}📊 Importando datos desde ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx...${NC}"
    
    cd "$BACKEND_DIR"
    
    # Archivo principal con todas las preguntas
    MAIN_FILE="$DATAIMG_DIR/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx"
    
    if [ -f "$MAIN_FILE" ]; then
        python -m scripts.import_icfes_excel \
            --file "$MAIN_FILE" \
            --validate \
            --batch-size 100
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Importación principal completada${NC}"
        else
            echo -e "${RED}❌ Error en importación principal${NC}"
        fi
    else
        echo -e "${RED}❌ Archivo principal no encontrado${NC}"
    fi
}

# Función para importar archivos Excel adicionales
import_additional_excel() {
    echo -e "${YELLOW}📊 Importando archivos Excel adicionales...${NC}"
    
    cd "$BACKEND_DIR"
    
    # Lista de archivos adicionales
    FILES=(
        "ICFES2 (1).xlsx"
        "ICFES_HADID.xlsx"
        "Diccionario_Datos.xlsx"
    )
    
    for FILE in "${FILES[@]}"; do
        FULL_PATH="$DATAIMG_DIR/$FILE"
        if [ -f "$FULL_PATH" ]; then
            echo "Procesando: $FILE"
            python -m scripts.import_icfes_excel \
                --file "$FULL_PATH" \
                --validate \
                --batch-size 50
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ $FILE importado${NC}"
            else
                echo -e "${YELLOW}⚠️ Advertencia al importar $FILE${NC}"
            fi
        fi
    done
}

# Función para procesar imágenes desde PDFs
process_pdf_images() {
    echo -e "${YELLOW}🖼️ Procesando imágenes desde PDFs...${NC}"
    
    cd "$DATAIMG_DIR/scripts"
    
    if [ -f "pdf_image_extractor.py" ]; then
        # Procesar PDFs por materia
        SUBJECTS=("Matematicas" "Ciencias Naturales" "Ciencias Sociales" "Lectura Critica" "Ingles")
        
        for SUBJECT in "${SUBJECTS[@]}"; do
            PDF_DIR="$DATAIMG_DIR/$SUBJECT"
            if [ -d "$PDF_DIR" ]; then
                echo "Procesando PDFs de $SUBJECT..."
                
                # Buscar PDFs en el directorio
                find "$PDF_DIR" -name "*.pdf" -type f | while read PDF_FILE; do
                    echo "Extrayendo imágenes de: $(basename "$PDF_FILE")"
                    python pdf_image_extractor.py \
                        --pdf "$PDF_FILE" \
                        --output "$BASE_DIR/IcfesLeveling/mathimg/$SUBJECT" \
                        --banco "$SUBJECT"
                done
            fi
        done
        
        echo -e "${GREEN}✅ Procesamiento de imágenes completado${NC}"
    else
        echo -e "${YELLOW}⚠️ Script de extracción de imágenes no encontrado${NC}"
    fi
}

# Función para vincular imágenes con preguntas
link_images_to_questions() {
    echo -e "${YELLOW}🔗 Vinculando imágenes con preguntas...${NC}"
    
    cd "$BACKEND_DIR"
    
    python << EOF
import os
import sys
sys.path.append('.')
from app.core.database import SessionLocal
from app.models.question import Question
from sqlalchemy import text

db = SessionLocal()

try:
    # Actualizar rutas de imágenes en preguntas
    result = db.execute(text("""
        UPDATE questions 
        SET image_url = REPLACE(image_url, '../dataimg/', '/mathimg/')
        WHERE image_url LIKE '%dataimg%'
    """))
    
    db.commit()
    print(f"✅ Actualizadas {result.rowcount} rutas de imágenes")
    
    # Verificar preguntas con imágenes
    questions_with_images = db.query(Question).filter(
        Question.image_url.isnot(None)
    ).count()
    
    total_questions = db.query(Question).count()
    
    print(f"📊 Estadísticas:")
    print(f"   - Total de preguntas: {total_questions}")
    print(f"   - Preguntas con imágenes: {questions_with_images}")
    print(f"   - Porcentaje con imágenes: {(questions_with_images/total_questions*100):.1f}%")
    
except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()
finally:
    db.close()
EOF
}

# Función para generar estadísticas
generate_statistics() {
    echo -e "${YELLOW}📈 Generando estadísticas de importación...${NC}"
    
    cd "$BACKEND_DIR"
    
    python << EOF
import sys
sys.path.append('.')
from app.core.database import SessionLocal
from app.models.question import Question
from app.models.subject import Subject
from app.models.topic import Topic
from sqlalchemy import func

db = SessionLocal()

try:
    # Estadísticas por materia
    stats = db.query(
        Subject.name,
        func.count(Question.id).label('count')
    ).join(
        Question, Question.subject_id == Subject.id
    ).group_by(Subject.name).all()
    
    print("\n📊 ESTADÍSTICAS DE IMPORTACIÓN")
    print("=" * 40)
    
    total = 0
    for subject, count in stats:
        print(f"  {subject}: {count} preguntas")
        total += count
    
    print("-" * 40)
    print(f"  TOTAL: {total} preguntas")
    
    # Verificar dificultades
    difficulties = db.query(
        Question.difficulty,
        func.count(Question.id)
    ).group_by(Question.difficulty).all()
    
    print("\n📊 DISTRIBUCIÓN POR DIFICULTAD")
    print("=" * 40)
    for diff, count in difficulties:
        print(f"  Nivel {diff}: {count} preguntas")
    
    # Verificar preguntas con explicación
    with_explanation = db.query(Question).filter(
        Question.explanation.isnot(None)
    ).count()
    
    print(f"\n📝 Preguntas con explicación: {with_explanation}/{total}")
    
except Exception as e:
    print(f"❌ Error generando estadísticas: {e}")
finally:
    db.close()
EOF
}

# Función principal
main() {
    echo -e "${GREEN}🚀 Iniciando carga completa de datos ICFES${NC}"
    echo ""
    
    # Verificar archivos
    check_excel_files
    
    # Inicializar base de datos
    init_database
    
    # Importar datos principales
    import_main_excel
    
    # Importar archivos adicionales
    import_additional_excel
    
    # Procesar imágenes
    process_pdf_images
    
    # Vincular imágenes
    link_images_to_questions
    
    # Generar estadísticas
    generate_statistics
    
    echo ""
    echo -e "${GREEN}=============================================${NC}"
    echo -e "${GREEN}   ✅ CARGA DE DATOS COMPLETADA${NC}"
    echo -e "${GREEN}=============================================${NC}"
    echo ""
    echo "Próximos pasos:"
    echo "1. Verificar los datos en: http://localhost:4001"
    echo "2. Ejecutar pruebas: cd apps/backend && pytest"
    echo "3. Iniciar servicios: docker-compose up -d"
}

# Ejecutar script principal
main