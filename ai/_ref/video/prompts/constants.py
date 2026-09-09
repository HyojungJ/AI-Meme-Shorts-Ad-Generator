CHARACTER_PROMPTS = {
    "부장": {
        "appearance": "Middle-aged Korean man in his 50s, wearing grey formal suit with red tie, round glasses, brown hair with slight grey, friendly but awkward demeanor",
        "style": "chibi 3D character style, cute proportions, expressive face",
        "personality": "enthusiastic about memes but slightly awkward, dad-joke energy",
        "position": "LEFT"  # 이미지에서 왼쪽에 위치
    },
    "사원": {
        "appearance": "Young Korean male office worker in his 20s, smart casual business attire, modern hairstyle, slightly tired expression",
        "style": "chibi 3D character style, cute proportions, expressive face",
        "personality": "Gen-Z energy, often confused or exasperated by the manager",
        "position": "RIGHT"  # 이미지에서 오른쪽에 위치
    }
}

SCENE_DEFAULTS = {
    "hook": {
        "camera": "Medium shot, eye level, static camera with slight push-in",
        "mood": "attention-grabbing, curious energy"
    },
    "setup": {
        "camera": "Medium two-shot, eye level, static camera",
        "mood": "building intrigue, comedic setup"
    },
    "buildup": {
        "camera": "Medium shot to close-up, slight dolly forward, building tension",
        "mood": "anticipation, nervous energy"
    },
    "meme": {
        "camera": "Medium full shot, centered framing, slight zoom out for action",
        "mood": "climactic, maximum energy, comedic payoff"
    },
    "punchline": {
        "camera": "Two-shot or reaction close-up, static, comedic timing",
        "mood": "comedic release, satisfaction vs disbelief"
    }
}

SCENE_PROMPT_SYSTEM = """You are a Sora 2 prompt writer. Keep prompts SHORT and SIMPLE.

## Characters (from reference image):
- Boss (LEFT): 50s Korean man, grey suit, glasses
- Employee (RIGHT): 20s Korean man, casual style

## Output Format (SIMPLE):
```
[Scene description in 1-2 sentences]

Characters:
- Boss (left): [brief action]
- Employee (right): [brief action]

Dialogue:
Boss: "[Korean line]"
Employee: "[Korean line]"

Style: Chibi 3D animation, vertical video (9:16), [duration]s
Audio: Clear dialogue only, no background music
```

## Rules:
1. Keep dialogue SHORT - max 1 sentence per character per turn
2. Label speakers as "Boss:" or "Employee:"
3. NO complex timing like "0.0-2.5s" - Sora handles timing
4. NO visual effects or transitions
5. Simple actions only - no elaborate choreography descriptions
6. For meme scenes: describe the key action simply"""

TRANSLATION_SYSTEM = """Translate the following Korean motion description to English for AI video generation. Keep it concise and descriptive."""

EMOTION_TRANSLATION_SYSTEM = """Convert the Korean emotion to an English facial/body expression description for AI video generation.
Output format: [expression], [body language]
Example: "의아함" → "puzzled and confused expression, tilted head, raised eyebrow"
Keep it concise (under 15 words). Output only the description."""

ENHANCEMENT_SYSTEM = """You are a Sora video generation prompt expert.
Enhance the given prompt to be more specific and cinematic.
Keep it under 150 words. Focus on:
- Clear character actions and movements
- Facial expressions
- Camera framing (vertical video)
- Animation style consistency
Output only the enhanced prompt, no explanations."""
