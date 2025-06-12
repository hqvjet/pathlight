from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user_profile',
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('first_name', sa.String()),
        sa.Column('last_name', sa.String()),
        sa.Column('dob', sa.Date(), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('current_exp', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sex', sa.Boolean(), nullable=False),
        sa.Column('bio', sa.String()),
    )
    op.create_table(
        'user',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_profile.profile_id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('password', sa.String(), nullable=False),
    )
    op.create_index('idx_user_profile_id', 'user', ['profile_id'])
    op.create_table(
        'admin',
        sa.Column('admin_id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('username', sa.String(), nullable=False, unique=True),
        sa.Column('password', sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('admin')
    op.drop_index('idx_user_profile_id', table_name='user')
    op.drop_table('user')
    op.drop_table('user_profile')
