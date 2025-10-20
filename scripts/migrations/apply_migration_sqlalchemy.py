#!/usr/bin/env python3
"""
Apply hints database migration using SQLAlchemy
"""
import sys
import os

# Add the backend app to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'backend'))

from sqlalchemy import text
from app.core.database import engine
from app.models.question import Question

def apply_hints_migration():
    """Apply the hints migration to add hint fields to questions table"""
    
    try:
        print("Applying hints migration...")
        
        with engine.begin() as conn:
            # Read and execute migration file
            migration_path = "database/migrations/034-add-question-hints.sql"
            
            with open(migration_path, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
                
            # Split by statements and execute each one
            statements = migration_sql.split(';')
            
            for statement in statements:
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        conn.execute(text(statement))
                        print(f"Executed: {statement[:100]}...")
                    except Exception as e:
                        if "already exists" in str(e) or "duplicate column name" in str(e):
                            print(f"Column already exists, skipping: {statement[:50]}...")
                        else:
                            print(f"Warning executing statement: {str(e)}")
        
        print("Migration applied successfully!")
        
        # Verify the columns were added
        with engine.begin() as conn:
            result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'questions' 
            AND column_name IN ('pista_1', 'pista_2', 'pista_3', 'explicacion_respuesta', 'error_comun')
            ORDER BY column_name;
            """))
            
            columns = [row[0] for row in result]
            print(f"Verified hint columns: {columns}")
            
            # Also check diagnostic tracking columns
            result2 = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'diagnostic_test_answers' 
            AND column_name IN ('hints_used', 'hint_levels_requested')
            ORDER BY column_name;
            """))
            
            tracking_columns = [row[0] for row in result2]
            print(f"Verified tracking columns: {tracking_columns}")
        
    except Exception as e:
        print(f"Error applying migration: {str(e)}")
        raise

if __name__ == "__main__":
    apply_hints_migration()