"""Add requiere_imagen field and update based on image presence

Revision ID: 20241209_120100
Revises: 20241209_120000
Create Date: 2024-12-09 12:01:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20241209_120100'
down_revision = '20241209_120000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add requiere_imagen field and populate based on image presence."""
    
    # Check if column already exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('questions')]
    
    # Add requiere_imagen column if it doesn't exist
    if 'requiere_imagen' not in columns:
        op.add_column('questions', 
                     sa.Column('requiere_imagen', sa.Boolean(), nullable=True, default=False))
    
    # Update requiere_imagen based on actual image presence
    op.execute("""
        UPDATE questions 
        SET requiere_imagen = true 
        WHERE (pregunta_imagen IS NOT NULL AND pregunta_imagen != '')
           OR (opcion_a_imagen IS NOT NULL AND opcion_a_imagen != '')
           OR (opcion_b_imagen IS NOT NULL AND opcion_b_imagen != '')
           OR (opcion_c_imagen IS NOT NULL AND opcion_c_imagen != '')
           OR (opcion_d_imagen IS NOT NULL AND opcion_d_imagen != '');
    """)
    
    # Set false for questions without images
    op.execute("""
        UPDATE questions 
        SET requiere_imagen = false 
        WHERE requiere_imagen IS NULL
          AND (pregunta_imagen IS NULL OR pregunta_imagen = '')
          AND (opcion_a_imagen IS NULL OR opcion_a_imagen = '')
          AND (opcion_b_imagen IS NULL OR opcion_b_imagen = '')
          AND (opcion_c_imagen IS NULL OR opcion_c_imagen = '')
          AND (opcion_d_imagen IS NULL OR opcion_d_imagen = '');
    """)
    
    # Set default false for any remaining NULL values
    op.execute("""
        UPDATE questions 
        SET requiere_imagen = false 
        WHERE requiere_imagen IS NULL;
    """)
    
    # Make column NOT NULL and set default
    op.alter_column('questions', 'requiere_imagen', nullable=False, server_default='false')
    
    # Create index on requiere_imagen for faster filtering
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_requiere_imagen 
        ON questions(requiere_imagen) 
        WHERE requiere_imagen = true;
    """)


def downgrade() -> None:
    """Remove requiere_imagen field and its index."""
    
    # Drop the index
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_questions_requiere_imagen;")
    
    # Drop the column
    op.drop_column('questions', 'requiere_imagen')