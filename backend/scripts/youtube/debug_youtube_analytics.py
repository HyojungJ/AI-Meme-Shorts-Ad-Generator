"""
YouTube Analytics API 디버깅 스크립트

문제를 진단하기 위해 더 자세한 정보를 출력합니다.
"""
import os
import sys
import pickle
from datetime import datetime, timedelta

# 프로젝트 루트를 Python 경로에 추가
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, backend_dir)

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/yt-analytics.readonly'
]


def get_authenticated_service():
    """YouTube Analytics API 인증 서비스 가져오기"""
    credentials = None
    
    token_file = 'token_analytics.pickle'
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            credentials = pickle.load(token)
    
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
        
        with open(token_file, 'wb') as token:
            pickle.dump(credentials, token)
    
    return build('youtubeAnalytics', 'v2', credentials=credentials)


def get_youtube_service():
    """YouTube Data API v3 서비스 가져오기"""
    credentials = None
    
    token_file = 'token_analytics.pickle'
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            credentials = pickle.load(token)
    
    return build('youtube', 'v3', credentials=credentials)


def check_video_details(video_id: str):
    """YouTube Data API로 영상 상세 정보 확인"""
    print(f"\n{'='*60}")
    print(f"1. YouTube Data API로 영상 정보 확인")
    print(f"{'='*60}")
    
    try:
        youtube = get_youtube_service()
        response = youtube.videos().list(
            part='snippet,status,statistics,contentDetails',
            id=video_id
        ).execute()
        
        if 'items' not in response or len(response['items']) == 0:
            print(f"❌ 영상을 찾을 수 없습니다: {video_id}")
            print("   → 영상 ID가 올바른지 확인하세요")
            return None
        
        video = response['items'][0]
        snippet = video['snippet']
        status = video['status']
        statistics = video.get('statistics', {})
        
        print(f"\n✅ 영상 찾음:")
        print(f"   제목: {snippet['title']}")
        print(f"   채널: {snippet['channelTitle']}")
        print(f"   업로드 날짜: {snippet['publishedAt']}")
        print(f"   공개 상태: {status['privacyStatus']}")
        print(f"   업로드 상태: {status.get('uploadStatus', 'N/A')}")
        
        print(f"\n📊 현재 통계 (YouTube Data API):")
        print(f"   조회수: {statistics.get('viewCount', 'N/A')}")
        print(f"   좋아요: {statistics.get('likeCount', 'N/A')}")
        print(f"   댓글: {statistics.get('commentCount', 'N/A')}")
        
        # 공개 상태 체크
        if status['privacyStatus'] == 'private':
            print(f"\n⚠️  영상이 '비공개' 상태입니다!")
            print(f"   → YouTube Analytics는 비공개 영상의 통계를 제공하지 않을 수 있습니다")
            print(f"   → '일부 공개' 또는 '공개'로 변경을 권장합니다")
        elif status['privacyStatus'] == 'unlisted':
            print(f"\n💡 영상이 '일부 공개' 상태입니다")
            print(f"   → Analytics 데이터가 수집될 수 있습니다")
        
        return video
        
    except HttpError as e:
        print(f"❌ YouTube Data API 오류: {e}")
        return None


