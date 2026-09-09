import os
import re

from typing import Dict, Any, List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from backend.scenario.config import config
from backend.scenario.prompts import CHARACTER_GUIDES

load_dotenv()


class DialogueGenerator:
    MODEL_PRESETS = {
        "eeve": {
            "type": "hf",
            "model_id": "HyojungJ/eeve-persona-memefluencer",
            "base_model_id": "yanolja/YanoljaNEXT-EEVE-Instruct-10.8B",
        },
        "gpt-4o": {"type": "openai", "model_id": "gpt-4o"},
        "gpt-4o-mini": {"type": "openai", "model_id": "gpt-4o-mini"},
        "gpt-4.1": {"type": "openai", "model_id": "gpt-4.1"},
    }

    def __init__(self, model: str = None, load_in_4bit: bool = None, device_map: str = None):
        model = model or config.dialogue_model
        load_in_4bit = load_in_4bit if load_in_4bit is not None else config.eeve_load_in_4bit
        device_map = device_map or config.eeve_device_map
        self.model_name = model
        self.load_in_4bit = load_in_4bit
        self.device_map = device_map

        if model in self.MODEL_PRESETS:
            preset = self.MODEL_PRESETS[model]
            self.model_type = preset["type"]
            self.model_id = preset["model_id"]
            self.base_model_id = preset.get("base_model_id")
        elif model.startswith("gpt"):
            self.model_type = "openai"
            self.model_id = model
            self.base_model_id = None
        else:
            self.model_type = "hf"
            self.model_id = model
            self.base_model_id = None

        self._hf_model = None
        self._hf_tokenizer = None
        self._openai_client = None
        self._loaded = False

    def _load_openai(self):
        if self._openai_client is not None:
            return
        self._openai_client = ChatOpenAI(
            model=self.model_id,
            temperature=config.dialogue_temperature,
            max_tokens=100,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        self._loaded = True

    def _load_hf_model(self):
        if self._loaded:
            return

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from peft import PeftModel

        base_model_id = self.base_model_id or self.model_id

        if self.load_in_4bit:
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True
            )
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_id,
                quantization_config=bnb_config,
                device_map=self.device_map,
                trust_remote_code=True
            )
        else:
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_id,
                torch_dtype=torch.float16,
                device_map=self.device_map,
                trust_remote_code=True
            )

        if self.base_model_id and self.model_id != self.base_model_id:
            self._hf_model = PeftModel.from_pretrained(base_model, self.model_id)
        else:
            self._hf_model = base_model

        self._hf_model.eval()

        self._hf_tokenizer = AutoTokenizer.from_pretrained(base_model_id, trust_remote_code=True)
        if self._hf_tokenizer.pad_token is None:
            self._hf_tokenizer.pad_token = self._hf_tokenizer.eos_token

        self._loaded = True

    def generate_all(
        self,
        skeleton: Dict[str, Any],
        characters: List[Dict[str, Any]],
        meme_data: Dict[str, Any] = None
    ) -> Dict[str, List[Dict[str, str]]]:
        dialogues = {}

        for character in characters:
            char_name = character["name"]
            char_dialogues = self._generate_for_character(skeleton, character, meme_data)
            dialogues[char_name] = char_dialogues

        return dialogues

    def _generate_for_character(
        self,
        skeleton: Dict[str, Any],
        character: Dict[str, Any],
        meme_data: Dict[str, Any] = None
    ) -> List[Dict[str, str]]:
        char_name = character["name"]
        dialogues = []

        scene_context = self._build_scene_context(skeleton)

        for scene in skeleton.get("scenes", []):
            for beat in scene.get("beats", []):
                if beat.get("character") != char_name:
                    continue
                if beat.get("type") != "dialogue":
                    continue

                text = beat.get("text", "")
                if not text.startswith("[PLACEHOLDER"):
                    dialogues.append({
                        "beat_id": beat["beat_id"],
                        "text": text
                    })
                    continue

                placeholder = self._extract_placeholder(text)
                generated_text = self._generate_single(
                    character, scene_context, {
                        "beat_id": beat["beat_id"],
                        "placeholder": placeholder,
                        "scene_type": scene.get("scene_type", ""),
                        "comedy_beat": scene.get("comedy_beat", "")
                    },
                    meme_data
                )

                dialogues.append({
                    "beat_id": beat["beat_id"],
                    "text": generated_text
                })

        return dialogues

    def _generate_single(
        self,
        character: Dict[str, Any],
        scene_context: str,
        beat_info: Dict[str, Any],
        meme_data: Dict[str, Any] = None
    ) -> str:
        if self.model_type == "openai":
            return self._generate_openai(character, scene_context, beat_info, meme_data)
        else:
            return self._generate_hf(character, scene_context, beat_info, meme_data)

    def _generate_openai(
        self,
        character: Dict[str, Any],
        scene_context: str,
        beat_info: Dict[str, Any],
        meme_data: Dict[str, Any] = None
    ) -> str:
        self._load_openai()

        system_prompt, user_prompt = self._build_chat_prompt(
            character, scene_context, beat_info, meme_data
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = self._openai_client.invoke(messages)
        result = response.content.strip().strip('"').strip("'")
        return result

    def _generate_hf(
        self,
        character: Dict[str, Any],
        scene_context: str,
        beat_info: Dict[str, Any],
        meme_data: Dict[str, Any] = None
    ) -> str:
        import torch

        self._load_hf_model()

        prompt = self._build_eeve_prompt(character, scene_context, beat_info, meme_data)

        inputs = self._hf_tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        ).to(self._hf_model.device)

        with torch.no_grad():
            outputs = self._hf_model.generate(
                **inputs,
                max_new_tokens=50,
                temperature=0.8,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1,
                pad_token_id=self._hf_tokenizer.pad_token_id,
                eos_token_id=self._hf_tokenizer.eos_token_id
            )

        generated = self._hf_tokenizer.decode(
            outputs[0][inputs.input_ids.shape[1]:],
            skip_special_tokens=True
        )
        return generated.strip().split("\n")[0].strip().strip('"').strip("'")

    def _build_chat_prompt(
        self,
        character: Dict[str, Any],
        scene_context: str,
        beat_info: Dict[str, Any],
        meme_data: Dict[str, Any] = None
    ) -> tuple[str, str]:
        char_name = character["name"]
        char_guide = CHARACTER_GUIDES.get(char_name, "")
        style_tags = ", ".join(character.get("style_tags", []))

        meme_hint = ""
        if meme_data:
            key_phrase = meme_data.get("key_phrase", "")
            if key_phrase:
                meme_hint = f"\n밈 핵심 대사: \"{key_phrase}\""

        system_prompt = f"""당신은 '{char_name}' 캐릭터입니다.

{character['description']}

말투: {character['style']}
스타일: {style_tags}
{char_guide}

규칙:
- 캐릭터의 말투와 성격을 유지하세요
- 10-30자 내외의 짧은 대사만 생성하세요
- 대사만 출력하세요 (따옴표, 설명 없이)"""

        user_prompt = f"""다음 상황에 맞는 대사를 생성하세요.

## 씬 맥락
{scene_context}

## 생성할 대사
- 비트 ID: {beat_info['beat_id']}
- 씬 타입: {beat_info.get('scene_type', '')}
- 상황: {beat_info.get('placeholder', '')}
{meme_hint}"""

        return system_prompt, user_prompt

    def _build_eeve_prompt(
        self,
        character: Dict[str, Any],
        scene_context: str,
        beat_info: Dict[str, Any],
        meme_data: Dict[str, Any] = None
    ) -> str:
        char_name = character["name"]
        char_guide = CHARACTER_GUIDES.get(char_name, "")
        style_tags = ", ".join(character.get("style_tags", []))

        meme_hint = ""
        if meme_data:
            key_phrase = meme_data.get("key_phrase", "")
            if key_phrase:
                meme_hint = f"\n밈 핵심 대사: \"{key_phrase}\""

        system_prompt = f"""당신은 '{char_name}' 캐릭터입니다.

{character['description']}

말투: {character['style']}
스타일: {style_tags}
{char_guide}"""

        user_prompt = f"""다음 상황에 맞는 대사를 생성하세요.

## 씬 맥락
{scene_context}

## 생성할 대사
- 비트 ID: {beat_info['beat_id']}
- 씬 타입: {beat_info.get('scene_type', '')}
- 상황: {beat_info.get('placeholder', '')}
{meme_hint}

규칙:
- {char_name}의 말투로 자연스럽게
- 10-30자 내외
- 대사만 출력 (따옴표 없이)"""

        return f"""### System:
{system_prompt}

### User:
{user_prompt}

### Assistant:
"""

    def _build_scene_context(self, skeleton: Dict[str, Any]) -> str:
        context_parts = [f"제목: {skeleton.get('title', '')}"]

        for scene in skeleton.get("scenes", []):
            scene_num = scene.get("scene_number", 0)
            scene_type = scene.get("scene_type", "")
            context_parts.append(f"\n[씬 {scene_num}: {scene_type}]")

            for beat in scene.get("beats", []):
                beat_id = beat.get("beat_id", "")
                beat_type = beat.get("type", "")
                char = beat.get("character", "")
                text = beat.get("text") or beat.get("emotion") or beat.get("motion_prompt") or ""
                context_parts.append(f"  - {beat_id} ({beat_type}): {char} - {text[:50]}...")

        return "\n".join(context_parts)

    def _extract_placeholder(self, text: str) -> str:
        match = re.search(r'\[PLACEHOLDER:\s*(.+?)\]', text)
        if match:
            return match.group(1)
        return text

    def unload(self):
        if self._hf_model is not None:
            import torch
            del self._hf_model
            del self._hf_tokenizer
            self._hf_model = None
            self._hf_tokenizer = None
            torch.cuda.empty_cache()
            self._loaded = False


