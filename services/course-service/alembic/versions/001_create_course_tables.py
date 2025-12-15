"""Create course related tables aligned to course ERD

Revision ID: 001
Revises:
Create Date: 2025-06-19 14:40:00.000000

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
        'course',
        sa.Column('course_id', sa.String(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('publish', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('finish', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('overview', sa.String(), nullable=False),
        sa.Column('level', sa.String(), nullable=False),
        sa.Column('duration', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    op.create_table(
        'lesson',
        sa.Column('lesson_id', sa.String(), primary_key=True, nullable=False),
        sa.Column('course_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('overview', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('duration', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['course_id'], ['course.course_id'], ondelete='CASCADE'),
    )

    op.create_table(
        'assessment',
        sa.Column('assessment_id', sa.String(), primary_key=True, nullable=False),
        sa.Column('lesson_id', sa.String(), nullable=False),
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
        sa.ForeignKeyConstraint(['lesson_id'], ['lesson.lesson_id'], ondelete='CASCADE'),
    )

    op.create_table(
        'learning_progress',
        sa.Column('user_id', sa.String(), primary_key=True, nullable=False),
        sa.Column('course_id', sa.String(), primary_key=True, nullable=False),
        sa.Column('num_finished_lesson', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('num_total_lesson', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['course_id'], ['course.course_id'], ondelete='CASCADE'),
    )


def downgrade() -> None:
    op.drop_table('learning_progress')
    op.drop_table('assessment')
    op.drop_table('lesson')
    op.drop_table('course')
