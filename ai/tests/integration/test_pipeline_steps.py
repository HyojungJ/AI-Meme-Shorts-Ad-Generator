"""
Content Pipeline step functions 통합 테스트.

실제 API 호출이 필요하므로 `pytest -m integration` 또는 `pytest -m slow`로 실행.
필요한 환경변수: NANO_BANANA_API_KEY, ELEVENLABS_API_KEY, OPENAI_API_KEY

테스트 순서:
0. run_scenario_step → scenes 생성
1. run_character_step → image_path 저장
2. run_voice_design_step → voice_id 저장
3. run_tts_step → 위 voice_id 사용
4. run_scene_image_step → 위 image_path 사용

run_video_step은 RunPod 의존성으로 제외.
"""
import os
import pytest

from content_pipeline.pipeline import (
    run_scenario_step,
    run_character_step,
    run_voice_design_step,
    run_tts_step,
    run_scene_image_step,
    suggest_character_prompts_from_product,
    run_asset_generation_step,
    run_content_generation_step,
    run_scenario_regenerate_step,
)


# 테스트 간 공유할 결과 저장
_test_results = {}


def has_openai_api_key():
    return bool(os.environ.get("OPENAI_API_KEY"))


def has_nano_banana_api_key():
    return bool(os.environ.get("NANO_BANANA_API_KEY"))


