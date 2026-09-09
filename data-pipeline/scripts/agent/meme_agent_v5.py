"""
Meme Data Collection Agent (v5) - Enhanced Universal Agent

핵심 개선:
1. 4단계 순차 수집: 기본정보 -> 배경스토리 -> 활용예시 -> 스크립트템플릿
2. 단계별 1회 도구 호출 후 다음 단계로 이동 (효율적)
3. 최종 정리 시 모든 정보 종합
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Annotated, TypedDict

import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from tools import ALL_TOOLS

load_dotenv()


def invoke_with_retry(llm, messages, max_retries=3, base_delay=20):
    """Rate limit 오류 시 재시도하는 래퍼 함수"""
    for attempt in range(max_retries):
        try:
            return llm.invoke(messages)
        except Exception as e:
            if "rate_limit" in str(e).lower() or "429" in str(e):
                delay = base_delay * (attempt + 1)
                print(f"  [Rate Limit] Waiting {delay}s before retry...")
                time.sleep(delay)
            else:
                raise
    # 마지막 시도
    return llm.invoke(messages)


MEME_TYPES = {
    "video_dance": "영상/댄스 밈 - 안무, 챌린지, 음악이 핵심",
    "catchphrase": "유행어/어록 밈 - 특정 문구나 말투가 핵심",
    "sound": "소리/음성 밈 - 특정 소리나 발음이 핵심",
    "character": "캐릭터/이미지 밈 - 특정 캐릭터나 이미지가 핵심",
    "reaction": "리액션 밈 - 특정 상황에 대한 반응이 핵심",
    "reference": "레퍼런스 밈 - 특정 작품/사건 인용이 핵심"
}


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    meme_name: str
    meme_type: str
    parent: str  # 부모 밈 (예: "흑백요리사 2" -> "안성재 옷 입히기")
    phase: str
    tool_called: bool
    phase_tool_count: int  # 단계별 도구 호출 횟수 추적


# =============================================================================
# 프롬프트
# =============================================================================

CLASSIFIER_PROMPT = """당신은 인터넷 밈 분류 전문가입니다.

## 밈 유형
1. video_dance: 영상/댄스 밈 (안무, 챌린지, 동작, 음악)
2. catchphrase: 유행어/어록 밈 (특정 문구, 말투, 텍스트 패턴)
3. sound: 소리/음성 밈 (특정 소리, 발음, 억양)
4. character: 캐릭터/이미지 밈 (캐릭터, 표정, 이미지)
5. reaction: 리액션 밈 (상황 반응, 표정)
6. reference: 레퍼런스 밈 (작품/사건 인용)

수집된 정보를 분석하고 응답:
MEME_TYPE: [유형]
REASON: [이유]
"""


def get_collect_prompt(phase: str, meme_name: str, meme_type: str, parent: str = "") -> str:
    """단계별 수집 프롬프트 생성"""

    # parent가 있으면 검색 쿼리에 포함
    parent_context = f' "{parent}"' if parent else ""
    parent_note = f"\n\n참고: 이 밈은 '{parent}'에서 파생된 밈입니다." if parent else ""

    if phase == "basic":
        return f"""'{meme_name}' 밈의 기본 정보를 수집하세요.{parent_note}

병렬로 다음 도구들을 호출하세요:
- search_namuwiki("{meme_name}")
- search_google("{meme_name}{parent_context} 밈 뜻 유래 원본")
- search_youtube("{meme_name}{parent_context} 원본")

필수 수집: 정의, 원본 출처, 제작자, 시작 시점

중요: 검색 결과에서 밈의 정확한 뜻과 유래를 찾아 원문 그대로 기록하세요.
- 단어의 의미를 추측하지 마세요
- 나무위키나 검색 결과의 정의를 그대로 사용하세요"""

    elif phase == "background":
        return f"""'{meme_name}' 밈의 배경 스토리를 수집하세요.{parent_note}

