"""remove_unused_columns

Revision ID: f3a8b9c2d1e4
Revises: f3a8b9c4d5e6
Create Date: 2026-01-27 17:43:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3a8b9c2d1e4'
down_revision = 'f3a8b9c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    불필요한 컬럼 삭제:
    - ad_requests.voice_description
    - company_characters.character_name
    - company_characters.character_mood
    - company_characters.character_style
    - company_characters.voice_tone
    """
    # ad_requests 테이블에서 voice_description 컬럼 삭제
    op.drop_column('ad_requests', 'voice_description')
    
    # company_characters 테이블에서 컬럼들 삭제
    op.drop_column('company_characters', 'character_name')
    op.drop_column('company_characters', 'character_mood')
    op.drop_column('company_characters', 'character_style')
    op.drop_column('company_characters', 'voice_tone')


def downgrade() -> None:
    """
    삭제한 컬럼 복구
    """
    # company_characters 테이블 컬럼 복구
    op.add_column('company_characters', 
        sa.Column('voice_tone', sa.VARCHAR(length=255), nullable=False, server_default='neutral')
    )
    op.add_column('company_characters', 
        sa.Column('character_style', sa.VARCHAR(length=255), nullable=False, server_default='default')
    )
    op.add_column('company_characters', 
        sa.Column('character_mood', sa.VARCHAR(length=255), nullable=False, server_default='neutral')
    )
    op.add_column('company_characters', 
        sa.Column('character_name', sa.VARCHAR(length=255), nullable=False, server_default='Character')
    )
    
    # ad_requests 테이블 컬럼 복구
    op.add_column('ad_requests', 
        sa.Column('voice_description', sa.TEXT(), nullable=True)
    )
    
    # server_default 제거 (복구 후 기본값 제거)
    op.alter_column('company_characters', 'voice_tone', server_default=None)
    op.alter_column('company_characters', 'character_style', server_default=None)
    op.alter_column('company_characters', 'character_mood', server_default=None)
    op.alter_column('company_characters', 'character_name', server_default=None)
