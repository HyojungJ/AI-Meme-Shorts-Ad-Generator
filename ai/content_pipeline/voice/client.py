import json
from dataclasses import dataclass
from typing import List, Optional

import requests


# --- 1. 데이터 모델 정의 ---
# - 응답 필드가 많고, 여러 곳에서 재사용/검증해야 해서 데이터 모델을 별도 클래스로 정의
@dataclass(frozen=True)
class ElevenLabsResponse:
    """API 응답으로 받은 오디오 데이터와 메타데이터"""
    audio_bytes: bytes          # 실제 오디오 이진 데이터 (파일 데이터)
    content_type: str           # 오디오 형식 (예: "audio/mpeg", "audio/wav" 등)


@dataclass(frozen=True)
class VoicePreview:
    """음성 디자인 미리보기 항목"""
    generated_voice_id: str     # 생성된 음성의 고유 ID
    audio_base_64: str          # Base64로 인코딩된 오디오 데이터 (미리보기용)


@dataclass(frozen=True)
class VoiceDesignResponse:
    """음성 디자인 응답 데이터"""
    previews: List[VoicePreview]    # 생성된 음성 미리보기 목록
    voice_description: str          # 음성 설명
    text: str                       # 입력 텍스트
    model_id: str                   # 사용된 모델 ID  


@dataclass(frozen=True)
class VoiceCreateResponse:
    """음성 생성 응답 데이터"""
    voice_id: str                   # 생성된 음성의 고유 ID
    name: Optional[str]             # 음성 이름
    description: Optional[str]      # 음성 설명


# --- 2. 유틸리티 함수 ---
def _generate_audio_from_text(
    *,
    api_key: str,
    base_url: str,
    voice_id: str,
    model_id: str,
    text: str,
    output_format: str,
    voice_settings: dict,
    timeout_seconds: int,
) -> ElevenLabsResponse:
    """ElevenLabs TTS API를 호출하고 원천 오디오 바이트 반환"""
    url = f"{base_url}/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": model_id,
        "output_format": output_format,
        "voice_settings": voice_settings,
    }
    response = requests.post(
        url,
        headers=headers,
        data=json.dumps(payload),
        timeout=timeout_seconds,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"ElevenLabs TTS failed ({response.status_code}): {response.text}")
    return ElevenLabsResponse(
        audio_bytes=response.content,
        content_type=response.headers.get("content-type", "audio/mpeg"),
    )


def _post_json(
    *,
    api_key: str,
    url: str,
    payload: dict,
    timeout_seconds: int,
) -> dict:
    """JSON 요청을 전송하고 파싱된 응답 반환"""
    headers = {
        "xi-api-key": api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    response = requests.post(
        url,
        headers=headers,
        data=json.dumps(payload),
        timeout=timeout_seconds,
    )
    if response is None or response.status_code >= 400:
        raise RuntimeError(
            f"ElevenLabs request failed ({response.status_code}): {response.text}"
        )
    return response.json()


def _get_json(
    *,
    api_key: str,
    url: str,
    params: dict | None,
    timeout_seconds: int,
) -> dict:
    """GET 요청을 보내고 JSON 응답을 반환."""
    headers = {
        "xi-api-key": api_key,
        "Accept": "application/json",
    }
    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=timeout_seconds,
    )
    if response is None or response.status_code >= 400:
        raise RuntimeError(
            f"ElevenLabs request failed ({response.status_code}): {response.text}"
        )
    return response.json()


