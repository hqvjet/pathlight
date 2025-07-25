"""Create quiz tables

Revision ID: 001
Revises: 
Create Date: 2025-06-19 14:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    
    # Create quiz_info table first
    op.create_table('quiz_info',
    sa.Column('quiz_info_id', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('duration', sa.Integer(), nullable=True),
    sa.Column('play_time', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('quiz_info_id')
    )
    
    # Create quiz table
    op.create_table('quiz',
    sa.Column('quiz_id', sa.String(), nullable=False),
    sa.Column('quiz_info_id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('finish', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['quiz_info_id'], ['quiz_info.quiz_info_id'], ),
    sa.PrimaryKeyConstraint('quiz_id')
    )
    
    # Create quiz_qa table
    op.create_table('quiz_qa',
    sa.Column('qa_id', sa.String(), nullable=False),
    sa.Column('quiz_id', sa.String(), nullable=False),
    sa.Column('question', sa.Text(), nullable=True),
    sa.Column('explain', sa.Text(), nullable=True),
    sa.Column('option1', sa.String(), nullable=True),
    sa.Column('option2', sa.String(), nullable=True),
    sa.Column('option3', sa.String(), nullable=True),
    sa.Column('option4', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['quiz_id'], ['quiz.quiz_id'], ),
    sa.PrimaryKeyConstraint('qa_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('quiz_qa')
    op.drop_table('quiz')
    op.drop_table('quiz_info')
    # ### end Alembic commands ###
