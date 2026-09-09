import pytest

from meme_collector import MemeAgent

GOLDEN_MEMES = [
    {"name": "무야호", "type": "quotable", "has_key_phrase": True},
    {"name": "내가 그걸 모를까", "type": "quotable", "has_key_phrase": True},
    {"name": "랫댄스", "type": "performable", "has_key_phrase": False},
]


@pytest.fixture
def agent():
    return MemeAgent(enable_tracing=False)


@pytest.mark.slow
@pytest.mark.parametrize("meme", GOLDEN_MEMES, ids=lambda m: m["name"])
def test_golden_meme(agent, meme):
    result = agent.process(meme["name"])
    output = result.get("meme_output", {})

    assert result["meta"]["success"] is True

    # Definition 마크다운 없음
    definition = output.get("definition", "")
    assert "**" not in definition, "definition should not contain bold markdown"
    assert "##" not in definition, "definition should not contain header markdown"

    # meme_type별 검증
    if meme["has_key_phrase"]:
        assert output.get("key_phrase"), f"{meme['name']} should have key_phrase"

    # 기본 검증
    assert output["name"] == meme["name"]
    assert output["meme_type"] in ["quotable", "performable", "hybrid"]
    assert len(output.get("motion_prompt", "")) > 20


@pytest.mark.slow
def test_verification_decision(agent):
    result = agent.process("무야호")
    assert result["verification"]["decision"] in ["PASS", "RETRY", "FAIL"]


@pytest.mark.slow
def test_processing_time(agent):
    result = agent.process("테스트")
    assert result["meta"]["processing_time_seconds"] < 120
