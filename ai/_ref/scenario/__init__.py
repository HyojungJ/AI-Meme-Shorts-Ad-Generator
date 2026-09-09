"""
Scenario Generation Module

3단계 시나리오 생성 파이프라인

구조:
- generators/     # 생성 모듈 (skeleton, dialogue, finalizer)
- prompts/        # 프롬프트 관리 (templates, manager)
- evaluation/     # 평가/테스트 (evaluator, test_prompt, ab_test)
"""

from backend.scenario.agent import ScenarioAgent
from backend.scenario.schema import ScenarioInput, ScenarioOutput, Scene, Beat
from backend.scenario.generators import SkeletonGenerator, DialogueGenerator, Finalizer
from backend.scenario.prompts import PromptManager
from backend.scenario.evaluation import ScenarioEvaluator, EvaluationResult

__all__ = [
    # Main
    "ScenarioAgent",
    # Schema
    "ScenarioInput",
    "ScenarioOutput",
    "Scene",
    "Beat",
    # Generators
    "SkeletonGenerator",
    "DialogueGenerator",
    "Finalizer",
    # Prompts
    "PromptManager",
    # Evaluation
    "ScenarioEvaluator",
    "EvaluationResult",
]
