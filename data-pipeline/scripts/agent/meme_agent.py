"""
Meme Data Collection Agent (v3)

개선사항:
1. 병렬 도구 호출 - 독립적인 검색을 동시에 실행
2. 정보 충분성 체크 - 필수 필드 수집 여부 검증
3. YouTube 자막 추출 - 타임스탬프 포함 스크립트
4. 상세 안무 스키마 - 시간순 동작 시퀀스
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Annotated, TypedDict
from pydantic import BaseModel, Field

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from tools import ALL_TOOLS

load_dotenv()


class CollectedInfo(BaseModel):
    """수집된 정보 추적용 스키마"""
    definition: bool = Field(default=False)
    origin: bool = Field(default=False)
    original_source: bool = Field(default=False)
    script: bool = Field(default=False)
    choreography: bool = Field(default=False)
    audio_elements: bool = Field(default=False)

    def get_missing(self) -> list[str]:
        """누락된 필드 목록 반환"""
        missing = []
        field_names = {
            "definition": "밈의 정의",
            "origin": "밈의 유래",
            "original_source": "원본 출처",
            "script": "자막/대사",
            "choreography": "동작/안무",
            "audio_elements": "오디오 요소"
        }
        for field, label in field_names.items():
            if not getattr(self, field):
                missing.append(f"{field} ({label})")
        return missing

    def is_complete(self) -> bool:
        """필수 정보 수집 완료 여부"""
        return self.definition and self.origin and (self.script or self.choreography)

    def completion_rate(self) -> float:
        """수집 완료율 (0.0 ~ 1.0)"""
        fields = [
            self.definition, self.origin, self.original_source,
            self.script, self.choreography, self.audio_elements
        ]
        return sum(fields) / len(fields)


class AgentState(TypedDict):
    """에이전트 상태"""
    messages: Annotated[list, add_messages]
    meme_name: str
    collected_info: dict
    iteration: int
    max_iterations: int


SYSTEM_PROMPT = """당신은 밈 데이터 수집 전문가입니다.
주어진 밈에 대해 캐릭터가 밈을 따라할 수 있도록 필요한 모든 정보를 수집합니다.

## 수집 체크리스트

1. definition: 밈의 정의/뜻
2. origin: 유래 (언제, 어디서, 누가, 어떻게)
3. original_source: 원본 영상/이미지 URL과 제작자
4. script: 자막/대사 (타임스탬프 포함)
5. choreography: 시간순 동작/안무 시퀀스
6. audio_elements: 배경음악, 효과음, 음성 특징

## 병렬 검색 전략

첫 번째 라운드 (동시 실행):
- search_namuwiki: 기본 정보 수집
- search_google: "밈이름 밈 뜻 유래" 검색
- search_youtube: "밈이름 원본" 검색

두 번째 라운드 (원본 영상 분석):
- 원본 영상 URL 발견시:
  - get_youtube_info: 영상 정보 확인
  - get_youtube_transcript: 자막/스크립트 추출 (타임스탬프 포함)
- 동작 정보 부족시 search_google: "밈이름 챌린지 안무"

세 번째 라운드 (보완):
- 추가 맥락 필요시 crawl_webpage: 관련 기사 크롤링

## 중요: 자막 추출

원본 영상 URL을 찾으면 반드시 get_youtube_transcript를 호출하세요.
자막에서 정확한 대사와 타이밍을 추출할 수 있습니다.

## 완료 조건

다음 조건을 만족하면 "COLLECTION_COMPLETE"를 선언:
1. definition, origin 수집 완료
2. 원본 영상 자막 추출 완료 (또는 자막 없음 확인)
3. 최소 2개 이상의 소스에서 정보 확인

부족한 정보가 있어도 {max_iterations}회 반복 후에는 현재까지 수집된 정보로 완료합니다.
"""


CHECKLIST_PROMPT = """
현재 수집 상태:
{checklist}

부족한 정보: {missing}
완료율: {rate}%