def test_analytics_queries(video_id: str, days_back: int = 30):
    """다양한 Analytics API 쿼리 테스트"""
    print(f"\n{'='*60}")
    print(f"2. YouTube Analytics API 쿼리 테스트")
    print(f"{'='*60}")
    
    youtube_analytics = get_authenticated_service()
    
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days_back)
    
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    print(f"\n기간: {start_date_str} ~ {end_date_str}")
    
    # 테스트 1: 원래 쿼리
    print(f"\n--- 테스트 1: 원래 쿼리 (video filter) ---")
    try:
        response = youtube_analytics.reports().query(
            ids='channel==MINE',
            startDate=start_date_str,
            endDate=end_date_str,
            metrics='views,likes,dislikes,comments,shares,estimatedMinutesWatched,averageViewDuration,subscribersGained',
            dimensions='video',
            filters=f'video=={video_id}',
            sort='-views'
        ).execute()
        
        print(f"✅ API 응답 성공")
        print(f"   응답 키: {response.keys()}")
        
        if 'rows' in response:
            print(f"   행 개수: {len(response['rows'])}")
            if len(response['rows']) > 0:
                print(f"   첫 번째 행: {response['rows'][0]}")
            else:
                print(f"   ⚠️  데이터 행이 없습니다")
        else:
            print(f"   ⚠️  'rows' 키가 없습니다")
            
        if 'columnHeaders' in response:
            print(f"   컬럼 헤더: {[h['name'] for h in response['columnHeaders']]}")
            
    except HttpError as e:
        print(f"❌ API 오류: {e}")
        print(f"   상세: {e.error_details if hasattr(e, 'error_details') else 'N/A'}")
    
    # 테스트 2: 더 짧은 기간 (최근 7일)
    print(f"\n--- 테스트 2: 최근 7일만 조회 ---")
    recent_start = end_date - timedelta(days=7)
    try:
        response = youtube_analytics.reports().query(
            ids='channel==MINE',
            startDate=recent_start.strftime('%Y-%m-%d'),
            endDate=end_date_str,
            metrics='views,likes,comments',
            dimensions='video',
            filters=f'video=={video_id}'
        ).execute()
        
        print(f"✅ API 응답 성공")
        if 'rows' in response and len(response['rows']) > 0:
            print(f"   데이터 있음: {response['rows'][0]}")
        else:
            print(f"   ⚠️  데이터 없음")
            
    except HttpError as e:
        print(f"❌ API 오류: {e}")
    
    # 테스트 3: 전체 채널 통계 (비교용)
    print(f"\n--- 테스트 3: 전체 채널 통계 (비교용) ---")
    try:
        response = youtube_analytics.reports().query(
            ids='channel==MINE',
            startDate=start_date_str,
            endDate=end_date_str,
            metrics='views,likes,comments',
            dimensions='day'
        ).execute()
        
        print(f"✅ API 응답 성공")
        if 'rows' in response:
            print(f"   행 개수: {len(response['rows'])}")
            if len(response['rows']) > 0:
                total_views = sum(row[1] for row in response['rows'])
                print(f"   전체 채널 조회수: {total_views}")
        else:
            print(f"   ⚠️  데이터 없음")
            
    except HttpError as e:
        print(f"❌ API 오류: {e}")
    
    # 테스트 4: dimensions 없이 조회
    print(f"\n--- 테스트 4: dimensions 없이 조회 ---")
    try:
        response = youtube_analytics.reports().query(
            ids='channel==MINE',
            startDate=start_date_str,
            endDate=end_date_str,
            metrics='views,likes,comments',
            filters=f'video=={video_id}'
        ).execute()
        
        print(f"✅ API 응답 성공")
        if 'rows' in response and len(response['rows']) > 0:
            print(f"   데이터 있음: {response['rows'][0]}")
        else:
            print(f"   ⚠️  데이터 없음")
            
    except HttpError as e:
        print(f"❌ API 오류: {e}")


def main():
    video_id = "pnHrAKjycKI"  # 실패한 영상 ID
    
    print(f"\n🔍 YouTube Analytics 문제 진단")
    print(f"영상 ID: {video_id}")
    
    # 1. 영상 정보 확인
    video_info = check_video_details(video_id)
    
    if video_info is None:
        print(f"\n❌ 영상 정보를 가져올 수 없어 중단합니다")
        return
    
    # 2. Analytics 쿼리 테스트
    test_analytics_queries(video_id, days_back=30)
    
    print(f"\n{'='*60}")
    print(f"진단 완료")
    print(f"{'='*60}")
    print(f"\n💡 다음 사항을 확인하세요:")
    print(f"   1. 영상이 '공개' 또는 '일부 공개' 상태인지")
    print(f"   2. 영상이 업로드된 지 24-48시간 이상 지났는지")
    print(f"   3. 실제로 조회수가 발생했는지")
    print(f"   4. YouTube Analytics에서 해당 영상의 데이터를 볼 수 있는지")


if __name__ == "__main__":
    main()