#!/bin/bash

# Script para cargar preguntas desde Excel a la base de datos
# Uso: ./upload_questions.sh

echo "🚀 ICFES LEVELING - CARGA DE PREGUNTAS DESDE EXCEL"
echo "=================================================="

# Verificar si existe el archivo Excel
EXCEL_FILE="database/seed_data/questions.xlsx"
if [ ! -f "$EXCEL_FILE" ]; then
    echo "❌ Error: Archivo no encontrado: $EXCEL_FILE"
    echo "   Por favor, asegúrate de que el archivo questions.xlsx esté en database/seed_data/"
    exit 1
fi

echo "✅ Archivo Excel encontrado: $EXCEL_FILE"

# Verificar dependencias de Python
echo "🔍 Verificando dependencias de Python..."
python3 -c "import pandas, psycopg2, openpyxl" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️ Instalando dependencias de Python..."
    pip install pandas psycopg2-binary openpyxl --break-system-packages 2>/dev/null || \
    apt-get update && apt-get install -y python3-pandas python3-psycopg2 python3-openpyxl
fi

# Verificar conexión a la base de datos
echo "🔌 Verificando conexión a la base de datos..."
python3 -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'gameplay_db'),
        user=os.getenv('DB_USER', 'gameplay'),
        password=os.getenv('DB_PASSWORD', 'gameplay123')
    )
    conn.close()
    print('✅ Conexión a base de datos exitosa')
except Exception as e:
    print(f'❌ Error de conexión: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ No se pudo conectar a la base de datos"
    echo "   Verifica que PostgreSQL esté ejecutándose y las credenciales sean correctas"
    exit 1
fi

# Ejecutar script de carga
echo "📊 Iniciando carga de preguntas..."
echo "   Archivo: $EXCEL_FILE"
echo "   Filas detectadas: $(python3 -c "import pandas as pd; print(len(pd.read_excel('$EXCEL_FILE')))")"
echo ""

# Ejecutar el script principal
python3 database/seed_data/upload_questions_to_db.py

# Verificar resultado
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 ¡CARGA COMPLETADA EXITOSAMENTE!"
    echo ""
    echo "📊 Para verificar los datos cargados:"
    echo "   curl http://localhost:4000/api/v1/diagnostic-public/subjects"
    echo ""
    echo "🌐 Para probar en el frontend:"
    echo "   http://localhost:4001/diagnostic-test"
    echo ""
else
    echo ""
    echo "❌ Error durante la carga. Revisa los logs arriba."
    echo ""
fi
