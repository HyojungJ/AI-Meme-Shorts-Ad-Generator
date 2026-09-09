import pytest

from meme_collector import MemeAgent


@pytest.fixture
def agent():
    return MemeAgent(enable_tracing=False)


@pytest.mark.slow
def test_performable_no_key_phrase(agent):
    """performable 밈은 key_phrase 없어도 PASS"""
    result = agent.process("랫댄스")

    assert result["meta"]["success"] is True

    output = result.get("meme_output", {})
    meme_type = output.get("meme_type")

    # performable이면 key_phrase 없어도 됨
    if meme_type == "performable":
        # key_phrase가 없거나 빈 문자열이어도 OK
        assert result["verification"]["decision"] in ["PASS", "RETRY"]


@pytest.mark.slow
def test_definition_length(agent):
    """definition 최소 길이 확인 (100자 이상)"""
    result = agent.process("무야호")

    assert result["meta"]["success"] is True

    output = result.get("meme_output", {})
    definition = output.get("definition", "")

    assert len(definition) >= 100, f"definition too short: {len(definition)} chars"


@pytest.mark.slow
def test_definition_no_markdown(agent):
    """definition에 마크다운 없음"""
    result = agent.process("도시락 다 쌌어요")

    assert result["meta"]["success"] is True

    output = result.get("meme_output", {})
    definition = output.get("definition", "")

    assert "**" not in definition, "definition contains bold markdown"
    assert "##" not in definition, "definition contains header markdown"
    assert "- " not in definition or definition.count("- ") < 3, "definition contains bullet points"


@pytest.mark.slow
def test_motion_prompt_english(agent):
    """motion_prompt는 영어로 작성되어야 함"""
    result = agent.process("무야호")

    assert result["meta"]["success"] is True

    output = result.get("meme_output", {})
    prompt = output.get("motion_prompt", "")

    # 한글 포함 비율 10% 미만이어야 함
    korean_chars = len([c for c in prompt if '가' <= c <= '힣'])
    total_chars = max(len(prompt), 1)
    korean_ratio = korean_chars / total_chars

    assert korean_ratio < 0.1, f"motion_prompt has too much Korean: {korean_ratio:.1%}"


@pytest.mark.slow
def test_usage_examples_have_source_url(agent):
    """usage_examples는 모두 source_url이 있어야 함 (LLM 생성 방지)"""
    result = agent.process("내 골반이 멈추지 않는 탓일까? ㅜ.ㅜ")

    assert result["meta"]["success"] is True

    output = result.get("meme_output", {})
    examples = output.get("usage_examples", [])

    # 예시가 있다면 모두 source_url 필수
    for ex in examples:
        assert ex.get("source_url"), f"usage_example missing source_url: {ex.get('context', '')[:30]}"


@pytest.mark.slow
def test_quotable_has_key_phrase(agent):
    """quotable 밈은 key_phrase 필수"""
    result = agent.process("어쩔티비")

    assert result["meta"]["success"] is True

    output = result.get("meme_output", {})
    meme_type = output.get("meme_type")

    if meme_type == "quotable":
        assert output.get("key_phrase"), "quotable meme should have key_phrase"


@pytest.mark.slow
def test_hybrid_has_both(agent):
    """hybrid 밈은 key_phrase와 motion_prompt 둘 다 필요"""
    result = agent.process("무야호")

    assert result["meta"]["success"] is True

    output = result.get("meme_output", {})
    meme_type = output.get("meme_type")

    if meme_type == "hybrid":
        assert output.get("key_phrase"), "hybrid meme should have key_phrase"
        assert len(output.get("motion_prompt", "")) > 50, "hybrid meme should have detailed motion_prompt"
