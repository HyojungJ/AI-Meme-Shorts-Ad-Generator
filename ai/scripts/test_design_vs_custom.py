"""Qwen TTS design vs custom 모드 일관성 비교 테스트

동일 voice_description + 동일 seed로 여러 씬 생성 후 비교.
"""
import time
from dotenv import load_dotenv
load_dotenv()

from content_pipeline.voice.client_qwen import get_qwen_client
from content_pipeline.voice.service import VoiceService
from content_pipeline.voice.config import load_voice_config


VOICE_DESC = "20대 후반 여성의 밝고 또렷한 목소리, 친근하고 에너지 넘치는 톤"

DIALOGUES = [
    "안녕하세요! 오늘 소개해드릴 제품이에요!",
    "이 제품의 핵심 기능을 알려드릴게요.",
    "와, 진짜 대박이죠? 지금 바로 확인해보세요!",
]


def run_test(mode: str, model_key: str):
    config = load_voice_config()
    service = VoiceService(config)
    client = get_qwen_client()

    model_id = getattr(config, model_key)
    speaker = "Sohee"

    print(f"\n{'=' * 60}")
    print(f"MODE: {mode} | model: {model_id}")
    print(f"instruct: {VOICE_DESC}")
    print(f"seed: {config.qwen_tts_seed}")
    print(f"{'=' * 60}")

    for i, text in enumerate(DIALOGUES, 1):
        t0 = time.time()

        # voice_id 생성 (업로드용)
        voice_id = client.build_voice_id(
            mode=mode,
            voice_name="design_test",
            voice_description=VOICE_DESC,
            model_id=model_id,
            speaker=speaker if mode == "custom" else None,
        )

        result = service.qwen_generate_and_upload(
            model_id=model_id,
            mode=mode,
            text=text,
            language="Korean",
            speaker=speaker,
            instruct=VOICE_DESC,
            voice_id=voice_id,
            user_id="test",
        )
        elapsed = time.time() - t0
        print(f"  Scene {i}: duration={result.duration_seconds:.1f}s, time={elapsed:.1f}s")
        print(f"    text: {text}")
        print(f"    url: {result.audio_url}")


def main():
    print("=" * 60)
    print("Qwen TTS: design vs custom 모드 비교")
    print("동일 seed + 동일 instruct로 3개 씬 생성")
    print("=" * 60)

    # 1. design 모드
    run_test("design", "qwen_tts_voice_design_model_id")

    # 2. custom 모드
    run_test("custom", "qwen_tts_custom_model_id")

    print("\n" + "=" * 60)
    print("완료! URL을 브라우저에서 열어 음색을 비교하세요.")
    print("=" * 60)


if __name__ == "__main__":
    main()
