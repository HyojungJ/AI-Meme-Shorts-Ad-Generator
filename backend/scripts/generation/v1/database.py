"""
?곸긽 ?앹꽦 愿???곗씠?곕쿋?댁뒪 紐⑤뜽 諛??⑥닔
?묒뾽 ?댁슜 3踰? ?뚰겕?뚮줈???ㅽ뻾 愿由?"""
import os
import sys
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from dotenv import load_dotenv
import uuid

# auth/v2??Base? 紐⑤뜽?ㅼ쓣 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'auth', 'v2'))
from database_v2 import Base, engine, SessionLocal, User, Company

load_dotenv()


# ============================================
# 紐⑤뜽 ?뺤쓽
# ============================================
class Meme(Base):
    """
    諛??곗씠???뚯씠釉?    DMG 愿???붽뎄?ы빆
    """
    __tablename__ = "memes"
    
    meme_id = Column(Integer, primary_key=True, index=True)
    meme_name = Column(String(255), unique=True, nullable=False)
    definition = Column(Text)
    key_phrase = Column(String(255))
    risk_level = Column(String(50))
    motion_prompt = Column(Text)
    quality_score = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class WorkflowExecution(Base):
    """
    ?곸긽 ?쒖옉 ?뚰겕?뚮줈???ㅽ뻾 ?뚯씠釉?    ?묒뾽 ?댁슜 3踰? ?뚰겕?뚮줈???ㅽ뻾 愿由?    """
    __tablename__ = "workflow_execution"
    
    # 湲곕낯 ?뺣낫
    execution_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(Integer, ForeignKey("companies.company_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    meme_id = Column(Integer, ForeignKey("memes.meme_id", ondelete="SET NULL"))
    
    # ?뚰겕?뚮줈?????諛??곹깭
    workflow_type = Column(String(50), nullable=False, default="video")
    status = Column(String(50), nullable=False, default="created")
    current_stage = Column(String(100))
    progress_percentage = Column(Integer, default=0)
    scenario_status = Column(String(50))
    
    # ?낅젰/異쒕젰 ?곗씠??(JSONB)
    input_params = Column(JSONB, nullable=False)
    output_result = Column(JSONB)
    
    # 鍮꾩슜 諛??먮윭
    total_cost_usd = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)
    
    # ?쒓컙 ?뺣낫
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))


# ============================================
# ?곗씠?곕쿋?댁뒪 ?몄뀡
# ============================================
def get_db():
    """?곗씠?곕쿋?댁뒪 ?몄뀡 ?앹꽦"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================
# WorkflowExecution 愿???⑥닔
# ============================================
def create_workflow(db, user_id: int, company_id: int, input_params: dict,
                   meme_id: int = None, workflow_type: str = "video"):
    """
    ???뚰겕?뚮줈???앹꽦
    ?묒뾽 ?댁슜 3踰? workflow_execution ?뚯씠釉붿뿉 ?묒뾽 湲곕줉 ?앹꽦
    """
    new_workflow = WorkflowExecution(
        user_id=user_id,
        company_id=company_id,
        meme_id=meme_id,
        workflow_type=workflow_type,
        input_params=input_params,
        status="created"
    )
    db.add(new_workflow)
    db.commit()
    db.refresh(new_workflow)
    print(f"???뚰겕?뚮줈???앹꽦: Execution ID {new_workflow.execution_id}")
    return new_workflow


def get_workflow_by_id(db, execution_id: uuid.UUID):
    """Execution ID濡??뚰겕?뚮줈??議고쉶"""
    return db.query(WorkflowExecution).filter(WorkflowExecution.execution_id == execution_id).first()


def get_workflows_by_user(db, user_id: int, limit: int = 10):
    """?ъ슜?먯쓽 ?뚰겕?뚮줈??紐⑸줉 議고쉶"""
    return db.query(WorkflowExecution).filter(
        WorkflowExecution.user_id == user_id
    ).order_by(WorkflowExecution.created_at.desc()).limit(limit).all()


def get_workflows_by_company(db, company_id: int, limit: int = 10):
    """?뚯궗???뚰겕?뚮줈??紐⑸줉 議고쉶"""
    return db.query(WorkflowExecution).filter(
        WorkflowExecution.company_id == company_id
    ).order_by(WorkflowExecution.created_at.desc()).limit(limit).all()


def update_workflow_status(db, execution_id: uuid.UUID, status: str, 
                          current_stage: str = None, progress: int = None,
                          error_message: str = None):
    """
    ?뚰겕?뚮줈???곹깭 ?낅뜲?댄듃
    """
    workflow = get_workflow_by_id(db, execution_id)
    if workflow:
        workflow.status = status
        if current_stage:
            workflow.current_stage = current_stage
        if progress is not None:
            workflow.progress_percentage = progress
        if error_message:
            workflow.error_message = error_message
        
        # ?꾨즺 ?쒓컙 ?낅뜲?댄듃
        if status in ["completed", "failed", "cancelled"]:
            workflow.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(workflow)
        print(f"?뚰겕?뚮줈???곹깭 ?낅뜲?댄듃: {execution_id} -> {status}")
        return workflow
    return None


def update_workflow_output(db, execution_id: uuid.UUID, output_result: dict):
    """
    ?뚰겕?뚮줈??異쒕젰 寃곌낵 ?낅뜲?댄듃
    """
    workflow = get_workflow_by_id(db, execution_id)
    if workflow:
        workflow.output_result = output_result
        db.commit()
        db.refresh(workflow)
        print(f"?뚰겕?뚮줈??異쒕젰 ?낅뜲?댄듃: {execution_id}")
        return workflow
    return None


def check_duplicate_workflow(db, company_id: int, product_name: str, meme_id: int):
    """
    以묐났 ?뚰겕?뚮줈???뺤씤 (DMG-AUTO-07)
    ?숈씪???쒗뭹紐낃낵 諛덉쑝濡?吏꾪뻾 以묒씤 ?묒뾽???덈뒗吏 ?뺤씤
    """
    return db.query(WorkflowExecution).filter(
        WorkflowExecution.company_id == company_id,
        WorkflowExecution.input_params['product_name'].astext == product_name,
        WorkflowExecution.meme_id == meme_id,
        WorkflowExecution.status.in_(['created', 'processing'])
    ).first()


def increment_retry_count(db, execution_id: uuid.UUID):
    """?ъ떆???잛닔 利앷?"""
    workflow = get_workflow_by_id(db, execution_id)
    if workflow:
        workflow.retry_count += 1
        db.commit()
        return workflow
    return None


# ============================================
# Meme 愿???⑥닔
# ============================================
def get_meme_by_id(db, meme_id: int):
    """諛?ID濡?議고쉶"""
    return db.query(Meme).filter(Meme.meme_id == meme_id).first()


def get_meme_by_name(db, meme_name: str):
    """諛??대쫫?쇰줈 議고쉶"""
    return db.query(Meme).filter(Meme.meme_name == meme_name).first()
