import json
import os

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

from backend.db import get_connection
from backend.scenario.config import config
from backend.scenario.schema import ScenarioOutput, LLMEvaluationResponse, EvaluationResult, EvaluationBreakdown

load_dotenv()


REQUIRED_SCENES = ["hook", "setup", "buildup", "meme", "punchline"]

CHARACTER_SETTINGS = {
    "부장": {
        "description": "50대 중년 남성, 밈에 진심으로 빠삭함",
        "personality": ["밈을 시전할 때 100% 자신감", "사원에게 자랑하고 싶어함", "밈 발동 시 과몰입"],
        "speech_style": "격식체 + 아재 감성"
    },
    "사원": {
        "description": "20대 후반, 밈에 관심 없거나 이미 질림",
        "personality": ["부장의 갑작스러운 행동에 당황", "속으로 '왜 저러시지...'", "점점 같이 웃거나 따라함"],
        "speech_style": "캐주얼, MZ 말투"
    }
}


class ScenarioEvaluator:
    def __init__(self, model: str = None):
        self.model = model or config.evaluator_model
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=config.evaluator_temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
        ).with_structured_output(LLMEvaluationResponse)
        self.conn = get_connection()

    def evaluate(self, scenario: ScenarioOutput, meme_data: Dict[str, Any]) -> EvaluationResult:
        structure_score = self._evaluate_structure(scenario)
        character_result = self._evaluate_character(scenario)
        meme_result = self._evaluate_meme_accuracy(scenario, meme_data)
        motion_result = self._evaluate_motion_quality(scenario, meme_data)
        naturalness_result = self._evaluate_naturalness(scenario)

        breakdown = EvaluationBreakdown(
            structure=structure_score,
            character=character_result["score"],
            meme_accuracy=meme_result["score"],
            motion_quality=motion_result["score"],
            naturalness=naturalness_result["score"]
        )

        suggestions = []
        feedback_parts = []
        for name, result in [("character", character_result), ("meme_accuracy", meme_result),
                            ("motion_quality", motion_result), ("naturalness", naturalness_result)]:
            if result.get("reasoning"):
                feedback_parts.append(f"{name}: {result['reasoning']}")
            suggestions.extend(result.get("suggestions", []))

        return EvaluationResult(
            total_score=sum([structure_score, character_result["score"], meme_result["score"],
                           motion_result["score"], naturalness_result["score"]]),
            breakdown=breakdown,
            feedback="\n".join(feedback_parts) if feedback_parts else "양호",
            suggestions=suggestions
        )

    def _evaluate_structure(self, scenario: ScenarioOutput) -> float:
        scene_types = [s.scene_type for s in scenario.scenes]
        scene_scores = {"hook": 4, "setup": 3, "buildup": 3, "meme": 6, "punchline": 4}
        score = sum(scene_scores.get(st, 0) for st in scene_types if st in scene_scores)
        expected_order = ["hook", "setup", "buildup", "meme", "punchline"]
        actual = [s for s in expected_order if s in scene_types]
        if len(actual) > 1:
            indices = [scene_types.index(s) for s in actual if s in scene_types]
            if indices != sorted(indices):
                score = max(0, score - 2)
        return score

    def _evaluate_character(self, scenario: ScenarioOutput) -> Dict[str, Any]:
        dialogues = []
        for scene in scenario.scenes:
            for beat in scene.beats:
                if beat.type == "dialogue" and beat.text:
                    dialogues.append({"scene": scene.scene_type, "character": beat.character, "text": beat.text})

        char_info = "\n".join([
            f"### {name}\n- 설명: {s['description']}\n- 성격: {', '.join(s['personality'])}\n- 말투: {s['speech_style']}"
            for name, s in CHARACTER_SETTINGS.items()
        ])

        prompt = f"""대사의 캐릭터 일관성 평가 (20점)

## 캐릭터 설정
{char_info}

## 대사
{json.dumps(dialogues, ensure_ascii=False)}

## 평가기준
1. 부장 적합성 (8점): 밈에 진심, 자신감, 아재감성
2. 사원 적합성 (8점): 당황, MZ말투, 츤데레 변화
3. 케미 (4점): 대비 명확, 티키타카"""

        return self._call_llm(prompt)

    def _evaluate_meme_accuracy(self, scenario: ScenarioOutput, meme_data: Dict[str, Any]) -> Dict[str, Any]:
        meme_type = meme_data.get("meme_type", "quotable")
        key_phrase = meme_data.get("key_phrase", "")
        scenario_text = json.dumps(scenario.model_dump(), ensure_ascii=False)

        auto_score = 0
        if meme_type == "quotable" and key_phrase:
            auto_score = 8 if key_phrase in scenario_text else (4 if any(k in scenario_text for k in key_phrase.split()) else 0)
        elif meme_type == "performable":
            auto_score = 8

        meme_scenes = [s.model_dump() for s in scenario.scenes if s.scene_type == "meme"]
        prompt = f"""밈 활용 적절성 평가 (12점)

## 밈정보
- 이름: {meme_data.get('meme_name')}
- 유형: {meme_type}
- 핵심: {key_phrase or '동작'}

## meme씬
{json.dumps(meme_scenes, ensure_ascii=False)}

## 평가기준
1. 핵심요소 반영 (5점)
2. 부장 밈시전 (4점)
3. 유머포인트 (3점)"""

        llm_result = self._call_llm(prompt)
        return {
            "score": auto_score + min(llm_result["score"], 12),
            "reasoning": f"자동({auto_score}/8)+LLM({llm_result['score']}/12): {llm_result.get('reasoning', '')}",
            "suggestions": llm_result.get("suggestions", [])
        }

    def _evaluate_motion_quality(self, scenario: ScenarioOutput, meme_data: Dict[str, Any]) -> Dict[str, Any]:
        motions = [{"scene": s.scene_type, "character": b.character, "prompt": b.motion_prompt}
                   for s in scenario.scenes for b in s.beats if b.type == "action" and b.motion_prompt]

        if not motions:
            return {"score": 5, "reasoning": "motion_prompt 없음", "suggestions": ["action beat 추가 고려"]}

        video = meme_data.get("video", {})
        prompt = f"""motion_prompt 품질 평가 (20점)

## motion목록
{json.dumps(motions, ensure_ascii=False)}

## 참조힌트: {video.get('motion_prompt_hint', '없음')}

## 평가기준
1. 동작상세도 (8점): 신체부위별, 표정, 순서
2. AI호환성 (6점): 영어, 명확한 동사
3. 밈동작반영 (6점)"""

        return self._call_llm(prompt)

    def _evaluate_naturalness(self, scenario: ScenarioOutput) -> Dict[str, Any]:
        summary = [{"scene_type": s.scene_type, "beats": [f"[{b.character}] {b.text or '(action)'}" for b in s.beats]}
                   for s in scenario.scenes]

        prompt = f"""자연스러움 평가 (20점)

## 시나리오
{json.dumps(summary, ensure_ascii=False)}

## 기대흐름: hook→setup→buildup→meme→punchline

## 평가기준
1. 5단흐름 (8점)
2. 대사자연스러움 (7점)
3. 타이밍 (5점)"""

        return self._call_llm(prompt)

    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        try:
            messages = [
                SystemMessage(content="숏폼 시나리오 평가 전문가. 공정하게 평가."),
                HumanMessage(content=prompt)
            ]
            result: LLMEvaluationResponse = self.llm.invoke(messages)
            return result.model_dump()
        except Exception as e:
            return {"score": 0, "reasoning": f"오류: {e}", "suggestions": []}

    def save_evaluation(self, script_id: int, result: EvaluationResult):
        evaluation_json = {"breakdown": result.breakdown.model_dump(), "feedback": result.feedback, "suggestions": result.suggestions}
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE script SET quality_score = %s, validation_result = %s WHERE script_id = %s",
                (result.total_score, json.dumps(evaluation_json), script_id)
            )
            self.conn.commit()


