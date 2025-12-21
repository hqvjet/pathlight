"""Initial course schema (ERD 2025-12-12)

Revision ID: reset_20251212
Revises: 
Create Date: 2025-12-12
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'reset_20251212'
down_revision = None
branch_labels = None
depends_on = None


def _create_course_tables():
    op.create_table(
        'course',
        sa.Column('course_id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), nullable=False, index=True),
        sa.Column('publish', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('finish', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('overview', sa.String(), nullable=False),
        sa.Column('level', sa.String(), nullable=False),
        sa.Column('duration', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'lesson',
        sa.Column('lesson_id', sa.String(), primary_key=True),
        sa.Column('course_id', sa.String(), sa.ForeignKey('course.course_id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('overview', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('duration', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'assessment',
        sa.Column('assessment_id', sa.String(), primary_key=True),
        sa.Column('lesson_id', sa.String(), sa.ForeignKey('lesson.lesson_id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('question', sa.String(), nullable=False),
        sa.Column('hint', sa.String(), nullable=True),
        sa.Column('explanation', sa.String(), nullable=False),
        sa.Column('difficulty', sa.String(), nullable=False),
        sa.Column('option1', sa.String(), nullable=False),
        sa.Column('option2', sa.String(), nullable=False),
        sa.Column('option3', sa.String(), nullable=False),
        sa.Column('option4', sa.String(), nullable=False),
        sa.Column('answer', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'learning_progress',
        sa.Column('user_id', sa.String(), nullable=False, primary_key=True, index=True),
        sa.Column('course_id', sa.String(), sa.ForeignKey('course.course_id', ondelete='CASCADE'), nullable=False, primary_key=True, index=True),
        sa.Column('num_finished_lesson', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('num_total_lesson', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def upgrade():
    _create_course_tables()


def downgrade():
    for tbl in ['learning_progress', 'assessment', 'lesson', 'course']:
        op.drop_table(tbl)
