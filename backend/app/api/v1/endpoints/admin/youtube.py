"""YouTube 게시 관련 엔드포인트"""
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session

from .common import (
    logger,
    admin_crud,
    settings,
    get_db,
    check_admin_permission,
    PublishVideoRequest,
    PublishVideoResponse,
)

router = APIRouter()


@router.post("/videos/{video_id}/publish", response_model=PublishVideoResponse)
async def publish_video(
    video_id: int,
    publish_request: PublishVideoRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """YouTube 게시 승인 및 즉시 업로드"""
    await check_admin_permission(request)

    video_info = admin_crud.get_video_with_company(db, video_id)
    if not video_info:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다")

    video = video_info['video']

    # 영상 상태 확인 (completed, client_approved, admin_approved 모두 허용)
    if video.status not in ['completed', 'client_approved', 'admin_approved']:
        raise HTTPException(status_code=400, detail="완료되거나 승인된 영상만 게시할 수 있습니다")

    # scheduled_at 파싱 (문자열이면 datetime으로 변환)
    scheduled_datetime = None
    if publish_request.scheduled_at:
        try:
            from dateutil import parser
            scheduled_datetime = parser.parse(publish_request.scheduled_at)
        except Exception:
            raise HTTPException(status_code=400, detail="잘못된 날짜 형식입니다")

    # AdminVideoPost 생성
    post = admin_crud.create_video_post(
        db=db,
        video_id=video_id,
        channel_id=publish_request.channel_id,
        yt_title=publish_request.yt_title,
        yt_description=publish_request.yt_description,
        scheduled_at=scheduled_datetime
    )

    # YouTube 즉시 업로드 (예약이 아닌 경우)
    youtube_video_id = None
    if not publish_request.scheduled_at:
        try:
            import os
            mock_mode = os.getenv("MOCK_MODE", "false").lower() == "true"

            if mock_mode:
                # Mock 업로드
                import time
                youtube_video_id = f"YT_{video_id}_{int(time.time())}"
                logger.info("MOCK YouTube upload successful: %s", youtube_video_id)
            else:
                # 실제 YouTube 업로드
                from app.services.youtube_uploader import upload_video
                import tempfile
                import boto3

                # 영상 파일 경로 확인
                video_url = video.s3_url
                if not video_url:
                    raise ValueError("영상 파일 경로가 없습니다")

                video_path = None
                temp_file = None

                try:
                    # S3 URL인 경우 임시 파일로 다운로드
                    if video_url.startswith('http') or video_url.startswith('s3://'):
                        logger.info("Downloading video from S3: %s", video_url)

                        # S3 클라이언트 생성
                        s3_client = boto3.client(
                            's3',
                            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                            region_name=os.getenv('AWS_REGION', 'ap-northeast-2')
                        )

                        # S3 URL에서 bucket과 key 추출
                        bucket_name = os.getenv('S3_BUCKET_NAME', 'admeme-media-dev')

                        if video_url.startswith('s3://'):
                            # s3://bucket-name/key 형식
                            parts = video_url.replace('s3://', '').split('/', 1)
                            if len(parts) == 2:
                                bucket_name = parts[0]
                                s3_key = parts[1]
                            else:
                                raise ValueError(f"S3 URL 형식이 잘못되었습니다: {video_url}")
                        elif '.amazonaws.com/' in video_url:
                            # https://s3.amazonaws.com/bucket-name/key 또는
                            # https://bucket.s3.region.amazonaws.com/key 형식
                            url_part = video_url.split('.amazonaws.com/')[-1]
                            # bucket-name/key 형식이면 bucket 제거
                            if url_part.startswith(f'{bucket_name}/'):
                                s3_key = url_part[len(bucket_name)+1:]
                            else:
                                s3_key = url_part
                        elif f'{bucket_name}/' in video_url:
                            s3_key = video_url.split(f'{bucket_name}/')[-1]
                        else:
                            raise ValueError(f"S3 URL 형식을 파싱할 수 없습니다: {video_url}")

                        # 임시 파일 생성
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                        video_path = temp_file.name
                        temp_file.close()

                        # S3에서 다운로드
                        logger.info("Downloading from bucket=%s, key=%s", bucket_name, s3_key)
                        s3_client.download_file(bucket_name, s3_key, video_path)
                        logger.info("Downloaded to: %s", video_path)
                    else:
                        # 로컬 파일 경로
                        video_path = video_url
                        if not os.path.exists(video_path):
                            raise ValueError(f"영상 파일을 찾을 수 없습니다: {video_path}")

                    # YouTube 업로드
                    logger.info("Uploading video to YouTube: %s", video_path)
                    youtube_video_id = upload_video(
                        video_path=video_path,
                        title=publish_request.yt_title or video.title,
                        description=publish_request.yt_description or video.description or "",
                        privacy_status="private"
                    )
                    logger.info("YouTube upload successful: %s", youtube_video_id)

                finally:
                    # 임시 파일 삭제
                    if temp_file and os.path.exists(video_path):
                        try:
                            os.unlink(video_path)
                            logger.info("Cleaned up temp file: %s", video_path)
                        except Exception as e:
                            logger.error("Failed to delete temp file: %s", e)

            # DB 업데이트
            post.yt_video_id = youtube_video_id
            post.post_status = 'published'  # 게시 완료

        except Exception as e:
            logger.error("YouTube upload failed: %s", e)

    # 영상 상태 업데이트
    video.status = 'admin_approved'
    
    # workflow_execution, ad_request 상태 동기화
    if video.ad_id:
        from app.crud.final import _sync_workflow_status
        _sync_workflow_status(db, video.ad_id, 'approved', 'admin_approved')
    
    db.commit()
    db.refresh(post)  # post 객체 새로고침

    return PublishVideoResponse(
        video_id=video_id,
        post_id=post.post_id,
        status='uploaded' if youtube_video_id else 'scheduled',
        message=f'YouTube 업로드 완료: {youtube_video_id}' if youtube_video_id else 'YouTube 게시가 예약되었습니다'
    )


@router.post("/videos/{video_id}/hold", response_model=PublishVideoResponse)
async def hold_video(
    video_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """게시 보류"""
    await check_admin_permission(request)

    video_info = admin_crud.get_video_with_company(db, video_id)
    if not video_info:
        raise HTTPException(status_code=404, detail="영상을 찾을 수 없습니다")

    video = video_info['video']

    # 영상 상태를 admin_rejected로 변경
    video.status = 'admin_rejected'
    video.rejection_reason = '게시 보류'
    video.rejected_at = datetime.utcnow()
    
    # workflow_execution, ad_request 상태 동기화
    if video.ad_id:
        from app.crud.final import _sync_workflow_status
        _sync_workflow_status(db, video.ad_id, 'rejected', 'admin_rejected')
    
    db.commit()

    return PublishVideoResponse(
        video_id=video_id,
        post_id=0,  # hold는 post를 생성하지 않음
        status='admin_rejected',
        message='영상 게시가 보류되었습니다'
    )
