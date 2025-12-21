"""add_creation_type

Revision ID: 002
Revises: 001
Create Date: 2024-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Add creation_type column with default 'ai' for existing quizzes
    op.add_column('quiz', sa.Column('creation_type', sa.String(), nullable=False, server_default='ai'))


def downgrade():
    op.drop_column('quiz', 'creation_type')
