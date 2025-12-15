"""Create quiz tables aligned to ERD

Revision ID: 001
Revises: 
Create Date: 2025-06-19 14:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'quiz',
        sa.Column('quiz_id', sa.String(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('publish', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('finish', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('overview', sa.String(), nullable=False),
        sa.Column('level', sa.String(), nullable=False),
        sa.Column('duration', sa.Integer(), nullable=False),
        sa.Column('num_questions', sa.Integer(), nullable=False),
        sa.Column('previous_score', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    op.create_table(
        'quiz_card',
        sa.Column('card_id', sa.String(), primary_key=True, nullable=False),
        sa.Column('quiz_id', sa.String(), nullable=False),
        sa.Column('question', sa.String(), nullable=False),
        sa.Column('hint', sa.String(), nullable=True),
        sa.Column('explanation', sa.String(), nullable=False),
        sa.Column('difficulty', sa.String(), nullable=False),
        sa.Column('option1', sa.String(), nullable=False),
        sa.Column('option2', sa.String(), nullable=False),
        sa.Column('option3', sa.String(), nullable=False),
        sa.Column('option4', sa.String(), nullable=False),
        sa.Column('answer', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['quiz_id'], ['quiz.quiz_id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('quiz_card')
    op.drop_table('quiz')
