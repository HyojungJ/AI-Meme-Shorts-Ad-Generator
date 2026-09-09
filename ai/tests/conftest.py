import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from unittest.mock import MagicMock, patch

from meme_collector.state import get_initial_state

# .env 파일 로드 (테스트 시작 전)
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


@pytest.fixture
def sample_state():
    return get_initial_state("테스트밈")


@pytest.fixture
def mock_openai():
    with patch("common.get_openai") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def sample_analysis():
    return {
        "meme_type": "quotable",
        "key_phrase": "테스트 문구",
        "definition": "테스트 정의입니다.",
        "emotion": "excited",
        "motion_prompt": "A person jumps with excitement...",
        "origin": {"source": "테스트", "creator": ""},
        "risk_level": "low",
    }
