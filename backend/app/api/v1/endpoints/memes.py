"""
밈 목록 조회 API 엔드포인트
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List

from app.models.meme import Meme
from app.models.ad_request import AdRequest
from app.core.security import get_current_user
from app.db.session import get_db
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class MemeListItem(BaseModel):
    meme_id: int
    meme_name: str
    description: Optional[str] = None
    meme_type: Optional[str] = None
    thumbnail_url: Optional[str] = None
    status: str
    usage_count: int = 0
    avg_engagement_rate: float = 0.0
    created_at: str


class MemeListResponse(BaseModel):
    """밈 목록 응답"""
    total_count: int
    memes: List[MemeListItem]


class MemeSortRequest(BaseModel):
    """밈 추천 정렬 요청"""
    item_description: str
    top_n: int = 30


class MemeSortItem(BaseModel):
    """유사도 기반 정렬된 밈"""
    meme_id: int
    meme_name: str
    situation: str
    example_id: int
    similarity: float


class MemeSortResponse(BaseModel):
    """밈 추천 정렬 응답"""
    results: List[MemeSortItem]


class MemeDetailResponse(BaseModel):
    meme_id: int
    meme_name: str
    description: Optional[str] = None
    origin: Optional[dict] = None
    key_phrase: Optional[str] = None
    sources: Optional[list] = None
    risk_info: Optional[str] = None
    meme_type: Optional[str] = None
    status: str
    confidence: Optional[float] = None
    created_at: str


@router.get("", response_model=MemeListResponse)
async def get_memes(
    request: Request,
    status: Optional[str] = Query(None, description="밈 상태 필터 (READY, COMPLETED 등)"),
    meme_type: Optional[str] = Query(None, description="밈 타입 필터 (quotable, performable, hybrid)"),
    search: Optional[str] = Query(None, description="밈 이름 검색"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    밈 목록 조회
    
    영상 생성 시 선택할 수 있는 밈 목록을 조회합니다.
    """
    # 인증 확인 (로그인한 사용자만)
    user_info = await get_current_user(request)
    
    # usage_count subquery (finetune_data 제외)
    usage_subq = db.query(
        AdRequest.meme_id,
        func.count(AdRequest.ad_id).label('count')
    ).filter(
        AdRequest.status != 'finetune_data'
    ).group_by(AdRequest.meme_id).subquery()

    # Meme + usage_count 조인
    query = db.query(
        Meme,
        func.coalesce(usage_subq.c.count, 0).label('usage_count')
    ).outerjoin(usage_subq, Meme.meme_id == usage_subq.c.meme_id)

    # 필터 적용
    if status:
        query = query.filter(Meme.status == status)

    if meme_type:
        query = query.filter(Meme.meme_type == meme_type)

    if search:
        query = query.filter(Meme.meme_name.ilike(f"%{search}%"))

    # 전체 개수
    total_count = query.count()

    # 인기순 정렬 + 페이지네이션
    results = query.order_by(
        func.coalesce(usage_subq.c.count, 0).desc()
    ).offset(offset).limit(limit).all()

    # 응답 생성
    meme_list = [
        MemeListItem(
            meme_id=meme.meme_id,
            meme_name=meme.meme_name,
            description=meme.definition,
            meme_type=meme.meme_type,
            thumbnail_url=None,
            status=meme.status,
            usage_count=usage_count,
            avg_engagement_rate=0.0,
            created_at=meme.created_at.isoformat()
        )
        for meme, usage_count in results
    ]

    return MemeListResponse(
        total_count=total_count,
        memes=meme_list
    )


@router.post("/sort", response_model=MemeSortResponse)
async def sort_memes(
    body: MemeSortRequest,
    request: Request,
):
    """
    제품 설명 기반 밈 추천 정렬

    제품 설명과 밈 situation 임베딩 간 유사도를 비교하여
    가장 적합한 밈을 내림차순으로 반환합니다.
    """
    await get_current_user(request)

    if not body.item_description.strip():
        raise HTTPException(status_code=400, detail="제품 설명을 입력하세요")

    try:
        from meme_collector.meme_sorting import sort_memes_by_similarity

        results = sort_memes_by_similarity(
            item_description=body.item_description,
            top_n=body.top_n,
        )
    except Exception as e:
        logger.error("밈 추천 정렬 실패: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="밈 추천 정렬에 실패했습니다")

    return MemeSortResponse(
        results=[MemeSortItem(**r) for r in results]
    )


@router.get("/{meme_id}", response_model=MemeDetailResponse)
async def get_meme_detail(
    meme_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    밈 상세 정보 조회
    
    특정 밈의 상세 정보를 조회합니다.
    """
    # 인증 확인
    user_info = await get_current_user(request)
    
    # 밈 조회
    meme = db.query(Meme).filter(Meme.meme_id == meme_id).first()
    
    if not meme:
        raise HTTPException(status_code=404, detail="밈을 찾을 수 없습니다")
    
    return MemeDetailResponse(
        meme_id=meme.meme_id,
        meme_name=meme.meme_name,
        description=meme.definition,
        origin=meme.origin,
        key_phrase=meme.key_phrase,
        sources=meme.sources,
        risk_info=meme.risk_info,
        meme_type=meme.meme_type,
        status=meme.status,
        confidence=meme.confidence,
        created_at=meme.created_at.isoformat()
    )


