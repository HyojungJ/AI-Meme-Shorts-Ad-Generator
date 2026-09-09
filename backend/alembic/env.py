from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Alembic Config 객체
config = context.config

# Python logging 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 모든 모델 import
from app.db.base import Base
from app.models import (
    Account, Client, Admin,
    Company, CompanyMember, CompanyCharacter,
    Meme, MemeExample,
    AdRequest,
    ScenarioScript,
    SceneAsset, VoiceGeneration, ImageGeneration, SceneVideo,
    Video,
    WorkflowExecution, WorkflowStage,
    AdminYoutubeChannel, AdminVideoPost,
    PerformanceMetric, PromptVersion, PromptUsageLog, RetryQueue
)

# MetaData 설정
target_metadata = Base.metadata

# .env 파일에서 DATABASE_URL 읽기
from dotenv import load_dotenv
load_dotenv()

database_url = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
