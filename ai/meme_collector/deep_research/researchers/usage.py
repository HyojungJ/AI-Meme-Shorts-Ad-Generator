"""UsageResearcher: 도구 직접 호출로 밈 활용 예시 수집

Note: ReAct Agent 패턴에서 직접 도구 호출 방식으로 변경됨 (source_url 보존 목적)
"""
from meme_collector.state import MemeState
from meme_collector.tools.usage_extractor import extract_usage_examples
from meme_collector.tools.video_analyzer import extract_usage_from_videos


def run_usage_researcher(state: MemeState) -> dict:
    """UsageResearcher: 도구 직접 호출로 밈 활용 예시 수집 (source_url 보존)

    Note: text→usage 순서로 실행되므로 _text_researcher 결과 활용 가능
    """
    meme_name = state["meme_name"]
    collected_info = state.get("collected_info", {})
    youtube_videos = collected_info.get("youtube_videos", [])

    # text_researcher 결과 활용 (text→usage 순서이므로 이제 사용 가능)
    text_data = collected_info.get("_text_researcher", {})
    definition = text_data.get("definition", "")
    key_phrase = text_data.get("key_phrase", "")

    # 더 풍부한 컨텍스트로 검색 (definition, key_phrase 활용)
    # Note: origin은 text_researcher에서 string으로 오므로 제외 (usage_extractor가 dict 기대)
    context = {
        "definition": definition,
        "key_phrase": key_phrase,
    }

    # 1. 웹 검색으로 활용 예시 수집 (source_url 포함)
    web_examples = extract_usage_examples.invoke({
        "meme_name": meme_name,
        "context": context if definition else None,
    })

    # 2. 영상에서 추가 수집 (source_url = YouTube URL)
    video_examples = []
    if youtube_videos and len(web_examples) < 5:
        video_examples = extract_usage_from_videos(youtube_videos[:2], meme_name, max_videos=2)

    # 3. 병합 및 중복 제거
    all_examples = web_examples + video_examples
    seen = set()
    unique_examples = []
    for ex in all_examples:
        key = (ex.get("context", ""), ex.get("usage", ""))
        if key not in seen:
            seen.add(key)
            unique_examples.append(ex)

    # 4. 톤 분석
    tones = [ex.get("tone", "playful") for ex in unique_examples]
    dominant_tone = max(set(tones), key=tones.count) if tones else "playful"

    # 구조화된 텍스트로 변환
    examples_text = ""
    for i, ex in enumerate(unique_examples[:7], 1):
        examples_text += f"{i}. 상황: {ex.get('context', '')}\n   사용: {ex.get('usage', '')}\n   톤: {ex.get('tone', 'playful')}\n   출처: {ex.get('source_url', '')}\n\n"

    notes_text = f"""## 활용 예시 ({len(unique_examples)}개)
{examples_text}
## 주된 톤
{dominant_tone}"""

    return {
        "research_notes": {"usage": notes_text},
        "researcher_status": {"usage": "done"},
        "collected_info": {"usage_examples": unique_examples},
    }
