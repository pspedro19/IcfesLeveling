#!/bin/bash
# YouTube Catalog Loading Script for PostgreSQL Container
# This script loads ONLY verified educational videos from the CSV catalog
# Executed automatically during container initialization

echo "============================================================"
echo "YOUTUBE CATALOG LOADING - DOCKER INITIALIZATION"
echo "============================================================"

# Install required packages
echo "Installing Python and dependencies..."
apt-get update -qq
apt-get install -y python3 python3-pip > /dev/null 2>&1

echo "Installing Python packages..."
pip3 install pandas psycopg2-binary > /dev/null 2>&1

# Check if YouTube catalog CSV exists
CSV_FILE="/docker-entrypoint-initdb.d/youtube_catalog_extendido_enriquecido.csv"
FALLBACK_CSV="/data/youtube_catalog_extendido_enriquecido.csv"

if [ -f "$CSV_FILE" ]; then
    CATALOG_FILE="$CSV_FILE"
    echo "Found YouTube catalog: $CSV_FILE"
elif [ -f "$FALLBACK_CSV" ]; then
    CATALOG_FILE="$FALLBACK_CSV"
    echo "Found YouTube catalog: $FALLBACK_CSV"
else
    echo "⚠️ YouTube catalog CSV not found, skipping video loading"
    exit 0
fi

# Wait for database to be ready
echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h localhost -p 5432 -U $POSTGRES_USER -d $POSTGRES_DB; do
    echo "  Waiting for database..."
    sleep 2
done

echo "Database is ready. Starting YouTube catalog import..."

# Create Python script to load YouTube videos
cat > /tmp/load_youtube_catalog.py << 'EOF'
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import json
import uuid
import os
import sys
import re
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD')
}

# Subject mapping
SUBJECT_MAPPING = {
    'Matemáticas': '550e8400-e29b-41d4-a716-446655440001',
    'Matematicas': '550e8400-e29b-41d4-a716-446655440001',
    'Lenguaje': '550e8400-e29b-41d4-a716-446655440002',
    'Lectura Crítica': '550e8400-e29b-41d4-a716-446655440002',
    'Lectura Critica': '550e8400-e29b-41d4-a716-446655440002',
    'Ciencias Naturales': '550e8400-e29b-41d4-a716-446655440003',
    'Ciencias Sociales': '550e8400-e29b-41d4-a716-446655440004',
    'Sociales y Competencias Ciudadanas': '550e8400-e29b-41d4-a716-446655440004',
    'Inglés': '550e8400-e29b-41d4-a716-446655440005',
    'InglÃ©s': '550e8400-e29b-41d4-a716-446655440005'
}

def extract_youtube_id(url):
    """Extract YouTube ID from URL"""
    if not url:
        return None
        
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            youtube_id = match.group(1)
            # Validate YouTube ID format (exactly 11 characters, alphanumeric + _ -)
            if len(youtube_id) == 11 and re.match(r'^[a-zA-Z0-9_-]+$', youtube_id):
                return youtube_id
    
    return None

def is_valid_youtube_id(youtube_id):
    """Validate YouTube ID format"""
    if not youtube_id:
        return False
    return len(youtube_id) == 11 and re.match(r'^[a-zA-Z0-9_-]+$', youtube_id)

