"""Qwen TTS 음성 일관성 테스트

1. voice_design으로 voice_id 생성
2. 같은 voice_description으로 여러 씬 TTS 생성 (일관성 테스트)
3. voice_description 없이 TTS 생성 (비교용)
"""
import time
from content_pipeline.pipeline import run_voice_design_step, run_tts_step


VOICE_DESC = "20대 후반 여성의 밝고 또렷한 목소리, 친근하고 에너지 넘치는 톤"
VOICE_NAME = "consistency_test"

DIALOGUES = [
    "(기쁨) 안녕하세요! 오늘 소개해드릴 제품이에요!",
    "(진지) 이 제품의 핵심 기능을 알려드릴게요.",
    "(흥분) 와, 진짜 대박이죠? 지금 바로 확인해보세요!",
]


def main():
    # 1. Voice Design
    print("=" * 60)
    print("1. Voice Design (voice_id 생성)")
    print("=" * 60)
    t0 = time.time()
    design_result = run_voice_design_step(
        voice_name=VOICE_NAME,
        voice_description=VOICE_DESC,
    )
    print(f"  Status: {design_result.get('status')}")
    print(f"  Voice ID: {design_result.get('voice_id')}")
    print(f"  Sample URL: {design_result.get('voice_sample_url')}")
    print(f"  Time: {time.time() - t0:.1f}s")

    if design_result.get("status") != "ok":
        print(f"  ERROR: {design_result.get('error')}")
        return

    voice_id = design_result["voice_id"]

    # 2. TTS with voice_description (일관성 보장)
    print()
    print("=" * 60)
    print("2. TTS WITH voice_description (일관성 보장)")
    print("=" * 60)
    for i, dialogue in enumerate(DIALOGUES, 1):
        t0 = time.time()
        result = run_tts_step(
            text=dialogue,
            voice_id=voice_id,
            voice_description=VOICE_DESC,
        )
        elapsed = time.time() - t0
        print(f"  Scene {i}: status={result.get('status')}, "
              f"duration={result.get('duration_seconds', 0):.1f}s, "
              f"time={elapsed:.1f}s")
        if result.get("audio_url"):
            print(f"    URL: {result['audio_url']}")
        if result.get("status") != "ok":
            print(f"    ERROR: {result.get('error')}")

    # 3. TTS without voice_description (DB fallback - 비교용)
    print()
    print("=" * 60)
    print("3. TTS WITHOUT voice_description (DB fallback)")
    print("=" * 60)
    t0 = time.time()
    result = run_tts_step(
        text=DIALOGUES[0],
        voice_id=voice_id,
        # voice_description 없음 → DB fallback 또는 빈 instruct
    )
    elapsed = time.time() - t0
    print(f"  Status: {result.get('status')}, "
          f"duration={result.get('duration_seconds', 0):.1f}s, "
          f"time={elapsed:.1f}s")
    if result.get("audio_url"):
        print(f"  URL: {result['audio_url']}")
    if result.get("status") != "ok":
        print(f"  ERROR: {result.get('error')}")

    print()
    print("=" * 60)
    print("테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
