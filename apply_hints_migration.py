#!/usr/bin/env python3
"""
Apply hints database migration
"""
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_hints_migration():
    """Apply the hints migration to add hint fields to questions table"""
    
    # Database connection
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://gameplay:gameplay123@localhost:5433/gameplay_db")
    
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("🔄 Applying hints migration...")
        
        # Read and execute migration file
        migration_path = "database/migrations/034-add-question-hints.sql"
        
        with open(migration_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
            
        cursor.execute(migration_sql)
        conn.commit()
        
        print("✅ Hints migration applied successfully!")
        
        # Verify the columns were added
        cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'questions' 
        AND column_name IN ('pista_1', 'pista_2', 'pista_3', 'explicacion_respuesta', 'error_comun')
        ORDER BY column_name;
        """)
        
        columns = cursor.fetchall()
        print(f"✅ Verified hint columns added: {[col[0] for col in columns]}")
        
        # Also check diagnostic tracking columns
        cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'diagnostic_test_answers' 
        AND column_name IN ('hints_used', 'hint_levels_requested')
        ORDER BY column_name;
        """)
        
        tracking_columns = cursor.fetchall()
        print(f"✅ Verified tracking columns added: {[col[0] for col in tracking_columns]}")
        
    except Exception as e:
        print(f"Error applying migration: {str(e)}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    apply_hints_migration()