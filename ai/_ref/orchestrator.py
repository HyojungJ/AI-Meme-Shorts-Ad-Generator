import hashlib

from langgraph.graph import END, StateGraph

from common.db import (
    get_connection,
    MemeRepository,
    CompanyCharacterRepository,
    VoiceGenerationRepository,
    ImageGenerationRepository,
    SceneVideoRepository,
    VideoRepository,
    ScriptRepository,
)
from content_pipeline.state import ContentPipelineState, SceneAsset
from content_pipeline.voice.graph import get_voice_graph
from content_pipeline.voice.state import get_initial_state as get_voice_state
from content_pipeline.image.nodes import generate_character_image_node, generate_scene_image_node
from content_pipeline.video.graph import run_video
from content_pipeline.pipeline import (
    generate_scenario_task,
    generate_character_image_task,
    generate_scene_image_task,
    convert_to_scenes,
)


# === Node: Init ===

def init_node(state: ContentPipelineState) -> dict:
    """Load meme data from DB."""
    meme_id = state.get("meme_id")

    if not meme_id:
        return {
            "phase": "character",
            "status": "running",
        }

    with get_connection() as conn:
        meme = MemeRepository(conn).get(meme_id)

    if not meme:
        return {
            "phase": "failed",
            "status": "failed",
            "errors": [f"Meme {meme_id} not found"],
        }

    return {
        "meme_name": meme.get("meme_name"),
        "meme_definition": meme.get("definition"),
        "meme_type": meme.get("meme_type", "quotable"),
        "key_phrase": meme.get("key_phrase"),
        "phase": "character",
        "status": "running",
    }


# === Node: Character ===

def character_node(state: ContentPipelineState) -> dict:
    """Load existing character or generate new character image."""
    character = state.get("character", {})
    character_id = character.get("character_id")

    # 1. ê¸°ì¡´ ìºë¦­??ë¡ë
    if character_id:
        with get_connection() as conn:
            char_data = CompanyCharacterRepository(conn).get(character_id)
        if char_data:
            return {
                "character": {
                    "character_id": char_data["character_id"],
                    "character_name": char_data.get("character_name"),
                    "image_url": char_data.get("image_url"),
                    "image_prompt": char_data.get("image_prompt"),
                    "elevenlabs_voice_id": char_data.get("elevenlabs_voice_id"),
                    "voice_design_prompt": char_data.get("voice_design_prompt"),
                },
                "phase": "scenario",
            }

    # 2. ??ìºë¦­???´ë?ì§ ?ì± (character_prompt ?ì)
    character_prompt = character.get("image_prompt") or state.get("character_style_raw")
    if character_prompt:
        result = generate_character_image_node({
            "character_prompt": character_prompt,
            "aspect_ratio": "9:16",
        })

        if result.get("status") == "ok":
            return {
                "character": {
                    **character,
                    "image_url": result.get("character_image_url"),
                    "image_prompt": character_prompt,
                },
                "phase": "scenario",
            }
        else:
            return {
                "phase": "failed",
                "status": "failed",
                "errors": state.get("errors", []) + [result.get("error", "Character image generation failed")],
            }

    # 3. ìºë¦­???ë³´ ?ì
    return {
        "phase": "failed",
        "status": "failed",
        "errors": state.get("errors", []) + ["No character_id or character_prompt provided"],
    }


# === Node: Scenario ===

def scenario_node(state: ContentPipelineState) -> dict:
    """Generate scenario script using team's scenario_agent."""
    ad_id = state.get("ad_id")
    meme_id = state.get("meme_id")

    if not ad_id or not meme_id:
        return {
            "phase": "failed",
            "status": "failed",
            "errors": state.get("errors", []) + ["ad_id and meme_id are required"],
        }

    try:
        result = generate_scenario_task(ad_id, meme_id).result()
    except Exception as e:
        return {
            "phase": "failed",
            "status": "failed",
            "errors": state.get("errors", []) + [str(e)],
        }

    return {
        "scenes": result.get("scenes", []),
        "title": result.get("title", f"{state.get('item_name', 'Unknown')} ê´ê³ "),
        "description": "",
        "total_duration": result.get("total_duration", 0),
        "hashtags": [],
        "script_id": result.get("script_id"),
        "phase": "voice",
    }


# === Node: Voice ===