{instruction}
"""


FINAL_OUTPUT_PROMPT = """수집된 모든 정보를 바탕으로 최종 데이터를 JSON으로 정리하세요.
캐릭터가 밈을 따라할 수 있도록 상세하게 작성하세요.

```json
{
    "name": "밈 이름",
    "definition": "밈의 정의 (2-3문장)",
    "origin": "밈의 유래 상세 설명",
    "original_source": {
        "url": "원본 영상/이미지 URL",
        "platform": "플랫폼명",
        "creator": "원작자/채널명",
        "duration": "영상 길이 (예: 0:15)"
    },
    "script": [
        {
            "timestamp": "00:00-00:02",
            "text": "대사 또는 가사",
            "voice_style": "음성 특징 (예: 외국인 억양, 또박또박)"
        }
    ],
    "choreography": [
        {
            "sequence": 1,
            "timestamp": "00:00-00:02",
            "description": "전체 동작 설명",
            "body": {
                "head": "머리/시선 동작",
                "face": "표정",
                "arms": "팔 동작",
                "hands": "손 동작",
                "body": "상체/몸통 동작",
                "legs": "다리/하체 동작"
            }
        }
    ],
    "audio": {
        "music": "배경음악 정보 (곡명, BPM 등)",
        "effects": ["효과음1", "효과음2"],
        "voice_characteristics": "음성 특징 (억양, 톤, 속도)"
    },
    "visual_style": {
        "camera": "카메라 앵글/구도",
        "editing": "편집 스타일",
        "text_overlay": "자막/텍스트 스타일"
    },
    "meme_essence": {
        "core_emotion": "핵심 감정",
        "timing": "핵심 타이밍/포인트",
        "what_makes_it_funny": "왜 웃긴지 설명"
    },
    "usage": {
        "when_to_use": ["사용 상황1", "사용 상황2"],
        "variations": ["변형1", "변형2"]
    },
    "source_urls": ["출처 URL1", "출처 URL2"],
    "keywords": ["키워드1", "키워드2"],
    "category": "밈 유형"
}
```

주의사항:
1. script와 choreography는 타임스탬프 순서대로 정렬
2. 자막에서 추출한 대사는 원문 그대로 사용
3. 동작은 캐릭터가 따라할 수 있도록 구체적으로 기술
4. 수집하지 못한 정보는 빈 문자열/배열로 표시

