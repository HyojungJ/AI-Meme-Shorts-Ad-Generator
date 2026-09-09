from typing import Dict, Any, List

from backend.video.prompts import (
    ScenePromptBuilder,
    PromptTranslator,
    CHARACTER_PROMPTS,
    SCENE_DEFAULTS,
)
from backend.video.config import config


class SoraPromptBuilder:
    def __init__(self, use_llm: bool = True, model: str = None):
        model = model or config.scene_builder_model
        self.scene_builder = ScenePromptBuilder(use_llm=use_llm, model=model)
        self.translator = PromptTranslator(model=model)
        self.use_llm = use_llm

    def build_scene_prompt(
        self,
        scene_data: Dict[str, Any],
        character_infos: Dict[str, Dict] = None,
        background_context: str = None
    ) -> str:
        return self.scene_builder.build(
            scene_data=scene_data,
            character_infos=character_infos,
            background_context=background_context
        )

    def build_prompts_for_scenes(
        self,
        scenes: List[Dict[str, Any]],
        character_infos: Dict[str, Dict] = None
    ) -> List[Dict[str, Any]]:
        return self.scene_builder.build_batch(scenes, character_infos)

    def build_prompt(
        self,
        beat: Dict[str, Any],
        character_info: Dict[str, Any] = None
    ) -> str:
        beat_type = beat.get("type", "dialogue")
        character = beat.get("character", "부장")
        duration = beat.get("duration", 4)

        char_prompt = self._get_character_prompt(character, character_info)

        if beat_type == "dialogue":
            motion = self._build_dialogue_motion(beat)
        elif beat_type == "reaction":
            motion = self._build_reaction_motion(beat)
        elif beat_type == "action":
            motion = self._build_action_motion(beat)
        else:
            motion = "Character in natural pose, subtle breathing animation."

        has_dialogue = beat_type == "dialogue" or beat.get("text")
        lip_sync = (
            "Character speaks with simple anime-style mouth animation."
            if has_dialogue else
            "Character remains silent with natural subtle movements."
        )

        return f"""{char_prompt}

{motion}

{lip_sync}
Chibi 3D rendered style, cute expressive character.
Vertical video format (9:16), office background.
Smooth animation, {duration} seconds duration."""

    def _get_character_prompt(
        self,
        character: str,
        character_info: Dict[str, Any] = None
    ) -> str:
        if character_info and character_info.get("video_gen_prompt"):
            return character_info["video_gen_prompt"]

        char_data = CHARACTER_PROMPTS.get(character, CHARACTER_PROMPTS["부장"])
        return f"{char_data['appearance']}, {char_data['style']}"

    def _build_dialogue_motion(self, beat: Dict[str, Any]) -> str:
        text = beat.get("text", "")

        if "!" in text:
            emotion = "excited and animated"
        elif "?" in text:
            emotion = "curious, slightly tilted head"
        elif "..." in text:
            emotion = "hesitant, trailing off"
        else:
            emotion = "natural conversational"

        return f"""Character is speaking with {emotion} expression.
Natural talking gestures, slight hand movements while speaking.
Mouth opens and closes rhythmically with speech.
Looking at conversation partner or camera."""

    def _build_reaction_motion(self, beat: Dict[str, Any]) -> str:
        emotion = beat.get("emotion", "neutral")
        emotion_desc = self.translator.translate_emotion(emotion)

        return f"""Character reacts with {emotion_desc}.
Expressive face showing clear emotion.
Subtle body language matching the reaction.
No dialogue, pure visual reaction."""

    def _build_action_motion(self, beat: Dict[str, Any]) -> str:
        motion_prompt = beat.get("motion_prompt", "")

        if motion_prompt:
            if self.translator.is_korean(motion_prompt):
                return self.translator.translate_to_english(motion_prompt)
            return motion_prompt

        return "Character performs natural idle animation, slight movements."


def main():
    builder = SoraPromptBuilder(use_llm=True)

    # 테스트 씬
    test_scene = {
        "scene_number": 1,
        "scene_type": "hook",
        "beats": [
            {
                "beat_id": "1-1",
                "type": "dialogue",
                "character": "부장",
                "text": "야, 이거 봐봐! 매끈매끈하다 매끈매끈한!",
                "duration": 2.5
            },
            {
                "beat_id": "1-2",
                "type": "reaction",
                "character": "사원",
                "emotion": "의아함",
                "duration": 2.5
            },
        ]
    }

    print("=== Scene Prompt Test ===\n")
    prompt = builder.build_scene_prompt(test_scene)
    print(prompt)


if __name__ == "__main__":
    main()
