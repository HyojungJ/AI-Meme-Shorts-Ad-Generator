"""
데이터베이스 연결 및 데이터 로드/저장 함수들
"""
import json
import logging
import re
from typing import Dict, Any, List
from psycopg2.extras import RealDictCursor, Json

from content_pipeline.db import get_db_connection

logger = logging.getLogger(__name__)


def load_company_data(ad_id: int) -> Dict[str, Any]:
    """
    회사/상품 정보 로드 (ad_requests, companies, company_characters 조인)
    
    Args:
        ad_id: 광고 ID (ad_requests 테이블의 PK)
        
    Returns:
        회사/상품 정보 딕셔너리
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 광고 정보 조회
        cursor.execute("""
            SELECT item_name, item_category, item_description, company_id, character_id, meme_id
            FROM ad_requests
            WHERE ad_id = %s
        """, (ad_id,))
        ad_info = cursor.fetchone()
        
        if not ad_info:
            raise ValueError(f"ad_id {ad_id}에 해당하는 데이터가 없습니다")
        
        # 회사 이름 조회
        cursor.execute("""
            SELECT company_name
            FROM companies
            WHERE company_id = %s
        """, (ad_info["company_id"],))
        company_info = cursor.fetchone()
        
        # 캐릭터 보이스 디자인 조회
        cursor.execute("""
            SELECT voice_design_prompt
            FROM company_characters
            WHERE character_id = %s
        """, (ad_info["character_id"],))
        character_info = cursor.fetchone()

        # 결과 조합
        return {
            "company_name": company_info["company_name"],
            "item_name": ad_info["item_name"],
            "item_category": ad_info["item_category"],
            "item_description": ad_info["item_description"],
            "voice_design_prompt": character_info["voice_design_prompt"],
            "meme_id": ad_info["meme_id"]
        }
    
    finally:
        cursor.close()
        conn.close()


def load_meme_data(meme_id: int, example_template: str) -> Dict[str, Any]:
    """
    밈 정보 + 활용 예시 로드 및 포매팅
    
    Args:
        meme_id: 밈 ID
        example_template: 활용 예시 템플릿 문자열
        
    Returns:
        밈 데이터 딕셔너리 (usage_examples 포함)
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 밈 기본 정보
        cursor.execute("""
            SELECT meme_name, definition, key_phrase
            FROM memes
            WHERE meme_id = %s
        """, (meme_id,))
        
        meme_info = cursor.fetchone()
        if not meme_info:
            raise ValueError(f"meme_id {meme_id}에 해당하는 데이터가 없습니다")
        
        # 밈 활용 예시
        cursor.execute("""
            SELECT 
                situation,
                dialogue_example,
                example_type,
                note,
                tone
            FROM meme_examples
            WHERE meme_id = %s
            ORDER BY example_id
        """, (meme_id,))
        
        examples = cursor.fetchall()
        
        # 활용 예시 포매팅
        formatted_examples = []
        for idx, ex in enumerate(examples, 1):
            formatted = example_template.format(
                index=idx,
                situation=ex['situation'],
                dialogue_example=ex['dialogue_example'],
                example_type=ex['example_type'],
                note=ex['note'] if ex['note'] else "해당 없음",
                tone=ex['tone']
            )
            formatted_examples.append(formatted)
        
        # 결과 조합
        result = dict(meme_info)
        result['usage_examples'] = "\n".join(formatted_examples)
        
        # key_phrase가 None이면 명시적으로 표시
        if result['key_phrase'] is None:
            result['key_phrase'] = "핵심 문구 없음"

        return result
    
    finally:
        cursor.close()
        conn.close()


