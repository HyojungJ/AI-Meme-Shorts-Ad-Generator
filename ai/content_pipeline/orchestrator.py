from dataclasses import dataclass

from common import get_connection, MemeRepository, ScriptRepository
from content_pipeline.schema import PipelineInput, ScenarioOutput, VideoOutput


@dataclass
class PipelineResult:
    scenario: ScenarioOutput
    video: VideoOutput = None
    error: str = None


class ContentPipeline:
    def __init__(self):
        # 시나리오/영상 그래프는 각 팀이 구현 후 연결
        self.scenario_graph = None
        self.video_graph = None

    def run(self, meme_id: int, character_ids: list[int] = None) -> PipelineResult:
        # 1. DB에서 밈 데이터 로드
        with get_connection() as conn:
            meme_repo = MemeRepository(conn)
            meme = meme_repo.get_with_details(meme_id)

        if not meme:
            return PipelineResult(scenario=None, error=f"Meme {meme_id} not found")

        # 2. PipelineInput 생성
        pipeline_input = self._build_input(meme, character_ids)

        # 3. 시나리오 생성
        scenario = self._run_scenario(pipeline_input)
        if not scenario:
            return PipelineResult(scenario=None, error="Scenario generation failed")

        # 4. 영상 생성
        video = self._run_video(scenario)

        return PipelineResult(scenario=scenario, video=video)

    def _build_input(self, meme: dict, character_ids: list[int]) -> PipelineInput:
        # TODO: character_ids로 캐릭터 정보 로드
        return PipelineInput(
            meme_id=meme["meme_id"],
            meme_name=meme["name"],
            definition=meme.get("definition", ""),
            meme_type=meme.get("meme_type", "quotable"),
            key_phrase=meme.get("key_phrase"),
        )

    def _run_scenario(self, input: PipelineInput) -> ScenarioOutput | None:
        if not self.scenario_graph:
            # TODO: 시나리오 팀 구현 후 연결
            return None

        result = self.scenario_graph.invoke({"input": input})
        return result.get("output")

    def _run_video(self, scenario: ScenarioOutput) -> VideoOutput | None:
        if not self.video_graph:
            # TODO: 영상 팀 구현 후 연결
            return None

        result = self.video_graph.invoke({"scenario": scenario})
        return result.get("output")
