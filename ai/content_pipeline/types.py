from typing import Literal, NotRequired, TypedDict


class StepResult(TypedDict):
    status: Literal["ok", "failed", "partial"]
    error: NotRequired[str]
    db_error: NotRequired[str]