def save_prompt_template_to_db(
    prompt_name: str,
    version: str,
    template: str
) -> int:
    """
    프롬프트 템플릿을 prompt_versions 테이블에 저장
    이미 존재하면 skip
    
    Args:
        prompt_name: 프롬프트 이름 (예: "GENERATE_SCENARIO_V1")
        version: 버전 (예: "1")
        template: 프롬프트 템플릿 문자열
        
    Returns:
        저장된 또는 기존 version_id
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 기존 템플릿 확인
        cur.execute("""
            SELECT version_id 
            FROM prompt_versions 
            WHERE prompt_name = %s AND version = %s
        """, (prompt_name, version))
        
        existing = cur.fetchone()
        
        # 이미 존재하면 skip
        if existing:
            version_id = existing[0]
            logger.debug("Skip: %s %s (version_id: %s)", prompt_name, version, version_id)
            return version_id
        
        # 없으면 새로 저장
        variables = re.findall(r'\{(\w+)\}', template)
        cur.execute("""
            INSERT INTO prompt_versions (
                prompt_name, version, content, variables, is_active
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING version_id
        """, (prompt_name, version, template, Json(variables), True))
        
        version_id = cur.fetchone()[0]
        conn.commit()
        logger.info("Saved: %s %s (version_id: %s)", prompt_name, version, version_id)
        return version_id
    
    finally:
        cur.close()
        conn.close()
    

def save_scenario_to_db(
    scenario: Dict[str, Any],
    ad_id: int,
    meme_id: int,
    generation_type: str,
    used_templates: List[str] = None,
    model: str = "gpt-4o",
    system_prompt: str = None,
    user_prompt: str = None,
    full_response: str = None,
    thinking: str = None,
) -> int:
    """
    생성된 시나리오를 scenario_scripts 테이블에 저장

    Args:
        scenario: Scenario.model_dump() 결과
        ad_id: 광고 ID
        meme_id: 밈 ID
        generation_type: 생성 타입
        used_templates: 사용한 템플릿 리스트 (initial일 때만 전달)
        model: 사용한 LLM 모델명
        system_prompt: 시스템 프롬프트
        user_prompt: 유저 프롬프트
        full_response: 모델 응답 전체
        thinking: CoT thinking 부분

    Returns:
        저장된 script_id
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # scenes에는 scene1-4만 저장 (title, description, hashtags 제외)
        scenes_only = {
            "scene1": scenario.get("scene1"),
            "scene2": scenario.get("scene2"),
            "scene3": scenario.get("scene3"),
            "scene4": scenario.get("scene4"),
        }

        cur.execute("""
            INSERT INTO scenario_scripts (
                ad_id,
                meme_id,
                title,
                description,
                hashtags,
                scenes,
                used_model,
                generation_type,
                used_templates,
                system_prompt,
                user_prompt,
                full_response,
                thinking
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING script_id
        """, (
            ad_id,
            meme_id,
            scenario['title'],
            scenario['description'],
            scenario['hashtags'],
            Json(scenes_only),
            model,
            generation_type,
            used_templates,
            system_prompt,
            user_prompt,
            full_response,
            thinking,
        ))

        script_id = cur.fetchone()[0]
        conn.commit()
        return script_id

    finally:
        cur.close()
        conn.close()


def update_review_result_to_db(script_id: int, review_result: Dict[str, Any]):
    """
    생성된 시나리오에 검수 결과 업데이트
    
    Args:
        script_id: 시나리오 ID
        review_result: 검수 결과 딕셔너리 (feedback_type 포함)
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE scenario_scripts 
            SET review_result = %s
            WHERE script_id = %s
        """, (Json(review_result), script_id))
        conn.commit()
    finally:
        cur.close()
        conn.close()


def load_latest_scenario_for_regeneration(ad_id: int) -> Dict[str, Any]:
    """
    휴먼 피드백 재생성을 위한 최신 시나리오 로드
    
    Args:
        ad_id: 광고 ID
        
    Returns:
        시나리오 데이터 (script_id, meme_id, scenes, review_result)
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT script_id, meme_id, title, description, hashtags, scenes, review_result
            FROM scenario_scripts
            WHERE ad_id = %s
              AND generation_type NOT LIKE 'finetuning_data%'
            ORDER BY created_at DESC
            LIMIT 1
        """, (ad_id,))
        
        latest_script = cur.fetchone()
        
        if not latest_script:
            raise ValueError(f"ad_id {ad_id}에 해당하는 시나리오가 없습니다")
        
        if not latest_script["review_result"]:
            raise ValueError(f"script_id {latest_script['script_id']}에 피드백이 없습니다")
        
        review_result = latest_script["review_result"]
        
        if review_result.get("feedback_type") != "human_feedback":
            raise ValueError(f"휴먼 피드백이 아닙니다: {review_result.get('feedback_type')}")
        
        return dict(latest_script)
    
    finally:
        cur.close()
        conn.close()