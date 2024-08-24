"""add title_image column to articles

Revision ID: 4ebff5744c16
Revises: 
Create Date: 2024-08-24 11:24:04.802558

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ebff5744c16'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the title_image column to the articles table
    op.add_column('articles', sa.Column('title_image', sa.String(length=255), nullable=False))
    

def downgrade() -> None:
    # Remove the title_image column from the articles table
    op.drop_column('articles', 'title_image')
