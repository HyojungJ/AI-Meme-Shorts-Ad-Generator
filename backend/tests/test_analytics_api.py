"""
YouTube Analytics API 연결 테스트 스크립트

YouTube Analytics API가 제대로 작동하는지 확인합니다.
"""
import os
import sys
from datetime import datetime, timedelta

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.youtube.youtube_analytics_collector import get_authenticated_service, get_video_statistics
from app.db.session import SessionLocal
from app.models.youtube import AdminVideoPost


def test_api_connection():
    """YouTube Analytics API 연결 테스트"""
    print("=" * 60)
    print("YouTube Analytics API 연결 테스트")
    print("=" * 60)
    
    try:
        print("\n1. API 인증 중...")
        youtube_analytics = get_authenticated_service()
        print("   ✓ 인증 성공!")
        
        print("\n2. 채널 정보 가져오기...")
        # 채널의 기본 통계 가져오기
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=7)
        
        response = youtube_analytics.reports().query(
            ids='channel==MINE',
            startDate=start_date.strftime('%Y-%m-%d'),
            endDate=end_date.strftime('%Y-%m-%d'),
            metrics='views,likes,comments,shares',
            dimensions='day'
        ).execute()
        
        if 'rows' in response:
            print(f"   ✓ 최근 7일간 데이터: {len(response['rows'])}개 행")
            print(f"   컬럼: {[h['name'] for h in response['columnHeaders']]}")
        else:
            print("   ⚠ 데이터가 없습니다 (채널에 영상이 없거나 데이터가 아직 생성되지 않음)")
        
        print("\n3. 게시된 영상 확인...")
        db = SessionLocal()
        try:
            published_posts = db.query(AdminVideoPost).filter(
                AdminVideoPost.post_status == 'published',
                AdminVideoPost.yt_video_id.isnot(None)
            ).limit(5).all()
            
            if published_posts:
                print(f"   ✓ 게시된 영상: {len(published_posts)}개 (최대 5개 표시)")
                
                for i, post in enumerate(published_posts, 1):
                    print(f"\n   [{i}] {post.yt_title or 'Untitled'}")
                    print(f"       YouTube ID: {post.yt_video_id}")
                    print(f"       게시일: {post.published_at}")
                    
                    # 첫 번째 영상의 통계 가져오기
                    if i == 1:
                        print(f"\n4. 첫 번째 영상의 통계 가져오기...")
                        stats = get_video_statistics(
                            youtube_analytics,
                            post.yt_video_id,
                            start_date.strftime('%Y-%m-%d'),
                            end_date.strftime('%Y-%m-%d')
                        )
                        
                        if stats:
                            print(f"   ✓ 통계 데이터:")
                            print(f"       조회수: {stats.get('views', 0):,}")
                            print(f"       좋아요: {stats.get('likes', 0):,}")
                            print(f"       댓글: {stats.get('comments', 0):,}")
                            print(f"       공유: {stats.get('shares', 0):,}")
                            print(f"       시청 시간: {stats.get('estimatedMinutesWatched', 0):,}분")
                        else:
                            print("   ⚠ 통계 데이터를 가져올 수 없습니다")
                            print("      (영상이 최근에 업로드되었거나 조회수가 없을 수 있음)")
            else:
                print("   ⚠ 게시된 영상이 없습니다")
                print("      먼저 영상을 YouTube에 업로드해주세요")
        finally:
            db.close()
        
        print("\n" + "=" * 60)
        print("✓ 모든 테스트 통과!")
        print("=" * 60)
        print("\n다음 단계:")
        print("  1. 특정 영상 데이터 수집:")
        print("     python scripts/youtube_analytics_collector.py --video-id <VIDEO_ID>")
        print("  2. 모든 영상 데이터 수집:")
        print("     python scripts/youtube_analytics_collector.py --all")
        print("  3. 스케줄러 시작:")
        print("     python scripts/schedule_analytics_collection.py")
        
    except Exception as e:
        print(f"\n✗ 오류 발생: {e}")
        print("\n해결 방법:")
        print("  1. .env 파일에 GOOGLE_CLIENT_ID와 GOOGLE_CLIENT_SECRET 설정 확인")
        print("  2. Google Cloud Console에서 YouTube Analytics API 활성화 확인")
        print("  3. OAuth 동의 화면 설정 확인")
        print("  4. token_analytics.pickle 파일 삭제 후 재시도")
        return False
    
    return True


if __name__ == "__main__":
    test_api_connection()