def main():
    import argparse
    from backend.db import ScenarioRepository
    from backend.scenario.schema import Scene, Beat

    parser = argparse.ArgumentParser(description="시나리오 품질 평가")
    parser.add_argument("--script-id", type=int, help="평가할 스크립트 ID")
    parser.add_argument("--save", action="store_true", help="평가 결과 저장")
    args = parser.parse_args()

    if not args.script_id:
        parser.print_help()
        return

    repo = ScenarioRepository()
    evaluator = ScenarioEvaluator()

    with get_connection().cursor() as cur:
        cur.execute("SELECT meme_id, title, description, total_duration, scenes, hashtags FROM script WHERE script_id = %s", (args.script_id,))
        row = cur.fetchone()

    if not row:
        print(f"스크립트 {args.script_id} 없음")
        return

    meme_id, title, description, total_duration, scenes_data, hashtags = row
    scenes = [Scene(scene_number=s.get("scene_number", 1), scene_type=s.get("scene_type", "hook"),
                    beats=[Beat(**b) for b in s.get("beats", [])]) for s in scenes_data]

    scenario = ScenarioOutput(meme_id=meme_id, title=title, description=description,
                              total_duration=total_duration, scenes=scenes, hashtags=hashtags or [])

    meme_data = repo.get_meme_with_details(meme_id)
    result = evaluator.evaluate(scenario, meme_data)

    print(f"\n총점: {result.total_score}/100")
    print(f"세부: {result.breakdown.model_dump()}")
    print(f"피드백:\n{result.feedback}")

    if args.save:
        evaluator.save_evaluation(args.script_id, result)
        print(f"저장 완료: script_id={args.script_id}")


if __name__ == "__main__":
    main()
