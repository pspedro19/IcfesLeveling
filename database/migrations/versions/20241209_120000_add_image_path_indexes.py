"""Add optimized indexes for image path searches and performance

Revision ID: 20241209_120000
Revises: 
Create Date: 2024-12-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20241209_120000'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add optimized indexes for image path searches and performance."""
    
    # Create index for pregunta_imagen searches
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_pregunta_imagen 
        ON questions(pregunta_imagen) 
        WHERE pregunta_imagen IS NOT NULL;
    """)
    
    # Create composite index for area and image requirement
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_area_imagen 
        ON questions(area_evaluada, requiere_imagen) 
        WHERE requiere_imagen = true;
    """)
    
    # Create unique index on natural_key if it exists
    op.execute("""
        CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_natural_key 
        ON questions(natural_key) 
        WHERE natural_key IS NOT NULL;
    """)
    
    # Create composite index for topic_id and subject_id joins
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_topic_subject 
        ON questions(topic_id, subject_id);
    """)
    
    # Create index on difficulty for filtering
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_difficulty 
        ON questions(difficulty);
    """)
    
    # Create composite index for answer and difficulty analysis
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_answer_difficulty 
        ON questions(respuesta_correcta, difficulty);
    """)
    
    # Create index on created_at for temporal queries
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_created_at 
        ON questions(created_at);
    """)
    
    # Create partial index for questions with explanation
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_with_explanation 
        ON questions(id, explanation) 
        WHERE explanation IS NOT NULL AND explanation != '';
    """)
    
    # Create index on question_type
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_type 
        ON questions(question_type);
    """)
    
    # Create GIN index for full-text search on pregunta_texto
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_pregunta_texto_gin 
        ON questions 
        USING gin(to_tsvector('spanish', pregunta_texto)) 
        WHERE pregunta_texto IS NOT NULL;
    """)


def downgrade() -> None:
    """Remove the optimized indexes."""
    
    # Drop all indexes created in upgrade
    indexes_to_drop = [
        'idx_questions_pregunta_imagen',
        'idx_questions_area_imagen', 
        'idx_questions_natural_key',
        'idx_questions_topic_subject',
        'idx_questions_difficulty',
        'idx_questions_answer_difficulty',
        'idx_questions_created_at',
        'idx_questions_with_explanation',
        'idx_questions_type',
        'idx_questions_pregunta_texto_gin'
    ]
    
    for index_name in indexes_to_drop:
        op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {index_name};")