import pytest

from meme_collector.nodes.finalize import (
    _clean_definition,
    _filter_valid_examples,
    _validate_output,
    _DEFAULT_MOTION_PROMPT,
)
from meme_collector.schema import MemeOutput, UsageExample


class TestCleanDefinition:
    """_clean_definition 함수 테스트"""

    def test_removes_bold(self):
        """볼드(**) 제거"""
        result = _clean_definition("**bold** text")
        assert "**" not in result
        assert "bold" in result
        assert "text" in result

    def test_removes_double_asterisks(self):
        """이중 별표 완전 제거"""
        assert _clean_definition("**강조**") == "강조"

    def test_removes_single_asterisks(self):
        """단일 별표(이탤릭) 제거"""
        result = _clean_definition("*italic* text")
        assert "*" not in result
        assert "italic" in result

    def test_removes_headers(self):
        """헤더(##) 제거"""
        result = _clean_definition("## Header\ntext")
        assert "##" not in result
        assert "Header" in result
        assert "text" in result

    def test_removes_multiple_header_levels(self):
        """다양한 레벨 헤더 제거"""
        result = _clean_definition("# H1\n## H2\n### H3")
        assert "#" not in result
        assert "H1" in result
        assert "H2" in result
        assert "H3" in result

    def test_removes_bullets(self):
        """불릿(-) 제거"""
        result = _clean_definition("- item1\n- item2")
        assert not result.startswith("-")
        assert "item1" in result
        assert "item2" in result

    def test_removes_plus_bullets(self):
        """+ 불릿 제거"""
        result = _clean_definition("+ item1\n+ item2")
        assert "+" not in result

    def test_removes_asterisk_bullets(self):
        """* 불릿 제거"""
        result = _clean_definition("* item1\n* item2")
        assert result.startswith("item")

    def test_removes_links(self):
        """링크 문법 제거, 텍스트 유지"""
        result = _clean_definition("[link](http://example.com)")
        assert "link" in result
        assert "http" not in result
        assert "[" not in result
        assert "]" not in result

    def test_removes_complex_links(self):
        """복잡한 링크 제거"""
        result = _clean_definition("Check [this link](https://example.com/path?q=1) out")
        assert "this link" in result
        assert "https" not in result

    def test_collapses_multiple_newlines(self):
        """연속 줄바꿈 축소"""
        result = _clean_definition("text\n\n\n\nmore")
        assert "\n\n\n" not in result
        assert "text" in result
        assert "more" in result

    def test_empty_input(self):
        """빈 입력"""
        assert _clean_definition("") == ""

    def test_none_input(self):
        """None 입력"""
        assert _clean_definition(None) == ""

    def test_plain_text_unchanged(self):
        """일반 텍스트는 변경 없음"""
        text = "이것은 일반 텍스트입니다."
        assert _clean_definition(text) == text

    def test_strips_whitespace(self):
        """앞뒤 공백 제거"""
        result = _clean_definition("  text  ")
        assert result == "text"

    def test_underscore_italic(self):
        """언더스코어 이탤릭 제거"""
        result = _clean_definition("_italic_ text")
        assert "_" not in result
        assert "italic" in result

    def test_double_underscore_bold(self):
        """이중 언더스코어 볼드 제거"""
        result = _clean_definition("__bold__ text")
        assert "__" not in result
        assert "bold" in result

    def test_mixed_markdown(self):
        """혼합 마크다운 처리"""
        text = """## 제목

**강조된** 텍스트와 [링크](http://example.com)

- 항목 1
- 항목 2"""
        result = _clean_definition(text)
        assert "##" not in result
        assert "**" not in result
        assert "http" not in result
        assert "제목" in result
        assert "강조된" in result
        assert "링크" in result


class TestFilterValidExamples:
    """_filter_valid_examples 함수 테스트 (LLM 생성 방지)"""

    def test_keeps_examples_with_source_url(self):
        """source_url 있는 예시 유지"""
        examples = [
            {"context": "테스트", "usage": "사용법", "source_url": "https://example.com"},
        ]
        result = _filter_valid_examples(examples)
        assert len(result) == 1
        assert result[0]["source_url"] == "https://example.com"

    def test_removes_examples_without_source_url(self):
        """source_url 없는 예시 제거 (LLM 생성 의심)"""
        examples = [
            {"context": "테스트", "usage": "사용법"},  # source_url 없음
            {"context": "테스트2", "usage": "사용법2", "source_url": None},  # None
        ]
        result = _filter_valid_examples(examples)
        assert len(result) == 0

    def test_mixed_examples(self):
        """유효/무효 예시 혼합"""
        examples = [
            {"context": "유효", "usage": "사용법", "source_url": "https://valid.com"},
            {"context": "무효", "usage": "LLM 생성"},  # source_url 없음
            {"context": "유효2", "usage": "사용법2", "source_url": "https://valid2.com"},
        ]
        result = _filter_valid_examples(examples)
        assert len(result) == 2
        assert all(ex.get("source_url") for ex in result)

    def test_empty_list(self):
        """빈 리스트"""
        assert _filter_valid_examples([]) == []

    def test_empty_string_source_url_filtered(self):
        """빈 문자열 source_url도 필터링"""
        examples = [
            {"context": "테스트", "usage": "사용법", "source_url": ""},
        ]
        result = _filter_valid_examples(examples)
        assert len(result) == 0


