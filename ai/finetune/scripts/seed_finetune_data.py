"""
파인튜닝용 가상 회사 데이터를 DB에 시딩하는 스크립트

실행:
    uv run python finetune/scripts/seed_finetune_data.py

생성되는 데이터:
    - companies: 40개 가상 회사
    - company_characters: 40개 캐릭터 (voice_design_prompt)
    - accounts: 파인튜닝용 계정 1개 (없으면 생성)
"""

import os
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# .env 로드
env_path = Path(__file__).parent.parent.parent.parent / "AI" / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # AI-finetune/.env도 시도
    load_dotenv()

from company_templates import COMPANY_TEMPLATES


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


def get_or_create_finetune_account(cur) -> int:
    """파인튜닝용 계정 조회 또는 생성"""
    email = "finetune@meme-fluencer.ai"

    cur.execute("SELECT account_id FROM accounts WHERE email = %s", (email,))
    row = cur.fetchone()

    if row:
        print(f"✓ 기존 계정 사용: {email} (account_id: {row['account_id']})")
        return row['account_id']

    cur.execute("""
        INSERT INTO accounts (email, account_type, is_active)
        VALUES (%s, 'admin', true)
        RETURNING account_id
    """, (email,))
    account_id = cur.fetchone()['account_id']
    print(f"✓ 계정 생성: {email} (account_id: {account_id})")
    return account_id


def seed_companies_and_characters(cur) -> dict:
    """
    회사 + 캐릭터 시딩

    Returns:
        {company_name: {"company_id": int, "character_id": int}}
    """
    result = {}

    for template in COMPANY_TEMPLATES:
        company_name = template["company_name"]

        # 회사 존재 여부 확인
        cur.execute("""
            SELECT company_id FROM companies WHERE company_name = %s
        """, (company_name,))
        existing = cur.fetchone()

        if existing:
            company_id = existing['company_id']
            print(f"  → Skip: {company_name} (이미 존재)")
        else:
            # 회사 생성
            cur.execute("""
                INSERT INTO companies (company_name, is_active)
                VALUES (%s, true)
                RETURNING company_id
            """, (company_name,))
            company_id = cur.fetchone()['company_id']
            print(f"  + Company: {company_name} (company_id: {company_id})")

        # 캐릭터 존재 여부 확인
        cur.execute("""
            SELECT character_id FROM company_characters
            WHERE company_id = %s AND voice_design_prompt = %s
        """, (company_id, template["voice_design_prompt"]))
        existing_char = cur.fetchone()

        if existing_char:
            character_id = existing_char['character_id']
        else:
            # 캐릭터 생성 (image_url은 placeholder)
            cur.execute("""
                INSERT INTO company_characters (
                    company_id, image_url, voice_design_prompt, is_active
                )
                VALUES (%s, %s, %s, true)
                RETURNING character_id
            """, (
                company_id,
                f"https://placeholder.com/finetune/{company_name}.png",
                template["voice_design_prompt"]
            ))
            character_id = cur.fetchone()['character_id']
            print(f"    + Character: {template['voice_design_prompt'][:30]}... (character_id: {character_id})")

        result[company_name] = {
            "company_id": company_id,
            "character_id": character_id,
            "item_name": template["item_name"],
            "item_category": template["item_category"],
            "item_keymessage": template["item_keymessage"],
            "voice_design_prompt": template["voice_design_prompt"],
        }

    return result


def main():
    print("=" * 60)
    print("파인튜닝용 회사/캐릭터 데이터 시딩")
    print("=" * 60)

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 1. 파인튜닝용 계정
        print("\n[1/2] 계정 확인/생성")
        account_id = get_or_create_finetune_account(cur)

        # 2. 회사 + 캐릭터 시딩
        print(f"\n[2/2] 회사 + 캐릭터 시딩 ({len(COMPANY_TEMPLATES)}개)")
        company_data = seed_companies_and_characters(cur)

        conn.commit()

        # 결과 요약
        print("\n" + "=" * 60)
        print("완료!")
        print(f"  - 계정: finetune@meme-fluencer.ai (account_id: {account_id})")
        print(f"  - 회사/캐릭터: {len(company_data)}개")
        print("=" * 60)

        # 다음 단계 안내
        print("\n다음 단계:")
        print("  uv run python finetune/scripts/generate_data.py --limit 100 --save-db")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