def main():
    try:
        catalog_file = sys.argv[1] if len(sys.argv) > 1 else '/docker-entrypoint-initdb.d/youtube_catalog_extendido_enriquecido.csv'
        
        print(f"Loading YouTube catalog from: {catalog_file}")
        
        # Try different encodings
        df = None
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                df = pd.read_csv(catalog_file, delimiter=';', encoding=encoding)
                print(f"CSV loaded with {encoding} encoding: {len(df)} rows")
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            print("Error: Could not read CSV with any encoding")
            return 1
        
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Create youtube_catalog table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS youtube_catalog (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                subject_id UUID REFERENCES subjects(id),
                topic_id UUID,
                codigo_tema VARCHAR(50),
                youtube_id VARCHAR(11) NOT NULL,
                youtube_url VARCHAR(500) NOT NULL,
                title VARCHAR(300) NOT NULL,
                channel_name VARCHAR(200),
                duration_minutes INTEGER DEFAULT 15,
                quality_score DECIMAL(3,2) DEFAULT 0.80,
                topics_covered TEXT[],
                icfes_competence VARCHAR(200),
                icfes_component VARCHAR(200),
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(youtube_id, subject_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_youtube_catalog_subject ON youtube_catalog(subject_id);
            CREATE INDEX IF NOT EXISTS idx_youtube_catalog_active ON youtube_catalog(is_active);
            CREATE INDEX IF NOT EXISTS idx_youtube_catalog_quality ON youtube_catalog(quality_score);
        """)
        
        print("YouTube catalog table created/verified")
        
        # Clear existing videos to avoid conflicts
        cur.execute("DELETE FROM youtube_catalog")
        print("Cleared existing videos")
        
        # Process CSV data
        videos_data = []
        skipped_count = 0
        
        for idx, row in df.iterrows():
            try:
                # Extract basic information
                codigo_tema = str(row.get('codigo_tema', f'TEMA_{idx+1}')).strip()
                area_evaluada = str(row.get('area_evaluada', '')).strip()
                tema_principal = str(row.get('tema_principal', 'General')).strip()
                canal_sugerido = str(row.get('canal_sugerido', '')).strip()
                youtube_url = str(row.get('youtube_url', '')).strip()
                
                # Map area to subject_id
                subject_id = SUBJECT_MAPPING.get(area_evaluada)
                if not subject_id:
                    skipped_count += 1
                    continue
                
                # Extract and validate YouTube ID
                youtube_id = extract_youtube_id(youtube_url)
                if not youtube_id or not is_valid_youtube_id(youtube_id):
                    skipped_count += 1
                    continue
                
                # Prepare video data
                video_data = (
                    str(uuid.uuid4()),  # id
                    subject_id,         # subject_id
                    None,              # topic_id (will be linked later)
                    codigo_tema,       # codigo_tema
                    youtube_id,        # youtube_id (validated)
                    youtube_url,       # youtube_url
                    tema_principal,    # title
                    canal_sugerido.replace('@', ''),  # channel_name
                    15,                # duration_minutes
                    0.80,              # quality_score
                    [tema_principal, area_evaluada],  # topics_covered
                    None,              # icfes_competence
                    None,              # icfes_component
                    f"Educational video about {tema_principal}",  # description
                    True,              # is_active
                    datetime.now(),    # created_at
                    datetime.now()     # updated_at
                )
                
                videos_data.append(video_data)
                
                # Insert in batches of 50
                if len(videos_data) >= 50:
                    execute_batch(
                        cur,
                        """INSERT INTO youtube_catalog (
                            id, subject_id, topic_id, codigo_tema, youtube_id, youtube_url,
                            title, channel_name, duration_minutes, quality_score,
                            topics_covered, icfes_competence, icfes_component, description,
                            is_active, created_at, updated_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (youtube_id, subject_id) DO NOTHING""",
                        videos_data
                    )
                    conn.commit()
                    print(f"  Inserted {len(videos_data)} videos...")
                    videos_data = []
                    
            except Exception as e:
                print(f"  Error in row {idx}: {str(e)[:50]}")
                skipped_count += 1
                continue
        
        # Insert remaining videos
        if videos_data:
            execute_batch(
                cur,
                """INSERT INTO youtube_catalog (
                    id, subject_id, topic_id, codigo_tema, youtube_id, youtube_url,
                    title, channel_name, duration_minutes, quality_score,
                    topics_covered, icfes_competence, icfes_component, description,
                    is_active, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (youtube_id, subject_id) DO NOTHING""",
                videos_data
            )
            conn.commit()
            print(f"  Inserted final {len(videos_data)} videos...")
        
        # Verify results
        cur.execute("SELECT COUNT(*) FROM youtube_catalog WHERE is_active = TRUE")
        total_active = cur.fetchone()[0]
        
        cur.execute("""
            SELECT s.name, COUNT(yc.id) as video_count
            FROM subjects s
            LEFT JOIN youtube_catalog yc ON s.id = yc.subject_id AND yc.is_active = TRUE
            GROUP BY s.name
            ORDER BY video_count DESC
        """)
        
        subject_stats = cur.fetchall()
        
        print(f"\nYouTube catalog import completed!")
        print(f"Total active videos: {total_active}")
        print(f"Skipped invalid entries: {skipped_count}")
        print("\nVideos by subject:")
        for subject, count in subject_stats:
            print(f"  {subject}: {count} videos")
        
        conn.close()
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
EOF

# Execute the Python script
python3 /tmp/load_youtube_catalog.py "$CATALOG_FILE"

if [ $? -eq 0 ]; then
    echo "✅ YouTube catalog successfully loaded!"
else
    echo "❌ Error loading YouTube catalog"
fi

echo "YouTube catalog initialization complete"
echo "============================================================"


