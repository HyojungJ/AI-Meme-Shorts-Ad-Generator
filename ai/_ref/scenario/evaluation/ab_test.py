import json
import argparse

from typing import List, Dict, Any
from datetime import datetime
from statistics import mean, stdev

from backend.db import ScenarioRepository
from backend.scenario.agent import ScenarioAgent
from backend.scenario.evaluation import ScenarioEvaluator
from backend.scenario.prompts import PromptManager


class ABTester:
    def __init__(self):
        self.repo = ScenarioRepository()
        self.prompt_manager = PromptManager()
        self.evaluator = ScenarioEvaluator()

    def run_test(
        self,
        version_a: str,
        version_b: str,
        meme_ids: List[int],
        prompt_name: str = "skeleton_prompt",
        save: bool = False
    ) -> Dict[str, Any]:
        print(f"\n{'='*70}")
        print(f"A/B 테스트: {prompt_name}")
        print(f"  Version A: {version_a}")
        print(f"  Version B: {version_b}")
        print(f"  테스트 밈: {len(meme_ids)}개")
        print(f"{'='*70}")

        # A 버전 테스트
        print(f"\n[Phase 1] Version {version_a} 테스트")
        print("-" * 50)
        self._activate_version(prompt_name, version_a)
        results_a = self._run_tests(meme_ids, f"A ({version_a})", save)

        # B 버전 테스트
        print(f"\n[Phase 2] Version {version_b} 테스트")
        print("-" * 50)
        self._activate_version(prompt_name, version_b)
        results_b = self._run_tests(meme_ids, f"B ({version_b})", save)

        # 비교 분석
        comparison = self._compare_results(results_a, results_b, version_a, version_b)

        return {
            "test_info": {
                "prompt_name": prompt_name,
                "version_a": version_a,
                "version_b": version_b,
                "meme_ids": meme_ids,
                "tested_at": datetime.now().isoformat()
            },
            "version_a_results": results_a,
            "version_b_results": results_b,
            "comparison": comparison
        }

    def _activate_version(self, prompt_name: str, version: str):
        success = self.prompt_manager.activate_version(prompt_name, version)
        if not success:
            raise ValueError(f"버전 활성화 실패: {prompt_name} {version}")

    def _run_tests(
        self,
        meme_ids: List[int],
        label: str,
        save: bool
    ) -> List[Dict[str, Any]]:
        results = []

        for i, meme_id in enumerate(meme_ids, 1):
            meme = self.repo.get_meme_with_details(meme_id)
            if not meme:
                print(f"  [{i}/{len(meme_ids)}] 밈 ID {meme_id} 없음 - 스킵")
                continue

            print(f"  [{i}/{len(meme_ids)}] {meme['meme_name']}...", end=" ")

            try:
                agent = ScenarioAgent()
                scenario = agent.generate(meme_id, save=save, evaluate=False)

                if scenario:
                    eval_result = self.evaluator.evaluate(scenario, meme)
                    results.append({
                        "meme_id": meme_id,
                        "meme_name": meme["meme_name"],
                        "score": eval_result.total_score,
                        "breakdown": eval_result.breakdown,
                        "success": True
                    })
                    print(f"점수: {eval_result.total_score}")
                else:
                    results.append({
                        "meme_id": meme_id,
                        "meme_name": meme["meme_name"],
                        "score": 0,
                        "success": False,
                        "error": "시나리오 생성 실패"
                    })
                    print("실패")

            except Exception as e:
                results.append({
                    "meme_id": meme_id,
                    "meme_name": meme.get("meme_name", "unknown"),
                    "score": 0,
                    "success": False,
                    "error": str(e)
                })
                print(f"에러: {e}")

        return results

    def _compare_results(
        self,
        results_a: List[Dict],
        results_b: List[Dict],
        version_a: str,
        version_b: str
    ) -> Dict[str, Any]:
        scores_a = [r["score"] for r in results_a if r.get("success")]
        scores_b = [r["score"] for r in results_b if r.get("success")]

        avg_a = mean(scores_a) if scores_a else 0
        avg_b = mean(scores_b) if scores_b else 0
        std_a = stdev(scores_a) if len(scores_a) > 1 else 0
        std_b = stdev(scores_b) if len(scores_b) > 1 else 0

        improvement = avg_b - avg_a
        improvement_pct = (improvement / avg_a * 100) if avg_a > 0 else 0

        # 승자 결정
        if abs(improvement) < 3:
            winner = "tie"
            winner_reason = "점수 차이가 3점 미만으로 통계적으로 유의미하지 않음"
        elif improvement > 0:
            winner = version_b
            winner_reason = f"{version_b}가 평균 {improvement:.1f}점 ({improvement_pct:.1f}%) 높음"
        else:
            winner = version_a
            winner_reason = f"{version_a}가 평균 {-improvement:.1f}점 ({-improvement_pct:.1f}%) 높음"

        # 항목별 비교
        breakdown_comparison = {}
        if scores_a and scores_b:
            categories = ["structure", "character", "meme_accuracy", "motion_quality", "naturalness"]
            for cat in categories:
                cat_scores_a = [r["breakdown"].get(cat, 0) for r in results_a if r.get("success")]
                cat_scores_b = [r["breakdown"].get(cat, 0) for r in results_b if r.get("success")]
                if cat_scores_a and cat_scores_b:
                    breakdown_comparison[cat] = {
                        "a": mean(cat_scores_a),
                        "b": mean(cat_scores_b),
                        "diff": mean(cat_scores_b) - mean(cat_scores_a)
                    }

        comparison = {
            "version_a": {
                "version": version_a,
                "avg_score": avg_a,
                "std_dev": std_a,
                "success_count": len(scores_a),
                "scores": scores_a
            },
            "version_b": {
                "version": version_b,
                "avg_score": avg_b,
                "std_dev": std_b,
                "success_count": len(scores_b),
                "scores": scores_b
            },
            "improvement": improvement,
            "improvement_pct": improvement_pct,
            "winner": winner,
            "winner_reason": winner_reason,
            "breakdown_comparison": breakdown_comparison
        }

        # 결과 출력
        print(f"\n{'='*70}")
        print("A/B 테스트 결과")
        print(f"{'='*70}")
        print(f"\nVersion {version_a}:")
        print(f"  평균 점수: {avg_a:.1f} (표준편차: {std_a:.1f})")
        print(f"  성공: {len(scores_a)}개")

        print(f"\nVersion {version_b}:")
        print(f"  평균 점수: {avg_b:.1f} (표준편차: {std_b:.1f})")
        print(f"  성공: {len(scores_b)}개")

        print(f"\n개선 효과: {improvement:+.1f}점 ({improvement_pct:+.1f}%)")
        print(f"\n결론: {winner_reason}")

        if breakdown_comparison:
            print("\n항목별 비교:")
            for cat, vals in breakdown_comparison.items():
                diff_str = f"{vals['diff']:+.1f}" if vals['diff'] != 0 else "0.0"
                print(f"  {cat}: A={vals['a']:.1f} vs B={vals['b']:.1f} ({diff_str})")

        return comparison


def main():
    parser = argparse.ArgumentParser(description="프롬프트 A/B 테스트")
    parser.add_argument("--version-a", type=str, required=True, help="A 버전 (예: v1.0)")
    parser.add_argument("--version-b", type=str, required=True, help="B 버전 (예: v1.1)")
    parser.add_argument("--meme-ids", type=str, default="2,3,6", help="밈 ID 목록 (콤마 구분)")
    parser.add_argument("--prompt-name", type=str, default="skeleton_prompt",
                       help="테스트할 프롬프트 (skeleton_prompt, dialogue_prompt, finalizer_prompt)")
    parser.add_argument("--save", action="store_true", help="결과 DB 저장")
    parser.add_argument("--output", "-o", help="결과 저장 경로")
    args = parser.parse_args()

    meme_ids = [int(x.strip()) for x in args.meme_ids.split(",")]

    tester = ABTester()
    result = tester.run_test(
        version_a=args.version_a,
        version_b=args.version_b,
        meme_ids=meme_ids,
        prompt_name=args.prompt_name,
        save=args.save
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n결과 저장: {args.output}")


if __name__ == "__main__":
    main()