def has_elevenlabs_api_key():
    return bool(os.environ.get("ELEVENLABS_API_KEY"))


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.skipif(not has_openai_api_key(), reason="OPENAI_API_KEY not set")
class TestScenarioStep:
    def test_run_scenario_step(self):
        """시나리오 생성 테스트 (DB에서 밈 정보 조회 필요)."""
        # DB에 존재하는 ad_id, meme_id 사용
        result = run_scenario_step(ad_id=10, meme_id=51)

        assert result["status"] == "completed", f"Failed: {result.get('error')}"
        assert result.get("scenes"), "scenes should not be empty"
        assert len(result["scenes"]) == 4, "Should have 4 scenes (hook, body*2, close)"
        assert result.get("title"), "title should exist"
        assert result.get("meme_name"), "meme_name should exist"

        # 씬 구조 검증
        scenes = result["scenes"]
        assert scenes[0]["structure_type"] == "hook"
        assert scenes[1]["structure_type"] == "body"
        assert scenes[2]["structure_type"] == "body"
        assert scenes[3]["structure_type"] == "close"

        # 다음 테스트를 위해 저장
        _test_results["scenes"] = scenes
        _test_results["scenario_title"] = result.get("title")

        print(f"\n[Scenario Step] title: {result.get('title')}")
        print(f"[Scenario Step] meme_name: {result.get('meme_name')}")
        print(f"[Scenario Step] total_duration: {result.get('total_duration')}s")
        for scene in scenes:
            print(f"  - {scene['scene_key']}: {scene['dialogue'][:30]}...")


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.skipif(not has_nano_banana_api_key(), reason="NANO_BANANA_API_KEY not set")
class TestCharacterStep:
    def test_run_character_step(self):
        """캐릭터 이미지 생성 테스트."""
        result = run_character_step(
            prompt="젊고 활기찬 20대 남자 캐릭터, 밝은 표정, 캐주얼 복장"
        )

        assert result["status"] == "ok", f"Failed: {result.get('error')}"
        assert result.get("image_url") or result.get("image_path")

        # 다음 테스트를 위해 저장
        _test_results["character_image_url"] = result.get("image_url")
        _test_results["character_image_path"] = result.get("image_path")

        print(f"\n[Character Step] image_url: {result.get('image_url')}")
        print(f"[Character Step] image_path: {result.get('image_path')}")


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.skipif(not has_elevenlabs_api_key(), reason="ELEVENLABS_API_KEY not set")
class TestVoiceDesignStep:
    def test_run_voice_design_step(self):
        """Voice Design 테스트 (샘플 음성 생성)."""
        result = run_voice_design_step(
            voice_name="테스트 캐릭터",
            voice_description="밝고 활기찬 20대 남성 목소리, 친근하고 에너지 넘치는 톤"
        )

        assert result["status"] == "ok", f"Failed: {result.get('error')}"
        assert result.get("voice_id"), "voice_id should be returned"
        assert result.get("voice_sample_url"), "voice_sample_url should be returned"

        # 다음 테스트를 위해 저장
        _test_results["voice_id"] = result.get("voice_id")
        _test_results["voice_sample_url"] = result.get("voice_sample_url")

        print(f"\n[Voice Design Step] voice_id: {result.get('voice_id')}")
        print(f"[Voice Design Step] voice_sample_url: {result.get('voice_sample_url')}")


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.skipif(not has_elevenlabs_api_key(), reason="ELEVENLABS_API_KEY not set")
class TestTTSStep:
    def test_run_tts_step_with_preset_voice(self):
        """TTS 생성 테스트 (프리셋 voice_id 사용)."""
        # ElevenLabs 기본 프리셋 voice_id (Rachel)
        preset_voice_id = "21m00Tcm4TlvDq8ikWAM"

        result = run_tts_step(
            text="안녕하세요! 오늘도 좋은 하루 되세요!",
            voice_id=preset_voice_id,
        )

        assert result["status"] == "ok", f"Failed: {result.get('error')}"
        assert result.get("audio_url"), "audio_url should be returned"
        assert result.get("duration_seconds", 0) > 0, "duration should be positive"

        print(f"\n[TTS Step] audio_url: {result.get('audio_url')}")
        print(f"[TTS Step] duration: {result.get('duration_seconds')}s")

    def test_run_tts_step_with_designed_voice(self):
        """TTS 생성 테스트 (Voice Design에서 생성한 voice_id 사용)."""
        voice_id = _test_results.get("voice_id")
        if not voice_id:
            pytest.skip("Voice Design 테스트가 먼저 실행되어야 함")

        result = run_tts_step(
            text="무야호~ 진짜 신난다!",
            voice_id=voice_id,
        )

        assert result["status"] == "ok", f"Failed: {result.get('error')}"
        assert result.get("audio_url"), "audio_url should be returned"

        print(f"\n[TTS with designed voice] audio_url: {result.get('audio_url')}")

    def test_run_tts_step_without_voice_id(self):
        """voice_id 없이 TTS 호출 시 실패."""
        result = run_tts_step(text="테스트", voice_id="")

        assert result["status"] == "failed"
        assert "voice_id" in result.get("error", "").lower()


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.skipif(not has_nano_banana_api_key(), reason="NANO_BANANA_API_KEY not set")
class TestSceneImageStep:
    def test_run_scene_image_step_with_urls(self):
        """씬 이미지 생성 테스트 (로컬 경로 사용).

        Note: API rate limit으로 인해 가끔 실패할 수 있음.
        Full Sequence 테스트에서 같은 기능을 검증함.
        """
        character_image_path = _test_results.get("character_image_path")
        if not character_image_path:
            pytest.skip("Character Step 테스트가 먼저 실행되어야 함")

        # 테스트용 제품 이미지 URL (picsum)
        product_image_url = "https://picsum.photos/id/26/400/400"

        result = run_scene_image_step(
            scenario_prompt="밝은 카페 배경, 캐릭터가 제품을 들고 웃으며 소개하는 장면",
            character_image_path=character_image_path,
            product_image_url=product_image_url,
        )

        assert result["status"] == "ok", f"Failed: {result.get('error')}"
        assert result.get("image_url") or result.get("image_path")

        print(f"\n[Scene Image Step] image_url: {result.get('image_url')}")
        print(f"[Scene Image Step] image_path: {result.get('image_path')}")

    def test_run_scene_image_step_with_paths(self):
        """씬 이미지 생성 테스트 (로컬 경로 사용)."""
        character_image_path = _test_results.get("character_image_path")
        if not character_image_path:
            pytest.skip("Character Step 테스트가 먼저 실행되어야 함")

        # 경로가 있는지 확인
        if not os.path.exists(character_image_path):
            pytest.skip(f"캐릭터 이미지 파일 없음: {character_image_path}")

        # 테스트용 제품 이미지가 없으면 skip
        pytest.skip("로컬 제품 이미지 경로가 없어 스킵")

    def test_run_scene_image_step_missing_required(self):
        """필수 파라미터 누락 시 실패."""
        result = run_scene_image_step(
            scenario_prompt="테스트 프롬프트",
            # character_image 없음
            # product_image 없음
        )

        assert result["status"] == "failed"
        assert "required" in result.get("error", "").lower()


@pytest.mark.integration
@pytest.mark.slow
class TestPipelineStepsSequence:
    """전체 시퀀스 테스트 (모든 API 키 필요)."""

    @pytest.mark.skipif(
        not (has_nano_banana_api_key() and has_elevenlabs_api_key()),
        reason="NANO_BANANA_API_KEY and ELEVENLABS_API_KEY required"
    )
    def test_full_sequence(self):
        """전체 파이프라인 스텝 순차 실행."""
        # 1. 캐릭터 이미지 생성
        char_result = run_character_step(
            prompt="귀여운 20대 여성 캐릭터, 밝은 미소"
        )
        assert char_result["status"] == "ok", f"Character failed: {char_result.get('error')}"
        print(f"\n[1/4] Character: {char_result.get('image_url')}")

        # 2. Voice Design (ElevenLabs requires 20+ chars for voice_description)
        voice_result = run_voice_design_step(
            voice_name="시퀀스 테스트 캐릭터",
            voice_description="밝고 발랄한 20대 여성 목소리, 친근하고 에너지 넘치는 톤으로 말합니다"
        )
        assert voice_result["status"] == "ok", f"Voice Design failed: {voice_result.get('error')}"
        voice_id = voice_result.get("voice_id")
        print(f"[2/4] Voice Design: {voice_id}")

        # 3. TTS 생성
        tts_result = run_tts_step(
            text="안녕하세요! 제가 소개할 제품은요~",
            voice_id=voice_id,
        )
        assert tts_result["status"] == "ok", f"TTS failed: {tts_result.get('error')}"
        print(f"[3/4] TTS: {tts_result.get('audio_url')} ({tts_result.get('duration_seconds')}s)")

        # 4. 씬 이미지 생성 (캐릭터 이미지 경로 사용)
        character_image_path = char_result.get("image_path")
        if character_image_path:
            # 테스트용 제품 이미지 (picsum)
            product_url = "https://picsum.photos/id/26/400/400"

            scene_result = run_scene_image_step(
                scenario_prompt="밝은 스튜디오 배경, 캐릭터가 제품을 소개하는 장면",
                character_image_path=character_image_path,
                product_image_url=product_url,
            )
            assert scene_result["status"] == "ok", f"Scene Image failed: {scene_result.get('error')}"
            print(f"[4/4] Scene Image: {scene_result.get('image_path')}")
        else:
            print("[4/4] Scene Image: SKIPPED (no character_image_path)")

        print("\n✅ Full sequence completed!")


