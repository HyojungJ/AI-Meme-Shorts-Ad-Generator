import os
from dataclasses import dataclass


@dataclass
class ScenarioConfig:
    skeleton_model: str = "gpt-4.1"
    dialogue_model: str = "gpt-4o-mini-2024-07-18"
    finalizer_model: str = "gpt-4.1"
    evaluator_model: str = "gpt-4o-mini-2024-07-18"
    skeleton_temperature: float = 0.7
    dialogue_temperature: float = 0.8
    finalizer_temperature: float = 0.5
    evaluator_temperature: float = 0.0
    eeve_load_in_4bit: bool = True
    eeve_device_map: str = "auto"
    max_retries: int = 2
    retry_threshold: float = 60.0

    def __post_init__(self):
        self.skeleton_model = os.getenv("SKELETON_MODEL", self.skeleton_model)
        self.dialogue_model = os.getenv("DIALOGUE_MODEL", self.dialogue_model)
        self.finalizer_model = os.getenv("FINALIZER_MODEL", self.finalizer_model)
        self.evaluator_model = os.getenv("EVALUATOR_MODEL", self.evaluator_model)


config = ScenarioConfig()