def voice_node(state: ContentPipelineState) -> dict:
    """Generate TTS for each scene."""
    character = state.get("character", {})
    voice_id = character.get("elevenlabs_voice_id")
    voice_description = character.get("voice_design_prompt")
    scenes = state.get("scenes", [])

    if not scenes:
        return {"phase": "image"}

    voice_graph = get_voice_graph()
    scene_assets: list[SceneAsset] = []

    for scene in scenes:
        dialogue = scene.get("dialogue", "")
        if not dialogue:
            continue

        voice_state = get_voice_state(
            text=dialogue,
            voice_id=voice_id,
            voice_description=voice_description,
        )
        result = voice_graph.invoke(voice_state)

        if result.get("status") == "failed":
            continue

        asset: SceneAsset = {
            "scene_key": scene["scene_key"],
            "audio_url": result.get("audio_url"),
            "duration_seconds": result.get("duration_seconds"),
        }

        # Update voice_id if newly designed
        if not voice_id and result.get("voice_id"):
            voice_id = result["voice_id"]

        scene_assets.append(asset)

    # Update character with voice_id if newly created
    updated_character = dict(character)
    if voice_id and not character.get("elevenlabs_voice_id"):
        updated_character["elevenlabs_voice_id"] = voice_id

    return {
        "scene_assets": scene_assets,
        "character": updated_character,
        "phase": "image",
    }


# === Node: Image ===

def image_node(state: ContentPipelineState) -> dict:
    """Generate scene image (character + product + scenario) for first scene."""
    character = state.get("character", {})
    item_images = state.get("item_images", [])
    scenes = state.get("scenes", [])
    scene_assets = list(state.get("scene_assets", []))

    if not scenes:
        return {"phase": "scene_video"}

    # ì²?ë²ì§¸ ?¬ì ??????´ë?ì§ ?ì±
    first_scene = scenes[0]
    product_image_url = item_images[0] if item_images else None
    character_image_url = character.get("image_url")

    # scenario_prompt: ?¬ë³ ?ë¡¬?í¸ ?ë ê¸°ë³¸ê°?
    scenario_prompt = first_scene.get("scenario_prompt") or f"{state.get('item_name', '')} ?í ê´ê³  ?¥ë©´"

    result = generate_scene_image_node({
        "scenario_prompt": scenario_prompt,
        "product_image_url": product_image_url,
        "character_image_url": character_image_url,
        "aspect_ratio": "9:16",
    })

    if result.get("status") == "ok":
        # scene_assets ?ë°?´í¸
        if scene_assets:
            scene_assets[0]["image_url"] = result.get("image_url")
        else:
            scene_assets.append({
                "scene_key": first_scene["scene_key"],
                "image_url": result.get("image_url"),
            })

    return {
        "scene_assets": scene_assets,
        "phase": "scene_video",
    }


# === Node: Scene Video ===

def scene_video_node(state: ContentPipelineState) -> dict:
    """Generate video for each scene using video module."""
    scene_assets = state.get("scene_assets", [])
    scenes = state.get("scenes", [])
    character = state.get("character", {})
    ad_id = state.get("ad_id")
    company_id = state.get("company_id")

    if not scene_assets:
        return {"phase": "compose"}

    result = run_video(
        script_id=state.get("script_id"),
        ad_id=ad_id,
        company_id=company_id,
        scenes=scenes,
        scene_assets=scene_assets,
        character_image_url=character.get("image_url"),
    )

    if result.get("status") == "failed":
        return {
            "phase": "failed",
            "status": "failed",
            "errors": state.get("errors", []) + result.get("errors", ["Video generation failed"]),
        }

    # Update scene_assets with video URLs
    updated_assets = list(scene_assets)
    for clip in result.get("scene_clips", []):
        scene_key = clip.get("scene_key")
        for asset in updated_assets:
            if asset.get("scene_key") == scene_key:
                asset["video_url"] = clip.get("video_url")
                break

    return {
        "scene_assets": updated_assets,
        "video_url": result.get("video_url"),
        "thumbnail_url": result.get("thumbnail_url"),
        "total_cost": state.get("total_cost", 0) + result.get("total_cost", 0),
        "phase": "compose",
    }


# === Node: Compose ===

def compose_node(state: ContentPipelineState) -> dict:
    """Final composition - video module handles this in scene_video_node."""
    video_url = state.get("video_url")

    if not video_url:
        return {
            "phase": "failed",
            "status": "failed",
            "errors": state.get("errors", []) + ["No video URL generated"],
        }

    return {
        "phase": "done",
        "status": "completed",
    }


# === Node: Save ===

