import json
import time
import uuid
from datetime import datetime
from pathlib import Path

from meme_collector.deep_research.graph import compile_graph
from meme_collector.infra.checkpointer import get_checkpointer
from meme_collector.infra.tracing import setup_tracing
from meme_collector.state import get_initial_state


class MemeAgent:
    def __init__(self, use_postgres=False, enable_tracing=True):
        if enable_tracing:
            setup_tracing("meme-agent")

        checkpointer = get_checkpointer(use_postgres)
        self._graph = compile_graph(checkpointer)

    def process(self, meme_name: str) -> dict:
        start_time = time.time()
        thread_id = str(uuid.uuid4())

        result = {
            "meta": {"meme_name": meme_name, "thread_id": thread_id, "started_at": datetime.now().isoformat()},
            "meme_output": None,
            "verification": {},
            "errors": [],
        }

        try:
            final_state = {}
            for state in self._graph.stream(get_initial_state(meme_name), config={"configurable": {"thread_id": thread_id}, "recursion_limit": 50}):
                for node_name, node_state in state.items():
                    # supervisor는 Command를 반환하므로 dict인지 확인
                    if not isinstance(node_state, dict):
                        continue
                    # Check for "errors" (list) and "error" (string)
                    if node_state.get("errors"):
                        result["errors"].extend(node_state["errors"])
                    if node_state.get("error"):
                        result["errors"].append(f"[{node_name}] {node_state['error']}")
                    # Check for nested errors in collected_info (e.g., video_analysis.error)
                    collected = node_state.get("collected_info", {})
                    if isinstance(collected, dict):
                        video_err = collected.get("video_analysis", {}).get("error")
                        if video_err:
                            result["errors"].append(f"[video_analysis] {video_err}")
                    for k, v in node_state.items():
                        if v is not None:
                            final_state[k] = v

            result["meme_output"] = final_state.get("meme_output")
            result["meta"]["meme_id"] = final_state.get("meme_id")
            result["verification"] = {
                "score": final_state.get("verification_score", 0),
                "decision": final_state.get("verification_decision"),
                "attempts": final_state.get("attempt", 0),
            }

        except Exception as e:
            result["errors"].append(f"[graph] {type(e).__name__}: {e}")

        # Deduplicate errors while preserving order
        result["errors"] = list(dict.fromkeys(result["errors"]))
        result["meta"]["processing_time_seconds"] = round(time.time() - start_time, 2)
        result["meta"]["success"] = len(result["errors"]) == 0 and result["meme_output"] is not None

        return result

    def save_result(self, result: dict, output_dir="data/agent_output") -> str:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        meme_name = result.get("meta", {}).get("meme_name", "unknown")
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in meme_name)
        filepath = output_path / f"meme_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return str(filepath)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="MemeAgent")
    parser.add_argument("meme_name")
    parser.add_argument("--output", "-o", default="data/agent_output")
    parser.add_argument("--no-trace", action="store_true")
    args = parser.parse_args()

    agent = MemeAgent(enable_tracing=not args.no_trace)
    result = agent.process(args.meme_name)

    if result.get("meme_output"):
        o = result["meme_output"]
        print(f"\nName: {o.get('name')}")
        print(f"Type: {o.get('meme_type')}")
        print(f"Motion: {o.get('motion_prompt', '')[:80]}...")

    v = result.get("verification", {})
    print(f"\nScore: {v.get('score')} | Decision: {v.get('decision')}")
    print(f"Time: {result['meta'].get('processing_time_seconds')}s")

    print(f"Saved: {agent.save_result(result, args.output)}")


if __name__ == "__main__":
    main()
