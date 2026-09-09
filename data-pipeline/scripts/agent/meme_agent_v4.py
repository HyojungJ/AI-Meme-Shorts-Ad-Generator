"""
Meme Data Collection Agent (v4) - Universal Meme Agent

핵심 개선:
1. 밈 유형 자동 분류 (video_dance, catchphrase, sound, character, reaction)
2. 유형별 맞춤 데이터 수집
3. 통합 스키마 + 유형별 상세 필드
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Annotated, TypedDict, Literal
from pydantic import BaseModel, Field

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from tools import ALL_TOOLS

load_dotenv()


# =============================================================================
# 밈 유형 정의
# =============================================================================

MEME_TYPES = {
    "video_dance": "영상/댄스 밈 - 안무, 챌린지, 음악이 핵심",
    "catchphrase": "유행어/어록 밈 - 특정 문구나 말투가 핵심",
    "sound": "소리/음성 밈 - 특정 소리나 발음이 핵심",
    "character": "캐릭터/이미지 밈 - 특정 캐릭터나 이미지가 핵심",
    "reaction": "리액션 밈 - 특정 상황에 대한 반응이 핵심",
    "reference": "레퍼런스 밈 - 특정 작품/사건 인용이 핵심"
}


# =============================================================================
# 상태 및 스키마
# =============================================================================

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    meme_name: str
    meme_type: str
    phase: str  # classify, collect, finalize
    iteration: int
    max_iterations: int


# =============================================================================
# 프롬프트
# =============================================================================

CLASSIFIER_PROMPT = """당신은 인터넷 밈 분류 전문가입니다.
수집된 정보를 바탕으로 이 밈의 유형을 판단하세요.

## 밈 유형

1. video_dance: 영상/댄스 밈
   - 특징: 안무, 챌린지, 특정 동작, 배경음악이 핵심
   - 예시: 매끈매끈하다, 골반통신, 랫 댄스, 미오 마오 댄스

2. catchphrase: 유행어/어록 밈
   - 특징: 특정 문구, 말투, 텍스트 패턴이 핵심
   - 예시: 개웃겨서 도티낳음, ~의 리즈시절, 앱솔루트 시네마, 사람이 죽는다고

3. sound: 소리/음성 밈
   - 특징: 특정 소리, 발음, 억양이 핵심 (동작은 부수적)
   - 예시: 햄부기햄북, 천천천국지옥국, 괜찮아 딩딩딩딩딩

4. character: 캐릭터/이미지 밈
   - 특징: 특정 캐릭터, 표정, 이미지가 핵심
   - 예시: Chill guy, 오이이아이 고양이, 도이 더 도우맨

5. reaction: 리액션 밈
   - 특징: 특정 상황에 대한 반응, 표정이 핵심
   - 예시: 어 그래요, 뭐요

6. reference: 레퍼런스 밈
   - 특징: 드라마, 영화, 게임 등 특정 작품 인용이 핵심
   - 예시: 오징어 게임 2, 중증외상센터

## 분류 기준

- 동작/안무가 핵심이면 -> video_dance
- 텍스트 문구가 핵심이면 -> catchphrase
- 소리/발음이 핵심이면 -> sound
- 캐릭터/이미지가 핵심이면 -> character
- 반응/표정이 핵심이면 -> reaction
- 작품 인용이 핵심이면 -> reference

수집된 정보를 분석하고, 다음 형식으로 응답하세요:
MEME_TYPE: [유형]
REASON: [분류 이유 1-2문장]
"""


COLLECT_PROMPTS = {
    "video_dance": """이 밈은 영상/댄스 밈입니다. 다음 정보를 수집하세요:

## 필수 수집 항목
1. 원본 영상 URL 및 제작자
2. 자막/가사 (타임스탬프 포함) - get_youtube_transcript 사용
3. 안무/동작 시퀀스 (시간순, 신체 부위별)
4. 배경음악 정보 (곡명, BPM, 특징)
5. 챌린지 방법 (있다면)

## 도구 사용 전략
- 원본 영상 찾으면: get_youtube_info + get_youtube_transcript
- 안무 정보 부족하면: search_google("{name} 안무 동작")
- 챌린지 정보: search_google("{name} 챌린지 따라하기")
""",

    "catchphrase": """이 밈은 유행어/어록 밈입니다. 다음 정보를 수집하세요:

## 필수 수집 항목
1. 원본 문구 (정확한 텍스트)
2. 문구 패턴/구조 (예: "개웃겨서 {X}낳음")
3. 변형 예시 목록
4. 말투/어조 특징
5. 사용 맥락/상황

