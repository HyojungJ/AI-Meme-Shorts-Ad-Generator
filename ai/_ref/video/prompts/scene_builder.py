import os

from typing import Dict, Any, List
from openai import OpenAI
from dotenv import load_dotenv

from backend.video.prompts.constants import (
    CHARACTER_PROMPTS,
    SCENE_DEFAULTS,
    SCENE_PROMPT_SYSTEM,
)
from backend.video.prompts.translator import PromptTranslator
from backend.video.config import config

load_dotenv()


class ScenePromptBuilder:
    def __init__(self, use_llm: bool = True, model: str = None):
        self.use_llm = use_llm
        self.model = model or config.scene_builder_model
        if use_llm:
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.translator = PromptTranslator(model=self.model)

    def build(
        self,
        scene_data: Dict[str, Any],
        character_infos: Dict[str, Dict] = None,
        background_context: str = None
    ) -> str:
        scene_type = scene_data.get("scene_type", "hook")
        beats = scene_data.get("beats", [])
        scene_motion_prompt = scene_data.get("scene_motion_prompt")

        extracted = self._extract_from_beats(beats)
        characters_in_scene = extracted["characters"]
        dialogues = extracted["dialogues"]
        emotions = extracted["emotions"]
        beat_motion_prompts = extracted["motion_prompts"]
        speaking_timings = extracted["speaking_timings"]
        total_duration = extracted["total_duration"]

        all_motions = []
        if scene_motion_prompt:
            all_motions.append(scene_motion_prompt)
        all_motions.extend(beat_motion_prompts)
        combined_motion = "\n".join(all_motions) if all_motions else None

        char_descriptions = self._build_character_descriptions(
            characters_in_scene or ["부장"],
            character_infos
        )

        if self.use_llm:
            return self._generate_with_llm(
                scene_type=scene_type,
                characters=char_descriptions,
                dialogues=dialogues,
                emotions=emotions,
                motion_prompt=combined_motion,
                background_context=background_context,
                speaking_timings=speaking_timings,
                total_duration=total_duration
            )

        return self._generate_from_template(
            scene_type=scene_type,
            characters=char_descriptions,
            emotions=emotions,
            motion_prompt=combined_motion,
            background_context=background_context
        )

    def build_batch(
        self,
        scenes: List[Dict[str, Any]],
        character_infos: Dict[str, Dict] = None
    ) -> List[Dict[str, Any]]:
        results = []

        for scene in scenes:
            sora_prompt = self.build(scene, character_infos)
            results.append({
                "scene_number": scene.get("scene_number"),
                "scene_type": scene.get("scene_type"),
                "sora_prompt": sora_prompt,
                "beats_count": len(scene.get("beats", [])),
            })

        return results

    def _extract_from_beats(self, beats: List[Dict]) -> Dict[str, Any]:
        dialogues = []
        emotions = []
        characters = set()
        motion_prompts = []
        speaking_timings = []

        current_time = 0.0
        for beat in beats:
            duration = beat.get("duration", 2.0)
            char = beat.get("character", "부장")
            beat_type = beat.get("type", "dialogue")
            text = beat.get("text", "")

            if text and beat_type in ("dialogue", "action"):
                dialogues.append(f"{char}: {text}")
                characters.add(char)
                position = "LEFT" if char == "부장" else "RIGHT"
                dialogue_start = current_time + 0.3 if speaking_timings else current_time
                speaking_timings.append({
                    "start": dialogue_start,
                    "end": dialogue_start + duration - 0.3,  # duration 내에서 처리
                    "character": char,
                    "position": position,
                    "text": text,
                })

            if beat.get("emotion"):
                emotions.append(beat["emotion"])

            if beat.get("motion_prompt"):
                motion_prompts.append(beat["motion_prompt"])
                characters.add(char)

            current_time += duration

        return {
            "dialogues": dialogues,
            "emotions": emotions,
            "characters": list(characters),
            "motion_prompts": motion_prompts,
            "speaking_timings": speaking_timings,
            "total_duration": current_time,
        }

    def _build_character_descriptions(
        self,
        characters: List[str],
        character_infos: Dict[str, Dict]
    ) -> List[str]:
        descriptions = []

        for char_name in characters:
            if character_infos and char_name in character_infos:
                desc = character_infos[char_name].get("video_gen_prompt", "")
                descriptions.append(f"{char_name}: {desc}")
            else:
                char_data = CHARACTER_PROMPTS.get(char_name, CHARACTER_PROMPTS["부장"])
                descriptions.append(f"{char_name}: {char_data['appearance']}")

        return descriptions

    def _generate_with_llm(
        self,
        scene_type: str,
        characters: List[str],
        dialogues: List[str],
        emotions: List[str],
        motion_prompt: str,
        background_context: str,
        speaking_timings: List[Dict] = None,
        total_duration: float = 5.0
    ) -> str:
        dialogue_lines = []
        if speaking_timings:
            for t in speaking_timings:
                if t.get("text"):
                    char = "Boss" if t["character"] == "부장" else "Employee"
                    dialogue_lines.append(f'{char}: "{t["text"]}"')

        action_desc = "natural conversation"
        if scene_type == "meme" and motion_prompt:
            action_desc = "Boss performs the meme dance with arm swinging movements"

        user_prompt = f"""Create a SIMPLE Sora prompt for a {total_duration:.0f}-second {scene_type} scene.

Setting: Modern Korean office
Action: {action_desc}

Dialogue (in order):
{chr(10).join(dialogue_lines) if dialogue_lines else 'No dialogue'}

Keep the prompt under 100 words. No timing numbers. No visual effects."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SCENE_PROMPT_SYSTEM},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=config.scene_builder_temperature,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()

        except Exception:
            return self._generate_from_template(
                scene_type, characters, emotions, motion_prompt, background_context
            )

    def _generate_from_template(
        self,
        scene_type: str,
        characters: List[str],
        emotions: List[str],
        motion_prompt: str,
        background_context: str
    ) -> str:
        defaults = SCENE_DEFAULTS.get(scene_type, SCENE_DEFAULTS["hook"])

        char_desc = " and ".join([
            c.split(": ")[1] if ": " in c else c
            for c in characters
        ])
        emotion_desc = ", ".join(emotions) if emotions else "natural expression"
        action = motion_prompt or f"Natural {scene_type} scene interaction"
        bg_setting = background_context or config.default_background

        return f"""[SETTING]
{bg_setting}

[CAMERA]
{defaults['camera']}

[LIGHTING]
Soft overhead fluorescent lighting, neutral white tones, subtle shadows on faces

[CHARACTERS & ACTION]
{char_desc}
{action}
Emotions: {emotion_desc}

[STYLE]
Chibi 3D animation, cute proportions, expressive faces, smooth motion
Vertical video format (9:16), 4 seconds duration
Mood: {defaults['mood']}"""
