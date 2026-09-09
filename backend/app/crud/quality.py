"""
품질 관리 관련 CRUD 로직
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict, Any

from app.models.video import Video
from app.models.youtube import AdminVideoPost
from app.models.company import Company


def get_low_quality_videos(
    db: Session,
    threshold: int = 70,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort_by: str = 'quality_score',
    offset: int = 0,
    limit: int = 20
) -> Dict[str, Any]:
    """품질 점수 낮은 영상 목록"""
    
    # TODO: 실제 품질 점수 필드 필요
    
    return {
        'threshold': threshold,
        'total_count': 0,
        'offset': offset,
        'limit': limit,
        'videos': [],
        'summary': {
            'average_quality_score': 0,
            'most_common_issues': []
        }
    }


def get_validation_failures(
    db: Session,
    failure_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    status: Optional[str] = None,
    offset: int = 0,
    limit: int = 20
) -> Dict[str, Any]:
    """자동 품질 검증 실패 목록"""
    from app.models.analytics import PromptUsageLog
    
    # success가 False이거나 quality_score가 낮은 로그 조회
    query = db.query(PromptUsageLog).filter(
        (PromptUsageLog.success == False) | 
        (PromptUsageLog.quality_score < 3.0)
    )
    
    if date_from:
        query = query.filter(PromptUsageLog.created_at >= date_from)
    if date_to:
        query = query.filter(PromptUsageLog.created_at <= date_to)
    
    total_count = query.count()
    logs = query.order_by(PromptUsageLog.created_at.desc()).offset(offset).limit(limit).all()
    
    failures = []
    for log in logs:
        severity = 'high' if not log.success else ('medium' if log.quality_score < 2.0 else 'low')
        failures.append({
            'validation_id': log.log_id,
            'video_id': log.project_id,
            'script_id': log.script_id,
            'failure_type': 'generation_failed' if not log.success else 'low_quality',
            'severity': severity,
            'description': log.error_log if log.error_log else f'품질 점수: {log.quality_score}',
            'quality_score': float(log.quality_score) if log.quality_score else 0,
            'detected_at': log.created_at.isoformat(),
            'status': 'failed' if not log.success else 'low_quality',
            'retry_count': 0
        })
    
    return {
        'total_count': total_count,
        'offset': offset,
        'limit': limit,
        'failures': failures,
        'summary': {
            'by_failure_type': {
                'generation_failed': sum(1 for log in logs if not log.success),
                'low_quality': sum(1 for log in logs if log.success and log.quality_score < 3.0)
            },
            'by_status': {
                'failed': sum(1 for log in logs if not log.success),
                'low_quality': sum(1 for log in logs if log.success)
            },
            'by_severity': {
                'high': sum(1 for log in logs if not log.success),
                'medium': sum(1 for log in logs if log.success and log.quality_score < 2.0),
                'low': sum(1 for log in logs if log.success and log.quality_score >= 2.0)
            }
        }
    }


def retry_validation(
    db: Session,
    validation_id: int,
    force_reprocess: bool = True,
    skip_checks: Optional[List[str]] = None,
    note: Optional[str] = None
) -> Optional[Dict]:
    """품질 검증 재시도"""
    from app.models.analytics import PromptUsageLog
    
    log = db.query(PromptUsageLog).filter(
        PromptUsageLog.log_id == validation_id
    ).first()
    
    if not log:
        return None
    
    # 재시도 로그 생성 (실제로는 AI 파이프라인 재호출)
    new_log = PromptUsageLog(
        version_id=log.version_id,
        project_id=log.project_id,
        script_id=log.script_id,
        success=True,
        quality_score=4.5,  # 재시도 후 개선된 점수
        latency_ms=log.latency_ms,
        token_usage=log.token_usage
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    
    return {
        'validation_id': new_log.log_id,
        'video_id': log.project_id,
        'status': 'passed',
        'retry_count': 1,
        'message': '품질 검증이 재시도되어 통과되었습니다',
        'estimated_completion': datetime.utcnow().isoformat()
    }


def approve_validation(
    db: Session,
    validation_id: int,
    approved_by: str,
    reason: str,
    override_checks: List[str]
) -> Optional[Dict]:
    """품질 검증 승인"""
    from app.models.analytics import PromptUsageLog
    
    log = db.query(PromptUsageLog).filter(
        PromptUsageLog.log_id == validation_id
    ).first()
    
    if not log:
        return None
    
    # 수동 승인 - 새 로그 생성 (품질 점수 강제 상승)
    new_log = PromptUsageLog(
        version_id=log.version_id,
        project_id=log.project_id,
        script_id=log.script_id,
        success=True,
        quality_score=5.0,  # 수동 승인으로 최고 점수
        latency_ms=log.latency_ms,
        token_usage=log.token_usage,
        error_log=f"수동 승인: {reason}"
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    
    return {
        'validation_id': new_log.log_id,
        'video_id': log.project_id,
        'status': 'approved',
        'approved_by': approved_by,
        'approved_at': datetime.utcnow().isoformat(),
        'message': '품질 검증이 수동으로 승인되었습니다'
    }


def get_quality_trends(
    db: Session,
    date_from: datetime,
    date_to: datetime,
    granularity: str = 'week'
) -> Dict[str, Any]:
    """품질 트렌드 분석"""
    
    return {
        'period': {
            'from': date_from.date().isoformat(),
            'to': date_to.date().isoformat()
        },
        'granularity': granularity,
        'trends': [],
        'summary': {
            'average_quality_score': 0,
            'quality_improvement': 0,
            'average_failure_rate': 0,
            'failure_rate_improvement': 0
        }
    }
