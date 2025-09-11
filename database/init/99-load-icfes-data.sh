#!/bin/bash
# ICFES Data Loading Script for PostgreSQL Container
# This script installs Python dependencies and loads ICFES data during container initialization

echo "============================================================"
echo "ICFES DATA LOADING - DOCKER INITIALIZATION"
echo "============================================================"

# Install required packages
echo "Installing Python and dependencies..."
apt-get update -qq
apt-get install -y python3 python3-pip python3-venv > /dev/null 2>&1

# Create virtual environment and install packages
python3 -m venv /tmp/venv
source /tmp/venv/bin/activate

echo "Installing Python packages..."
pip install pandas psycopg2-binary openpyxl > /dev/null 2>&1

# Check if Excel file exists
EXCEL_FILE="/data/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx"

if [ -f "$EXCEL_FILE" ]; then
    echo "Found Excel file: $EXCEL_FILE"
    
    # Wait for database to be ready
    echo "Waiting for PostgreSQL to be ready..."
    until pg_isready -h localhost -p 5432 -U $POSTGRES_USER -d $POSTGRES_DB; do
        echo "  Waiting for database..."
        sleep 2
    done
    
    echo "Database is ready. Starting ICFES data import..."
    
    # Create Python script to load data
    cat > /tmp/load_data.py << 'EOF'
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import uuid
import os
import sys

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD')
}

def main():
    try:
        print("Loading Excel file...")
        df = pd.read_excel('/data/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx')
        print(f"Loaded {len(df)} questions from Excel")
        
        # Clean column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Subject mapping
        subject_map = {
            'ciencias naturales': '550e8400-e29b-41d4-a716-446655440003',
            'ciencias sociales': '550e8400-e29b-41d4-a716-446655440004',
            'ciencias sociales y ciudadanas': '550e8400-e29b-41d4-a716-446655440004',
            'matemáticas': '550e8400-e29b-41d4-a716-446655440001',
            'lectura crítica': '550e8400-e29b-41d4-a716-446655440002',
            'lenguaje': '550e8400-e29b-41d4-a716-446655440002',
            'inglés': '550e8400-e29b-41d4-a716-446655440005'
        }
        
        # Clear existing questions
        cur.execute("DELETE FROM questions")
        print("Cleared existing questions")
        
        inserted = 0
        for index, row in df.iterrows():
            try:
                question_id = str(uuid.uuid4())
                area = str(row.get('área_evaluada', '')).lower()
                subject_id = subject_map.get(area, '550e8400-e29b-41d4-a716-446655440001')
                
                # Basic question data
                question_data = {
                    'id': question_id,
                    'subject_id': subject_id,
                    'question_text': str(row.get('pregunta', '')),
                    'option_a': str(row.get('opcion_a', '')),
                    'option_b': str(row.get('opcion_b', '')),
                    'option_c': str(row.get('opcion_c', '')),
                    'option_d': str(row.get('opcion_d', '')),
                    'correct_answer': str(row.get('respuesta_correcta', 'a')).lower()[:1],
                    'topic': str(row.get('tema_específico', 'General')),
                    'difficulty': 5,
                    'options': json.dumps({
                        'a': str(row.get('opcion_a', '')),
                        'b': str(row.get('opcion_b', '')),
                        'c': str(row.get('opcion_c', '')),
                        'd': str(row.get('opcion_d', ''))
                    }),
                    'area_evaluada': str(row.get('área_evaluada', '')),
                    'competencia': str(row.get('competencia', '')),
                    'componente': str(row.get('componente', ''))
                }
                
                # Insert question
                columns = list(question_data.keys())
                values = list(question_data.values())
                placeholders = ['%s'] * len(values)
                
                insert_query = f"""
                    INSERT INTO questions ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                """
                
                cur.execute(insert_query, values)
                inserted += 1
                
                if inserted % 50 == 0:
                    print(f"  Inserted {inserted} questions...")
                    
            except Exception as e:
                print(f"  Error in row {index}: {str(e)[:50]}")
        
        conn.commit()
        print(f"\nImport completed: {inserted} questions inserted")
        
        # Verify results
        cur.execute("SELECT COUNT(*) FROM questions")
        total = cur.fetchone()[0]
        print(f"Total questions in database: {total}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
EOF
    
    # Execute the Python script
    python3 /tmp/load_data.py
    
    if [ $? -eq 0 ]; then
        echo "✅ ICFES data successfully loaded!"
    else
        echo "❌ Error loading ICFES data"
    fi
    
else
    echo "⚠️ Excel file not found at $EXCEL_FILE"
    echo "Skipping ICFES data import"
fi

echo "ICFES initialization complete"
echo "============================================================"