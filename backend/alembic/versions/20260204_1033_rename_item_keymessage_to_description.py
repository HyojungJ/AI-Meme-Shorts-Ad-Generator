"""rename item_keymessage to item_description

Revision ID: 20260204_1033
Revises: 6e2f2b3d1c9a
Create Date: 2026-02-04 10:33:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260204_1033'
down_revision = '6e2f2b3d1c9a'
branch_labels = None
depends_on = None


def upgrade():
    # item_keymessage 컬럼이 존재하는지 확인 후 이름 변경
    from sqlalchemy import inspect
    from alembic import op
    
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('ad_requests')]
    
    if 'item_keymessage' in columns:
        op.alter_column('ad_requests', 'item_keymessage', new_column_name='item_description')
    elif 'item_description' not in columns:
        # 둘 다 없으면 item_description 컬럼 추가
        import sqlalchemy as sa
        op.add_column('ad_requests', sa.Column('item_description', sa.Text(), nullable=True))


def downgrade():
    # 롤백 시 item_description을 item_keymessage로 되돌림
    op.alter_column('ad_requests', 'item_description', new_column_name='item_keymessage')
