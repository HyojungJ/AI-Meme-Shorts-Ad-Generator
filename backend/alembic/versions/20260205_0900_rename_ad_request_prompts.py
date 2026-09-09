"""rename ad_request prompt columns

Revision ID: 20260205_0900
Revises: 20260204_1033
Create Date: 2026-02-05 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260205_0900'
down_revision = '20260204_1033'
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import inspect

    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('ad_requests')]

    if 'character_style_raw' in columns and 'character_image_prompt' not in columns:
        op.alter_column('ad_requests', 'character_style_raw', new_column_name='character_image_prompt')
    elif 'character_image_prompt' not in columns:
        op.add_column('ad_requests', sa.Column('character_image_prompt', sa.Text(), nullable=True))

    if 'notes' in columns and 'character_voice_prompt' not in columns:
        op.alter_column('ad_requests', 'notes', new_column_name='character_voice_prompt')
    elif 'character_voice_prompt' not in columns:
        op.add_column('ad_requests', sa.Column('character_voice_prompt', sa.Text(), nullable=True))


def downgrade():
    from sqlalchemy import inspect

    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('ad_requests')]

    if 'character_image_prompt' in columns and 'character_style_raw' not in columns:
        op.alter_column('ad_requests', 'character_image_prompt', new_column_name='character_style_raw')
    elif 'character_style_raw' not in columns:
        op.add_column('ad_requests', sa.Column('character_style_raw', sa.Text(), nullable=True))

    if 'character_voice_prompt' in columns and 'notes' not in columns:
        op.alter_column('ad_requests', 'character_voice_prompt', new_column_name='notes')
    elif 'notes' not in columns:
        op.add_column('ad_requests', sa.Column('notes', sa.Text(), nullable=True))