병렬로 다음 도구들을 호출하세요:
- search_google("{meme_name}{parent_context} 유행 이유 왜 인기")
- search_google("{meme_name}{parent_context} 확산 퍼진 계기")

필수 수집: 유행 이유, 확산 경로, 핵심 포인트, 연관 트렌드"""

    elif phase == "popular_content":
        return f"""'{meme_name}' 밈의 인기 콘텐츠를 분석하세요.{parent_note}

병렬로 다음 도구들을 호출하세요:
- search_youtube("{meme_name}{parent_context} 레전드")
- search_google("{meme_name}{parent_context} 밈 조롱 풍자 논란")
- search_google("{meme_name}{parent_context} 실제 사용 맥락 반응")

## 중요: 톤/뉘앙스 분석
검색 결과에서 밈이 어떤 톤으로 사용되는지 파악하세요:
- 긍정적: 칭찬, 존경, 부러움
- 부정적: 비판, 불쾌함
- 조롱/풍자: 놀림, 비꼼, 패러디
- 중립: 단순 설명, 정보 전달

특히 "조롱", "논란", "비판", "풍자" 같은 키워드가 있으면 반드시 기록하세요.

필수 수집:
1. 인기 콘텐츠 3개 (제목, URL)
2. 밈이 사용되는 실제 맥락
3. 공통 사용 패턴
4. 밈의 실제 톤/뉘앙스 (긍정/부정/조롱/풍자)
5. 시청자/사용자들의 일반적인 반응"""

    elif phase == "examples_search":
        return f"""'{meme_name}' 밈의 실제 사용 사례를 찾기 위해 검색하세요.{parent_note}

병렬로 다음 도구들을 호출하세요:
- search_google("{meme_name}{parent_context} 뜻 특징 예시")
- search_google("{meme_name}{parent_context} 의미 사용법 총정리")
- search_google("site:bbc.com OR site:hankyung.com OR site:donga.com {meme_name}{parent_context}")

검색 결과에서 **뉴스 기사, 블로그 글** URL을 찾아 기록하세요.
(커뮤니티 이미지 게시물은 크롤링이 안 되므로 피하세요)"""

    elif phase == "examples_crawl":
        return f"""이전 검색 결과에서 **텍스트 기반 페이지**를 크롤링하세요.

## 크롤링 우선순위 (중요!)
1순위: 뉴스 기사 (bbc.com, hankyung.com, donga.com 등)
2순위: 블로그 글 (blog.naver.com, brunch.co.kr, tistory.com 등)
3순위: 나무위키 문서

## 피해야 할 페이지 (크롤링 금지)
- ruliweb.com, dcinside.com, dogdrip.net 등 커뮤니티 이미지 게시물
- "jpg", "모음"이 제목에 있는 이미지 갤러리 게시물

## 크롤링 방법
이전 메시지에서 뉴스/블로그 URL을 찾아 crawl_webpage로 크롤링하세요.
병렬로 2-3개 URL을 크롤링하세요."""

    elif phase == "examples_extract":
        return f"""방금 크롤링한 기사/블로그 내용에서 **구체적인 예시**를 추출하세요.

## 추출 대상 (반드시 찾아서 기록)

### 1. 구체적 행동/대사 예시
크롤링한 텍스트에서 다음을 찾아 **원문 그대로** 인용하세요:
- 실제 인터뷰 발언 (따옴표로 된 부분)
- 구체적 행동 묘사 ("~하는 행동", "~하는 모습")
- 파생 표현/변형

### 2. 통계/수치
- "~%가 부정적", "~%가 긍정적" 같은 데이터
- 연관 키워드 목록

### 3. 특징 묘사
- 외모/패션 묘사 (어떤 옷, 어떤 스타일)
- 말투/행동 패턴

## 출력 형식
찾은 내용을 다음 형식으로 정리하세요:

[구체적 예시 1]: "원문 인용"
[구체적 예시 2]: "원문 인용"
[통계]: "원문 인용"
[파생 표현]: "원문 인용"
[특징]: "원문 인용"

