"""
YouTube Analytics 데이터 수집 스케줄러

매일 정해진 시간에 자동으로 YouTube Analytics 데이터를 수집합니다.
"""
import os
import sys
import schedule
import time
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.youtube.youtube_analytics_collector import collect_analytics_for_all_videos


def job():
    """스케줄된 작업 실행"""
    print(f"\n{'='*60}")
    print(f"YouTube Analytics 데이터 수집 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    try:
        # 어제 데이터 수집 (YouTube Analytics는 실시간이 아니라 하루 정도 지연됨)
        collect_analytics_for_all_videos(days_back=1)
        
        print(f"\n{'='*60}")
        print(f"수집 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n오류 발생: {e}")
        print(f"{'='*60}\n")


def main():
    """스케줄러 메인 함수"""
    print("YouTube Analytics 데이터 수집 스케줄러 시작")
    print("매일 오전 9시에 데이터를 수집합니다.")
    print("Ctrl+C를 눌러 종료할 수 있습니다.\n")
    
    # 매일 오전 9시에 실행
    schedule.every().day.at("09:00").do(job)
    
    # 즉시 한 번 실행 (테스트용)
    print("초기 데이터 수집을 시작합니다...\n")
    job()
    
    # 스케줄 실행
    while True:
        schedule.run_pending()
        time.sleep(60)  # 1분마다 체크


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n스케줄러를 종료합니다.")
