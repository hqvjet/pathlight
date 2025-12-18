"""Initial auth tables with password reset expiry

Revision ID: 002
Revises: 
Create Date: 2025-12-18
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
	op.create_table(
		'users',
		sa.Column('id', sa.String(), primary_key=True),
		sa.Column('email', sa.String(), nullable=False, unique=True, index=True),
		sa.Column('password', sa.String(), nullable=True),
		sa.Column('is_email_verified', sa.Boolean(), nullable=False, server_default=sa.false()),
		sa.Column('email_verification_token', sa.String(), nullable=True),
		sa.Column('email_verification_expires_at', sa.DateTime(timezone=True), nullable=True),
		sa.Column('password_reset_token', sa.String(), nullable=True),
		sa.Column('google_id', sa.String(), nullable=True, unique=True),
		sa.Column('given_name', sa.String(), nullable=True),
		sa.Column('family_name', sa.String(), nullable=True),
		sa.Column('avatar_url', sa.String(), nullable=True),
		sa.Column('dob', sa.DateTime(timezone=True), nullable=True),
		sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
		sa.Column('current_exp', sa.BigInteger(), nullable=False, server_default='0'),
		sa.Column('require_exp', sa.BigInteger(), nullable=False, server_default='10'),
		sa.Column('remind_time', sa.String(), nullable=True),
		sa.Column('sex', sa.Boolean(), nullable=True),
		sa.Column('bio', sa.Text(), nullable=True),
		sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
		sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
		sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
		sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
	)

	op.create_table(
		'admins',
		sa.Column('id', sa.String(), primary_key=True),
		sa.Column('username', sa.String(), unique=True, nullable=False),
		sa.Column('password', sa.String(), nullable=False),
		sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
		sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
	)

	op.create_table(
		'token_blacklist',
		sa.Column('id', sa.String(), primary_key=True),
		sa.Column('token', sa.String(), nullable=False, unique=True, index=True),
		sa.Column('blacklisted_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
		sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
	)


def downgrade():
	op.drop_table('token_blacklist')
	op.drop_table('admins')
	op.drop_table('users')
