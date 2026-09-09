def has_quoted_dialogue(text: str) -> bool:
    return any(q in text for q in ["'", '"', "'", "'", """, """])


def is_valid_korean_definition(definition: str, min_length: int = 100) -> tuple[bool, str]:
    """definition이 유효한 한국어인지 검증.

    Returns:
        (is_valid, reason)
    """
    if not definition:
        return False, "definition 없음"

    if len(definition) < min_length:
        return False, f"definition 너무 짧음 ({len(definition)}자, 최소 {min_length}자)"

    # "정보 없음" 등 무의미한 값 체크
    invalid_phrases = ["정보 없음", "알 수 없", "확인 필요", "정보가 없", "찾을 수 없"]
    for phrase in invalid_phrases:
        if phrase in definition:
            return False, f"무의미한 definition: '{phrase}' 포함"

    # 불확실/일반적 표현 체크 (밈 설명이 아닌 것들)
    vague_phrases = [
        "추정됩니다", "추정된다", "으로 보입니다", "으로 보인다",
        "특정 밈보다는", "밈으로 사용되는 경우는",
        "금색을 의미", "를 의미하며",
        "특정 상황에서 유행하는 인터넷 표현",
    ]
    for phrase in vague_phrases:
        if phrase in definition:
            return False, f"불확실/일반적 definition: '{phrase}' 포함"

    # 한국어 비율 체크 (최소 30% 이상이어야 함)
    korean_chars = len([c for c in definition if '가' <= c <= '힣'])
    total_chars = len(definition.replace(" ", ""))
    korean_ratio = korean_chars / total_chars if total_chars > 0 else 0

    if korean_ratio < 0.3:
        return False, f"영어 definition (한국어 비율: {korean_ratio:.0%})"

    # 영어로 시작하는 경우 체크 (The, This, It, A 등)
    english_starts = ["the ", "this ", "it ", "a ", "an ", "in ", "on ", "for "]
    lower_def = definition.lower().strip()
    for start in english_starts:
        if lower_def.startswith(start):
            return False, "영어로 시작하는 definition"

    return True, "OK"


def clean_html(text: str) -> str:
    """HTML 태그 및 엔티티 제거"""
    return (
        text.replace("<b>", "")
        .replace("</b>", "")
        .replace("&quot;", '"')
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    )
