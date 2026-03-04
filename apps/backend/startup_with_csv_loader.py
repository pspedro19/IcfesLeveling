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
        'password': os.getenv('DB_PASSWORD', '')
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

def run_migrations():
    """Run Alembic migrations to ensure DB schema is up to date."""
    try:
        migrations_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'migrations')
        if not os.path.exists(migrations_dir):
            migrations_dir = '/app/database/migrations'

        if os.path.exists(os.path.join(migrations_dir, 'alembic.ini')):
            logger.info("Running Alembic migrations...")
            result = subprocess.run(
                ['alembic', 'upgrade', 'head'],
                cwd=migrations_dir,
                capture_output=True, text=True,
                timeout=60
            )
            if result.returncode == 0:
                logger.info("Alembic migrations completed successfully!")
            else:
                logger.warning(f"Alembic migration failed: {result.stderr}")
                logger.info("Falling back to SQLAlchemy create_all...")
                _create_tables_fallback()
        else:
            logger.info("No Alembic config found, using SQLAlchemy create_all...")
            _create_tables_fallback()
    except Exception as e:
        logger.warning(f"Migration error: {e}, falling back to create_all")
        _create_tables_fallback()

def _create_tables_fallback():
    """Create all tables via SQLAlchemy metadata as fallback."""
    try:
        from app.core.database import engine, Base
        from app.models import *  # noqa: F401,F403 — import all models
        Base.metadata.create_all(bind=engine)
        logger.info("SQLAlchemy create_all completed!")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")

def load_seed_data():
    """Load seed data into database by calling the main loader script."""
    try:
        # The new structure is standardized, so we can call the loader directly.
        # This script assumes it's being run from the project root.
        loader_script = 'database/seed_data/load_all_data.py'
        
        if os.path.exists(loader_script):
            logger.info(f"🚀 Found loader script at: {loader_script}")
            
            # Execute the script using python3
            result = subprocess.run(['python3', loader_script], capture_output=True, text=True)
            
            logger.info("--- Loader Script STDOUT ---")
            logger.info(result.stdout)
            
            if result.returncode != 0:
                logger.error("--- Loader Script STDERR ---")
                logger.error(result.stderr)
                logger.warning("⚠️ CSV data loading script failed")
            else:
                logger.info("✅ CSV data loading script finished successfully!")
        else:
            logger.warning(f"⚠️ Loader script not found at: {loader_script}, skipping CSV loading")
            
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
    
    # Run database migrations
    logger.info("Running database migrations...")
    run_migrations()

    # Load seed data from CSV files
    logger.info("Starting CSV data loading process...")
    load_seed_data()
    
    # Start FastAPI
    start_fastapi()