## 도구 사용 전략
- 원본 출처: search_namuwiki, search_google
- 변형 예시: search_google("{name} 변형 짤")
- 사용법: crawl_webpage (관련 기사)
""",

    "sound": """이 밈은 소리/음성 밈입니다. 다음 정보를 수집하세요:

## 필수 수집 항목
1. 원본 소리/음성 출처
2. 발음/소리 표기 (한글, 영어 등)
3. 음성 특징 (톤, 속도, 억양)
4. 따라하기 가이드
5. 사용 맥락

## 도구 사용 전략
- 원본: search_youtube("{name} 원본")
- 발음 정보: search_namuwiki, search_google
- 음성 특징: get_youtube_info (영상 설명 참고)
""",

    "character": """이 밈은 캐릭터/이미지 밈입니다. 다음 정보를 수집하세요:

## 필수 수집 항목
1. 캐릭터/이미지 출처
2. 외형 설명 (표정, 포즈, 스타일)
3. 캐릭터 특성/성격
4. 대표 이미지 URL
5. 사용 맥락/의미

## 도구 사용 전략
- 캐릭터 정보: search_namuwiki, search_google
- 이미지 출처: search_google("{name} 원본 이미지")
- 사용법: crawl_webpage (관련 기사)
""",

    "reaction": """이 밈은 리액션 밈입니다. 다음 정보를 수집하세요:

## 필수 수집 항목
1. 원본 출처 (영상/이미지)
2. 리액션 대상 (어떤 상황에 반응?)
3. 표정/동작 설명
4. 감정 표현 (어떤 감정?)
5. 사용 예시

## 도구 사용 전략
- 원본: search_youtube, search_google
- 맥락: search_namuwiki
- 사용법: crawl_webpage
""",

    "reference": """이 밈은 레퍼런스 밈입니다. 다음 정보를 수집하세요:

## 필수 수집 항목
1. 원작 정보 (작품명, 등장인물)
2. 밈이 된 장면/대사
3. 원작에서의 맥락
4. 밈으로서의 의미/사용법
5. 패러디/변형 예시

## 도구 사용 전략
- 원작 정보: search_namuwiki
- 밈 맥락: search_google("{name} 밈 뜻")
- 사용 예시: crawl_webpage
"""
}


FINALIZE_PROMPTS = {
    "video_dance": """수집된 정보를 바탕으로 영상/댄스 밈 데이터를 JSON으로 정리하세요.

```json
{
    "name": "밈 이름",
    "type": "video_dance",
    "definition": "밈 정의 (2-3문장)",
    "origin": {
        "source": "원본 출처 설명",
        "url": "원본 URL",
        "creator": "제작자",
        "date": "시작 시점"
    },
    "script": [
        {"timestamp": "00:00-00:02", "text": "가사/대사", "voice_style": "음성 특징"}
    ],
    "choreography": [
        {
            "sequence": 1,
            "timestamp": "00:00-00:02",
            "description": "동작 설명",
            "body": {
                "face": "표정",
                "arms": "팔 동작",
                "hands": "손 동작",
                "body": "몸통 동작",
                "legs": "다리 동작"
            }
        }
    ],
    "audio": {
        "music_name": "곡명",
        "bpm": "BPM",
        "characteristics": "음악 특징"
    },
    "how_to_recreate": {
        "difficulty": "상/중/하",
        "key_points": ["핵심 포인트1", "포인트2"],
        "common_mistakes": ["주의할 점"]
    },
    "usage": {
        "when_to_use": ["사용 상황"],
        "platforms": ["유행 플랫폼"]
    },
    "keywords": ["키워드"],
    "source_urls": ["출처 URL"]
}
```
JSON만 출력하세요.
""",

    "catchphrase": """수집된 정보를 바탕으로 유행어/어록 밈 데이터를 JSON으로 정리하세요.

