import json

from typing import Dict, Any, List

from backend.db import get_connection


class PromptManager:
    PROMPT_NAMES = ["skeleton_prompt", "dialogue_prompt", "finalizer_prompt"]

    def __init__(self):
        self.conn = get_connection()
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get_active_prompt(self, prompt_name: str):
        cache_key = f"active_{prompt_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT version_id, prompt_name, version, prompt_content, is_active, metrics, created_at
                FROM prompt_version
                WHERE prompt_name = %s AND is_active = true
                ORDER BY created_at DESC
                LIMIT 1
            """, (prompt_name,))
            row = cur.fetchone()

        if not row:
            return None

        result = {
            "version_id": row[0],
            "prompt_name": row[1],
            "version": row[2],
            "prompt_content": row[3],
            "is_active": row[4],
            "metrics": row[5] or {},
            "created_at": row[6].isoformat() if row[6] else None
        }

        self._cache[cache_key] = result
        return result

    def get_active_prompts(self) -> Dict[str, Dict[str, Any]]:
        result = {}
        for name in self.PROMPT_NAMES:
            prompt = self.get_active_prompt(name)
            if prompt:
                result[name] = prompt
        return result

    def get_active_version_ids(self) -> Dict[str, int]:
        prompts = self.get_active_prompts()
        return {
            "skeleton": prompts.get("skeleton_prompt", {}).get("version_id"),
            "dialogue": prompts.get("dialogue_prompt", {}).get("version_id"),
            "finalizer": prompts.get("finalizer_prompt", {}).get("version_id"),
        }

    def get_prompt_by_version(self, prompt_name: str, version: str):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT version_id, prompt_name, version, prompt_content, is_active, metrics, created_at
                FROM prompt_version
                WHERE prompt_name = %s AND version = %s
            """, (prompt_name, version))
            row = cur.fetchone()

        if not row:
            return None

        return {
            "version_id": row[0],
            "prompt_name": row[1],
            "version": row[2],
            "prompt_content": row[3],
            "is_active": row[4],
            "metrics": row[5] or {},
            "created_at": row[6].isoformat() if row[6] else None
        }

    def create_version(
        self,
        prompt_name: str,
        version: str,
        prompt_content: str,
        activate: bool = False
    ) -> int:
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT version_id FROM prompt_version
                WHERE prompt_name = %s AND version = %s
            """, (prompt_name, version))
            if cur.fetchone():
                raise ValueError(f"버전 '{version}'이 이미 존재합니다: {prompt_name}")

            if activate:
                cur.execute("""
                    UPDATE prompt_version
                    SET is_active = false
                    WHERE prompt_name = %s AND is_active = true
                """, (prompt_name,))

            cur.execute("""
                INSERT INTO prompt_version (prompt_name, version, prompt_content, is_active, metrics)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING version_id
            """, (prompt_name, version, prompt_content, activate, json.dumps({})))

            version_id = cur.fetchone()[0]
            self.conn.commit()

        self._invalidate_cache(prompt_name)
        return version_id

    def activate_version(self, prompt_name: str, version: str) -> bool:
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT version_id FROM prompt_version
                WHERE prompt_name = %s AND version = %s
            """, (prompt_name, version))
            row = cur.fetchone()
            if not row:
                return False

            cur.execute("""
                UPDATE prompt_version
                SET is_active = false
                WHERE prompt_name = %s AND is_active = true
            """, (prompt_name,))

            # 새 버전 활성화
            cur.execute("""
                UPDATE prompt_version
                SET is_active = true
                WHERE prompt_name = %s AND version = %s
            """, (prompt_name, version))

            self.conn.commit()

        self._invalidate_cache(prompt_name)
        return True

    def list_versions(self, prompt_name: str) -> List[Dict[str, Any]]:
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT version_id, version, is_active, metrics, created_at
                FROM prompt_version
                WHERE prompt_name = %s
                ORDER BY created_at DESC
            """, (prompt_name,))
            rows = cur.fetchall()

        return [
            {
                "version_id": row[0],
                "version": row[1],
                "is_active": row[2],
                "metrics": row[3] or {},
                "created_at": row[4].isoformat() if row[4] else None
            }
            for row in rows
        ]

    def update_metrics(self, version_id: int, metrics: Dict[str, Any]):
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT metrics FROM prompt_version WHERE version_id = %s
            """, (version_id,))
            row = cur.fetchone()
            if not row:
                return

            existing = row[0] or {}
            existing.update(metrics)

            cur.execute("""
                UPDATE prompt_version
                SET metrics = %s
                WHERE version_id = %s
            """, (json.dumps(existing), version_id))

            self.conn.commit()

    def increment_usage(self, version_id: int):
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE prompt_version
                SET metrics = jsonb_set(
                    COALESCE(metrics, '{}'),
                    '{usage_count}',
                    (COALESCE((metrics->>'usage_count')::int, 0) + 1)::text::jsonb
                )
                WHERE version_id = %s
            """, (version_id,))
            self.conn.commit()

    def _invalidate_cache(self, prompt_name: str):
        cache_key = f"active_{prompt_name}"
        if cache_key in self._cache:
            del self._cache[cache_key]


DEFAULT_PROMPTS = {
    "skeleton_prompt": {
        "version": "v1.0",
        "content": """숏폼 영상 시나리오 작가입니다.

