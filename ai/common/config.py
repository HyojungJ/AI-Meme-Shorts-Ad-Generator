import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class DBConfig:
    host: str
    port: int
    name: str
    user: str
    password: str


@dataclass(frozen=True)
class ModelConfig:
    analyzer: str = "gpt-4o"
    default: str = "gpt-4o-mini"
    vision: str = "gemini-2.0-flash"
    fast: str = "gpt-4o-mini"


@dataclass(frozen=True)
class AgentConfig:
    max_turns: int = 3
    max_attempts: int = 2
    min_examples: int = 3


@dataclass(frozen=True)
class ApiConfig:
    timeout: int = 15


@dataclass(frozen=True)
class Config:
    db: DBConfig
    models: ModelConfig
    agent: AgentConfig
    api: ApiConfig
    openai_api_key: str
    gemini_api_key: str
    naver_client_id: str
    naver_client_secret: str
    youtube_api_key: str


def _load_config() -> Config:
    return Config(
        db=DBConfig(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
            name=os.getenv("DB_NAME", "memedb"),
            user=os.getenv("DB_USER", ""),
            password=os.getenv("DB_PASSWORD", ""),
        ),
        models=ModelConfig(),
        agent=AgentConfig(),
        api=ApiConfig(),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        naver_client_id=os.getenv("NAVER_CLIENT_ID", ""),
        naver_client_secret=os.getenv("NAVER_CLIENT_SECRET", ""),
        youtube_api_key=os.getenv("YOUTUBE_API_KEY", ""),
    )


config = _load_config()