JSON만 출력하세요.
"""


def analyze_collected_info(messages: list) -> CollectedInfo:
    """메시지에서 수집된 정보 분석"""
    info = CollectedInfo()
    full_text = ""

    for msg in messages:
        if hasattr(msg, "content") and msg.content:
            full_text += str(msg.content).lower()

    # 키워드 기반 수집 여부 판단
    if any(kw in full_text for kw in ["정의", "뜻", "의미", "밈은", "~입니다"]):
        info.definition = True
    if any(kw in full_text for kw in ["유래", "시작", "기원", "만들어", "처음", "업로드"]):
        info.origin = True
    if any(kw in full_text for kw in ["youtube.com", "youtu.be", "원본", "영상 정보"]):
        info.original_source = True
    if any(kw in full_text for kw in ["스크립트", "자막", "[00:", "[01:", "transcript"]):
        info.script = True
    if any(kw in full_text for kw in ["동작", "안무", "춤", "손을", "팔을", "몸을"]):
        info.choreography = True
    if any(kw in full_text for kw in ["음악", "비트", "효과음", "멜로디", "bpm"]):
        info.audio_elements = True

    return info


def create_agent():
    """에이전트 그래프 생성"""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    llm_with_tools = llm.bind_tools(ALL_TOOLS, parallel_tool_calls=True)

    def should_continue(state: AgentState) -> str:
        """다음 단계 결정"""
        messages = state["messages"]
        last_message = messages[-1]

        # 도구 호출이 있으면 도구 실행
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        # 최대 반복 횟수 도달
        if state["iteration"] >= state["max_iterations"]:
            return "finalize"

        # 완료 선언 확인
        if hasattr(last_message, "content"):
            if "COLLECTION_COMPLETE" in str(last_message.content):
                return "finalize"

        # 정보 충분성 체크
        info = analyze_collected_info(messages)
        if info.is_complete() and state["iteration"] >= 2:
            return "finalize"

        return "finalize"

    def agent_node(state: AgentState) -> AgentState:
        """에이전트 노드 - LLM 호출"""
        messages = state["messages"]
        iteration = state["iteration"]

        # 첫 호출시 시스템 프롬프트 추가
        if iteration == 0:
            system_msg = SYSTEM_PROMPT.format(max_iterations=state["max_iterations"])
            messages = [SystemMessage(content=system_msg)] + messages

        # 2회차 이후 체크리스트 추가
        elif iteration >= 1:
            info = analyze_collected_info(messages)
            missing = info.get_missing()
            rate = int(info.completion_rate() * 100)

            checklist = "\n".join([
                f"- definition: {'O' if info.definition else 'X'}",
                f"- origin: {'O' if info.origin else 'X'}",
                f"- original_source: {'O' if info.original_source else 'X'}",
                f"- script: {'O' if info.script else 'X'}",
                f"- choreography: {'O' if info.choreography else 'X'}",
                f"- audio_elements: {'O' if info.audio_elements else 'X'}",
            ])

            if info.is_complete():
                instruction = "필수 정보가 수집되었습니다. COLLECTION_COMPLETE를 선언하세요."
            elif iteration >= state["max_iterations"] - 1:
                instruction = "마지막 라운드입니다. 현재까지 수집된 정보로 완료하세요."
            else:
                instruction = f"부족한 정보를 추가로 검색하세요: {', '.join(missing[:3])}"

            check_msg = CHECKLIST_PROMPT.format(
                checklist=checklist,
                missing=missing if missing else "없음",
                rate=rate,
                instruction=instruction
            )
            messages = messages + [HumanMessage(content=check_msg)]

        response = llm_with_tools.invoke(messages)

        return {
            "messages": [response],
            "iteration": iteration + 1,
            "collected_info": analyze_collected_info(messages + [response]).model_dump()
        }

    def finalize_node(state: AgentState) -> AgentState:
        """최종 정리 노드"""
        messages = state["messages"]
        finalize_messages = messages + [HumanMessage(content=FINAL_OUTPUT_PROMPT)]

        llm_final = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        response = llm_final.invoke(finalize_messages)

        return {"messages": [response]}

    # 그래프 구성
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(ALL_TOOLS))
    workflow.add_node("finalize", finalize_node)

    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "finalize": "finalize"})
    workflow.add_edge("tools", "agent")
    workflow.add_edge("finalize", END)

    return workflow.compile()


class MemeCollectorAgent:
    """밈 데이터 수집 에이전트"""

    def __init__(self, max_iterations: int = 6):
        self.agent = create_agent()
        self.max_iterations = max_iterations

    def collect(self, meme_name: str, verbose: bool = True) -> dict:
        """밈 데이터 수집 실행"""
        if verbose:
            print(f"\n{'='*60}")
            print(f"Meme Data Collection: {meme_name}")
            print(f"{'='*60}\n")

        initial_state = {
            "messages": [
                HumanMessage(content=f"""'{meme_name}' 밈 정보를 수집해주세요.