크롤링한 텍스트를 다시 꼼꼼히 읽고, 위 내용을 찾아 기록하세요.
찾지 못한 항목은 "없음"으로 표시하세요."""

    elif phase == "scripts":
        type_prompts = {
            "video_dance": f"""'{meme_name}' 영상/댄스 밈의 스크립트 정보를 수집하세요.

병렬로 호출:
- search_google("{meme_name} 안무 동작 가사")
- search_google("{meme_name} 챌린지 따라하기 방법")
- search_youtube("{meme_name} 튜토리얼")

필수: 가사/대사, 안무 시퀀스, 음악 정보, 따라하기 가이드""",

            "catchphrase": f"""'{meme_name}' 유행어 밈의 스크립트 정보를 수집하세요.

병렬로 호출:
- search_google("{meme_name} 변형 모음 드립")
- search_google("{meme_name} 사용 상황 예시")

필수: 원본 문구 패턴, 변형 예시 5개 이상, 사용 맥락, 발화 방식""",

            "sound": f"""'{meme_name}' 소리 밈의 스크립트 정보를 수집하세요.

병렬로 호출:
- search_google("{meme_name} 발음 방법 따라하기")
- search_youtube("{meme_name} 원본 소리")

필수: 정확한 발음 표기, 발음 가이드, 톤/속도/억양, 연출 방법""",

            "character": f"""'{meme_name}' 캐릭터 밈의 스크립트 정보를 수집하세요.

병렬로 호출:
- search_google("{meme_name} 짤 사용법 합성")
- search_google("{meme_name} 활용 예시")

필수: 캐릭터 외형 상세, 사용 상황, 함께 쓰는 문구, 활용법""",

            "reaction": f"""'{meme_name}' 리액션 밈의 스크립트 정보를 수집하세요.

병렬로 호출:
- search_google("{meme_name} 리액션 사용법")
- search_google("{meme_name} 짤 모음")

필수: 표정/동작 상세, 사용 상황, 타이밍, 텍스트 오버레이""",

            "reference": f"""'{meme_name}' 레퍼런스 밈의 스크립트 정보를 수집하세요.

병렬로 호출:
- search_google("{meme_name} 패러디 모음")
- search_google("{meme_name} 원작 장면 대사")
- search_youtube("{meme_name} 패러디")

