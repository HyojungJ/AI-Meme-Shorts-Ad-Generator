"""YouTube 업로드 서비스"""
import logging
import os
import pickle
from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


def get_authenticated_service():
    """YouTube API 인증 서비스 가져오기"""
    credentials = None
    
    # token.pickle 파일에서 저장된 토큰 로드
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    
    # 유효한 credentials가 없으면 로그인
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            client_id = os.getenv('GOOGLE_CLIENT_ID')
            client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
            
            if not client_id or not client_secret:
                raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set")
            
            flow = InstalledAppFlow.from_client_config(
                {
                    "installed": {
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "redirect_uris": ["http://localhost:8080/"],
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token"
                    }
                },
                SCOPES
            )
            credentials = flow.run_local_server(port=8080)
        
        # 토큰 저장
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)
    
    return build('youtube', 'v3', credentials=credentials)


def upload_video(
    video_path: str,
    title: str,
    description: str,
    category_id: str = "22",
    privacy_status: str = "private",
    tags: Optional[list] = None
) -> str:
    """
    YouTube에 영상 업로드
    
    Args:
        video_path: 업로드할 영상 파일 경로
        title: 영상 제목
        description: 영상 설명
        category_id: 카테고리 ID (기본값: 22 = People & Blogs)
        privacy_status: 공개 상태 (private, unlisted, public)
        tags: 태그 리스트
    
    Returns:
        YouTube video ID
    """
    youtube = get_authenticated_service()
    
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags or [],
            'categoryId': category_id
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False
        }
    }
    
    # 파일 업로드
    media = MediaFileUpload(
        video_path,
        chunksize=-1,
        resumable=True,
        mimetype='video/*'
    )
    
    try:
        request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info("업로드 진행: %d%%", int(status.progress() * 100))
        
        video_id = response['id']
        logger.info("업로드 완료: %s", video_id)
        return video_id
        
    except HttpError as e:
        logger.error("YouTube HTTP 에러 %s: %s", e.resp.status, e.content)
        raise