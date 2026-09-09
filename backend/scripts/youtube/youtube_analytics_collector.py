"""
YouTube Analytics 데이터 수집 스크립트 (수정 버전)

업로드된 영상의 성과 데이터를 YouTube Analytics API에서 가져와서
PerformanceMetric 테이블에 저장합니다.

주요 수정사항:
- dislikes 메트릭 제거 (2021년부터 YouTube에서 비공개 처리)
- 상세한 에러 로깅 추가
"""
import os
import sys
import pickle
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# 프로젝트 루트를 Python 경로에 추가
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, backend_dir)

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.youtube import AdminVideoPost
from app.models.analytics import PerformanceMetric
from app.models.video import Video


SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/yt-analytics.readonly'
]


def get_authenticated_service():
    """YouTube Analytics API 인증 서비스 가져오기"""
    credentials = None
    
    # token_analytics.pickle 파일에서 저장된 토큰 로드
    token_file = 'token_analytics.pickle'
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
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
        with open(token_file, 'wb') as token:
            pickle.dump(credentials, token)
    
    return build('youtubeAnalytics', 'v2', credentials=credentials)


def get_video_statistics(youtube_analytics, video_id: str, start_date: str, end_date: str) -> Optional[Dict[str, Any]]:
    """
    특정 영상의 통계 데이터 가져오기
    
    Args:
        youtube_analytics: YouTube Analytics API 서비스
        video_id: YouTube 영상 ID
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
    
    Returns:
        통계 데이터 딕셔너리 또는 None
    """
    try:
        # dislikes는 2021년부터 YouTube가 비공개 처리했으므로 제거
        response = youtube_analytics.reports().query(
            ids='channel==MINE',
            startDate=start_date,
            endDate=end_date,
            metrics='views,likes,comments,shares,estimatedMinutesWatched,averageViewDuration,subscribersGained',
            dimensions='video',
            filters=f'video=={video_id}',
            sort='-views'
        ).execute()
        
        print(f"  [DEBUG] API 응답 키: {response.keys()}")
        
        if 'rows' in response and len(response['rows']) > 0:
            row = response['rows'][0]
            column_headers = response['columnHeaders']
            
            print(f"  [DEBUG] 데이터 행: {row}")
            print(f"  [DEBUG] 컬럼 수: {len(column_headers)}")
            
            # 컬럼 헤더와 값을 매핑
            stats = {}
            for i, header in enumerate(column_headers):
                stats[header['name']] = row[i]
            
            # dislikes는 0으로 설정 (더 이상 제공되지 않음)
            stats['dislikes'] = 0
            
            print(f"  [DEBUG] 파싱된 통계: views={stats.get('views')}, likes={stats.get('likes')}")
            
            return stats
        else:
            print(f"  [WARNING] 응답에 'rows'가 없거나 비어있습니다")
            print(f"  [INFO] 가능한 원인:")
            print(f"         1. YouTube Analytics 데이터 집계 대기 중 (24-48시간 소요)")
            print(f"         2. 해당 기간에 조회수가 없음")
            print(f"         3. 영상 업로드 날짜가 조회 기간보다 최근임")
            print(f"  [TIP] --days 값을 늘려보세요 (예: --days 30)")
            print(f"  [DEBUG] 전체 응답: {response}")
        
        return None
        
    except HttpError as e:
        print(f"  [ERROR] YouTube Analytics API HTTP 오류")
        print(f"  [ERROR] 상태 코드: {e.resp.status if hasattr(e, 'resp') else 'N/A'}")
        print(f"  [ERROR] 메시지: {e}")
        if hasattr(e, 'error_details'):
            print(f"  [ERROR] 상세: {e.error_details}")
        return None
    except Exception as e:
        print(f"  [ERROR] 예상치 못한 오류: {type(e).__name__}: {e}")
        import traceback
        print(f"  [ERROR] 스택 트레이스:")
        traceback.print_exc()
        return None


def calculate_engagement_rate(views: int, likes: int, comments: int, shares: int) -> float:
    """반응률 계산"""
    if views == 0:
        return 0.0
    
    total_engagement = likes + comments + shares
    return round((total_engagement / views) * 100, 2)


