"""Initial empty migration placeholder

Revision ID: 0001_create_tables
Revises: 
Create Date: 2026-08-24
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_create_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # For SQLModel autogenerate use: alembic revision --autogenerate
    pass


def downgrade():
    pass
