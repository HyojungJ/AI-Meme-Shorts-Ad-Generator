"""
자산 관련 모델 (COMPLETE_SCHEMA.sql 기준)
"""
from sqlalchemy import Column, Integer, BigInteger, String, Text, Float, DateTime, ForeignKey, Numeric, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class SceneAsset(Base):
    """장면별 자산"""
    __tablename__ = "scene_assets"
    
    asset_id = Column(Integer, primary_key=True, autoincrement=True)
    script_id = Column(Integer, ForeignKey("scenario_scripts.script_id", ondelete="CASCADE"), nullable=False, index=True)
    scene_key = Column(String(50), nullable=False)
    audio_url = Column(Text)
    audio_duration_seconds = Column(Float)
    audio_storage_path = Column(String(500))
    character_image_url = Column(Text)
    character_image_storage_path = Column(String(500))
    scene_video_url = Column(Text)
    scene_video_storage_path = Column(String(500))
    scene_video_duration = Column(Float)
    character_similarity_score = Column(Float)
    generation_model = Column(String(50))
    generation_cost = Column(Numeric(10, 4))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('script_id', 'scene_key', name='scene_assets_script_id_scene_key_key'),
    )
    
    # 관계
    script = relationship("ScenarioScript", back_populates="scene_assets")


class VoiceGeneration(Base):
    """음성 생성"""
    __tablename__ = "voice_generations"
    
    voice_gen_id = Column(Integer, primary_key=True, autoincrement=True)
    character_id = Column(Integer, ForeignKey("company_characters.character_id"), nullable=False, index=True)
    script_id = Column(Integer, ForeignKey("scenario_scripts.script_id"), index=True)
    scene_key = Column(String(50), nullable=False)
    text_content = Column(Text, nullable=False)
    text_hash = Column(String(64))
    audio_url = Column(Text)
    duration_seconds = Column(Float)
    size_bytes = Column(BigInteger)
    settings_json = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('character_id', 'text_hash', name='voice_generations_character_id_text_hash_key'),
    )
    
    # 관계
    character = relationship("CompanyCharacter", back_populates="voice_generations")
    script = relationship("ScenarioScript", back_populates="voice_generations")
    scene_videos = relationship("SceneVideo", back_populates="voice_generation")


class ImageGeneration(Base):
    """이미지 생성"""
    __tablename__ = "image_generations"
    
    image_id = Column(Integer, primary_key=True, autoincrement=True)
    character_id = Column(Integer, ForeignKey("company_characters.character_id"), nullable=False, index=True)
    script_id = Column(Integer, ForeignKey("scenario_scripts.script_id"), nullable=False, unique=True)
    prompt = Column(Text)
    model = Column(String(50))
    image_url = Column(Text)
    size_bytes = Column(BigInteger)
    metadata_json = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    
    # 관계
    character = relationship("CompanyCharacter", back_populates="image_generations")
    script = relationship("ScenarioScript", back_populates="image_generations")
    scene_videos = relationship("SceneVideo", back_populates="image")


class SceneVideo(Base):
    """장면 비디오"""
    __tablename__ = "scene_videos"
    
    scene_video_id = Column(Integer, primary_key=True, autoincrement=True)
    script_id = Column(Integer, ForeignKey("scenario_scripts.script_id"), nullable=False, index=True)
    scene_key = Column(String(50), nullable=False)
    voice_gen_id = Column(Integer, ForeignKey("voice_generations.voice_gen_id"))
    image_id = Column(Integer, ForeignKey("image_generations.image_id"))
    video_url = Column(Text)
    duration_seconds = Column(Float)
    size_bytes = Column(BigInteger)
    generation_model = Column(String(50))
    generation_cost = Column(Numeric(10, 4))
    generation_metadata = Column(JSONB, default={})
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('script_id', 'scene_key', name='scene_videos_script_id_scene_key_key'),
    )
    
    # 관계
    script = relationship("ScenarioScript", back_populates="scene_videos")
    voice_generation = relationship("VoiceGeneration", back_populates="scene_videos")
    image = relationship("ImageGeneration", back_populates="scene_videos")
