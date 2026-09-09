from functools import lru_cache

from google import genai
from openai import OpenAI

from common.config import config


@lru_cache(maxsize=1)
def get_openai() -> OpenAI:
    return OpenAI(api_key=config.openai_api_key)


@lru_cache(maxsize=1)
def get_gemini() -> genai.Client:
    return genai.Client(api_key=config.gemini_api_key)