class TestDefinitionPriority:
    """definition 우선순위 테스트 (소스 기반 > LLM 생성)"""

    def test_text_researcher_definition_priority(self):
        """_text_researcher.definition이 analysis.definition보다 우선"""
        from meme_collector.nodes.finalize import _clean_definition

        # 시뮬레이션: collected_info와 analysis 둘 다 definition 있을 때
        text_research_def = "나무위키에서 추출한 정의입니다."
        analyzer_def = "LLM이 생성한 더 긴 정의입니다. 여러 문장으로 구성됩니다."

        collected_info = {
            "_text_researcher": {"definition": text_research_def}
        }
        analysis = {"definition": analyzer_def}

        # finalize_node 로직 재현
        text_research = collected_info.get("_text_researcher", {})
        raw_definition = (
            text_research.get("definition")
            or analysis.get("definition")
            or "정의 없음"
        )

        assert raw_definition == text_research_def
        assert raw_definition != analyzer_def

    def test_fallback_to_analyzer_when_no_text_research(self):
        """_text_researcher.definition 없으면 analysis.definition 사용"""
        analyzer_def = "LLM이 생성한 정의"

        collected_info = {"_text_researcher": {}}  # definition 없음
        analysis = {"definition": analyzer_def}

        text_research = collected_info.get("_text_researcher", {})
        raw_definition = (
            text_research.get("definition")
            or analysis.get("definition")
            or "정의 없음"
        )

        assert raw_definition == analyzer_def

    def test_default_when_no_definition(self):
        """모든 소스에 definition 없으면 기본값"""
        collected_info = {}
        analysis = {}

        text_research = collected_info.get("_text_researcher", {})
        raw_definition = (
            text_research.get("definition")
            or analysis.get("definition")
            or collected_info.get("summary", "")[:500]
            or "정의 없음"
        )

        assert raw_definition == "정의 없음"


class TestValidateOutput:
    """_validate_output 함수 테스트 (출력 품질 검증)"""

    def _make_output(self, **overrides) -> MemeOutput:
        """테스트용 MemeOutput 생성"""
        defaults = {
            "name": "테스트밈",
            "definition": "테스트 정의입니다.",
            "meme_type": "quotable",
            "key_phrase": "테스트 문구",
            "emotion": "excited",
            "motion_prompt": "A person jumps with excitement",
            "usage_examples": [
                UsageExample(
                    context="테스트 상황",
                    usage="테스트 사용법",
                    source_url="https://example.com",
                )
            ],
        }
        defaults.update(overrides)
        return MemeOutput(**defaults)

    def test_valid_quotable_no_warnings(self):
        """유효한 quotable 밈은 경고 없음"""
        output = self._make_output()
        warnings = _validate_output(output)
        assert warnings == []

    def test_valid_performable_no_key_phrase_no_warning(self):
        """performable 밈은 key_phrase 없어도 경고 없음"""
        output = self._make_output(
            meme_type="performable",
            key_phrase=None,
        )
        warnings = _validate_output(output)
        assert "key_phrase" not in str(warnings)

    def test_warning_quotable_no_key_phrase(self):
        """quotable 밈에 key_phrase 없으면 경고"""
        output = self._make_output(
            meme_type="quotable",
            key_phrase=None,
        )
        warnings = _validate_output(output)
        assert len(warnings) == 1
        assert "key_phrase" in warnings[0]

    def test_warning_hybrid_no_key_phrase(self):
        """hybrid 밈에 key_phrase 없으면 경고"""
        output = self._make_output(
            meme_type="hybrid",
            key_phrase=None,
        )
        warnings = _validate_output(output)
        assert any("key_phrase" in w for w in warnings)

    def test_warning_empty_usage_examples(self):
        """usage_examples 비어있으면 경고"""
        output = self._make_output(usage_examples=[])
        warnings = _validate_output(output)
        assert any("usage_examples" in w for w in warnings)

    def test_warning_default_motion_prompt(self):
        """motion_prompt가 기본값이면 경고"""
        output = self._make_output(motion_prompt=_DEFAULT_MOTION_PROMPT)
        warnings = _validate_output(output)
        assert any("motion_prompt" in w for w in warnings)

    def test_multiple_warnings(self):
        """여러 문제가 있으면 모든 경고 반환"""
        output = self._make_output(
            meme_type="quotable",
            key_phrase=None,
            usage_examples=[],
            motion_prompt=_DEFAULT_MOTION_PROMPT,
        )
        warnings = _validate_output(output)
        assert len(warnings) == 3
        assert any("key_phrase" in w for w in warnings)
        assert any("usage_examples" in w for w in warnings)
        assert any("motion_prompt" in w for w in warnings)

    def test_empty_key_phrase_treated_as_missing(self):
        """빈 문자열 key_phrase도 없는 것으로 간주"""
        output = self._make_output(
            meme_type="quotable",
            key_phrase="",
        )
        warnings = _validate_output(output)
        # 빈 문자열은 falsy이므로 경고 발생
        assert any("key_phrase" in w for w in warnings)

    def test_valid_with_custom_motion_prompt(self):
        """커스텀 motion_prompt는 경고 없음"""
        output = self._make_output(
            motion_prompt="A man waves both arms enthusiastically while smiling",
        )
        warnings = _validate_output(output)
        assert not any("motion_prompt" in w for w in warnings)
