"""reset schema to ERD 2025-12-12

Revision ID: reset_20251212
Revises: 001_create_course_tables
Create Date: 2025-12-12
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'reset_20251212'
down_revision = '001_create_course_tables'
branch_labels = None
depends_on = None


def _drop_if_exists(inspector, table_name: str):
    if inspector.has_table(table_name):
        op.drop_table(table_name)


def _create_course_tables(inspector):
    if not inspector.has_table('course'):
        op.create_table(
            'course',
            sa.Column('course_id', sa.String(), primary_key=True),
            sa.Column('user_id', sa.String(), nullable=False, index=True),
            sa.Column('finish', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('overview', sa.String(), nullable=False),
            sa.Column('level', sa.String(), nullable=False),
            sa.Column('duration', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )

    if not inspector.has_table('lesson'):
        op.create_table(
            'lesson',
            sa.Column('lesson_id', sa.String(), primary_key=True),
            sa.Column('course_id', sa.String(), sa.ForeignKey('course.course_id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('overview', sa.String(), nullable=False),
            sa.Column('content', sa.String(), nullable=False),
            sa.Column('duration', sa.Integer(), nullable=False),
            sa.Column('finish', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )

    if not inspector.has_table('assessment'):
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

    if not inspector.has_table('quiz'):
        op.create_table(
            'quiz',
            sa.Column('quiz_id', sa.String(), primary_key=True),
            sa.Column('course_id', sa.String(), sa.ForeignKey('course.course_id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('finish', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )

    if not inspector.has_table('quiz_qa'):
        op.create_table(
            'quiz_qa',
            sa.Column('qa_id', sa.String(), primary_key=True),
            sa.Column('quiz_id', sa.String(), sa.ForeignKey('quiz.quiz_id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('question', sa.String(), nullable=False),
            sa.Column('explain', sa.String(), nullable=False),
            sa.Column('option1', sa.String(), nullable=False),
            sa.Column('option2', sa.String(), nullable=False),
            sa.Column('option3', sa.String(), nullable=False),
            sa.Column('option4', sa.String(), nullable=False),
            sa.Column('answer', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # drop legacy tables if they exist
    for tbl in [
        'lesson_qa',
        'test',
        'final_qa',
        'final_test',
        'difficult_level',
        'understand_level_tag',
        'course_info',
    ]:
        _drop_if_exists(inspector, tbl)

    _create_course_tables(inspector)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for tbl in ['quiz_qa', 'quiz', 'assessment', 'lesson', 'course']:
        if inspector.has_table(tbl):
            op.drop_table(tbl)
