"""
시나리오 자동 승인 스케줄러
24시간 내 미응답 시 자동 승인 처리
"""
import sys
import os
from datetime import datetime
from typing import List

# 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from scenario.v1.database import (
    SessionLocal,
    get_pending_scenarios_for_auto_approval,
    auto_approve_scenario,
    reject_other_scenarios,
    update_workflow_after_approval,
    ScenarioScript
)


def process_auto_approval():
    """
    24시간 경과한 미승인 시나리오 자동 승인 처리
    
    처리 로직:
    1. 24시간 경과한 pending 시나리오 조회
    2. 각 프로젝트별로 첫 번째 시나리오 자동 승인
    3. 다른 시나리오들 거부 처리
    4. 워크플로우 상태 업데이트
    5. 알림 발송 (TODO)
    """
    db = SessionLocal()
    
    try:
        # 1. 자동 승인 대상 시나리오 조회
        pending_scenarios = get_pending_scenarios_for_auto_approval(db)
        
        if not pending_scenarios:
            print(f"[{datetime.utcnow()}] 자동 승인 대상 없음")
            return
        
        print(f"[{datetime.utcnow()}] 자동 승인 대상: {len(pending_scenarios)}개")
        
        # 2. 프로젝트별로 그룹화
        projects = {}
        for scenario in pending_scenarios:
            project_id = scenario.project_id
            if project_id not in projects:
                projects[project_id] = []
            projects[project_id].append(scenario)
        
        # 3. 각 프로젝트별로 첫 번째 시나리오 자동 승인
        for project_id, scenarios in projects.items():
            # 생성 시간 기준 정렬 (가장 먼저 생성된 것)
            scenarios.sort(key=lambda x: x.created_at)
            first_scenario = scenarios[0]
            
            # 자동 승인 처리
            auto_approve_scenario(db, first_scenario.script_id)
            
            # 다른 시나리오 거부
            reject_other_scenarios(db, project_id, first_scenario.script_id)
            
            # 워크플로우 상태 업데이트 (job_id 찾기)
            # TODO: workflow_execution과 scenario_scripts 연결 필요
            # update_workflow_after_approval(db, job_id, 'audio_generation')
            
            print(f"  - 프로젝트 {project_id}: 시나리오 {first_scenario.script_id} 자동 승인")
            
            # TODO: 알림 발송
            # send_auto_approval_notification(first_scenario)
        
        print(f"[{datetime.utcnow()}] 자동 승인 완료: {len(projects)}개 프로젝트")
        
    except Exception as e:
        print(f"[{datetime.utcnow()}] 자동 승인 처리 오류: {str(e)}")
        db.rollback()
    
    finally:
        db.close()


def send_auto_approval_notification(scenario: ScenarioScript):
    """
    자동 승인 알림 발송
    
    Args:
        scenario: 자동 승인된 시나리오
    
    TODO:
    - 이메일 알림
    - 인앱 알림
    - SMS 알림 (선택)
    """
    print(f"  - 알림 발송: 시나리오 {scenario.script_id} 자동 승인됨")
    
    # TODO: 이메일 발송
    # send_email(
    #     to=user_email,
    #     subject="시나리오가 자동 승인되었습니다",
    #     body=f"24시간 내 응답이 없어 시나리오 '{scenario.title}'이(가) 자동 승인되었습니다."
    # )
    
    # TODO: 인앱 알림
    # send_in_app_notification(
    #     user_id=scenario.project.user_id,
    #     message=f"시나리오 '{scenario.title}'이(가) 자동 승인되었습니다."
    # )


def run_scheduler():
    """
    스케줄러 실행
    
    사용 방법:
    1. Cron Job으로 실행 (매 시간마다)
       0 * * * * python scripts/scenario/v1/scheduler.py
    
    2. APScheduler로 실행
       from apscheduler.schedulers.background import BackgroundScheduler
       scheduler = BackgroundScheduler()
       scheduler.add_job(process_auto_approval, 'interval', hours=1)
       scheduler.start()
    
    3. Celery Beat로 실행
       @celery.task
       def auto_approval_task():
           process_auto_approval()
    """
    print(f"[{datetime.utcnow()}] 자동 승인 스케줄러 시작")
    process_auto_approval()
    print(f"[{datetime.utcnow()}] 자동 승인 스케줄러 종료")


if __name__ == "__main__":
    # 직접 실행 시
    run_scheduler()
