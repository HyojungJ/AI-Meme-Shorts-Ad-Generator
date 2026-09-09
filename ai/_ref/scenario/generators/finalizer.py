import os

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

from backend.scenario.config import config
from backend.scenario.prompts import get_finalizer_prompt
from backend.scenario.schema import ScenarioOutput, Scene, Beat, MemeReference

load_dotenv()


class Finalizer:
    def __init__(self, model: str = None):
        self.model = model or config.finalizer_model
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=config.finalizer_temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
        ).with_structured_output(ScenarioOutput)

    def finalize(
        self,
        skeleton: Dict[str, Any],
        dialogues: Dict[str, List[Dict[str, str]]],
        meme_data: Dict[str, Any]
    ) -> ScenarioOutput:
        prompt = get_finalizer_prompt(skeleton, dialogues, meme_data)
        messages = [
            SystemMessage(content="당신은 시나리오 편집자입니다."),
            HumanMessage(content=prompt)
        ]
        result: ScenarioOutput = self.llm.invoke(messages)
        result.meme_id = meme_data.get("meme_id")
        result.description = f"'{meme_data.get('meme_name', '')}' 밈 시나리오: {result.title}"
        self._inject_meme_reference(result, meme_data)
        return result

    def _inject_meme_reference(self, scenario: ScenarioOutput, meme_data: Dict[str, Any]):
        for scene in scenario.scenes:
            if scene.scene_type == "meme" and not scene.meme_reference:
                scene.meme_reference = MemeReference(
                    meme_id=meme_data.get("meme_id"),
                    meme_name=meme_data.get("meme_name", ""),
                    meme_type=meme_data.get("meme_type", "quotable"),
                    key_phrase=meme_data.get("key_phrase")
                )


def main():
    """3단계 테스트 (전체 파이프라인)"""
    import argparse
    from backend.db import ScenarioRepository
    from backend.scenario.skeleton_generator import SkeletonGenerator
    from backend.scenario.dialogue_generator import DialogueGenerator

    parser = argparse.ArgumentParser(description="시나리오 생성 (전체)")
    parser.add_argument("--meme-id", type=int, required=True, help="밈 ID")
    parser.add_argument("--save", action="store_true", help="DB에 저장")
    args = parser.parse_args()

    repo = ScenarioRepository()

    # 밈 데이터 조회
    meme = repo.get_meme_with_details(args.meme_id)
    if not meme:
        print(f"[ERROR] 밈 ID {args.meme_id} 없음")
        return

    print(f"밈: {meme['meme_name']} ({meme.get('meme_type', '')})")

    # 캐릭터 조회
    characters = repo.get_characters()
    if not characters:
        repo.init_default_characters()
        characters = repo.get_characters()

    # 1단계: 골격 생성
    print("\n[1단계] 골격 생성 중...")
    skeleton_gen = SkeletonGenerator()
    skeleton = skeleton_gen.generate(meme, characters)
    print(f"  → 제목: {skeleton.title}")

    # 2단계: 대사 생성
    print("\n[2단계] 대사 생성 중...")
    dialogue_gen = DialogueGenerator()
    dialogues = dialogue_gen.generate_all(skeleton.model_dump(), characters, meme)
    for char, texts in dialogues.items():
        print(f"  → {char}: {len(texts)}개 대사")

    # 3단계: 최종화
    print("\n[3단계] 최종 시나리오 완성 중...")
    finalizer = Finalizer()
    scenario = finalizer.finalize(skeleton.model_dump(), dialogues, meme)

    print("\n=== 완성된 시나리오 ===")
    print(json.dumps(scenario.model_dump(), ensure_ascii=False, indent=2))

    # DB 저장
    if args.save:
        script_id = repo.save_script(scenario.to_db_format())
        print(f"\n[DB] 저장 완료: script_id = {script_id}")


if __name__ == "__main__":
    main()
