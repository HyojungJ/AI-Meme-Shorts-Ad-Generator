import os

from openai import OpenAI
from dotenv import load_dotenv

from backend.video.prompts.constants import (
    TRANSLATION_SYSTEM,
    EMOTION_TRANSLATION_SYSTEM,
)
from backend.video.config import config

load_dotenv()


class PromptTranslator:
    def __init__(self, model: str = None):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model or config.scene_builder_model

    def is_korean(self, text: str) -> bool:
        for char in text:
            if '가' <= char <= '힣':
                return True
        return False

    def translate_to_english(self, korean_text: str) -> str:
        if not korean_text or not self.is_korean(korean_text):
            return korean_text

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": TRANSLATION_SYSTEM},
                    {"role": "user", "content": korean_text}
                ],
                temperature=config.translator_temperature,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return korean_text

    def translate_emotion(self, emotion: str) -> str:
        if not emotion:
            return "neutral expression"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": EMOTION_TRANSLATION_SYSTEM},
                    {"role": "user", "content": emotion}
                ],
                temperature=config.translator_temperature,
                max_tokens=50
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return f"{emotion} expression"
