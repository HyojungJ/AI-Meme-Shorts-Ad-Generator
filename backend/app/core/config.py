"""
환경 변수 및 전역 설정 (Pydantic Settings)
"""
import logging
from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 데이터베이스
    DATABASE_URL: str = ""
    DB_URL: str = ""

    # JWT
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = Field(
        default="HS256",
        validation_alias=AliasChoices("JWT_ALGORITHM", "ALGORITHM"),
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Google OAuth (유튜브 영상 자동 게시용)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # AWS S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-northeast-2"
    S3_BUCKET_NAME: str = ""

    # OpenAI
    OPENAI_API_KEY: str = ""

    # Pinecone
    PINECONE_API_KEY: str = ""

    # LangSmith
    LANGSMITH_TRACING: bool = False
    LANGSMITH_ENDPOINT: str = ""
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = ""

    # HuggingFace
    HUGGINGFACEHUB_API_TOKEN: str = ""

    # Tavily
    TAVILY_API_KEY: str = ""

    # 애플리케이션
    APP_NAME: str = "Meme Influencer API"
    APP_VERSION: str = "4.0.0"
    DEBUG: bool = False
    MOCK_MODE: bool = False
    AI_PIPELINE_MOCK_MODE: bool = False
    AI_PIPELINE_DIRECT_MODE: bool = False

    # AI 파이프라인
    AI_PIPELINE_URL: str = "http://localhost:8001"

    # 파인튜닝 모델 (RunPod Serverless)
    USE_FINETUNED_SCENARIO: bool = False
    RUNPOD_ENDPOINT_ID: str = ""
    RUNPOD_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS origins를 리스트로 반환"""
        if isinstance(self.CORS_ORIGINS, str):
            return [s.strip() for s in self.CORS_ORIGINS.split(",") if s.strip()]
        return []

    @model_validator(mode="after")
    def _post_init(self):
        # DATABASE_URL fallback to DB_URL
        if not self.DATABASE_URL and self.DB_URL:
            self.DATABASE_URL = self.DB_URL

        # Mock mode 프로덕션 가드
        if self.MOCK_MODE and not self.DEBUG:
            logger.warning(
                "MOCK_MODE is enabled without DEBUG=true. "
                "This allows authentication bypass. "
                "Set DEBUG=true or disable MOCK_MODE in production."
            )
        return self


settings = Settings()
