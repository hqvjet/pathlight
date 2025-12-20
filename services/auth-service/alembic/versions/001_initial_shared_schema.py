"""Initial shared auth schema (users/admins/user_profile/token_blacklist)

Revision ID: 001_initial_shared
Revises: 
Create Date: 2025-12-20
"""

from alembic import op
import sqlalchemy as sa

revision = "001_initial_shared"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # user_profile table (profile and gamification fields)
    op.create_table(
        "user_profile",
        sa.Column("profile_id", sa.String(), primary_key=True),
        sa.Column("subscription", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("family_name", sa.String(), nullable=True),
        sa.Column("given_name", sa.String(), nullable=True),
        sa.Column("avatar_id", sa.String(), nullable=True),
        sa.Column("dob", sa.DateTime(timezone=True), nullable=True),
        sa.Column("streak", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("level", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("current_exp", sa.BigInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("require_exp", sa.BigInteger(), nullable=False, server_default=sa.text("10")),
        sa.Column("remind_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sex", sa.Boolean(), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
    )

    # users table (auth core)
    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("profile_id", sa.String(), sa.ForeignKey("user_profile.profile_id", ondelete="SET NULL"), nullable=True),
        sa.Column("email", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("password", sa.String(), nullable=True),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("email_verification_token", sa.String(), nullable=True),
        sa.Column("email_verification_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("password_reset_token", sa.String(), nullable=True),
        sa.Column("google_id", sa.String(), nullable=True, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
    )

    # admins table
    op.create_table(
        "admins",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("username", sa.String(), unique=True, nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # token blacklist
    op.create_table(
        "token_blacklist",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("token", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("blacklisted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table("token_blacklist")
    op.drop_table("admins")
    op.drop_table("users")
    op.drop_table("user_profile")
