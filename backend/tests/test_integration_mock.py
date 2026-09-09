"""
Mock 모드 통합 테스트

AI_PIPELINE_MOCK_MODE=true 상태에서 엔드포인트 동작 검증.
DB는 mock 처리하여 GPU/DB 없이 실행 가능.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from fastapi.testclient import TestClient


@pytest.fixture
def mock_video():
    """Mock Video ORM 객체"""
    video = MagicMock()
    video.video_id = 1
    video.ad_id = 1
    video.company_id = 1
    video.s3_url = "s3://bucket/video.mp4"
    video.status = "completed"
    video.review_result = None
    video.updated_at = datetime.utcnow()
    video.duration_seconds = 30
    video.thumbnail_url = "https://example.com/thumb.jpg"
    video.file_size_bytes = 1024000
    return video


@pytest.fixture
def mock_ad_request():
    """Mock AdRequest ORM 객체"""
    ad = MagicMock()
    ad.ad_id = 1
    ad.company_id = 1
    ad.character_id = 1
    ad.meme_id = 1
    ad.status = "pending_approval"
    ad.item_name = "Test Product"
    ad.item_category = "test"
    ad.item_description = "test highlight"
    return ad


@pytest.fixture
def mock_character():
    """Mock CompanyCharacter ORM 객체"""
    char = MagicMock()
    char.character_id = 1
    char.company_id = 1
    char.image_url = "https://example.com/char.png"
    char.image_prompt = "young male character"
    char.is_active = True
    char.elevenlabs_voice_id = "voice_123"
    char.voice_sample_url = "https://example.com/voice.mp3"
    char.voice_design_prompt = "cheerful male voice"
    char.created_at = datetime.utcnow()
    char.updated_at = datetime.utcnow()
    return char


@pytest.fixture
def mock_scenario():
    """Mock ScenarioScript ORM 객체"""
    scenario = MagicMock()
    scenario.script_id = 1
    scenario.ad_id = 1
    scenario.title = "테스트 시나리오"
    scenario.description = "테스트용"
    scenario.approval_status = "pending"
    scenario.scenes = [
        {"scene_number": 1, "content": "훅 씬", "timestamp": "0:00"},
        {"scene_number": 2, "content": "바디 씬 1", "timestamp": "0:05"},
        {"scene_number": 3, "content": "바디 씬 2", "timestamp": "0:10"},
        {"scene_number": 4, "content": "클로즈 씬", "timestamp": "0:15"},
    ]
    return scenario


@pytest.fixture
def client(mock_db):
    """FastAPI TestClient (DB mock 주입)"""
    from app.db.session import get_db
    from app.main import app

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# === final.py 엔드포인트 테스트 ===


class TestFinalReviseVideo:
    """POST /{video_id}/revise 엔드포인트 테스트"""

    @patch("app.api.v1.endpoints.final.final_crud")
    def test_revise_video_success(
        self, mock_crud, client, auth_headers, mock_video
    ):
        mock_crud.get_video_for_approval.return_value = mock_video

        response = client.post(
            "/api/v1/videos/1/revise",
            json={
                "revision_notes": "씬 2 영상 수정 필요",
                "feedback": "더 역동적으로",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == 1
        assert data["status"] == "processing"

    @patch("app.api.v1.endpoints.final.final_crud")
    def test_revise_video_not_found(self, mock_crud, client, auth_headers):
        mock_crud.get_video_for_approval.return_value = None

        response = client.post(
            "/api/v1/videos/1/revise",
            json={"revision_notes": "수정", "feedback": ""},
            headers=auth_headers,
        )

        assert response.status_code == 404

    @patch("app.api.v1.endpoints.final.final_crud")
    def test_revise_video_forbidden(
        self, mock_crud, client, auth_headers, mock_video
    ):
        mock_video.company_id = 999  # 다른 회사
        mock_crud.get_video_for_approval.return_value = mock_video

        response = client.post(
            "/api/v1/videos/1/revise",
            json={"revision_notes": "수정"},
            headers=auth_headers,
        )

        assert response.status_code == 403


# === content_pipeline 엔드포인트 테스트 ===


class TestCharacterRevise:
    """POST /{ad_id}/character/revise 엔드포인트 테스트"""

    @patch("app.api.v1.endpoints.content_pipeline.helpers.video_crud")
    def test_revise_character_with_notes(
        self, mock_crud, client, auth_headers, mock_ad_request, mock_character
    ):
        mock_crud.get_ad_request_by_id.return_value = mock_ad_request
        mock_crud.get_character_by_id.return_value = mock_character

        response = client.post(
            "/api/v1/video/1/character/revise",
            json={
                "revision_notes": "더 밝은 표정으로",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["character_id"] == 1
        assert data["status"] == "regenerated"
        assert data["image_url"] is not None

    @patch("app.api.v1.endpoints.content_pipeline.helpers.video_crud")
    def test_revise_character_with_new_prompt(
        self, mock_crud, client, auth_headers, mock_ad_request, mock_character
    ):
        mock_crud.get_ad_request_by_id.return_value = mock_ad_request
        mock_crud.get_character_by_id.return_value = mock_character

        response = client.post(
            "/api/v1/video/1/character/revise",
            json={
                "revision_notes": "완전히 다른 스타일로",
                "character_prompt": "cute anime girl with pink hair",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "regenerated"

    @patch("app.api.v1.endpoints.content_pipeline.helpers.video_crud")
    def test_revise_character_no_character(
        self, mock_crud, client, auth_headers, mock_ad_request
    ):
        mock_ad_request.character_id = None
        mock_crud.get_ad_request_by_id.return_value = mock_ad_request

        response = client.post(
            "/api/v1/video/1/character/revise",
            json={"revision_notes": "수정"},
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestVideoRevise:
    """POST /{ad_id}/video/revise 엔드포인트 테스트"""

    @patch("app.api.v1.endpoints.content_pipeline.helpers.video_crud")
    def test_revise_video_scenes(
        self, mock_crud, client, auth_headers, mock_ad_request, mock_video
    ):
        mock_crud.get_ad_request_by_id.return_value = mock_ad_request
        mock_crud.get_video_by_ad.return_value = mock_video

        response = client.post(
            "/api/v1/video/1/video/revise",
            json={
                "scene_revisions": [
                    {"scene_number": 1, "video_notes": "더 빠르게"},
                    {"scene_number": 3, "video_notes": "카메라 앵글 변경"},
                ]
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert data["video_id"] == mock_video.video_id

    @patch("app.api.v1.endpoints.content_pipeline.helpers.video_crud")
    def test_revise_video_no_video(
        self, mock_crud, client, auth_headers, mock_ad_request
    ):
        mock_crud.get_ad_request_by_id.return_value = mock_ad_request
        mock_crud.get_video_by_ad.return_value = None

        response = client.post(
            "/api/v1/video/1/video/revise",
            json={
                "scene_revisions": [
                    {"scene_number": 1, "video_notes": "수정"},
                ]
            },
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestScenarioRevise:
    """POST /{ad_id}/scenario/revise 엔드포인트 테스트"""

    @patch("app.api.v1.endpoints.content_pipeline.helpers.video_crud")
    def test_revise_scenario_success(
        self, mock_crud, client, auth_headers, mock_ad_request, mock_scenario
    ):
        mock_crud.get_ad_request_by_id.return_value = mock_ad_request
        mock_crud.get_scenario_by_ad.return_value = mock_scenario

        response = client.post(
            "/api/v1/video/1/scenario/revise",
            json={
                "scene_revisions": [
                    {"scene_number": 1, "scenario_notes": "훅을 더 임팩트있게"},
                    {"scene_number": 3, "scenario_notes": "대사 수정"},
                ],
                "general_notes": "전체적으로 톤 밝게",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "revised"
        assert data["script_id"] == mock_scenario.script_id
        assert "scenes" in data
        assert len(data["scenes"]) > 0

        # DB에 피드백 저장 호출 확인
        mock_crud.update_scenario_scenes.assert_called()
        first_call_args = mock_crud.update_scenario_scenes.call_args_list[0]
        review_result = first_call_args[0][3] if len(first_call_args[0]) > 3 else first_call_args[1].get("revision_notes")
        if isinstance(review_result, dict):
            assert review_result["feedback_type"] == "human_feedback"
            assert "hook" in review_result["scene_feedback"]
            assert review_result["overall_comment"] == "전체적으로 톤 밝게"

    @patch("app.api.v1.endpoints.content_pipeline.helpers.video_crud")
    def test_revise_scenario_no_scenario(
        self, mock_crud, client, auth_headers, mock_ad_request
    ):
        mock_crud.get_ad_request_by_id.return_value = mock_ad_request
        mock_crud.get_scenario_by_ad.return_value = None

        response = client.post(
            "/api/v1/video/1/scenario/revise",
            json={
                "scene_revisions": [
                    {"scene_number": 1, "scenario_notes": "수정"},
                ],
            },
            headers=auth_headers,
        )

        assert response.status_code == 404

    @patch("app.api.v1.endpoints.content_pipeline.helpers.video_crud")
    def test_revise_scenario_scene_key_mapping(
        self, mock_crud, client, auth_headers, mock_ad_request, mock_scenario
    ):
        """scene_number → scene_key 변환 검증 (1=hook, 2=body_1, 3=body_2, 4=close)"""
        mock_crud.get_ad_request_by_id.return_value = mock_ad_request
        mock_crud.get_scenario_by_ad.return_value = mock_scenario

        response = client.post(
            "/api/v1/video/1/scenario/revise",
            json={
                "scene_revisions": [
                    {"scene_number": 1, "scenario_notes": "훅 수정"},
                    {"scene_number": 2, "scenario_notes": "바디1 수정"},
                    {"scene_number": 4, "scenario_notes": "클로즈 수정"},
                ],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200

        # update_scenario_scenes 첫 번째 호출 (피드백 저장)의 review_result 확인
        first_call = mock_crud.update_scenario_scenes.call_args_list[0]
        review_result = first_call[0][3]
        assert review_result["scene_feedback"]["hook"] == "훅 수정"
        assert review_result["scene_feedback"]["body_1"] == "바디1 수정"
        assert review_result["scene_feedback"]["close"] == "클로즈 수정"
        assert "body_2" not in review_result["scene_feedback"]

    @patch("app.api.v1.endpoints.content_pipeline.helpers.video_crud")
    def test_revise_scenario_without_general_notes(
        self, mock_crud, client, auth_headers, mock_ad_request, mock_scenario
    ):
        mock_crud.get_ad_request_by_id.return_value = mock_ad_request
        mock_crud.get_scenario_by_ad.return_value = mock_scenario

        response = client.post(
            "/api/v1/video/1/scenario/revise",
            json={
                "scene_revisions": [
                    {"scene_number": 2, "scenario_notes": "수정"},
                ],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200

        first_call = mock_crud.update_scenario_scenes.call_args_list[0]
        review_result = first_call[0][3]
        assert review_result["overall_comment"] == ""


# === Mock 클라이언트 응답 필드 검증 ===


class TestMockClientResponses:
    """Mock 클라이언트가 필요한 필드를 반환하는지 검증"""

    @pytest.mark.asyncio
    async def test_regenerate_character_image_fields(self):
        from app.services.ai_pipeline_mock import AIPipelineMockClient

        client = AIPipelineMockClient()
        result = await client.regenerate_character_image(
            character_id=1,
            original_image_url="https://example.com/char.png",
            revision_notes="더 밝은 표정",
            character_prompt="young male",
            company_id=1,
        )

        assert "image_url" in result
        assert "verification_score" in result
        assert "verification_decision" in result
        assert "retry_count" in result
        assert isinstance(result["verification_score"], (int, float))

    @pytest.mark.asyncio
    async def test_revise_video_fields(self):
        from app.services.ai_pipeline_mock import AIPipelineMockClient

        client = AIPipelineMockClient()
        result = await client.revise_video(
            video_id=1,
            scene_revisions=[
                {"scene_number": 1, "video_notes": "수정"},
            ],
            company_id=1,
        )

        assert "video_id" in result
        assert "status" in result
        assert "estimated_duration" in result

    @pytest.mark.asyncio
    async def test_revise_scenario_fields(self):
        from app.services.ai_pipeline_mock import AIPipelineMockClient

        client = AIPipelineMockClient()
        result = await client.revise_scenario(
            script_id=1,
            scene_revisions=[
                {"scene_number": 1, "scenario_notes": "훅 수정"},
                {"scene_number": 3, "scenario_notes": "바디2 수정"},
            ],
            company_id=1,
            ad_id=1,
        )

        assert "script_id" in result
        assert "scenes" in result
        assert "status" in result
        assert result["script_id"] == 1
        assert result["status"] == "revised"
        assert len(result["scenes"]) == 2

    @pytest.mark.asyncio
    async def test_revise_scenario_without_ad_id(self):
        from app.services.ai_pipeline_mock import AIPipelineMockClient

        client = AIPipelineMockClient()
        result = await client.revise_scenario(
            script_id=5,
            scene_revisions=[{"scene_number": 2, "scenario_notes": "수정"}],
            company_id=1,
        )

        assert result["script_id"] == 5
        assert result["status"] == "revised"

    @pytest.mark.asyncio
    async def test_regenerate_video_fields(self):
        from app.services.ai_pipeline_mock import AIPipelineMockClient

        client = AIPipelineMockClient()
        result = await client.regenerate_video(
            video_id=1,
            ad_id=1,
            revision_notes="수정 요청",
            feedback="피드백",
            company_id=1,
        )

        assert "video_id" in result
        assert "status" in result