필수: 원작 장면/대사, 패러디 방법, 인기 패러디 예시"""
        }
        return type_prompts.get(meme_type, type_prompts["catchphrase"])

    return ""


def get_finalize_prompt(meme_type: str, parent: str = "") -> str:
    """최종 정리 프롬프트"""

    # 간소화된 스키마 - 배열 개수를 주석으로 명확히 표시
    base_schema = {
        "name": "밈 이름",
        "type": meme_type,
        "parent": parent if parent else None,  # 부모 밈 (파생 밈인 경우)
        "definition": "밈에 대한 상세한 정의 (5문장 이상)",
        "origin": {"source": "", "url": "", "creator": "", "date": "", "platform": ""},
        "background_story": {
            "why_viral": "왜 유행했는지",
            "spread_path": "확산 경로",
            "key_moments": ["주요 순간"],
            "what_makes_it_funny": "재미 포인트",
            "related_trends": ["연관 트렌드"]
        },
        "real_usage_context": {
            "popular_examples": "// 배열: 최소 3개 객체 필수! [{title, url, view_count, how_meme_used, context, why_funny}, ...]",
            "common_patterns": ["패턴1", "패턴2", "패턴3"],
            "tone": "조롱/풍자 또는 긍정적 또는 부정적",
            "best_timing": "사용 타이밍",
            "audience_reaction": "시청자 반응"
        },
        "usage_examples": "// 배열: 최소 5개 객체 필수! [{situation, description, platform, why_effective}, ...]",
        "script_templates": "// 배열: 최소 3개 객체 필수! [{name, setup, action, punchline, example}, ...]",
        "keywords": ["검색 키워드"],
        "source_urls": ["참고 URL"]
    }

    type_specific = {
        "video_dance": {
            "script": [{"timestamp": "00:00-00:05", "lyrics": "가사", "voice_style": "음성 특징"}],
            "choreography": [{
                "sequence": 1,
                "timestamp": "시간",
                "description": "동작 설명",
                "body": {"face": "", "arms": "", "hands": "", "torso": "", "legs": ""}
            }],
            "audio": {"music_name": "", "artist": "", "bpm": "", "characteristics": ""},
            "how_to_recreate": {"difficulty": "", "key_points": [], "tips": []}
        },
        "catchphrase": {
            "phrase": {
                "original": "원본 문구",
                "pattern": "패턴 (예: 개웃겨서 {X}낳음)",
                "pronunciation": "발음법",
                "tone": "말투"
            },
            "variations": [{"text": "변형", "context": "맥락"}]
        },
        "sound": {
            "sound": {
                "transcription": "소리 표기",
                "pronunciation_guide": "발음 가이드",
                "tone": "톤",
                "speed": "속도",
                "rhythm": "리듬"
            },
            "how_to_recreate": {"steps": [], "tips": []}
        },
        "character": {
            "character": {
                "appearance": "외형",
                "expression": "표정",
                "pose": "포즈",
                "style": "스타일",
                "signature_elements": []
            },
            "meaning": {"represents": "", "emotion": "", "message": ""}
        },
        "reaction": {
            "reaction": {
                "trigger": "반응 유발 상황",
                "expression": "표정",
                "body_language": "바디랭귀지",
                "emotion": "감정"
            }
        },
        "reference": {
            "original_work": {
                "title": "원작 제목",
                "type": "유형",
                "scene": "장면 설명",
                "dialogue": "대사"
            },
            "parodies": [{"title": "", "description": "", "url": ""}]
        }
    }

    schema = {**base_schema, **type_specific.get(meme_type, {})}

    return f"""
#######################################
#  필수 개수 규칙 (절대 준수!)  #
#######################################

이 규칙을 어기면 출력이 무효 처리됩니다:

1. popular_examples 배열: 최소 3개 객체
2. usage_examples 배열: 최소 5개 객체
3. script_templates 배열: 최소 3개 객체

예시가 부족하면 수집된 정보를 다시 읽고 더 찾으세요.
정말 없으면 유사한 상황을 다양하게 변형해서 생성하세요.

#######################################

## 톤/뉘앙스 결정 (중요!)
수집된 메시지에서 "조롱", "비꼼", "놀림", "비하", "논란", "비판" 키워드가 하나라도 있으면:
→ tone: "조롱/풍자" 사용

## usage_examples 작성 규칙 (매우 중요!)

### 필수: 크롤링한 기사에서 직접 인용
usage_examples는 **크롤링한 뉴스/블로그에서 발견한 실제 사례**만 포함하세요.
- 기사에서 인용된 실제 사용 예시
- 기사에서 언급된 구체적 행동/대사
- 기사에 나온 통계나 조사 결과

### 금지: LLM이 생성한 일반적 상황
다음과 같은 예시는 절대 생성하지 마세요:
- "파티에서 친구들과 함께"
- "온라인 게임에서 사용"
- "SNS에 게시"
- "학교에서 친구들과"
이런 일반적인 상황은 크롤링 데이터가 아닙니다!

### 크롤링 데이터가 부족하면
구체적 사례를 찾지 못했다면:
- "정보 없음"으로 표시
- 기사에서 언급된 **파생 표현/변형**을 예시로 사용
- 기사에서 언급된 **사용 맥락 설명**을 인용

## 원칙
- 수집된 원문 정보만 사용
- 확실하지 않으면 "정보 없음"
- 톤을 임의로 "긍정적"으로 바꾸지 마세요

## JSON 스키마 (배열 개수 주의!)
```json
{json.dumps(schema, ensure_ascii=False, indent=2)}
```

