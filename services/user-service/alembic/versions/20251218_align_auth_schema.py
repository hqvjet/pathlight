"""Align user-service schema to auth-service tables

Revision ID: align_auth_schema_20251218
Revises: reset_user_20251212
Create Date: 2025-12-18
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "align_auth_schema_20251218"
down_revision = "reset_user_20251212"
branch_labels = None
depends_on = None


def _drop_if_exists(inspector, table_name: str):
    if inspector.has_table(table_name):
        op.drop_table(table_name)


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Remove legacy tables we no longer use
    for tbl in ["learning_activity", "user", "user_profile", "app_user", "admin"]:
        _drop_if_exists(inspector, tbl)

    # Ensure admins table matches auth-service
    if not inspector.has_table("admins"):
        op.create_table(
            "admins",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("username", sa.String(), nullable=False, unique=True),
            sa.Column("password", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        )

    # learning_activity now references users.id
    if not inspector.has_table("learning_activity"):
        op.create_table(
            "learning_activity",
            sa.Column("user_id", sa.String(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False, index=True),
            sa.Column("date", sa.DateTime(timezone=True), primary_key=True, nullable=False),
            sa.Column("count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        )
    else:
        # If it exists, rebuild FK to users
        fk = next((f for f in inspector.get_foreign_keys("learning_activity") if f.get("constrained_columns") == ["user_id"]), None)
        if fk:
            op.drop_constraint(fk.get("name"), "learning_activity", type_="foreignkey")
        op.create_foreign_key(None, "learning_activity", "users", ["user_id"], ["id"], ondelete="CASCADE")


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for tbl in ["learning_activity", "admins"]:
        if inspector.has_table(tbl):
            op.drop_table(tbl)
    # Legacy tables are not recreated in downgrade to avoid data loss/confusion.
