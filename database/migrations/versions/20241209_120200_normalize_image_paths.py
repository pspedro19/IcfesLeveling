"""Normalize image paths and add validation constraints

Revision ID: 20241209_120200
Revises: 20241209_120100
Create Date: 2024-12-09 12:02:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20241209_120200'
down_revision = '20241209_120100'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Normalize image paths and add validation constraints."""
    
    # Normalize image paths - replace backslashes with forward slashes
    image_columns = [
        'pregunta_imagen',
        'opcion_a_imagen', 
        'opcion_b_imagen',
        'opcion_c_imagen',
        'opcion_d_imagen'
    ]
    
    for column in image_columns:
        # Replace backslashes with forward slashes
        op.execute(f"""
            UPDATE questions 
            SET {column} = REPLACE({column}, '\\', '/') 
            WHERE {column} IS NOT NULL AND {column} LIKE '%\\%';
        """)
        
        # Remove duplicate slashes
        op.execute(f"""
            UPDATE questions 
            SET {column} = REGEXP_REPLACE({column}, '/+', '/', 'g') 
            WHERE {column} IS NOT NULL;
        """)
        
        # Trim whitespace
        op.execute(f"""
            UPDATE questions 
            SET {column} = TRIM({column}) 
            WHERE {column} IS NOT NULL;
        """)
    
    # Add check constraints for valid image paths
    # Constraint to ensure image paths don't contain invalid characters
    op.execute("""
        ALTER TABLE questions 
        ADD CONSTRAINT check_pregunta_imagen_valid 
        CHECK (pregunta_imagen IS NULL OR pregunta_imagen NOT LIKE '%<%' AND pregunta_imagen NOT LIKE '%>%');
    """)
    
    # Add constraints for option images as well
    for option in ['a', 'b', 'c', 'd']:
        op.execute(f"""
            ALTER TABLE questions 
            ADD CONSTRAINT check_opcion_{option}_imagen_valid 
            CHECK (opcion_{option}_imagen IS NULL OR 
                   (opcion_{option}_imagen NOT LIKE '%<%' AND 
                    opcion_{option}_imagen NOT LIKE '%>%'));
        """)
    
    # Add constraint to ensure respuesta_correcta is valid
    op.execute("""
        ALTER TABLE questions 
        ADD CONSTRAINT check_respuesta_correcta_valid 
        CHECK (respuesta_correcta IN ('a', 'b', 'c', 'd', 'A', 'B', 'C', 'D'));
    """)
    
    # Add constraint for difficulty range
    op.execute("""
        ALTER TABLE questions 
        ADD CONSTRAINT check_difficulty_range 
        CHECK (difficulty >= 1 AND difficulty <= 10);
    """)
    
    # Create function to automatically update requiere_imagen on image changes
    op.execute("""
        CREATE OR REPLACE FUNCTION update_requiere_imagen()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.requiere_imagen := (
                (NEW.pregunta_imagen IS NOT NULL AND NEW.pregunta_imagen != '') OR
                (NEW.opcion_a_imagen IS NOT NULL AND NEW.opcion_a_imagen != '') OR
                (NEW.opcion_b_imagen IS NOT NULL AND NEW.opcion_b_imagen != '') OR
                (NEW.opcion_c_imagen IS NOT NULL AND NEW.opcion_c_imagen != '') OR
                (NEW.opcion_d_imagen IS NOT NULL AND NEW.opcion_d_imagen != '')
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger to automatically update requiere_imagen
    op.execute("""
        CREATE TRIGGER trigger_update_requiere_imagen
            BEFORE INSERT OR UPDATE OF pregunta_imagen, opcion_a_imagen, 
                                       opcion_b_imagen, opcion_c_imagen, opcion_d_imagen
            ON questions
            FOR EACH ROW
            EXECUTE FUNCTION update_requiere_imagen();
    """)


def downgrade() -> None:
    """Remove validation constraints and triggers."""
    
    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS trigger_update_requiere_imagen ON questions;")
    op.execute("DROP FUNCTION IF EXISTS update_requiere_imagen();")
    
    # Drop check constraints
    constraints_to_drop = [
        'check_pregunta_imagen_valid',
        'check_opcion_a_imagen_valid',
        'check_opcion_b_imagen_valid', 
        'check_opcion_c_imagen_valid',
        'check_opcion_d_imagen_valid',
        'check_respuesta_correcta_valid',
        'check_difficulty_range'
    ]
    
    for constraint in constraints_to_drop:
        op.execute(f"ALTER TABLE questions DROP CONSTRAINT IF EXISTS {constraint};")