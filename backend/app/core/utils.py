"""
공통 유틸리티 함수
"""
from datetime import datetime
from typing import Optional, Tuple
from fastapi import HTTPException


def parse_date_range(
    date_from: Optional[str],
    date_to: Optional[str],
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """ISO 8601 날짜 문자열을 datetime으로 변환. Z suffix 처리 포함."""
    date_from_dt = None
    date_to_dt = None

    if date_from:
        try:
            date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 date_from 형식")

    if date_to:
        try:
            date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 date_to 형식")

    return date_from_dt, date_to_dt
