#!/usr/bin/env python3
"""
Startup script that loads CSV seed data and then starts the FastAPI server
Ensures all CSV files are loaded with proper field mapping
"""
import os
import sys
import time
import subprocess
import logging
import shutil

# Add the app directory to Python path
sys.path.insert(0, '/app')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_postgres(max_retries=30):
    """Wait for PostgreSQL to be ready"""
    import psycopg2
    
    db_config = {
        'host': os.getenv('DB_HOST', 'postgres'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'gameplay_db'),
        'user': os.getenv('DB_USER', 'gameplay'),
        'password': os.getenv('DB_PASSWORD', 'gameplay123')
    }
    
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(**db_config)
            conn.close()
            logger.info("✅ PostgreSQL is ready!")
            return True
        except Exception as e:
            logger.info(f"⏳ Waiting for PostgreSQL... ({i+1}/{max_retries})")
            time.sleep(2)
    
    return False

def copy_seed_data_if_needed():
    """Copy seed data files to expected location if they exist"""
    sources = [
        ('/seed_data', '/app/seed_data'),
        ('./database/seed_data', '/app/seed_data'),
        ('/app/database/seed_data', '/app/seed_data')
    ]
    
    for source, dest in sources:
        if os.path.exists(source) and not os.path.exists(dest):
            logger.info(f"📁 Copying seed data from {source} to {dest}")
            shutil.copytree(source, dest)
            return dest
        elif os.path.exists(source):
            return source
    
    # Check for individual CSV files in various locations
    csv_locations = [
        '/app/database/data',
        '/app/database',
        '/app',
        './database/data'
    ]
    
    for location in csv_locations:
        if os.path.exists(location):
            csv_files = [f for f in os.listdir(location) if f.endswith('.csv')]
            if csv_files:
                logger.info(f"📊 Found {len(csv_files)} CSV files in {location}")
                return location
    
    return None

def load_seed_data():
    """Load seed data into database from CSV files"""
    try:
        # Find seed data location
        seed_data_path = copy_seed_data_if_needed()
        
        if not seed_data_path:
            logger.warning("⚠️ No seed data directory found")
            return
        
        logger.info(f"📂 Using seed data from: {seed_data_path}")
        
        # Check for CSV files
        csv_files = {
            'questions.csv': False,
            'topics_catalog.csv': False,
            'study_plan_templates.csv': False,
            'youtube_catalog_extendido_enriquecido.csv': False
        }
        
        for filename in csv_files.keys():
            full_path = os.path.join(seed_data_path, filename)
            if os.path.exists(full_path):
                csv_files[filename] = True
                logger.info(f"✅ Found: {filename}")
            else:
                # Try alternate names
                alt_names = {
                    'youtube_catalog_extendido_enriquecido.csv': ['youtube_catalog.csv', '01_icfes_youtube_catalog.csv'],
                    'topics_catalog.csv': ['01_icfes_topics_catalog.csv', 'ICFES_topics.csv']
                }
                for alt in alt_names.get(filename, []):
                    alt_path = os.path.join(seed_data_path, alt)
                    if os.path.exists(alt_path):
                        csv_files[filename] = True
                        logger.info(f"✅ Found (as {alt}): {filename}")
                        break
        
        # Check if we have the updated load_all_data.py
        loader_script = os.path.join(seed_data_path, 'load_all_data.py')
        if os.path.exists(loader_script):
            logger.info("🚀 Using load_all_data.py script")
            sys.path.insert(0, seed_data_path)
            from load_all_data import DataLoader
            
            loader = DataLoader()
            success = loader.run()
            
            if success:
                logger.info("✅ CSV data loaded successfully!")
            else:
                logger.warning("⚠️ CSV data loading had issues")
        else:
            logger.warning("⚠️ load_all_data.py not found, skipping CSV loading")
            logger.info(f"📍 Looked for script at: {loader_script}")
            
    except Exception as e:
        logger.error(f"Error loading seed data: {e}")
        import traceback
        logger.error(traceback.format_exc())
        logger.info("Continuing without seed data...")

def start_fastapi():
    """Start the FastAPI server"""
    logger.info("🚀 Starting FastAPI server...")
    os.execvp("uvicorn", [
        "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "4000",
        "--reload"
    ])

if __name__ == "__main__":
    logger.info("="*60)
    logger.info("🎯 ICFES LEVELING - STARTUP WITH CSV LOADER")
    logger.info("="*60)
    
    # Wait for PostgreSQL
    if not wait_for_postgres():
        logger.error("PostgreSQL is not available after waiting")
        sys.exit(1)
    
    # Load seed data from CSV files
    logger.info("📊 Starting CSV data loading process...")
    load_seed_data()
    
    # Start FastAPI
    start_fastapi()