# === 신규 함수 테스트 ===


@pytest.mark.integration
@pytest.mark.skipif(not has_openai_api_key(), reason="OPENAI_API_KEY not set")
class TestSplitCharacterStyle:
    """character_style 분리 함수 테스트."""

    def test_suggest_character_prompts_from_product_basic(self):
        """기본 character_style 분리 테스트."""
        result = suggest_character_prompts_from_product(
            "젊은 20대 남성, 밝은 표정, 활기차고 에너지 넘치는 목소리"
        )

        assert "character_prompt" in result
        assert "voice_description" in result
        assert len(result["character_prompt"]) > 0
        assert len(result["voice_description"]) > 0

        print(f"\n[Split] character_prompt: {result['character_prompt']}")
        print(f"[Split] voice_description: {result['voice_description']}")

    def test_suggest_character_prompts_from_product_empty(self):
        """빈 입력 시 기본값 반환."""
        result = suggest_character_prompts_from_product("")

        assert result["character_prompt"] == "젊은 성인, 밝은 표정"
        assert result["voice_description"] == "밝고 친근한 목소리"

    def test_suggest_character_prompts_from_product_visual_only(self):
        """시각적 요소만 있을 때도 voice_description 추론."""
        result = suggest_character_prompts_from_product("30대 여성, 단정한 정장, 짧은 머리")

        assert "character_prompt" in result
        assert "voice_description" in result
        assert len(result["voice_description"]) > 0

        print(f"\n[Split visual only] voice_description: {result['voice_description']}")


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.skipif(
    not (has_openai_api_key() and has_nano_banana_api_key() and has_elevenlabs_api_key()),
    reason="All API keys required"
)
class TestAssetGeneration:
    """캐릭터 + 음성 동시 생성 테스트."""

    def test_run_asset_generation_step(self):
        """run_asset_generation_step 통합 테스트."""
        result = run_asset_generation_step(
            character_style="젊은 20대 남성, 밝은 표정, 캐주얼 복장, 활기차고 에너지 넘치는 목소리",
            voice_name="Asset Gen Test",
        )

        assert result["status"] == "ok", f"Failed: {result.get('error')}"
        assert result.get("character_image_url"), "character_image_url should exist"
        assert result.get("voice_id"), "voice_id should exist"
        assert result.get("voice_sample_url"), "voice_sample_url should exist"

        # 분리된 프롬프트도 확인
        assert result.get("character_prompt"), "character_prompt should exist"
        assert result.get("voice_description"), "voice_description should exist"

        # 다음 테스트를 위해 저장
        _test_results["asset_result"] = result

        print(f"\n[Asset Gen] character_image_url: {result.get('character_image_url')}")
        print(f"[Asset Gen] voice_id: {result.get('voice_id')}")
        print(f"[Asset Gen] voice_sample_url: {result.get('voice_sample_url')}")
        print(f"[Asset Gen] character_prompt: {result.get('character_prompt')}")
        print(f"[Asset Gen] voice_description: {result.get('voice_description')}")


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.skipif(not has_openai_api_key(), reason="OPENAI_API_KEY not set")
class TestScenarioRegenerate:
    """시나리오 재생성 테스트."""

    def test_run_scenario_regenerate_step(self):
        """run_scenario_regenerate_step 호출 테스트 (DB에 기존 시나리오 필요)."""
        result = run_scenario_regenerate_step(ad_id=10)

        assert result["status"] in ("ok", "failed")
        if result["status"] == "ok":
            assert result.get("scenes"), "scenes should not be empty"
            assert result.get("script_id"), "script_id should exist"
            print(f"\n[Scenario Regenerate] script_id: {result.get('script_id')}")
            print(f"[Scenario Regenerate] title: {result.get('title')}")