```json
{
    "name": "밈 이름",
    "type": "catchphrase",
    "definition": "밈 정의 (2-3문장)",
    "origin": {
        "source": "원본 출처 설명",
        "url": "원본 URL",
        "creator": "원작자",
        "date": "시작 시점"
    },
    "phrase": {
        "original": "원본 문구 그대로",
        "pattern": "문구 패턴 (예: 개웃겨서 {X}낳음)",
        "pronunciation": "발음/읽는 법",
        "tone": "말투/어조 (예: 과장된, 진지한)"
    },
    "variations": [
        {"text": "변형1", "context": "사용 맥락"},
        {"text": "변형2", "context": "사용 맥락"}
    ],
    "how_to_use": {
        "situations": ["사용 상황1", "상황2"],
        "emotion": "표현하는 감정",
        "delivery": "전달 방법 (진지하게, 장난스럽게 등)"
    },
    "keywords": ["키워드"],
    "source_urls": ["출처 URL"]
}
```
JSON만 출력하세요.
""",

    "sound": """수집된 정보를 바탕으로 소리/음성 밈 데이터를 JSON으로 정리하세요.

```json
{
    "name": "밈 이름",
    "type": "sound",
    "definition": "밈 정의 (2-3문장)",
    "origin": {
        "source": "원본 출처 설명",
        "url": "원본 URL",
        "creator": "원작자",
        "date": "시작 시점"
    },
    "sound": {
        "transcription": "소리를 글자로 표기",
        "pronunciation_guide": "발음 가이드",
        "tone": "톤 (높음/낮음/변화)",
        "speed": "속도 (빠름/보통/느림)",
        "accent": "억양/강세 특징"
    },
    "how_to_recreate": {
        "steps": ["따라하기 단계1", "단계2"],
        "tips": ["팁1", "팁2"],
        "common_mistakes": ["주의할 점"]
    },
    "usage": {
        "situations": ["사용 상황"],
        "emotion": "표현하는 감정"
    },
    "keywords": ["키워드"],
    "source_urls": ["출처 URL"]
}
```
JSON만 출력하세요.
""",

    "character": """수집된 정보를 바탕으로 캐릭터/이미지 밈 데이터를 JSON으로 정리하세요.

```json
{
    "name": "밈 이름",
    "type": "character",
    "definition": "밈 정의 (2-3문장)",
    "origin": {
        "source": "원본 출처 설명",
        "url": "원본 URL",
        "creator": "원작자",
        "date": "시작 시점"
    },
    "character": {
        "appearance": "외형 설명",
        "expression": "표정",
        "pose": "포즈/자세",
        "style": "스타일 (그림체, 실사 등)",
        "personality": "캐릭터 성격/특성"
    },
    "meaning": {
        "represents": "상징하는 것",
        "emotion": "표현하는 감정",
        "context": "사용 맥락"
    },
    "usage": {
        "situations": ["사용 상황"],
        "platforms": ["유행 플랫폼"]
    },
    "keywords": ["키워드"],
    "source_urls": ["출처 URL"]
}
```
JSON만 출력하세요.
""",

    "reaction": """수집된 정보를 바탕으로 리액션 밈 데이터를 JSON으로 정리하세요.

```json
{
    "name": "밈 이름",
    "type": "reaction",
    "definition": "밈 정의 (2-3문장)",
    "origin": {
        "source": "원본 출처 설명",
        "url": "원본 URL",
        "creator": "원작자",
        "date": "시작 시점"
    },
    "reaction": {
        "trigger": "반응을 유발하는 상황",
        "expression": "표정 설명",
        "action": "동작 설명",
        "emotion": "감정",
        "phrase": "함께 사용되는 문구 (있다면)"
    },
    "usage": {
        "situations": ["사용 상황"],
        "meaning": "밈으로서의 의미"
    },
    "keywords": ["키워드"],
    "source_urls": ["출처 URL"]
}
```
JSON만 출력하세요.
""",

    "reference": """수집된 정보를 바탕으로 레퍼런스 밈 데이터를 JSON으로 정리하세요.