# --- 3.ElevenLabs TTS API 클라이언트 클래스 ---
class ElevenLabsClient:
    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self, api_key: str, model_id: str):
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY is required")
        self.api_key = api_key
        self.model_id = model_id

    def text_to_speech(
        self,
        voice_id: str,
        text: str,
        *,
        stability: float,
        similarity_boost: float,
        style: float,
        use_speaker_boost: bool,
        speed: float,
        output_format: str,
        timeout_seconds: int = 120,
    ) -> ElevenLabsResponse:
        """
        텍스트를 음성으로 변환하는 API 호출 메서드
        - 음성 ID와 텍스트를 받아 오디오 데이터를 반환
        - 다양한 음성 설정 파라미터를 지원
        - 반환값: 오디오 데이터 및 메타데이터
        """
        voice_settings = {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
            "use_speaker_boost": use_speaker_boost,
            "speed": speed,
        }

        # 오디오 생성 API 호출
        result = _generate_audio_from_text(
            api_key=self.api_key,
            base_url=self.BASE_URL,
            voice_id=voice_id,
            model_id=self.model_id,
            text=text,
            output_format=output_format,
            voice_settings=voice_settings,
            timeout_seconds=timeout_seconds,
        )

        return result

    def text_to_voice_design(
        self,
        *,
        model_id: str,
        voice_description: str,
        text: str,
        timeout_seconds: int = 120,
    ) -> VoiceDesignResponse:
        """
        테스트 보이스 디자인 생성 API 호출 메서드
        - 음성 설명과 텍스트를 받아 보이스 디자인 미리보기 반환
        - 반환값: 미리보기 목록, 설명, 텍스트, 모델 ID
        """
        # ElevenLabs 음성 디자인 API 엔드포인트
        url = f"{self.BASE_URL}/text-to-voice/design"

        # API에서 요구하는 JSON 데이터 페이로드 구성
        payload = {
            "model_id": model_id,
            "voice_description": voice_description,
            "text": text,
        }

        # 보이스 생성 및 등록 API 호출
        data = _post_json(
            api_key=self.api_key,
            url=url,
            payload=payload,
            timeout_seconds=timeout_seconds,
        )
        
        # 성공 시 응답 데이터 파싱 및 반환
        previews = [
            VoicePreview(
                generated_voice_id=item["generated_voice_id"],
                audio_base_64=item["audio_base_64"],
            )
            for item in data.get("previews", [])
        ]

        return VoiceDesignResponse(
            previews=previews,
            voice_description=data.get("voice_description", voice_description),
            text=data.get("text", text),
            model_id=data.get("model_id", model_id),
        )


    def text_to_voice_create(
        self,
        *,
        voice_name: str,
        voice_description: str,
        generated_voice_id: str,
        timeout_seconds: int = 120,
    ) -> VoiceCreateResponse:
        """
        실제 보이스 생성 및 등록 API 호출 메서드
        - 생성된 보이슨의 고유 ID를 받아 영구 등록
        - 반환값: 생성된 음성 정보 (ID, 이름, 설명)
        """
        # ElevenLabs 음성 생성 API 엔드포인트
        url = f"{self.BASE_URL}/voice-generation/create-voice"
        
        # API에서 요구하는 JSON 데이터 페이로드 구성
        payload = {
            "voice_name": voice_name,
            "voice_description": voice_description,
            "generated_voice_id": generated_voice_id,
        }

        # 보이스 생성 및 등록 API 호출
        data = _post_json(
            api_key=self.api_key,
            url=url,
            payload=payload,
            timeout_seconds=timeout_seconds,
        )
        
        # 성공 시 응답 데이터 파싱 및 반환
        return VoiceCreateResponse(
            voice_id=data["voice_id"],
            name=data.get("name"),
            description=data.get("description"),
        )

    def list_voices(
        self,
        *,
        voice_type: str = "non-default",
        sort: str = "created_at_unix",
        sort_direction: str = "asc",
        page_size: int = 100,
        next_page_token: str | None = None,
        include_total_count: bool = True,
        timeout_seconds: int = 30,
    ) -> dict:
        """ElevenLabs 보이스 목록 조회."""
        url = f"{self.BASE_URL}/voices"
        params = {
            "voice_type": voice_type,
            "sort": sort,
            "sort_direction": sort_direction,
            "page_size": page_size,
            "include_total_count": include_total_count,
        }
        if next_page_token:
            params["next_page_token"] = next_page_token
        return _get_json(
            api_key=self.api_key,
            url=url,
            params=params,
            timeout_seconds=timeout_seconds,
        )

    def delete_voice(
        self,
        *,
        voice_id: str,
        timeout_seconds: int = 30,
    ) -> None:
        """ElevenLabs 보이스 삭제."""
        url = f"{self.BASE_URL}/voices/{voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Accept": "application/json",
        }
        response = requests.delete(url, headers=headers, timeout=timeout_seconds)
        if response is None or response.status_code >= 400:
            raise RuntimeError(
                f"ElevenLabs delete failed ({response.status_code}): {response.text}"
            )

