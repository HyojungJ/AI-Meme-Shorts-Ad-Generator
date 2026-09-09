class ScenarioError(Exception):
    pass


class ScenarioGenerationError(ScenarioError):
    pass


class ScenarioValidationError(ScenarioError):
    pass
