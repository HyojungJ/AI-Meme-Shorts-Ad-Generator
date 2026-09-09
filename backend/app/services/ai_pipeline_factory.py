"""
AI 파이프라인 클라이언트 Factory

settings.AI_PIPELINE_MOCK_MODE / AI_PIPELINE_DIRECT_MODE 에 따라
올바른 클라이언트를 반환한다.
"""
from app.core.config import settings
from app.services.ai_pipeline_base import AIPipelineBase


def get_ai_client() -> AIPipelineBase:
    """설정에 따라 적절한 AI Pipeline 클라이언트를 반환."""
    if settings.AI_PIPELINE_MOCK_MODE:
        from app.services.ai_pipeline_mock import AIPipelineMockClient
        return AIPipelineMockClient()
    elif settings.AI_PIPELINE_DIRECT_MODE:
        from app.services.ai_pipeline_direct import AIPipelineDirectClient
        return AIPipelineDirectClient()
    else:
        from app.services.ai_pipeline_client import AIPipelineClient
        return AIPipelineClient()


# 모듈 레벨에서 올바른 클래스를 AIPipelineClient 이름으로 alias.
# 기존 코드가 `from ... import AIPipelineClient` 후 `AIPipelineClient()` 로
# 인스턴스를 생성하므로, 해당 패턴과 호환되도록 한다.
if settings.AI_PIPELINE_MOCK_MODE:
    from app.services.ai_pipeline_mock import AIPipelineMockClient as AIPipelineClient
elif settings.AI_PIPELINE_DIRECT_MODE:
    from app.services.ai_pipeline_direct import AIPipelineDirectClient as AIPipelineClient
else:
    from app.services.ai_pipeline_client import AIPipelineClient  # noqa: F811
