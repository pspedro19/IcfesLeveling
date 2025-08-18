#!/usr/bin/env python3
"""
Startup script that loads data and then starts the FastAPI server
"""
import os
import sys
import time
import subprocess
import logging

# Add the app directory to Python path
sys.path.insert(0, '/app')
sys.path.insert(0, '/seed_data')

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

def load_seed_data():
    """Load seed data into database"""
    try:
        # Import and run the data loader
        sys.path.insert(0, '/seed_data')
        from load_all_data import DataLoader
        
        loader = DataLoader()
        success = loader.run()
        
        if success:
            logger.info("✅ Seed data loaded successfully!")
        else:
            logger.warning("⚠️ Seed data loading had issues, but continuing...")
            
    except Exception as e:
        logger.error(f"Error loading seed data: {e}")
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
    # Wait for PostgreSQL
    if not wait_for_postgres():
        logger.error("PostgreSQL is not available after waiting")
        sys.exit(1)
    
    # Load seed data
    load_seed_data()
    
    # Start FastAPI
    start_fastapi()