첫 번째 라운드에서 다음 도구들을 동시에 호출하세요:
1. search_namuwiki("{meme_name}")
2. search_google("{meme_name} 밈 뜻 유래")
3. search_youtube("{meme_name} 원본")""")
            ],
            "meme_name": meme_name,
            "collected_info": CollectedInfo().model_dump(),
            "iteration": 0,
            "max_iterations": self.max_iterations
        }

        final_state = None
        for state in self.agent.stream(initial_state):
            if verbose:
                for node_name, node_state in state.items():
                    if "messages" in node_state:
                        for msg in node_state["messages"]:
                            self._print_message(node_name, msg)
                    if "collected_info" in node_state:
                        info = CollectedInfo(**node_state["collected_info"])
                        rate = int(info.completion_rate() * 100)
                        if rate > 0:
                            print(f"[Progress] {rate}%")
            final_state = state

        result = self._parse_result(final_state, meme_name)

        if verbose:
            print(f"\n{'='*60}")
            print(f"Collection Complete: {meme_name}")
            print(f"{'='*60}\n")

        return result

    def _print_message(self, node_name: str, message):
        """메시지 출력"""
        if hasattr(message, "tool_calls") and message.tool_calls:
            tool_names = [tc["name"] for tc in message.tool_calls]
            if len(tool_names) > 1:
                print(f"[Parallel Tools] {', '.join(tool_names)}")
            for tc in message.tool_calls:
                print(f"  - {tc['name']}: {str(tc['args'])[:60]}...")

        elif hasattr(message, "content") and message.content:
            content = str(message.content)
            if node_name == "tools":
                print(f"[Tool Result] {content[:80]}...")
            elif "COLLECTION_COMPLETE" in content:
                print(f"[Done] Generating final JSON...")
            elif "```json" in content:
                print(f"[Output] JSON generated")
            else:
                if len(content) > 120:
                    content = content[:120] + "..."
                print(f"[Agent] {content}")

    def _parse_result(self, final_state: dict, meme_name: str) -> dict:
        """결과 파싱"""
        default_result = {
            "name": meme_name,
            "definition": "",
            "origin": "",
            "original_source": {"url": "", "platform": "", "creator": "", "duration": ""},
            "script": [],
            "choreography": [],
            "audio": {"music": "", "effects": [], "voice_characteristics": ""},
            "visual_style": {"camera": "", "editing": "", "text_overlay": ""},
            "meme_essence": {"core_emotion": "", "timing": "", "what_makes_it_funny": ""},
            "usage": {"when_to_use": [], "variations": []},
            "source_urls": [],
            "keywords": [],
            "category": "",
            "collected_at": datetime.now().isoformat(),
            "collection_method": "langchain_agent_v3"
        }

        if not final_state:
            return default_result

        for node_state in final_state.values():
            if "messages" not in node_state:
                continue
            for msg in node_state["messages"]:
                if not hasattr(msg, "content"):
                    continue
                content = str(msg.content)

                # JSON 추출
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
                        parsed["collection_method"] = "langchain_agent_v2"
                        return parsed
                    except json.JSONDecodeError:
                        continue

        return default_result

    def save_result(self, result: dict, output_dir: str = "data/agent_output") -> str:
        """결과 저장"""
        import re
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        safe_name = re.sub(r'[\\/*?:"<>|]', "_", result.get("name", "unknown"))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"agent_meme_{safe_name}_{timestamp}.json"
        filepath = output_path / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"Saved: {filepath}")
        return str(filepath)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Meme Data Collection Agent v3")
    parser.add_argument("meme_name", help="Name of the meme to collect")
    parser.add_argument("--max-iter", "-m", type=int, default=6, help="Max iterations")
    parser.add_argument("--output", "-o", default="data/agent_output", help="Output directory")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress progress output")
    args = parser.parse_args()

    agent = MemeCollectorAgent(max_iterations=args.max_iter)
    result = agent.collect(args.meme_name, verbose=not args.quiet)
    agent.save_result(result, args.output)

    # Summary
    print(f"\n{'='*50}")
    print(f"Summary: {result.get('name', '')}")
    print(f"{'='*50}")
    print(f"Definition: {result.get('definition', '')[:80]}...")
    print(f"Origin: {result.get('origin', '')[:80]}...")

    script = result.get("script", [])
    if script:
        print(f"Script: {len(script)} entries")

    choreo = result.get("choreography", [])
    if choreo:
        print(f"Choreography: {len(choreo)} sequences")

    source = result.get("original_source", {})
    if source.get("url"):
        print(f"Original: {source.get('platform', '')} - {source.get('creator', '')}")


if __name__ == "__main__":
    main()
