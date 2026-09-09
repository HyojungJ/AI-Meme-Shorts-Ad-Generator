import json
import re
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from scripts.agent.state import AgentV8State, get_initial_state, get_next_phase
from scripts.agent.tools_v8 import ALL_TOOLS
from scripts.agent.nodes.crawl_examples import parse_crawled_sources
from scripts.agent.nodes.finalize import parse_final_result
from scripts.agent.config import get_config
from scripts.utils.logging import AgentLogger, setup_file_logging

load_dotenv()


class MemeAgentV8:
    def __init__(self, verbose=True, skip_video_analysis=False, enable_file_logging=False):
        self.verbose = verbose
        self.skip_video_analysis = skip_video_analysis
        self.logger = AgentLogger("meme_agent_v8", verbose)
        self.errors = []

        if enable_file_logging:
            log_file = setup_file_logging(self.logger.logger, "logs", "agent_v8")
            self.logger.info(f"File logging enabled: {log_file}")

        self.agent = self._create_agent()

    def _create_agent(self):
        cfg = get_config()
        llm = ChatOpenAI(model=cfg.primary_model, temperature=0)
        llm_with_tools = llm.bind_tools(ALL_TOOLS, parallel_tool_calls=True)
        llm_strong = ChatOpenAI(model=cfg.strong_model, temperature=0)

        def collect_node(state: AgentV8State) -> AgentV8State:
            from scripts.agent.nodes.definition import definition_node
            from scripts.agent.nodes.risk_info import risk_info_node
            from scripts.agent.nodes.usage_search import usage_search_node
            from scripts.agent.nodes.crawl_examples import crawl_examples_node

            phase = state["phase"]
            if phase == "definition":
                return definition_node(state, llm_with_tools, llm)
            elif phase == "risk_info":
                return risk_info_node(state, llm_with_tools)
            elif phase == "usage_search":
                return usage_search_node(state, llm_with_tools)
            elif phase == "crawl_examples":
                return crawl_examples_node(state, llm_with_tools)
            return state

        skip_video = self.skip_video_analysis

        def direct_node(state: AgentV8State) -> AgentV8State:
            from scripts.agent.nodes.youtube_search import youtube_search_node
            from scripts.agent.nodes.video_analysis import video_analysis_node
            from scripts.agent.nodes.meme_typing import meme_typing_node
            from scripts.agent.nodes.audio_analysis import audio_analysis_node
            from scripts.agent.nodes.ssml_generation import ssml_generation_node

            phase = state["phase"]
            if phase == "youtube_search":
                return youtube_search_node(state)
            elif phase == "video_analysis":
                return video_analysis_node(state, skip=skip_video)
            elif phase == "meme_typing":
                return meme_typing_node(state, llm)
            elif phase == "audio_analysis":
                return audio_analysis_node(state)
            elif phase == "ssml_generation":
                return ssml_generation_node(state)
            return state

        def finalize_node(state: AgentV8State) -> AgentV8State:
            from scripts.agent.nodes.finalize import finalize_node as _finalize
            return _finalize(state, llm_strong)

        def next_phase_node(state: AgentV8State) -> AgentV8State:
            phase = state["phase"]
            messages = state["messages"]
            crawled_sources = state.get("crawled_sources", [])
            if phase == "crawl_examples":
                crawled_sources = parse_crawled_sources(messages)
            needs_audio = state.get("needs_audio", False)
            next_phase = get_next_phase(phase, needs_audio)
            return {
                "messages": messages,
                "phase": next_phase,
                "tool_called": False,
                "crawled_sources": crawled_sources,
            }

        def should_continue(state: AgentV8State) -> str:
            messages = state["messages"]
            last_message = messages[-1] if messages else None
            if not last_message:
                return "next_phase"
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"
            return "next_phase"

        def route_phase(state: AgentV8State) -> str:
            phase = state["phase"]
            if phase in ["definition", "risk_info", "usage_search", "crawl_examples"]:
                return "collect"
            if phase in ["youtube_search", "video_analysis", "meme_typing",
                         "audio_analysis", "ssml_generation"]:
                return "direct"
            if phase == "finalize":
                return "finalize"
            if phase == "done":
                return "end"
            return "finalize"

        workflow = StateGraph(AgentV8State)
        workflow.add_node("collect", collect_node)
        workflow.add_node("tools", ToolNode(ALL_TOOLS))
        workflow.add_node("direct", direct_node)
        workflow.add_node("next_phase", next_phase_node)
        workflow.add_node("finalize", finalize_node)

        workflow.set_entry_point("collect")
        workflow.add_conditional_edges("collect", should_continue, {
            "tools": "tools", "next_phase": "next_phase"
        })
        workflow.add_edge("tools", "next_phase")
        workflow.add_edge("direct", "next_phase")
        workflow.add_conditional_edges("next_phase", route_phase, {
            "collect": "collect", "direct": "direct", "finalize": "finalize", "end": END
        })
        workflow.add_edge("finalize", END)
        return workflow.compile()

    def process(self, meme_name, save_to_db=False):
        start_time = time.time()
        self.errors = []
        self.logger.info(f"Processing meme: {meme_name}")

        if self.verbose:
            print(f"\n{'='*60}\nMeme Agent v8: {meme_name}\n{'='*60}\n")

        try:
            initial_state = get_initial_state(meme_name)
            accumulated_state = {}
            current_phase = "definition"

            for state in self.agent.stream(initial_state, config={"recursion_limit": 50}):
                for node_name, node_state in state.items():
                    if "phase" in node_state and node_state["phase"] != current_phase:
                        if current_phase != "definition":
                            self.logger.phase_end(current_phase, success=True)
                        current_phase = node_state["phase"]
                        if current_phase != "done":
                            self.logger.phase_start(current_phase, meme_name)

                    if "errors" in node_state and node_state["errors"]:
                        for err in node_state["errors"]:
                            if err not in self.errors:
                                self.errors.append(err)
                                self.logger.warning(f"Node error: {err}")

                    if self.verbose:
                        self._print_state(node_name, node_state)

                    for key, value in node_state.items():
                        if value is not None and value != "" and value != [] and value != {}:
                            accumulated_state[key] = value
                        elif key not in accumulated_state:
                            accumulated_state[key] = value

            if current_phase != "done":
                self.logger.phase_end(current_phase, success=True)

            result = parse_final_result({"merged": accumulated_state}, meme_name)
            result["meta"]["has_errors"] = bool(self.errors)
            if self.errors:
                result["meta"]["errors"] = self.errors

            elapsed = time.time() - start_time
            result["meta"]["processing_time_seconds"] = round(elapsed, 2)

            if self.verbose:
                self._print_summary(result)
            self.logger.info(f"Processing completed in {elapsed:.2f}s")

            if save_to_db:
                self._save_to_db(result)
            return result

        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"Processing failed after {elapsed:.2f}s", e)
            self.errors.append(str(e))
            return {
                "meta": {
                    "agent_version": "v8",
                    "processed_at": datetime.now().isoformat(),
                    "has_errors": True,
                    "errors": self.errors,
                    "processing_time_seconds": round(elapsed, 2)
                },
                "basic_info": {"name": meme_name},
                "error": str(e)
            }

    def _save_to_db(self, result):
        try:
            from scripts.db import MemeRepository
            repo = MemeRepository()
            meme_id = repo.save_agent_result(result)
            self.logger.data_collected("DB", details=f"Saved meme_id: {meme_id}")
            if self.verbose:
                print(f"  [DB] Saved meme_id: {meme_id}")
            if meme_id and "meta" in result:
                result["meta"]["meme_id"] = meme_id
            return meme_id
        except Exception as e:
            self.logger.error("DB save failed", e)
            self.errors.append(f"DB save error: {e}")
            if self.verbose:
                print(f"  [DB] Save failed: {e}")
            return None

    def _print_state(self, node_name, node_state):
        phase_names = {
            "definition": "[Phase 1] Definition & Origin",
            "risk_info": "[Phase 2] Risk Information",
            "usage_search": "[Phase 3] Usage Examples Search",
            "crawl_examples": "[Phase 4] Crawl Examples",
            "youtube_search": "[Phase 5] YouTube Search",
            "video_analysis": "[Phase 6] Video Analysis (Gemini)",
            "meme_typing": "[Phase 7] Meme Type Classification",
            "audio_analysis": "[Phase 8] Audio Analysis",
            "ssml_generation": "[Phase 9] SSML Generation",
            "finalize": "[Phase 10] Finalize",
            "done": "[Complete]"
        }

        if "phase" in node_state:
            phase = node_state["phase"]
            if phase in phase_names:
                print(f"\n{phase_names[phase]}")

        # 수집된 데이터 출력
        if "youtube_shorts" in node_state and node_state["youtube_shorts"]:
            count = len(node_state["youtube_shorts"])
            print(f"  [YouTube] {count} shorts found")

        if "video_analysis" in node_state:
            va = node_state["video_analysis"]
            if va.get("enabled"):
                print(f"  [Video] motion_prompt generated")

        if "meme_type" in node_state and node_state["meme_type"]:
            mtype = node_state["meme_type"]
            kp = node_state.get("key_phrase", "")
            print(f"  [Type] {mtype}" + (f" - '{kp}'" if kp else ""))

        if "audio_analysis" in node_state:
            aa = node_state["audio_analysis"]
            if aa.get("enabled"):
                print(f"  [Audio] prosody analyzed")

        if "crawled_sources" in node_state:
            sources = node_state["crawled_sources"]
            if sources:
                print(f"  [Crawled] {len(sources)} sources")

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

    def _print_summary(self, result: Dict[str, Any]):
        """결과 요약 출력"""
        print(f"\n{'='*60}")
        print("Summary")
        print(f"{'='*60}")

        basic = result.get("basic_info", {})
        print(f"  Name: {basic.get('name', 'N/A')}")
        print(f"  Definition: {basic.get('definition', '')[:100]}...")

        classification = result.get("meme_classification", {})
        print(f"  Type: {classification.get('meme_type', 'N/A')}")
        if classification.get("key_phrase"):
            print(f"  Key Phrase: {classification.get('key_phrase')}")

        risk = result.get("risk_info", {})
        print(f"  Risk Level: {risk.get('risk_level', 'N/A')}")

        shorts = result.get("youtube_shorts", [])
        print(f"  YouTube Shorts: {len(shorts)}")

        video = result.get("video_analysis", {})
        if video.get("enabled"):
            print(f"  Video Analysis: Yes")

        audio = result.get("audio_analysis", {})
        if audio.get("enabled"):
            print(f"  Audio Analysis: Yes")
            if audio.get("ssml"):
                print(f"  SSML: Generated")

        print(f"{'='*60}\n")

    def save_result(self, result, output_dir="data/agent_output"):
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        name = result.get("basic_info", {}).get("name", "unknown")
        safe_name = re.sub(r'[\\/*?:"<>|]', "_", name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"meme_{safe_name}_{timestamp}.json"
        filepath = output_path / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        if self.verbose:
            print(f"Saved: {filepath}")

        return str(filepath)


# Backward compatibility
MemeAgent = MemeAgentV8


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Meme Agent v8 - Unified Pipeline")
    parser.add_argument("meme_name", help="Name of the meme")
    parser.add_argument("--output", "-o", default="data/agent_output")
    parser.add_argument("--quiet", "-q", action="store_true")
    parser.add_argument("--db", action="store_true", help="Save result to database")
    parser.add_argument("--skip-video", action="store_true", help="Skip Gemini video analysis")
    parser.add_argument("--log-file", action="store_true", help="Enable file logging")
    args = parser.parse_args()

    agent = MemeAgentV8(
        verbose=not args.quiet,
        skip_video_analysis=args.skip_video,
        enable_file_logging=args.log_file
    )
    result = agent.process(args.meme_name, save_to_db=args.db)
    agent.save_result(result, args.output)


if __name__ == "__main__":
    main()
