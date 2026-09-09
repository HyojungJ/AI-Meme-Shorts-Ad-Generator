"""
YouTube 업로드 서비스
"""
import logging
import httplib2
import random
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from oauth2client.client import OAuth2Credentials, AccessTokenRefreshError

from app.core.config import settings


# Retry 설정
httplib2.RETRIES = 1
MAX_RETRIES = 10
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError)
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


class YouTubeService:
    """YouTube 업로드 서비스"""
    
    def __init__(self, access_token: str, refresh_token: str, token_expiry: datetime):
        """
        YouTube 서비스 초기화
        
        Args:
            access_token: OAuth 액세스 토큰
            refresh_token: OAuth 리프레시 토큰
            token_expiry: 토큰 만료 시간
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expiry = token_expiry
    
    def _get_authenticated_service(self):
        """인증된 YouTube 서비스 객체 생성"""
        credentials = OAuth2Credentials(
            access_token=self.access_token,
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            refresh_token=self.refresh_token,
            token_expiry=self.token_expiry,
            token_uri="https://oauth2.googleapis.com/token",
            user_agent=None
        )
        
        return build(
            YOUTUBE_API_SERVICE_NAME,
            YOUTUBE_API_VERSION,
            http=credentials.authorize(httplib2.Http())
        )
    
    def upload_video(
        self,
        file_path: str,
        title: str,
        description: str,
        category_id: str = "22",
        keywords: Optional[str] = None,
        privacy_status: str = "private"
    ) -> Dict[str, Any]:
        """
        YouTube에 영상 업로드
        
        Args:
            file_path: 업로드할 영상 파일 경로
            title: 영상 제목
            description: 영상 설명
            category_id: 카테고리 ID (기본값: 22 = People & Blogs)
            keywords: 태그 (쉼표로 구분)
            privacy_status: 공개 설정 (public, private, unlisted)
        
        Returns:
            업로드 결과 (video_id, status 등)
        """
        youtube = self._get_authenticated_service()
        
        tags = None
        if keywords:
            tags = keywords.split(",")
        
        body = dict(
            snippet=dict(
                title=title,
                description=description,
                tags=tags,
                categoryId=category_id
            ),
            status=dict(
                privacyStatus=privacy_status
            )
        )
        
        # 업로드 요청 생성
        insert_request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True)
        )
        
        # 업로드 실행 (재시도 로직 포함)
        return self._resumable_upload(insert_request)
    
    def _resumable_upload(self, insert_request) -> Dict[str, Any]:
        """
        재시도 로직이 포함된 업로드
        
        Args:
            insert_request: YouTube API 업로드 요청
        
        Returns:
            업로드 결과
        """
        response = None
        error = None
        retry = 0
        
        while response is None:
            try:
                logger.info("YouTube 파일 업로드 중...")
                status, response = insert_request.next_chunk()
                
                if response is not None:
                    if 'id' in response:
                        logger.info("YouTube 업로드 완료: %s", response['id'])
                        return {
                            'success': True,
                            'video_id': response['id'],
                            'message': 'Upload successful'
                        }
                    else:
                        return {
                            'success': False,
                            'error': f"Unexpected response: {response}"
                        }
            
            except HttpError as e:
                if e.resp.status in RETRIABLE_STATUS_CODES:
                    error = f"A retriable HTTP error {e.resp.status} occurred:\n{e.content}"
                else:
                    raise
            
            except RETRIABLE_EXCEPTIONS as e:
                error = f"A retriable error occurred: {e}"
            
            if error is not None:
                logger.error("YouTube 업로드 에러: %s", error)
                retry += 1
                
                if retry > MAX_RETRIES:
                    return {
                        'success': False,
                        'error': 'Max retries exceeded'
                    }
                
                max_sleep = 2 ** retry
                sleep_seconds = random.random() * max_sleep
                logger.info("재시도 대기: %ds", sleep_seconds)
                time.sleep(sleep_seconds)
        
        return {
            'success': False,
            'error': 'Unknown error'
        }
    
    def refresh_access_token(self) -> Optional[str]:
        """
        액세스 토큰 갱신
        
        Returns:
            새로운 액세스 토큰 또는 None
        """
        try:
            credentials = OAuth2Credentials(
                access_token=self.access_token,
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                refresh_token=self.refresh_token,
                token_expiry=self.token_expiry,
                token_uri="https://oauth2.googleapis.com/token",
                user_agent=None
            )
            
            credentials.refresh(httplib2.Http())
            
            return credentials.access_token
        
        except AccessTokenRefreshError:
            return None
    
    def get_video_analytics(self, video_id: str) -> Dict[str, Any]:
        """
        YouTube 영상 통계 조회
        
        Args:
            video_id: YouTube 영상 ID
        
        Returns:
            통계 데이터 (views, likes, comments 등)
        """
        try:
            youtube = self._get_authenticated_service()
            
            # 기본 통계 조회 (조회수, 좋아요, 댓글, 공유)
            request = youtube.videos().list(
                part='statistics',
                id=video_id
            )
            response = request.execute()
            
            if not response.get('items'):
                return {
                    'success': False,
                    'error': f'영상을 찾을 수 없습니다: {video_id}'
                }
            
            stats = response['items'][0].get('statistics', {})
            
            return {
                'success': True,
                'video_id': video_id,
                'views': int(stats.get('viewCount', 0)),
                'likes': int(stats.get('likeCount', 0)),
                'dislikes': int(stats.get('dislikeCount', 0)),  # 공개되지 않을 수 있음
                'comments': int(stats.get('commentCount', 0)),
                'favorites': int(stats.get('favoriteCount', 0))
            }
        
        except HttpError as e:
            return {
                'success': False,
                'error': f'YouTube API 오류: {e.content}'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'통계 조회 실패: {str(e)}'
            }
    
    def get_video_analytics_detailed(self, video_id: str) -> Dict[str, Any]:
        """
        YouTube 영상 상세 통계 조회 (YouTube Analytics API 사용)
        
        Args:
            video_id: YouTube 영상 ID
        
        Returns:
            상세 통계 데이터 (시청 시간, 평균 시청 시간, 시청자 유지율 등)
        """
        try:
            youtube = self._get_authenticated_service()
            
            # YouTube Analytics API 사용
            analytics = build(
                'youtubeAnalytics',
                'v2',
                http=youtube.http
            )
            
            # 어제 데이터 조회
            end_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            request = analytics.reports().query(
                ids='channel==MINE',
                startDate=start_date,
                endDate=end_date,
                metrics='views,estimatedMinutesWatched,averageViewDuration,subscribersGained',
                dimensions='video',
                filters=f'video=={video_id}'
            )
            response = request.execute()
            
            if not response.get('rows'):
                return {
                    'success': False,
                    'error': '통계 데이터가 없습니다'
                }
            
            row = response['rows'][0]
            
            return {
                'success': True,
                'video_id': video_id,
                'views': int(row[1]) if len(row) > 1 else 0,
                'watch_time_seconds': int(float(row[2]) * 60) if len(row) > 2 else 0,  # 분을 초로 변환
                'average_view_duration': float(row[3]) if len(row) > 3 else 0,
                'subscribers_gained': int(row[4]) if len(row) > 4 else 0
            }
        
        except HttpError as e:
            return {
                'success': False,
                'error': f'YouTube Analytics API 오류: {e.content}'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'상세 통계 조회 실패: {str(e)}'
            }