def save_node(state: ContentPipelineState) -> dict:
    """Save results to DB."""
    ad_id = state.get("ad_id")
    company_id = state.get("company_id")
    character = state.get("character", {})
    character_id = character.get("character_id")
    scenes = state.get("scenes", [])
    scene_assets = state.get("scene_assets", [])
    title = state.get("title", "")
    description = state.get("description", "")
    video_url = state.get("video_url")
    thumbnail_url = state.get("thumbnail_url")
    total_duration = state.get("total_duration", 0)

    try:
        with get_connection() as conn:
            # 1. Save script
            script_repo = ScriptRepository(conn)
            script_id = script_repo.save({
                "meme_id": state.get("meme_id"),
                "title": title,
                "description": description,
                "total_duration": total_duration,
                "scenes": scenes,
                "hashtags": state.get("hashtags", []),
            })

            # 2. Save voice_generations
            voice_repo = VoiceGenerationRepository(conn)
            for asset in scene_assets:
                if asset.get("audio_url"):
                    text = ""
                    for scene in scenes:
                        if scene.get("scene_key") == asset.get("scene_key"):
                            text = scene.get("dialogue", "")
                            break
                    voice_repo.create({
                        "character_id": character_id,
                        "script_id": script_id,
                        "scene_key": asset.get("scene_key"),
                        "text_content": text,
                        "text_hash": hashlib.md5(text.encode()).hexdigest() if text else None,
                        "audio_url": asset.get("audio_url"),
                        "duration_seconds": asset.get("duration_seconds"),
                    })

            # 3. Save image_generations
            image_repo = ImageGenerationRepository(conn)
            for asset in scene_assets:
                if asset.get("image_url"):
                    prompt = ""
                    for scene in scenes:
                        if scene.get("scene_key") == asset.get("scene_key"):
                            prompt = scene.get("scenario_prompt", "")
                            break
                    image_repo.create({
                        "character_id": character_id,
                        "script_id": script_id,
                        "prompt": prompt,
                        "model": "nanobanana",
                        "image_url": asset.get("image_url"),
                    })

            # 4. Save scene_videos
            scene_video_repo = SceneVideoRepository(conn)
            for asset in scene_assets:
                if asset.get("video_url"):
                    scene_video_repo.create({
                        "script_id": script_id,
                        "scene_key": asset.get("scene_key"),
                        "voice_gen_id": asset.get("voice_gen_id"),
                        "image_id": asset.get("image_id"),
                        "video_url": asset.get("video_url"),
                        "duration_seconds": asset.get("duration_seconds"),
                        "generation_model": "sora",
                    })

            # 5. Save final video
            video_repo = VideoRepository(conn)
            video_id = video_repo.create({
                "ad_id": ad_id,
                "company_id": company_id,
                "script_id": script_id,
                "title": title,
                "description": description,
                "s3_url": video_url,
                "thumbnail_url": thumbnail_url,
                "duration_seconds": int(total_duration),
                "status": "completed",
            })

            return {
                "script_id": script_id,
                "video_id": video_id,
            }

    except Exception as e:
        return {
            "errors": state.get("errors", []) + [f"DB save failed: {str(e)}"],
        }


# === Router ===

def route_after_init(state: ContentPipelineState) -> str:
    if state.get("phase") == "failed":
        return "end"
    return "character"


def route_after_character(state: ContentPipelineState) -> str:
    if state.get("phase") == "failed":
        return "end"
    return "scenario"


def route_after_compose(state: ContentPipelineState) -> str:
    return "save"


# === Graph Builder ===

def create_pipeline_graph():
    graph = StateGraph(ContentPipelineState)

    # Add nodes
    graph.add_node("init", init_node)
    graph.add_node("character", character_node)
    graph.add_node("scenario", scenario_node)
    graph.add_node("voice", voice_node)
    graph.add_node("image", image_node)
    graph.add_node("scene_video", scene_video_node)
    graph.add_node("compose", compose_node)
    graph.add_node("save", save_node)

    # Set entry point
    graph.set_entry_point("init")

    # Add edges
    graph.add_conditional_edges("init", route_after_init, {"character": "character", "end": END})
    graph.add_conditional_edges("character", route_after_character, {"scenario": "scenario", "end": END})
    graph.add_edge("scenario", "voice")
    graph.add_edge("voice", "image")
    graph.add_edge("image", "scene_video")
    graph.add_edge("scene_video", "compose")
    graph.add_conditional_edges("compose", route_after_compose, {"save": "save"})
    graph.add_edge("save", END)

    return graph.compile()


_pipeline_graph = None


def get_pipeline_graph():
    global _pipeline_graph
    if _pipeline_graph is None:
        _pipeline_graph = create_pipeline_graph()
    return _pipeline_graph


# === Public API ===

