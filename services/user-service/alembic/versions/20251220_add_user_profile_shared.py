"""Initial user-service schema (shared users/admins, adds user_profile + learning_activity)

Revision ID: user_service_initial_shared
Revises: 
Create Date: 2025-12-20
"""

from alembic import op
import sqlalchemy as sa

revision = "user_service_initial_shared"
down_revision = None
branch_labels = None
depends_on = None


def _drop_if_exists(inspector, table_name: str):
    if inspector.has_table(table_name):
        op.drop_table(table_name)


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Fresh init: drop legacy tables if present (idempotent for clean DB)
    for tbl in ["user", "user_profile", "app_user", "admin", "learning_activity"]:
        _drop_if_exists(inspector, tbl)

    # Create user_profile table
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

    # learning_activity FK to users.id
    op.create_table(
        "learning_activity",
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False, index=True),
        sa.Column("date", sa.DateTime(timezone=True), primary_key=True, nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("learning_activity"):
        op.drop_table("learning_activity")
    # Keep user_profile to avoid data loss; no action on downgrade
