"""Manually add columns to questions and diagnostic_tests

Revision ID: 20251228_001029
Revises: 20241209_120200
Create Date: 2025-12-28 00:10:29.234567

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251228_001029'
down_revision = '20241209_120200'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Run the upgrade."""
    # ### commands for questions table ###
    op.add_column('questions', sa.Column('pregunta_texto', sa.Text(), nullable=True))
    op.add_column('questions', sa.Column('pregunta_imagen', sa.String(length=500), nullable=True))
    op.add_column('questions', sa.Column('opcion_a_texto', sa.Text(), nullable=True))
    op.add_column('questions', sa.Column('opcion_a_imagen', sa.String(length=500), nullable=True))
    op.add_column('questions', sa.Column('opcion_b_texto', sa.Text(), nullable=True))
    op.add_column('questions', sa.Column('opcion_b_imagen', sa.String(length=500), nullable=True))
    op.add_column('questions', sa.Column('opcion_c_texto', sa.Text(), nullable=True))
    op.add_column('questions', sa.Column('opcion_c_imagen', sa.String(length=500), nullable=True))
    op.add_column('questions', sa.Column('opcion_d_texto', sa.Text(), nullable=True))
    op.add_column('questions', sa.Column('opcion_d_imagen', sa.String(length=500), nullable=True))
    op.add_column('questions', sa.Column('puntos_xp', sa.Integer(), server_default='10', nullable=True))
    
    # ### commands for diagnostic_tests table ###
    op.add_column('diagnostic_tests', sa.Column('reassessment_type', sa.String(length=50), nullable=True))
    op.add_column('diagnostic_tests', sa.Column('original_test_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('diagnostic_tests', sa.Column('is_monthly_reassessment', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('diagnostic_tests', sa.Column('days_since_initial', sa.Integer(), nullable=True))
    op.add_column('diagnostic_tests', sa.Column('comparison_with_initial', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('diagnostic_tests', sa.Column('plan_regenerated', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('diagnostic_tests', sa.Column('new_goals_generated', sa.Boolean(), server_default='false', nullable=True))
    op.add_column('diagnostic_tests', sa.Column('notification_sent', sa.Boolean(), server_default='false', nullable=True))
    # Note: questions_answered and time_spent_seconds already existed, adding them again might cause errors if not checked.
    # The manual DDL used 'ADD COLUMN IF NOT EXISTS', op.add_column does not have this.
    # We will assume they might not exist and let Alembic handle it.
    op.add_column('diagnostic_tests', sa.Column('score_percentage', sa.DECIMAL(precision=5, scale=2), server_default='0.00', nullable=True))
    op.add_column('diagnostic_tests', sa.Column('score_by_topic', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True))
    op.add_column('diagnostic_tests', sa.Column('status', sa.String(length=20), server_default='in_progress', nullable=True))
    op.add_column('diagnostic_tests', sa.Column('started_at', sa.DateTime(), nullable=True))
    
    # Foreign key for original_test_id
    op.create_foreign_key('fk_diagnostic_tests_original_test_id', 'diagnostic_tests', 'diagnostic_tests', ['original_test_id'], ['id'])


def downgrade() -> None:
    """Run the downgrade."""
    # ### commands for diagnostic_tests table ###
    op.drop_constraint('fk_diagnostic_tests_original_test_id', 'diagnostic_tests', type_='foreignkey')
    op.drop_column('diagnostic_tests', 'completed_at')
    op.drop_column('diagnostic_tests', 'started_at')
    op.drop_column('diagnostic_tests', 'status')
    op.drop_column('diagnostic_tests', 'score_by_topic')
    op.drop_column('diagnostic_tests', 'score_percentage')
    op.drop_column('diagnostic_tests', 'notification_sent')
    op.drop_column('diagnostic_tests', 'new_goals_generated')
    op.drop_column('diagnostic_tests', 'plan_regenerated')
    op.drop_column('diagnostic_tests', 'comparison_with_initial')
    op.drop_column('diagnostic_tests', 'days_since_initial')
    op.drop_column('diagnostic_tests', 'is_monthly_reassessment')
    op.drop_column('diagnostic_tests', 'original_test_id')
    op.drop_column('diagnostic_tests', 'reassessment_type')

    # ### commands for questions table ###
    op.drop_column('questions', 'puntos_xp')
    op.drop_column('questions', 'opcion_d_imagen')
    op.drop_column('questions', 'opcion_d_texto')
    op.drop_column('questions', 'opcion_c_imagen')
    op.drop_column('questions', 'opcion_c_texto')
    op.drop_column('questions', 'opcion_b_imagen')
    op.drop_column('questions', 'opcion_b_texto')
    op.drop_column('questions', 'opcion_a_imagen')
    op.drop_column('questions', 'opcion_a_texto')
    op.drop_column('questions', 'pregunta_imagen')
    op.drop_column('questions', 'pregunta_texto')
