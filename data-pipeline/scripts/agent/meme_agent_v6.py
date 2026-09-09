"""
Meme Data Collection Agent (v6) - Simplified Schema

v5 대비 변경:
- 간소화된 출력 스키마 (밈 DB + 정적 게시물 DB 전용)
- 영상/음성 분석 관련 필드 제거 (별도 파이프라인에서 처리)
- script_templates 제거 (생성 단계에서 처리)
- 불필요한 phase 제거
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
    """Rate limit 오류 시 재시도"""
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
    return llm.invoke(messages)


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    meme_name: str
    parent: str  # 부모 밈
    phase: str
    tool_called: bool


# =============================================================================
# 프롬프트
# =============================================================================

def get_collect_prompt(phase: str, meme_name: str, parent: str = "") -> str:
    """단계별 수집 프롬프트"""
    parent_context = f' "{parent}"' if parent else ""
    parent_note = f"\n\n참고: 이 밈은 '{parent}'에서 파생된 밈입니다." if parent else ""

    if phase == "basic":
        return f"""'{meme_name}' 밈의 기본 정보를 수집하세요.{parent_note}

병렬로 다음 도구들을 호출하세요:
- search_namuwiki("{meme_name}")
- search_google("{meme_name}{parent_context} 밈 뜻 유래 원본")

필수 수집:
1. 정확한 정의 (밈이 무엇인지)
2. 출처 (어디서 시작됐는지)
3. 제작자/원작자
4. 시작 시점
5. 유행 이유

중요: 검색 결과에서 밈의 정확한 뜻과 유래를 찾아 원문 그대로 기록하세요."""

    elif phase == "posts":
        return f"""'{meme_name}' 밈이 사용된 게시물/콘텐츠를 찾으세요.{parent_note}

병렬로 다음 도구들을 호출하세요:
- search_google("{meme_name}{parent_context} 밈 사용 예시")
- search_google("site:youtube.com {meme_name}{parent_context}")
- search_google("site:twitter.com OR site:x.com {meme_name}{parent_context}")

필수 수집:
1. 게시물 제목
2. URL
3. 밈이 어떻게 활용되었는지 (한 문장 설명)

최소 5개 이상의 게시물 정보를 수집하세요."""

    elif phase == "crawl":
        return f"""이전 검색 결과에서 뉴스/블로그 URL을 크롤링하세요.

## 크롤링 우선순위
1순위: 뉴스 기사 (hankyung.com, donga.com, mt.co.kr 등)
2순위: 블로그 (blog.naver.com, tistory.com, brunch.co.kr 등)

## 금지
- 커뮤니티 이미지 게시물 (ruliweb, dcinside, dogdrip)

이전 메시지에서 찾은 URL 중 2-3개를 crawl_webpage로 크롤링하세요."""

    return ""


def get_finalize_prompt(parent: str = "") -> str:
    """최종 정리 프롬프트 - 간소화된 스키마"""

    schema = {
        "name": "밈 이름",
        "parent": parent if parent else None,
        "definition": "밈에 대한 상세한 정의 (3-5문장). 무엇인지, 어떤 의미인지, 어떻게 사용되는지 포함.",
        "origin": {
            "source": "출처 (예: 유튜브 채널명, 웹툰명, 방송명)",
            "creator": "제작자/원작자",
            "date": "시작 시점 (예: 2024년 11월)",
            "platform": "플랫폼 (예: YouTube, TikTok, 웹툰)"
        },
        "is_video": "boolean - 영상 밈인 경우 true (댄스, 챌린지, 영상 클립)",
        "is_audio": "boolean - 음성/소리 밈인 경우 true (특정 발음, 음성, 노래)",
        "keywords": ["검색 키워드 3-5개"],
        "popular_posts": [
            {
                "title": "게시물/콘텐츠 제목",
                "url": "URL",
                "meme_usage": "이 게시물에서 밈이 어떻게 활용되었는지 (한 문장)"
            }
        ]
    }

    return f"""수집된 정보를 바탕으로 JSON을 생성하세요.

## 필수 규칙

1. **popular_posts**: 최소 5개 이상
   - 실제 검색/크롤링에서 찾은 URL만 사용
   - URL을 찾지 못했으면 빈 배열 []

2. **is_video / is_audio 판단 기준**:
   - is_video: 댄스, 챌린지, 영상 클립, 안무가 핵심인 밈
   - is_audio: 특정 발음, 음성, 노래, 소리가 핵심인 밈
   - 둘 다 아니면 false (텍스트/이미지 밈)

3. **definition**: 수집된 정보에서 정의를 그대로 인용
   - 추측하지 말고 검색 결과의 정의 사용

## JSON 스키마
```json
{json.dumps(schema, ensure_ascii=False, indent=2)}
```

