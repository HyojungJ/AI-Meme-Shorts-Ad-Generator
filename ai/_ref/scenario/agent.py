import json
from dotenv import load_dotenv

load_dotenv()

from backend.db import ScenarioRepository
from backend.scenario.schema import ScenarioOutput
from backend.scenario.prompts import PromptManager
from backend.scenario.state import get_initial_state
from backend.scenario.graph import get_scenario_graph
from backend.scenario.logging_config import setup_logger

logger = setup_logger(__name__)


class ScenarioAgent:
    def __init__(self, model="gpt-4.1"):
        self.model = model
        self.repo = ScenarioRepository()
        self.prompt_manager = PromptManager()
        self.graph = get_scenario_graph()

    def generate(self, meme_id, save=False, evaluate=False):
        meme = self.repo.get_meme_with_details(meme_id)
        if not meme:
            logger.error(f"밈 ID {meme_id} 없음")
            return None

        logger.info(f"밈: {meme['meme_name']} ({meme.get('meme_type', '')})")

        video = meme.get("video")
        audio = meme.get("audio")
        if video:
            logger.debug("video 데이터: motion_prompt_hint 있음")
        if audio and audio.get("audio_json", {}).get("ssml"):
            logger.debug("audio 데이터: ssml 있음")

        prompt_versions = self.prompt_manager.get_active_version_ids()
        logger.debug(f"프롬프트 버전: {prompt_versions}")

        for version_id in prompt_versions.values():
            if version_id:
                self.prompt_manager.increment_usage(version_id)

        characters = self.repo.get_characters()
        if not characters:
            logger.info("기본 캐릭터 초기화 중...")
            self.repo.init_default_characters()
            characters = self.repo.get_characters()

        initial_state = get_initial_state(
            meme_id=meme_id,
            meme_data=meme,
            characters=characters,
            prompt_versions=prompt_versions,
            save_to_db=save,
            do_evaluate=evaluate,
        )

        logger.info("LangGraph 실행 시작")
        final_state = self.graph.invoke(initial_state)

        scenario_dict = final_state.get("scenario")
        if not scenario_dict:
            logger.error(f"시나리오 생성 실패: {final_state.get('errors', [])}")
            return None

        scenario = ScenarioOutput(**scenario_dict)
        scenario.script_id = final_state.get("script_id")

        quality_score = final_state.get("quality_score")
        retry_count = final_state.get("retry_count", 0)

        if quality_score:
            logger.info(f"품질 점수: {quality_score}/100")
        if retry_count > 0:
            logger.info(f"retry 횟수: {retry_count}")
        if scenario.script_id:
            logger.info(f"DB 저장: script_id={scenario.script_id}")

        return scenario

    def generate_from_selection(self, save=True):
        memes = self.repo.get_selected_memes()
        if not memes:
            logger.warning("선정된 밈이 없습니다.")
            return []

        logger.info(f"선정된 밈 {len(memes)}개 처리")

        results = []
        for meme in memes:
            try:
                scenario = self.generate(meme["meme_id"], save=save)
                if scenario:
                    results.append(scenario)
            except Exception as e:
                logger.error(f"{meme['meme_name']}: {e}")

        return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="시나리오 생성 Agent")
    parser.add_argument("--meme-id", type=int, help="밈 ID")
    parser.add_argument("--from-selection", action="store_true", help="선정된 밈으로 생성")
    parser.add_argument("--save", action="store_true", help="DB에 저장")
    parser.add_argument("--evaluate", action="store_true", help="품질 평가 실행")
    parser.add_argument("--output", "-o", help="결과 저장 경로")
    args = parser.parse_args()

    agent = ScenarioAgent()

    if args.from_selection:
        scenarios = agent.generate_from_selection(save=args.save)
        logger.info(f"{len(scenarios)}개 시나리오 생성 완료")
    elif args.meme_id:
        scenario = agent.generate(args.meme_id, save=args.save, evaluate=args.evaluate)
        if scenario:
            result = scenario.model_dump()
            print(json.dumps(result, ensure_ascii=False, indent=2))
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                logger.info(f"저장: {args.output}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
