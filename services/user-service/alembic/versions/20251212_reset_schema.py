"""reset user-service schema to ERD 2025-12-12

Revision ID: reset_user_20251212
Revises: 58052b22a77f
Create Date: 2025-12-12
"""

from alembic import op
import sqlalchemy as sa

revision = 'reset_user_20251212'
down_revision = '58052b22a77f'
branch_labels = None
depends_on = None


def _drop_if_exists(inspector, table_name: str):
    if inspector.has_table(table_name):
        op.drop_table(table_name)


def _create_tables(inspector):
    if not inspector.has_table('user_profile'):
        op.create_table(
            'user_profile',
            sa.Column('profile_id', sa.String(), primary_key=True),
            sa.Column('family_name', sa.String(), nullable=True),
            sa.Column('given_name', sa.String(), nullable=True),
            sa.Column('avatar_id', sa.String(), nullable=True),
            sa.Column('dob', sa.DateTime(timezone=True), nullable=True),
            sa.Column('level', sa.Integer(), nullable=False, server_default=sa.text('1')),
            sa.Column('current_exp', sa.BigInteger(), nullable=False, server_default=sa.text('0')),
            sa.Column('require_exp', sa.BigInteger(), nullable=False, server_default=sa.text('10')),
            sa.Column('remind_time', sa.DateTime(timezone=True), nullable=True),
            sa.Column('sex', sa.Boolean(), nullable=True),
            sa.Column('bio', sa.Text(), nullable=True),
        )

    if not inspector.has_table('user'):
        op.create_table(
            'user',
            sa.Column('user_id', sa.String(), primary_key=True),
            sa.Column('profile_id', sa.String(), sa.ForeignKey('user_profile.profile_id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('email', sa.String(), nullable=False, unique=True, index=True),
            sa.Column('password', sa.String(), nullable=True),
            sa.Column('google_id', sa.String(), nullable=True, unique=True),
            sa.Column('is_email_verified', sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column('email_verification_token', sa.String(), nullable=True),
            sa.Column('email_verification_expires_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('password_reset_token', sa.String(), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        )

    if not inspector.has_table('learning_activity'):
        op.create_table(
            'learning_activity',
            sa.Column('activity_id', sa.String(), primary_key=True),
            sa.Column('user_id', sa.String(), sa.ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False, index=True),
            sa.Column('date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('date_of_the_week', sa.String(), nullable=False),
            sa.Column('count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        )

    if not inspector.has_table('admin'):
        op.create_table(
            'admin',
            sa.Column('admin_id', sa.String(), primary_key=True),
            sa.Column('username', sa.String(), nullable=False, unique=True),
            sa.Column('password', sa.String(), nullable=False),
        )


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # drop legacy tables
    for tbl in ['learning_activity', 'admins', 'users']:
        _drop_if_exists(inspector, tbl)

    _create_tables(inspector)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for tbl in ['learning_activity', 'user', 'user_profile', 'admin']:
        if inspector.has_table(tbl):
            op.drop_table(tbl)