JSON만 출력하세요."""


# =============================================================================
# 에이전트 생성
# =============================================================================

def create_agent():
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    llm_with_tools = llm.bind_tools(ALL_TOOLS, parallel_tool_calls=True)
    llm_strong = ChatOpenAI(model="gpt-4o", temperature=0)

    def collect_node(state: AgentState) -> AgentState:
        """데이터 수집"""
        phase = state["phase"]
        meme_name = state["meme_name"]
        parent = state.get("parent", "")

        prompt = get_collect_prompt(phase, meme_name, parent)
        response = llm_with_tools.invoke(state["messages"] + [HumanMessage(content=prompt)])

        return {
            "messages": [response],
            "tool_called": True
        }

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
        phase_order = ["basic", "posts", "crawl", "finalize"]

        current_idx = phase_order.index(phase) if phase in phase_order else 0
        next_phase = phase_order[min(current_idx + 1, len(phase_order) - 1)]

        return {
            "phase": next_phase,
            "tool_called": False
        }

    def should_finalize(state: AgentState) -> str:
        """최종 단계 확인"""
        if state["phase"] == "finalize":
            return "finalize"
        return "collect"

    def finalize_node(state: AgentState) -> AgentState:
        """최종 정리 (GPT-4)"""
        parent = state.get("parent", "")
        prompt = get_finalize_prompt(parent)

        response = invoke_with_retry(llm_strong, state["messages"] + [HumanMessage(content=prompt)])

        return {
            "messages": [response],
            "phase": "done"
        }

    # 그래프 구성
    workflow = StateGraph(AgentState)

    workflow.add_node("collect", collect_node)
    workflow.add_node("tools", ToolNode(ALL_TOOLS))
    workflow.add_node("next_phase", next_phase_node)
    workflow.add_node("finalize", finalize_node)

    workflow.set_entry_point("collect")

    workflow.add_conditional_edges("collect", should_continue, {
        "tools": "tools",
        "next_phase": "next_phase"
    })

    workflow.add_edge("tools", "next_phase")

    workflow.add_conditional_edges("next_phase", should_finalize, {
        "finalize": "finalize",
        "collect": "collect"
    })

    workflow.add_edge("finalize", END)

    return workflow.compile()


class MemeAgent:
    """밈 데이터 수집 에이전트 (v6) - 간소화된 스키마"""

    def __init__(self):
        self.agent = create_agent()

    def collect(self, meme_name: str, parent: str = "", verbose: bool = True) -> dict:
        if verbose:
            print(f"\n{'='*60}")
            print(f"Meme Agent v6: {meme_name}")
            if parent:
                print(f"  Parent: {parent}")
            print(f"{'='*60}\n")

        parent_msg = f" (← {parent})" if parent else ""
        initial_state = {
            "messages": [
                HumanMessage(content=f"'{meme_name}'{parent_msg} 밈 정보를 수집합니다.")
            ],
            "meme_name": meme_name,
            "parent": parent,
            "phase": "basic",
            "tool_called": False
        }

        final_state = None
        config = {"recursion_limit": 20}

        for state in self.agent.stream(initial_state, config=config):
            if verbose:
                for node_name, node_state in state.items():
                    self._print_state(node_name, node_state)
            final_state = state

        result = self._parse_result(final_state, meme_name, parent)

        if verbose:
            print(f"\n{'='*60}")
            print(f"Complete: {meme_name}")
            print(f"  is_video: {result.get('is_video', False)}")
            print(f"  is_audio: {result.get('is_audio', False)}")
            print(f"  posts: {len(result.get('popular_posts', []))}")
            print(f"{'='*60}\n")

        return result

    def _print_state(self, node_name: str, node_state: dict):
        phase_names = {
            "basic": "[Phase 1] Basic Info",
            "posts": "[Phase 2] Popular Posts",
            "crawl": "[Phase 3] Crawl Details",
            "finalize": "[Phase 4] Finalize",
            "done": "[Complete]"
        }

        if "phase" in node_state:
            phase = node_state["phase"]
            if phase in phase_names:
                print(f"\n{phase_names[phase]}")

        if "messages" not in node_state:
            return

        for msg in node_state["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                names = [tc["name"] for tc in msg.tool_calls]
                print(f"  [Tools] {', '.join(names)}")
            elif hasattr(msg, "content") and msg.content:
                content = str(msg.content)
                if "```json" in content:
                    print("  [Output] JSON generated")
                elif node_name == "tools":
                    preview = content[:80].replace("\n", " ")
                    print(f"  [Result] {preview}...")

    def _parse_result(self, final_state: dict, meme_name: str, parent: str = "") -> dict:
        default_result = {
            "name": meme_name,
            "parent": parent if parent else None,
            "definition": "",
            "origin": {},
            "is_video": False,
            "is_audio": False,
            "keywords": [],
            "popular_posts": [],
            "collected_at": datetime.now().isoformat(),
            "agent_version": "v6"
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
                        parsed["agent_version"] = "v6"
                        if "parent" not in parsed:
                            parsed["parent"] = parent if parent else None
                        return parsed
                    except json.JSONDecodeError:
                        continue

        return default_result

    def save_result(self, result: dict, output_dir: str = "data/agent_output_v6") -> str:
        import re
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        safe_name = re.sub(r'[\\/*?:"<>|]', "_", result.get("name", "unknown"))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"meme_{safe_name}_{timestamp}.json"
        filepath = output_path / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"Saved: {filepath}")
        return str(filepath)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Meme Agent v6 - Simplified Schema")
    parser.add_argument("meme_name", help="Name of the meme")
    parser.add_argument("--parent", "-p", default="", help="Parent meme name")
    parser.add_argument("--output", "-o", default="data/agent_output_v6")
    parser.add_argument("--quiet", "-q", action="store_true")
    args = parser.parse_args()

    agent = MemeAgent()
    result = agent.collect(args.meme_name, parent=args.parent, verbose=not args.quiet)
    agent.save_result(result, args.output)

    # Summary
    print(f"\nDefinition: {result.get('definition', '')[:200]}...")
    print(f"Origin: {result.get('origin', {}).get('source', 'Unknown')}")
    print(f"Posts found: {len(result.get('popular_posts', []))}")


if __name__ == "__main__":
    main()
