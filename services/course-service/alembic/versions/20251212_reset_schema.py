"""reset schema to ERD 2025-12-12

Revision ID: reset_20251212
Revises: 001
Create Date: 2025-12-12
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'reset_20251212'
down_revision = '001'
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
            sa.Column('is_public', sa.Boolean(), nullable=False, server_default=sa.false()),
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

    if not inspector.has_table('course_progress'):
        op.create_table(
            'course_progress',
            sa.Column('progress_id', sa.String(), primary_key=True),
            sa.Column('course_id', sa.String(), sa.ForeignKey('course.course_id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('user_id', sa.String(), nullable=False, index=True),
            sa.Column('is_completed', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.UniqueConstraint('user_id', 'course_id', name='uq_user_course_progress'),
        )

    if not inspector.has_table('lesson_progress'):
        op.create_table(
            'lesson_progress',
            sa.Column('progress_id', sa.String(), primary_key=True),
            sa.Column('lesson_id', sa.String(), sa.ForeignKey('lesson.lesson_id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('course_id', sa.String(), sa.ForeignKey('course.course_id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('user_id', sa.String(), nullable=False, index=True),
            sa.Column('is_completed', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.UniqueConstraint('user_id', 'lesson_id', name='uq_user_lesson_progress'),
        )


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # add new columns if tables already exist
    if inspector.has_table('course'):
        cols = {c['name'] for c in inspector.get_columns('course')}
        if 'is_public' not in cols:
            op.add_column('course', sa.Column('is_public', sa.Boolean(), nullable=False, server_default=sa.false()))

    # create progress tables if missing
    if not inspector.has_table('course_progress'):
        op.create_table(
            'course_progress',
            sa.Column('progress_id', sa.String(), primary_key=True),
            sa.Column('course_id', sa.String(), sa.ForeignKey('course.course_id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('user_id', sa.String(), nullable=False, index=True),
            sa.Column('is_completed', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.UniqueConstraint('user_id', 'course_id', name='uq_user_course_progress'),
        )
    if not inspector.has_table('lesson_progress'):
        op.create_table(
            'lesson_progress',
            sa.Column('progress_id', sa.String(), primary_key=True),
            sa.Column('lesson_id', sa.String(), sa.ForeignKey('lesson.lesson_id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('course_id', sa.String(), sa.ForeignKey('course.course_id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('user_id', sa.String(), nullable=False, index=True),
            sa.Column('is_completed', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.UniqueConstraint('user_id', 'lesson_id', name='uq_user_lesson_progress'),
        )

    # best-effort remove legacy completion columns from content tables
    if inspector.has_table('course'):
        cols = {c['name'] for c in inspector.get_columns('course')}
        if 'finish' in cols:
            op.drop_column('course', 'finish')
    if inspector.has_table('lesson'):
        cols = {c['name'] for c in inspector.get_columns('lesson')}
        if 'finish' in cols:
            op.drop_column('lesson', 'finish')

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

    # quiz domain belongs to quiz-service; drop legacy quiz tables if present
    if inspector.has_table('quiz_qa'):
        op.drop_table('quiz_qa')
    if inspector.has_table('quiz'):
        op.drop_table('quiz')

    _create_course_tables(inspector)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for tbl in ['lesson_progress', 'course_progress', 'assessment', 'lesson', 'course']:
        if inspector.has_table(tbl):
            op.drop_table(tbl)
