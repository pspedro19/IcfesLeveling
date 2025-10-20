#!/usr/bin/env python3
"""
Apply diagnostic tracking migrations to the database
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'icfes_leveling'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password')
}

def apply_migration(cursor, migration_file_path):
    """Apply a single migration file"""
    try:
        with open(migration_file_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        print(f"Applying migration: {os.path.basename(migration_file_path)}")
        cursor.execute(migration_sql)
        print(f"✓ Successfully applied: {os.path.basename(migration_file_path)}")
        return True
    except Exception as e:
        print(f"✗ Error applying {os.path.basename(migration_file_path)}: {e}")
        return False

def main():
    """Apply diagnostic tracking migrations"""
    # Migration files to apply
    migrations = [
        'database/migrations/033-add-diagnostic-tracking-metrics.sql',
        'database/migrations/034-add-puntos-xp-to-questions.sql'
    ]
    
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        cursor = conn.cursor()
        
        print("Connected successfully!")
        
        # Apply migrations
        success_count = 0
        for migration_file in migrations:
            if os.path.exists(migration_file):
                if apply_migration(cursor, migration_file):
                    success_count += 1
                    conn.commit()
                else:
                    conn.rollback()
                    print(f"Rolled back transaction for {migration_file}")
            else:
                print(f"Migration file not found: {migration_file}")
        
        print(f"\nCompleted: {success_count}/{len(migrations)} migrations applied successfully")
        
        if success_count == len(migrations):
            print("\n🎉 All diagnostic tracking migrations applied successfully!")
            print("\nThe following features are now available:")
            print("- Response time tracking (Tiempo_Estimado baseline)")
            print("- Difficulty level tracking (Nivel_Dificultad)")
            print("- Performance level tracking (Nivel_Desempeño_Esperado)")
            print("- XP earned tracking (Puntos_XP)")
            print("\nData will be automatically stored in the diagnostic_test_results table.")
        else:
            print("\n⚠️  Some migrations failed. Please check the error messages above.")
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
    finally:
        try:
            cursor.close()
            conn.close()
            print("Database connection closed.")
        except:
            pass
    
    return 0 if success_count == len(migrations) else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)