```json
{
    "name": "밈 이름",
    "type": "reference",
    "definition": "밈 정의 (2-3문장)",
    "origin": {
        "work": "원작 제목",
        "type": "원작 유형 (드라마/영화/게임 등)",
        "scene": "밈이 된 장면 설명",
        "character": "관련 캐릭터",
        "original_context": "원작에서의 맥락"
    },
    "meme_usage": {
        "meaning": "밈으로서의 의미",
        "situations": ["사용 상황"],
        "phrase": "관련 대사/문구"
    },
    "parodies": [
        {"description": "패러디 설명", "example": "예시"}
    ],
    "keywords": ["키워드"],
    "source_urls": ["출처 URL"]
}
```
JSON만 출력하세요.
"""
}


# =============================================================================
# 에이전트 함수
# =============================================================================

def create_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    llm_with_tools = llm.bind_tools(ALL_TOOLS, parallel_tool_calls=True)

    def classify_node(state: AgentState) -> AgentState:
        """밈 유형 분류"""
        messages = state["messages"]

        # 분류 요청
        classify_msg = HumanMessage(content=CLASSIFIER_PROMPT)
        response = llm.invoke(messages + [classify_msg])

        # 유형 추출
        content = response.content
        meme_type = "catchphrase"  # 기본값

        for t in MEME_TYPES.keys():
            if f"MEME_TYPE: {t}" in content or f"MEME_TYPE:{t}" in content:
                meme_type = t
                break

        return {
            "messages": [response],
            "meme_type": meme_type,
            "phase": "collect"
        }

    def collect_node(state: AgentState) -> AgentState:
        """유형별 데이터 수집"""
        messages = state["messages"]
        meme_type = state.get("meme_type", "catchphrase")
        iteration = state["iteration"]

        # 첫 수집이면 유형별 프롬프트 추가
        if iteration == 0 or state.get("phase") == "collect":
            collect_prompt = COLLECT_PROMPTS.get(meme_type, COLLECT_PROMPTS["catchphrase"])
            system_msg = SystemMessage(content=f"""당신은 밈 데이터 수집 전문가입니다.
이 밈은 '{MEME_TYPES.get(meme_type, '')}'입니다.

{collect_prompt}

여러 도구를 병렬로 호출하여 효율적으로 수집하세요.
충분한 정보가 수집되면 "COLLECTION_COMPLETE"를 선언하세요.
""")
            messages = [system_msg] + messages

        response = llm_with_tools.invoke(messages)

        return {
            "messages": [response],
            "iteration": iteration + 1
        }

    def should_continue(state: AgentState) -> str:
        """다음 단계 결정"""
        messages = state["messages"]
        last_message = messages[-1] if messages else None
        phase = state.get("phase", "classify")

        if not last_message:
            return "collect"

        # 도구 호출이 있으면 도구 실행
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        # 분류 완료 후 수집으로
        if phase == "classify":
            return "collect"

        # 최대 반복 도달
        if state["iteration"] >= state["max_iterations"]:
            return "finalize"

        # 완료 선언
        if hasattr(last_message, "content"):
            if "COLLECTION_COMPLETE" in str(last_message.content):
                return "finalize"

        return "finalize"

    def finalize_node(state: AgentState) -> AgentState:
        """최종 정리"""
        messages = state["messages"]
        meme_type = state.get("meme_type", "catchphrase")

        finalize_prompt = FINALIZE_PROMPTS.get(meme_type, FINALIZE_PROMPTS["catchphrase"])
        finalize_msg = HumanMessage(content=finalize_prompt)

        response = llm.invoke(messages + [finalize_msg])

        return {
            "messages": [response],
            "phase": "done"
        }

    # 그래프 구성
    workflow = StateGraph(AgentState)

    workflow.add_node("classify", classify_node)
    workflow.add_node("collect", collect_node)
    workflow.add_node("tools", ToolNode(ALL_TOOLS))
    workflow.add_node("finalize", finalize_node)

    workflow.set_entry_point("classify")
    workflow.add_edge("classify", "collect")
    workflow.add_conditional_edges("collect", should_continue, {
        "tools": "tools",
        "collect": "collect",
        "finalize": "finalize"
    })
    workflow.add_edge("tools", "collect")
    workflow.add_edge("finalize", END)

    return workflow.compile()


class UniversalMemeAgent:
    """범용 밈 데이터 수집 에이전트"""

    def __init__(self, max_iterations: int = 8):
        self.agent = create_agent()
        self.max_iterations = max_iterations

    def collect(self, meme_name: str, verbose: bool = True) -> dict:
        if verbose:
            print(f"\n{'='*60}")
            print(f"Universal Meme Agent: {meme_name}")
            print(f"{'='*60}\n")

        initial_state = {
            "messages": [
                HumanMessage(content=f"""'{meme_name}' 밈 정보를 수집해주세요.

1단계: 먼저 다음 도구들을 병렬로 호출하여 기본 정보를 수집하세요:
- search_namuwiki("{meme_name}")
- search_google("{meme_name} 밈 뜻 유래")
- search_youtube("{meme_name} 원본")

2단계: 수집된 정보를 바탕으로 밈 유형을 분류하세요.