def main():
    import argparse
    import json
    from backend.db import ScenarioRepository
    from backend.scenario.generators import SkeletonGenerator

    parser = argparse.ArgumentParser(description="캐릭터 대사 생성")
    parser.add_argument("--meme-id", type=int, required=True, help="밈 ID")
    parser.add_argument("--model", type=str, default="gpt-4o-mini",
                        help="모델 (gpt-4o-mini, gpt-4o, eeve)")
    parser.add_argument("--no-4bit", action="store_true", help="4bit 양자화 비활성화 (EEVE)")
    args = parser.parse_args()

    repo = ScenarioRepository()

    # 밈 데이터 조회
    meme = repo.get_meme_with_details(args.meme_id)
    if not meme:
        print(f"[ERROR] 밈 ID {args.meme_id} 없음")
        return

    # 캐릭터 조회
    characters = repo.get_characters()

    # 1단계: 골격 생성
    print("[1단계] 골격 생성 중...")
    skeleton_gen = SkeletonGenerator()
    skeleton = skeleton_gen.generate(meme, characters)
    print(f"  → 제목: {skeleton.title}")

    # 2단계: 대사 생성
    print(f"\n[2단계] 대사 생성 중... (모델: {args.model})")
    dialogue_gen = DialogueGenerator(
        model=args.model,
        load_in_4bit=not args.no_4bit
    )
    dialogues = dialogue_gen.generate_all(skeleton.model_dump(), characters, meme)

    print("\n=== 생성된 대사 ===")
    print(json.dumps(dialogues, ensure_ascii=False, indent=2))

    # 메모리 정리
    dialogue_gen.unload()


if __name__ == "__main__":
    main()