위 스키마에서 "// 배열: 최소 N개" 주석이 있는 필드는 반드시 해당 개수 이상 작성하세요.
JSON만 출력하세요."""


# =============================================================================
# 에이전트 생성
# =============================================================================

def create_agent():
    # 일반 작업용 (빠르고 저렴)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    llm_with_tools = llm.bind_tools(ALL_TOOLS, parallel_tool_calls=True)

    # 추출/정리용 (더 정확함)
    llm_strong = ChatOpenAI(model="gpt-4o", temperature=0)

    def initial_collect_node(state: AgentState) -> AgentState:
        """초기 정보 수집 (분류 전)"""
        meme_name = state["meme_name"]
        parent = state.get("parent", "")
        parent_context = f' "{parent}"' if parent else ""
        parent_note = f"\n\n참고: 이 밈은 '{parent}'에서 파생된 밈입니다." if parent else ""

        prompt = f"""'{meme_name}' 밈의 기본 정보를 수집하세요.{parent_note}

병렬로 다음 도구들을 호출하세요:
- search_namuwiki("{meme_name}")
- search_google("{meme_name}{parent_context} 밈 뜻 유래")

중요: 밈의 정확한 뜻과 유래를 찾아주세요."""

        response = llm_with_tools.invoke(state["messages"] + [HumanMessage(content=prompt)])

        return {
            "messages": [response],
            "phase": "initial"
        }

    def classify_node(state: AgentState) -> AgentState:
        """수집된 정보 기반 밈 유형 분류"""
        messages = state["messages"]

        classify_prompt = """수집된 정보를 바탕으로 이 밈의 유형을 분류하세요.

## 밈 유형
1. video_dance: 영상/댄스 밈 (안무, 챌린지, 동작, 음악)
2. catchphrase: 유행어/어록 밈 (특정 문구, 말투, 텍스트 패턴)
3. sound: 소리/음성 밈 (특정 소리, 발음, 억양)
4. character: 캐릭터/이미지 밈 (캐릭터, 표정, 이미지)
5. reaction: 리액션 밈 (상황 반응, 표정)
6. reference: 레퍼런스 밈 (작품/사건 인용)

중요: 수집된 검색 결과에서 밈의 실제 의미를 확인하고 분류하세요.
- 단어를 자의적으로 해석하지 마세요
- 검색 결과의 정의를 그대로 사용하세요

