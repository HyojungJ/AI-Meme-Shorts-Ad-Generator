"""애플리케이션 예외 체계"""


class AppException(Exception):
    """Base exception. status_code와 detail을 갖는다."""
    status_code: int = 500
    detail: str = "서버 내부 오류가 발생했습니다"

    def __init__(self, detail: str | None = None, *, status_code: int | None = None):
        if detail is not None:
            self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.detail)


class NotFoundError(AppException):
    status_code = 404
    detail = "리소스를 찾을 수 없습니다"


class PermissionDeniedError(AppException):
    status_code = 403
    detail = "접근 권한이 없습니다"


class ValidationError(AppException):
    status_code = 400
    detail = "요청이 올바르지 않습니다"


class AIServiceError(AppException):
    status_code = 502
    detail = "AI 서비스 통신 오류가 발생했습니다"


class ConflictError(AppException):
    status_code = 409
    detail = "리소스 충돌이 발생했습니다"
