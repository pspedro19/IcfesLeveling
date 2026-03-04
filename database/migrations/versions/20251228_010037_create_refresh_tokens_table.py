"""Create refresh_tokens table

Revision ID: 20251228_010037
Revises: 20251228_001029
Create Date: 2025-12-28 01:00:37.123456

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251228_010037'
down_revision = '20251228_001029'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Run the upgrade."""
    op.create_table('refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('jti', sa.String(), unique=True, nullable=False, index=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    """Run the downgrade."""
    op.drop_table('refresh_tokens')