def run_pipeline(
    ad_id: int,
    company_id: int,
    item_name: str,
    item_category: str,
    item_description: str,
    item_images: list[str],
    meme_id: int = None,
    item_url: str = None,
    character_id: int = None,
    character_prompt: str = None,
) -> ContentPipelineState:
    """Run content generation pipeline."""
    from content_pipeline.state import get_initial_state

    initial_state = get_initial_state(
        ad_id=ad_id,
        company_id=company_id,
        item_name=item_name,
        item_category=item_category,
        item_description=item_description,
        item_images=item_images,
        meme_id=meme_id,
        item_url=item_url,
        character_id=character_id,
    )

    # character_promptê° ?ì¼ë©?character??ì¶ê?
    if character_prompt:
        initial_state["character"] = initial_state.get("character", {})
        initial_state["character"]["image_prompt"] = character_prompt

    graph = get_pipeline_graph()
    result = graph.invoke(initial_state)

    return result


def run_pipeline_from_ad_request(ad_id: int) -> ContentPipelineState:
    """Load ad_request from DB and run pipeline."""
    with get_connection() as conn:
        from psycopg2.extras import RealDictCursor
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM ad_requests WHERE ad_id = %s", (ad_id,))
            row = cur.fetchone()

    if not row:
        return {"status": "failed", "errors": [f"ad_request {ad_id} not found"]}

    return run_pipeline(
        ad_id=row["ad_id"],
        company_id=row["company_id"],
        item_name=row["item_name"],
        item_category=row["item_category"],
        item_description=row.get("item_description", ""),
        item_images=row.get("item_images", []),
        meme_id=row.get("meme_id"),
        item_url=row.get("item_url"),
        character_id=row.get("character_id"),
        character_prompt=row.get("character_style_raw"),
    )


# === ?¨ê³ë³??¤í ?¨ì (ê²???í¬?ë¡?°ì©) ===

def run_character_generation(ad_id: int, character_prompt: str) -> dict:
    """ìºë¦­???´ë?ì§ë§??ì± (ê²?ì©)"""
    result = generate_character_image_node({
        "character_prompt": character_prompt,
        "aspect_ratio": "9:16",
    })
    return {
        "ad_id": ad_id,
        "status": result.get("status"),
        "image_url": result.get("character_image_url"),
        "error": result.get("error"),
    }


def run_voice_design(ad_id: int, voice_description: str) -> dict:
    """ë³´ì´???ì?¸ë§ ?¤í (ê²?ì©)"""
    voice_graph = get_voice_graph()
    result = voice_graph.invoke(get_voice_state(
        text="?ë?ì¸?? ?ì¤???ì±?ë??",
        voice_description=voice_description,
    ))
    return {
        "ad_id": ad_id,
        "status": result.get("status"),
        "voice_id": result.get("voice_id"),
        "audio_url": result.get("audio_url"),
        "error": result.get("error"),
    }


def run_scene_image_generation(
    ad_id: int,
    scenario_prompt: str,
    character_image_url: str,
    product_image_url: str,
) -> dict:
    """???´ë?ì§ ?ì± (ê²?ì©)"""
    result = generate_scene_image_node({
        "scenario_prompt": scenario_prompt,
        "character_image_url": character_image_url,
        "product_image_url": product_image_url,
        "aspect_ratio": "9:16",
    })
    return {
        "ad_id": ad_id,
        "status": result.get("status"),
        "image_url": result.get("image_url"),
        "error": result.get("error"),
    }


def run_scenario_generation(ad_id: int, meme_id: int) -> dict:
    """?ëë¦¬ì¤ ?ì± (ê²?ì©) - ???ì½ë ?¸ì¶."""
    try:
        result = generate_scenario_task(ad_id, meme_id).result()
        return {
            "ad_id": ad_id,
            "status": "completed",
            "scenes": result.get("scenes", []),
            "title": result.get("title"),
            "total_duration": result.get("total_duration"),
            "script_id": result.get("script_id"),
            "meme_name": result.get("meme_name"),
        }
    except Exception as e:
        return {
            "ad_id": ad_id,
            "status": "failed",
            "errors": [str(e)],
        }


def run_video_generation(
    ad_id: int,
    scenes: list[dict],
    scene_assets: list[dict],
    character_image_url: str = None,
) -> dict:
    """?ì ?ì± (ê²?ì©)"""
    result = run_video(
        ad_id=ad_id,
        scenes=scenes,
        scene_assets=scene_assets,
        character_image_url=character_image_url,
    )
    return {
        "ad_id": ad_id,
        "status": result.get("status"),
        "video_url": result.get("video_url"),
        "thumbnail_url": result.get("thumbnail_url"),
        "total_duration": result.get("total_duration"),
        "total_cost": result.get("total_cost"),
        "errors": result.get("errors"),
    }