## 밈 정보
- 이름: {meme_name}
- 정의: {definition}
- 유형: {meme_type}
{type_specific_info}

## 캐릭터
{character_desc}

## 구조
1. intro: 사원이 부장에게 밈을 소개하는 상황 설정
2. meme: 부장이 밈을 따라하는 장면 (핵심)
3. outro: 리액션 및 마무리"""
    },
    "dialogue_prompt": {
        "version": "v1.0",
        "content": """캐릭터 대사 작가입니다.

## 캐릭터
- 이름: {character_name}
- 설명: {character_description}
- 말투: {character_style}
{meme_phrase_hint}

## 씬 맥락
{scene_context}

## 대사 정보
- 비트 ID: {beat_id}
- 상황: {placeholder}

규칙: {character_name}의 말투 특성 반영, 10-30자 내외"""
    },
    "finalizer_prompt": {
        "version": "v1.0",
        "content": """시나리오 편집자입니다.

## 골격
{skeleton}

## 대사
{dialogues}
{video_hint}

요청:
1. [PLACEHOLDER]를 대사로 교체
2. 전체 흐름 검토
3. duration 확인"""
    }
}


def migrate_prompts_to_db():
    from backend.scenario.prompts.templates import (
        get_skeleton_prompt,
        get_dialogue_prompt,
        get_finalizer_prompt
    )
    import inspect

    manager = PromptManager()

    # skeleton_prompt
    skeleton_source = inspect.getsource(get_skeleton_prompt)
    try:
        manager.create_version(
            "skeleton_prompt",
            "v1.0",
            skeleton_source,
            activate=True
        )
    except ValueError as e:
        print(f"[마이그레이션] skeleton_prompt: {e}")

    # dialogue_prompt
    dialogue_source = inspect.getsource(get_dialogue_prompt)
    try:
        manager.create_version(
            "dialogue_prompt",
            "v1.0",
            dialogue_source,
            activate=True
        )
    except ValueError as e:
        print(f"[마이그레이션] dialogue_prompt: {e}")

    # finalizer_prompt
    finalizer_source = inspect.getsource(get_finalizer_prompt)
    try:
        manager.create_version(
            "finalizer_prompt",
            "v1.0",
            finalizer_source,
            activate=True
        )
    except ValueError as e:
        print(f"[마이그레이션] finalizer_prompt: {e}")

    print("[마이그레이션] 완료")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="프롬프트 버전 관리")
    parser.add_argument("--migrate", action="store_true", help="기본 프롬프트를 DB로 마이그레이션")
    parser.add_argument("--list", type=str, help="프롬프트 버전 목록 (skeleton_prompt, dialogue_prompt, finalizer_prompt)")
    parser.add_argument("--activate", nargs=2, metavar=("PROMPT_NAME", "VERSION"), help="버전 활성화")
    parser.add_argument("--show-active", action="store_true", help="활성 프롬프트 표시")
    args = parser.parse_args()

    manager = PromptManager()

    if args.migrate:
        migrate_prompts_to_db()

    elif args.list:
        versions = manager.list_versions(args.list)
        print(f"\n=== {args.list} 버전 목록 ===")
        for v in versions:
            status = "[활성]" if v["is_active"] else ""
            usage = v["metrics"].get("usage_count", 0)
            print(f"  {v['version']} {status} (사용: {usage}회) - {v['created_at']}")

    elif args.activate:
        prompt_name, version = args.activate
        success = manager.activate_version(prompt_name, version)
        if success:
            print(f"활성화 완료: {prompt_name} {version}")
        else:
            print(f"활성화 실패: {prompt_name} {version}")

    elif args.show_active:
        prompts = manager.get_active_prompts()
        print("\n=== 활성 프롬프트 ===")
        for name, info in prompts.items():
            print(f"  {name}: {info['version']} (id={info['version_id']})")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