def save_performance_metric(
    db: Session,
    video_id: Optional[int],
    post_id: Optional[int],
    stats: Dict[str, Any],
    snapshot_type: str = 'daily'
) -> PerformanceMetric:
    """성과 데이터를 DB에 저장"""
    
    views = stats.get('views', 0)
    likes = stats.get('likes', 0)
    dislikes = stats.get('dislikes', 0)
    comments = stats.get('comments', 0)
    shares = stats.get('shares', 0)
    estimated_minutes_watched = stats.get('estimatedMinutesWatched', 0)
    average_view_duration = stats.get('averageViewDuration', 0)
    subscribers_gained = stats.get('subscribersGained', 0)
    
    # 초 단위로 변환
    watch_time_seconds = estimated_minutes_watched * 60
    
    # 반응률 계산
    engagement_rate = calculate_engagement_rate(views, likes, comments, shares)
    
    # 시청 유지율 계산 (평균 시청 시간 / 전체 영상 길이)
    # 영상 길이를 알 수 없으므로 일단 None으로 설정
    audience_retention_rate = None
    
    metric = PerformanceMetric(
        video_id=video_id,
        post_id=post_id,
        captured_at=datetime.utcnow(),
        snapshot_type=snapshot_type,
        views=views,
        likes=likes,
        dislikes=dislikes,
        comments=comments,
        shares=shares,
        watch_time_seconds=watch_time_seconds,
        average_view_duration=average_view_duration,
        audience_retention_rate=audience_retention_rate,
        engagement_rate=engagement_rate,
        subscribers_gained=subscribers_gained
    )
    
    db.add(metric)
    db.commit()
    db.refresh(metric)
    
    return metric


