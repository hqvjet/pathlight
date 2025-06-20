"""Initial migration

Revision ID: 58052b22a77f
Revises: 
Create Date: 2025-06-19 10:31:30.903853

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '58052b22a77f'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create user_profile table first (referenced by user table)
    op.create_table('user_profile',
        sa.Column('profile_id', sa.String(), nullable=False),
        sa.Column('family_name', sa.String(), nullable=False),
        sa.Column('given_name', sa.String(), nullable=True),
        sa.Column('avatar_id', sa.String(), nullable=False),
        sa.Column('dob', sa.DateTime(), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False, default=1),
        sa.Column('current_exp', sa.BigInteger(), nullable=False, default=0),
        sa.Column('require_exp', sa.BigInteger(), nullable=False, default=10),
        sa.Column('remind_time', sa.DateTime(), nullable=False),
        sa.Column('sex', sa.Boolean(), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('profile_id')
    )
    
    # Create user table
    op.create_table('app_user',
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('profile_id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('password', sa.String(), nullable=True),
        sa.Column('google_id', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('user_id'),
        sa.ForeignKeyConstraint(['profile_id'], ['user_profile.profile_id']),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('google_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('app_user')
    op.drop_table('user_profile')