응답 형식:
MEME_TYPE: [유형]
REASON: [수집된 정보 기반 이유]
DEFINITION: [수집된 정의 원문]"""

        response = llm.invoke(messages + [HumanMessage(content=classify_prompt)])

        content = response.content
        meme_type = "catchphrase"
        for t in MEME_TYPES.keys():
            if f"MEME_TYPE: {t}" in content or f"MEME_TYPE:{t}" in content:
                meme_type = t
                break

        return {
            "messages": [response],
            "meme_type": meme_type,
            "phase": "background"
        }

    def collect_node(state: AgentState) -> AgentState:
        """단계별 데이터 수집"""
        phase = state["phase"]
        meme_name = state["meme_name"]
        meme_type = state.get("meme_type", "catchphrase")
        parent = state.get("parent", "")

        prompt = get_collect_prompt(phase, meme_name, meme_type, parent)
        collect_msg = HumanMessage(content=prompt)

        response = llm_with_tools.invoke(state["messages"] + [collect_msg])

        return {
            "messages": [response],
            "tool_called": True
        }

    def should_continue_initial(state: AgentState) -> str:
        """초기 수집 후 라우팅"""
        messages = state["messages"]
        last_message = messages[-1] if messages else None

        if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools_initial"
        return "classify"

    def should_continue(state: AgentState) -> str:
        """다음 단계 결정"""
        messages = state["messages"]
        last_message = messages[-1] if messages else None

        if not last_message:
            return "collect"

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        return "next_phase"

    def next_phase_node(state: AgentState) -> AgentState:
        """다음 단계로 전환"""
        phase = state["phase"]
        # examples_extract 단계 추가
        phase_order = ["background", "popular_content", "examples_search", "examples_crawl", "examples_extract", "scripts", "finalize"]

        current_idx = phase_order.index(phase) if phase in phase_order else 0
        next_phase = phase_order[min(current_idx + 1, len(phase_order) - 1)]

        return {
            "phase": next_phase,
            "tool_called": False,
            "phase_tool_count": 0  # 새 단계에서 카운트 초기화
        }

    def should_finalize(state: AgentState) -> str:
        """최종 단계 확인"""
        phase = state["phase"]
        if phase == "finalize":
            return "finalize"
        elif phase == "examples_extract":
            return "extract"
        return "collect"

    def extract_node(state: AgentState) -> AgentState:
        """크롤링된 내용에서 구체적 예시 추출 (GPT-4)"""
        meme_name = state["meme_name"]
        parent = state.get("parent", "")
        prompt = get_collect_prompt("examples_extract", meme_name, "", parent)

        response = invoke_with_retry(llm_strong, state["messages"] + [HumanMessage(content=prompt)])

        return {
            "messages": [response],
            "phase": "examples_extract"
        }

    def finalize_node(state: AgentState) -> AgentState:
        """최종 정리 (GPT-4)"""
        meme_type = state.get("meme_type", "catchphrase")
        parent = state.get("parent", "")
        prompt = get_finalize_prompt(meme_type, parent)

        response = invoke_with_retry(llm_strong, state["messages"] + [HumanMessage(content=prompt)])

        return {
            "messages": [response],
            "phase": "done"
        }

    # 그래프 구성
    workflow = StateGraph(AgentState)

    workflow.add_node("initial_collect", initial_collect_node)
    workflow.add_node("tools_initial", ToolNode(ALL_TOOLS))
    workflow.add_node("classify", classify_node)
    workflow.add_node("collect", collect_node)
    workflow.add_node("tools", ToolNode(ALL_TOOLS))
    workflow.add_node("next_phase", next_phase_node)
    workflow.add_node("extract", extract_node)  # GPT-4 추출 노드
    workflow.add_node("finalize", finalize_node)

    # 시작: 먼저 정보 수집
    workflow.set_entry_point("initial_collect")

    workflow.add_conditional_edges("initial_collect", should_continue_initial, {
        "tools_initial": "tools_initial",
        "classify": "classify"
    })

    # 초기 도구 실행 후 분류
    workflow.add_edge("tools_initial", "classify")

    # 분류 후 수집 시작
    workflow.add_edge("classify", "collect")

    workflow.add_conditional_edges("collect", should_continue, {
        "tools": "tools",
        "next_phase": "next_phase"
    })

    workflow.add_edge("tools", "next_phase")

    workflow.add_conditional_edges("next_phase", should_finalize, {
        "finalize": "finalize",
        "extract": "extract",
        "collect": "collect"
    })

    # extract 후 다음 단계로
    workflow.add_edge("extract", "next_phase")

    workflow.add_edge("finalize", END)

    return workflow.compile()


class EnhancedMemeAgent:
    """강화된 밈 데이터 수집 에이전트 (v5)"""

    def __init__(self):
        self.agent = create_agent()

    def collect(self, meme_name: str, parent: str = "", verbose: bool = True) -> dict:
        if verbose:
            print(f"\n{'='*60}")
            print(f"Enhanced Meme Agent v5: {meme_name}")
            if parent:
                print(f"  (Parent: {parent})")
            print(f"{'='*60}\n")

        parent_msg = f" ('{parent}'에서 파생)" if parent else ""
        initial_state = {
            "messages": [
                HumanMessage(content=f"'{meme_name}' 밈{parent_msg} 정보를 수집합니다.")
            ],
            "meme_name": meme_name,
            "meme_type": "",
            "parent": parent,
            "phase": "classify",
            "tool_called": False,
            "phase_tool_count": 0
        }

        final_state = None
        config = {"recursion_limit": 30}

        for state in self.agent.stream(initial_state, config=config):
            if verbose:
                for node_name, node_state in state.items():
                    self._print_state(node_name, node_state)
            final_state = state

        result = self._parse_result(final_state, meme_name, parent)

        if verbose:
            print(f"\n{'='*60}")
            print(f"Complete: {meme_name} (type: {result.get('type', 'unknown')})")
            print(f"{'='*60}\n")

        return result

    def _print_state(self, node_name: str, node_state: dict):
        phase_names = {
            "initial": "[Phase 0] Initial Collection",
            "background": "[Phase 1] Background Story",
            "popular_content": "[Phase 2] Popular Content Analysis",
            "examples_search": "[Phase 3a] Examples Search",
            "examples_crawl": "[Phase 3b] Examples Crawl",
            "examples_extract": "[Phase 3c] Examples Extract (GPT-4)",
            "scripts": "[Phase 4] Script Templates",
            "finalize": "[Phase 5] Finalize (GPT-4)",
            "done": "[Complete]"
        }

        if "phase" in node_state:
            phase = node_state["phase"]
            if phase in phase_names:
                print(f"\n{phase_names[phase]}")

        if "meme_type" in node_state and node_state["meme_type"]:
            print(f"  [Type] {node_state['meme_type']}")

        if "messages" not in node_state:
            return

        for msg in node_state["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                names = [tc["name"] for tc in msg.tool_calls]
                print(f"  [Tools] {', '.join(names)}")
            elif hasattr(msg, "content") and msg.content:
                content = str(msg.content)
                if "MEME_TYPE:" in content:
                    for line in content.split("\n"):
                        if "MEME_TYPE" in line or "REASON" in line:
                            print(f"  {line.strip()}")
                elif "```json" in content:
                    print("  [Output] JSON generated")
                elif node_name == "tools":
                    preview = content[:80].replace("\n", " ")
                    print(f"  [Result] {preview}...")

    def _parse_result(self, final_state: dict, meme_name: str, parent: str = "") -> dict:
        default_result = {
            "name": meme_name,
            "type": "unknown",
            "parent": parent if parent else None,
            "definition": "",
            "collected_at": datetime.now().isoformat(),
            "collection_method": "enhanced_meme_agent_v5"
        }

        if not final_state:
            return default_result

        for node_state in final_state.values():
            if "meme_type" in node_state and node_state["meme_type"]:
                default_result["type"] = node_state["meme_type"]

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
                        parsed["collection_method"] = "enhanced_meme_agent_v5"
                        # parent가 없으면 추가
                        if "parent" not in parsed:
                            parsed["parent"] = parent if parent else None
                        return parsed
                    except json.JSONDecodeError:
                        continue

        return default_result

    def save_result(self, result: dict, output_dir: str = "data/agent_output_v5") -> str:
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
    parser = argparse.ArgumentParser(description="Enhanced Meme Agent v5")
    parser.add_argument("meme_name", help="Name of the meme")
    parser.add_argument("--parent", "-p", default="", help="Parent meme name (for derived memes)")
    parser.add_argument("--output", "-o", default="data/agent_output_v5")
    parser.add_argument("--quiet", "-q", action="store_true")
    args = parser.parse_args()

    agent = EnhancedMemeAgent()
    result = agent.collect(args.meme_name, parent=args.parent, verbose=not args.quiet)
    agent.save_result(result, args.output)

    # Summary
    print(f"\n{'='*60}")
    print(f"Summary: {result.get('name', '')}")
    print(f"Type: {result.get('type', '')}")
    print(f"{'='*60}")

    definition = result.get("definition", "")
    if definition:
        print(f"\nDefinition:\n{definition[:300]}...")

    examples = result.get("usage_examples", [])
    templates = result.get("script_templates", [])
    print(f"\nUsage Examples: {len(examples)}")
    print(f"Script Templates: {len(templates)}")

    bg = result.get("background_story", {})
    if bg.get("why_viral"):
        print(f"\nWhy Viral:\n{bg['why_viral'][:200]}...")


if __name__ == "__main__":
    main()