def collect_analytics_for_all_videos(days_back: int = 7, include_private: bool = True):
    """
    모든 게시된 영상의 성과 데이터 수집
    
    Args:
        days_back: 며칠 전부터 데이터를 수집할지 (기본값: 1일)
        include_private: 비공개/일부공개 영상도 포함할지 (기본값: True)
    """
    db = SessionLocal()
    youtube_analytics = get_authenticated_service()
    
    try:
        # 게시된 영상 목록 가져오기
        published_posts = db.query(AdminVideoPost).filter(
            AdminVideoPost.post_status == 'published',
            AdminVideoPost.yt_video_id.isnot(None)
        ).all()
        
        print(f"총 {len(published_posts)}개의 게시된 영상을 찾았습니다.")
        if include_private:
            print("💡 비공개/일부공개 영상도 포함됩니다 (채널 소유자는 모든 영상 통계 확인 가능)")
        
        # 날짜 범위 설정
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days_back)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        print(f"기간: {start_date_str} ~ {end_date_str}")
        
        success_count = 0
        error_count = 0
        
        for post in published_posts:
            youtube_video_id = post.yt_video_id
            
            print(f"\n{'='*60}")
            print(f"영상 처리 중: {post.yt_title or 'Untitled'}")
            print(f"YouTube ID: {youtube_video_id}")
            print(f"Video ID: {post.video_id}, Post ID: {post.post_id}")
            
            # YouTube Analytics에서 통계 가져오기
            stats = get_video_statistics(
                youtube_analytics,
                youtube_video_id,
                start_date_str,
                end_date_str
            )
            
            if stats:
                # DB에 저장
                try:
                    # YouTube 영상은 post_id만 저장 (DB 제약 조건: video_id OR post_id 중 하나만)
                    metric = save_performance_metric(
                        db=db,
                        video_id=None,  # YouTube 게시물은 video_id 사용 안 함
                        post_id=post.post_id,
                        stats=stats,
                        snapshot_type='daily'
                    )
                    
                    views = stats.get('views', 0)
                    likes = stats.get('likes', 0)
                    comments = stats.get('comments', 0)
                    
                    print(f"  ✅ 성과 데이터 저장 완료!")
                    print(f"     조회수: {views:,}")
                    print(f"     좋아요: {likes:,}")
                    print(f"     댓글: {comments:,}")
                    print(f"     반응률: {metric.engagement_rate}%")
                    
                    # 비공개 영상 경고
                    if views == 0:
                        print(f"  ⚠️  조회수가 0입니다. 영상이 비공개 상태이거나 최근에 업로드되었을 수 있습니다.")
                        print(f"      → YouTube에서 공개 상태를 '일부 공개' 또는 '공개'로 변경하면 조회수가 집계됩니다.")
                    
                    success_count += 1
                    
                except Exception as e:
                    print(f"  ❌ DB 저장 중 오류: {e}")
                    import traceback
                    traceback.print_exc()
                    error_count += 1
            else:
                print(f"  ❌ 통계 데이터를 가져올 수 없습니다.")
                error_count += 1
        
        print(f"\n{'='*60}")
        print(f"=== 수집 완료 ===")
        print(f"{'='*60}")
        print(f"성공: {success_count}개")
        print(f"실패: {error_count}개")
        
    except Exception as e:
        print(f"\n❌ 치명적 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


def collect_analytics_for_video(video_id: int, days_back: int = 30):
    """
    특정 영상의 성과 데이터 수집 (테스트용)
    
    Args:
        video_id: Video 테이블의 video_id
        days_back: 며칠 전부터 데이터를 수집할지
    """
    db = SessionLocal()
    youtube_analytics = get_authenticated_service()
    
    try:
        # 영상 정보 가져오기
        video = db.query(Video).filter(Video.video_id == video_id).first()
        if not video:
            print(f"영상을 찾을 수 없습니다: video_id={video_id}")
            return
        
        # 게시 정보 가져오기
        post = db.query(AdminVideoPost).filter(
            AdminVideoPost.video_id == video_id,
            AdminVideoPost.post_status == 'published'
        ).first()
        
        if not post or not post.yt_video_id:
            print(f"게시된 YouTube 영상을 찾을 수 없습니다: video_id={video_id}")
            return
        
        youtube_video_id = post.yt_video_id
        
        print(f"영상: {video.title}")
        print(f"YouTube ID: {youtube_video_id}")
        
        # 날짜 범위 설정
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days_back)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # YouTube Analytics에서 통계 가져오기
        stats = get_video_statistics(
            youtube_analytics,
            youtube_video_id,
            start_date_str,
            end_date_str
        )
        
        if stats:
            # DB에 저장
            metric = save_performance_metric(
                db=db,
                video_id=None,  # YouTube 게시물은 video_id 사용 안 함
                post_id=post.post_id,
                stats=stats,
                snapshot_type='daily'
            )
            
            print(f"\n✅ 성과 데이터 저장 완료:")
            print(f"  - 조회수: {stats.get('views', 0):,}")
            print(f"  - 좋아요: {stats.get('likes', 0):,}")
            print(f"  - 댓글: {stats.get('comments', 0):,}")
            print(f"  - 공유: {stats.get('shares', 0):,}")
            print(f"  - 반응률: {metric.engagement_rate}%")
        else:
            print("❌ 통계 데이터를 가져올 수 없습니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='YouTube Analytics 데이터 수집')
    parser.add_argument('--video-id', type=int, help='특정 영상의 video_id (테스트용)')
    parser.add_argument('--days', type=int, default=7, help='며칠 전부터 데이터를 수집할지 (기본값: 7)')
    parser.add_argument('--all', action='store_true', help='모든 게시된 영상의 데이터 수집')
    
    args = parser.parse_args()
    
    if args.video_id:
        # 특정 영상만 수집
        collect_analytics_for_video(args.video_id, args.days)
    elif args.all:
        # 모든 영상 수집
        collect_analytics_for_all_videos(args.days)
    else:
        print("사용법:")
        print("  특정 영상: python youtube_analytics_collector.py --video-id 123")
        print("  모든 영상: python youtube_analytics_collector.py --all")
        print("  기간 지정: python youtube_analytics_collector.py --all --days 30")
        print("")
        print("💡 참고:")
        print("  - YouTube Analytics는 데이터 집계에 24-48시간이 걸립니다")
        print("  - 기본 수집 기간은 7일입니다 (최근 영상도 포함하기 위해)")
        print("  - 비공개 영상도 데이터를 수집할 수 있지만 조회수가 0일 수 있습니다")