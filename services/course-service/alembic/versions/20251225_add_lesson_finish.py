"""Add finish column to lesson table

Revision ID: 20251225_add_lesson_finish
Revises: 20251212_reset_schema
Create Date: 2025-12-25
"""

from alembic import op
import sqlalchemy as sa

revision = "20251225_add_lesson_finish"
down_revision = "20251212_reset_schema"
branch_labels = None
depends_on = None


def upgrade():
    # Add finish column to lesson table
    op.add_column('lesson', sa.Column('finish', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    op.drop_column('lesson', 'finish')
