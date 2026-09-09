"""add review_result columns to videos and company_characters

Revision ID: f3a8b9c4d5e6
Revises: e02bb8c83b9d
Create Date: 2026-01-27 12:48:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f3a8b9c4d5e6'
down_revision = 'e02bb8c83b9d'
branch_labels = None
depends_on = None


def upgrade():
    # Add review_result column to videos table
    op.add_column('videos', sa.Column('review_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Add review_result column to company_characters table
    op.add_column('company_characters', sa.Column('review_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade():
    # Remove review_result column from company_characters table
    op.drop_column('company_characters', 'review_result')
    
    # Remove review_result column from videos table
    op.drop_column('videos', 'review_result')
