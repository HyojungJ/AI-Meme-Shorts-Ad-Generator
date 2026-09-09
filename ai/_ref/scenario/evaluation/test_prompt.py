import json
import argparse

from typing import List, Dict, Any
from datetime import datetime

from backend.db import ScenarioRepository
from backend.scenario.agent import ScenarioAgent
from backend.scenario.evaluation import ScenarioEvaluator
from backend.scenario.prompts import PromptManager


def test_single(
    meme_id: int,
    prompt_version: str = None,
    save: bool = False,
    verbose: bool = True
) -> Dict[str, Any]:
    repo = ScenarioRepository()
    agent = ScenarioAgent()
    evaluator = ScenarioEvaluator()
    prompt_manager = PromptManager()

    # 밈 데이터 조회
    meme = repo.get_meme_with_details(meme_id)
    if not meme:
        print(f"[ERROR] 밈 ID {meme_id} 없음")
        return None

    if verbose:
        print(f"\n{'='*60}")
        print(f"테스트: {meme['meme_name']} (meme_id={meme_id})")
        print(f"유형: {meme.get('meme_type', 'unknown')}")
        print(f"{'='*60}")

    # 프롬프트 버전 확인
    version_ids = prompt_manager.get_active_version_ids()
    if verbose:
        print(f"\n사용 프롬프트 버전: {version_ids}")

    # 시나리오 생성
    scenario = agent.generate(meme_id, save=save, evaluate=False)
    if not scenario:
        return None

    # 평가
    eval_result = evaluator.evaluate(scenario, meme)

    if verbose:
        print(f"\n{'='*40}")
        print("평가 결과")
        print(f"{'='*40}")
        print(f"총점: {eval_result.total_score}/100")
        print("\n세부 점수:")
        for name, score in eval_result.breakdown.items():
            print(f"  {name}: {score}/20")

        if eval_result.suggestions:
            print("\n개선 제안:")
            for s in eval_result.suggestions:
                print(f"  - {s}")

    return {
        "meme_id": meme_id,
        "meme_name": meme["meme_name"],
        "meme_type": meme.get("meme_type"),
        "prompt_version_ids": version_ids,
        "scenario": scenario.model_dump() if scenario else None,
        "evaluation": {
            "total_score": eval_result.total_score,
            "breakdown": eval_result.breakdown,
            "feedback": eval_result.feedback,
            "suggestions": eval_result.suggestions
        },
        "tested_at": datetime.now().isoformat()
    }


def test_batch(
    meme_ids: List[int],
    save: bool = False,
    output_path: str = None
) -> List[Dict[str, Any]]:
    results = []

    print(f"\n배치 테스트: {len(meme_ids)}개 밈")
    print("=" * 60)

    for i, meme_id in enumerate(meme_ids, 1):
        print(f"\n[{i}/{len(meme_ids)}] 테스트 중...")
        try:
            result = test_single(meme_id, save=save, verbose=True)
            if result:
                results.append(result)
        except Exception as e:
            print(f"[ERROR] meme_id={meme_id}: {e}")
            results.append({
                "meme_id": meme_id,
                "error": str(e)
            })

    # 요약
    print("\n" + "=" * 60)
    print("테스트 요약")
    print("=" * 60)

    successful = [r for r in results if "evaluation" in r]
    if successful:
        avg_score = sum(r["evaluation"]["total_score"] for r in successful) / len(successful)
        print(f"성공: {len(successful)}/{len(meme_ids)}")
        print(f"평균 점수: {avg_score:.1f}/100")

        print("\n개별 점수:")
        for r in successful:
            print(f"  {r['meme_name']}: {r['evaluation']['total_score']}/100")

    # 결과 저장
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "tested_at": datetime.now().isoformat(),
                "meme_count": len(meme_ids),
                "avg_score": avg_score if successful else 0,
                "results": results
            }, f, ensure_ascii=False, indent=2)
        print(f"\n결과 저장: {output_path}")

    return results


def main():
    parser = argparse.ArgumentParser(description="프롬프트 테스트")
    parser.add_argument("--meme-id", type=int, help="단일 밈 ID")
    parser.add_argument("--meme-ids", type=str, help="밈 ID 목록 (콤마 구분)")
    parser.add_argument("--prompt-version", type=str, help="특정 프롬프트 버전")
    parser.add_argument("--save", action="store_true", help="DB에 저장")
    parser.add_argument("--output", "-o", help="결과 저장 경로")
    args = parser.parse_args()

    if args.meme_id:
        result = test_single(
            args.meme_id,
            prompt_version=args.prompt_version,
            save=args.save
        )
        if result and args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n결과 저장: {args.output}")

    elif args.meme_ids:
        meme_ids = [int(x.strip()) for x in args.meme_ids.split(",")]
        test_batch(meme_ids, save=args.save, output_path=args.output)

    else:
        # 기본 테스트 세트 (나니가 스키, 랫댄스, 스키비디 토일렛)
        print("기본 테스트 세트 실행 (meme_id: 2, 3, 6)")
        test_batch([2, 3, 6], save=args.save, output_path=args.output)


if __name__ == "__main__":
    main()