3단계: 유형에 맞는 추가 정보를 수집하세요.""")
            ],
            "meme_name": meme_name,
            "meme_type": "",
            "phase": "classify",
            "iteration": 0,
            "max_iterations": self.max_iterations
        }

        final_state = None
        for state in self.agent.stream(initial_state):
            if verbose:
                for node_name, node_state in state.items():
                    self._print_state(node_name, node_state)
            final_state = state

        result = self._parse_result(final_state, meme_name)

        if verbose:
            print(f"\n{'='*60}")
            print(f"Complete: {meme_name} (type: {result.get('type', 'unknown')})")
            print(f"{'='*60}\n")

        return result

    def _print_state(self, node_name: str, node_state: dict):
        if "meme_type" in node_state and node_state["meme_type"]:
            print(f"[Type] {node_state['meme_type']}")

        if "messages" not in node_state:
            return

        for msg in node_state["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                names = [tc["name"] for tc in msg.tool_calls]
                if len(names) > 1:
                    print(f"[Parallel] {', '.join(names)}")
                else:
                    print(f"[Tool] {names[0]}")
            elif hasattr(msg, "content") and msg.content:
                content = str(msg.content)
                if "MEME_TYPE:" in content:
                    for line in content.split("\n"):
                        if "MEME_TYPE" in line or "REASON" in line:
                            print(f"[Classify] {line.strip()}")
                elif "COLLECTION_COMPLETE" in content:
                    print("[Done] Collection complete")
                elif "```json" in content:
                    print("[Output] JSON generated")
                elif node_name == "tools":
                    print(f"[Result] {content[:80]}...")

    def _parse_result(self, final_state: dict, meme_name: str) -> dict:
        default_result = {
            "name": meme_name,
            "type": "unknown",
            "definition": "",
            "origin": {},
            "collected_at": datetime.now().isoformat(),
            "collection_method": "universal_meme_agent_v4"
        }

        if not final_state:
            return default_result

        # meme_type 추출
        for node_state in final_state.values():
            if "meme_type" in node_state and node_state["meme_type"]:
                default_result["type"] = node_state["meme_type"]

        # JSON 추출
        for node_state in final_state.values():
            if "messages" not in node_state:
                continue
            for msg in node_state["messages"]:
                if not hasattr(msg, "content"):
                    continue
                content = str(msg.content)

                json_str = None
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "{" in content and "}" in content:
                    start = content.find("{")
                    end = content.rfind("}") + 1
                    json_str = content[start:end]

                if json_str:
                    try:
                        parsed = json.loads(json_str)
                        parsed["collected_at"] = datetime.now().isoformat()
                        parsed["collection_method"] = "universal_meme_agent_v4"
                        return parsed
                    except json.JSONDecodeError:
                        continue

        return default_result

    def save_result(self, result: dict, output_dir: str = "data/agent_output") -> str:
        import re
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        safe_name = re.sub(r'[\\/*?:"<>|]', "_", result.get("name", "unknown"))
        meme_type = result.get("type", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"meme_{meme_type}_{safe_name}_{timestamp}.json"
        filepath = output_path / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"Saved: {filepath}")
        return str(filepath)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Universal Meme Agent v4")
    parser.add_argument("meme_name", help="Name of the meme")
    parser.add_argument("--max-iter", "-m", type=int, default=8)
    parser.add_argument("--output", "-o", default="data/agent_output")
    parser.add_argument("--quiet", "-q", action="store_true")
    args = parser.parse_args()

    agent = UniversalMemeAgent(max_iterations=args.max_iter)
    result = agent.collect(args.meme_name, verbose=not args.quiet)
    agent.save_result(result, args.output)

    # Summary
    print(f"\n{'='*50}")
    print(f"Summary: {result.get('name', '')}")
    print(f"Type: {result.get('type', '')}")
    print(f"{'='*50}")
    print(f"Definition: {result.get('definition', '')[:100]}...")

    # Type-specific summary
    meme_type = result.get("type", "")
    if meme_type == "video_dance":
        script = result.get("script", [])
        choreo = result.get("choreography", [])
        print(f"Script: {len(script)} entries")
        print(f"Choreography: {len(choreo)} sequences")
    elif meme_type == "catchphrase":
        phrase = result.get("phrase", {})
        variations = result.get("variations", [])
        print(f"Pattern: {phrase.get('pattern', '')}")
        print(f"Variations: {len(variations)}")
    elif meme_type == "sound":
        sound = result.get("sound", {})
        print(f"Transcription: {sound.get('transcription', '')}")
    elif meme_type == "character":
        char = result.get("character", {})
        print(f"Appearance: {char.get('appearance', '')[:50]}...")


if __name__ == "__main__":
    main()
