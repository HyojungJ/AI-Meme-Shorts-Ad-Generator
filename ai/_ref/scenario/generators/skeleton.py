import os

from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

from backend.scenario.config import config
from backend.scenario.prompts import get_skeleton_prompt
from backend.scenario.schema import SkeletonOutput

load_dotenv()


class SkeletonGenerator:
    def __init__(self, model: str = None):
        self.model = model or config.skeleton_model
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=config.skeleton_temperature,
            api_key=os.getenv("OPENAI_API_KEY"),
        ).with_structured_output(SkeletonOutput)

    def generate(self, meme_data: Dict[str, Any], characters: list) -> SkeletonOutput:
        prompt = get_skeleton_prompt(meme_data, characters)
        messages = [
            SystemMessage(content="당신은 숏폼 영상 시나리오 작가입니다."),
            HumanMessage(content=prompt)
        ]
        return self.llm.invoke(messages)


def main():
    """1단계 테스트"""
    import argparse
    from backend.db import ScenarioRepository

    parser = argparse.ArgumentParser(description="시나리오 골격 생성")
    parser.add_argument("--meme-id", type=int, required=True, help="밈 ID")
    args = parser.parse_args()

    repo = ScenarioRepository()

    # 밈 데이터 조회
    meme = repo.get_meme_with_details(args.meme_id)
    if not meme:
        print(f"[ERROR] 밈 ID {args.meme_id} 없음")
        return

    # 캐릭터 조회
    characters = repo.get_characters()
    if not characters:
        repo.init_default_characters()
        characters = repo.get_characters()

    # 골격 생성
    generator = SkeletonGenerator()
    skeleton = generator.generate(meme, characters)

    print("=== 시나리오 골격 ===")
    print(json.dumps(skeleton.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
