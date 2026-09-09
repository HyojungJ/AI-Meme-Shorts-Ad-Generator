"""
AWS S3 파일 업로드 및 관리 서비스
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from app.core.config import settings

# 로거 설정
logger = logging.getLogger(__name__)

# S3 클라이언트 초기화
try:
    s3_client = boto3.client(
        's3',
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )
    logger.info(f"S3 클라이언트 초기화 완료 (Region: {settings.AWS_REGION})")
except NoCredentialsError:
    logger.warning("AWS 자격 증명을 찾을 수 없습니다. Mock 모드를 사용하세요.")
    s3_client = None


# ============================================
# S3 파일 경로 생성
# ============================================
def get_s3_path(file_type: str, company_id: int, filename: str) -> str:
    """
    S3 파일 경로 생성
    
    Args:
        file_type: 파일 타입 (character_image, character_voice, product_image, output_video)
        company_id: 회사 ID
        filename: 파일명
    
    Returns:
        S3 키 경로
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    path_mapping = {
        "character_image": f"characters/{company_id}/{timestamp}_{filename}",
        "character_voice": f"voices/{company_id}/{timestamp}_{filename}",
        "product_image": f"products/{company_id}/{timestamp}_{filename}",
        "output_video": f"videos/{company_id}/{timestamp}_{filename}"
    }
    
    return path_mapping.get(file_type, f"misc/{company_id}/{timestamp}_{filename}")


# ============================================
# 파일 업로드
# ============================================
def upload_file_to_s3(
    file_content: bytes,
    file_type: str,
    company_id: int,
    filename: str,
    content_type: Optional[str] = None
) -> str:
    """
    파일을 S3에 업로드
    
    Args:
        file_content: 파일 바이너리 데이터
        file_type: 파일 타입
        company_id: 회사 ID
        filename: 파일명
        content_type: MIME 타입 (선택사항)
    
    Returns:
        S3 URL (s3://bucket/key)
    
    Raises:
        Exception: 업로드 실패 시
    """
    if not s3_client:
        raise Exception("S3 클라이언트가 초기화되지 않았습니다. AWS 자격 증명을 확인하세요.")
    
    if not settings.S3_BUCKET_NAME:
        raise Exception("S3_BUCKET_NAME 환경 변수가 설정되지 않았습니다.")
    
    try:
        # S3 경로 생성
        s3_key = get_s3_path(file_type, company_id, filename)
        
        # Content-Type 자동 감지
        if not content_type:
            ext = os.path.splitext(filename)[1].lower()
            content_type_mapping = {
                '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
                '.webp': 'image/webp', '.mp3': 'audio/mpeg', '.wav': 'audio/wav',
                '.m4a': 'audio/mp4', '.mp4': 'video/mp4', '.mov': 'video/quicktime',
                '.avi': 'video/x-msvideo'
            }
            content_type = content_type_mapping.get(ext, 'application/octet-stream')
        
        # S3 업로드
        s3_client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_content,
            ContentType=content_type
        )
        
        # S3 URL 생성
        s3_url = f"s3://{settings.S3_BUCKET_NAME}/{s3_key}"
        
        logger.info(f"✅ S3 업로드 성공: {s3_url} (크기: {len(file_content)} bytes)")
        
        return s3_url
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"❌ S3 업로드 실패 ({error_code}): {error_message}")
        raise Exception(f"S3 업로드 실패: {error_message}")
    
    except Exception as e:
        logger.error(f"❌ S3 업로드 중 오류 발생: {str(e)}")
        raise


# ============================================
# Pre-signed URL 생성
# ============================================
def _parse_s3_url(url: str) -> Tuple[str, str]:
    """S3 URL을 (bucket, key)로 파싱. s3:// 및 https:// 형식 모두 지원."""
    import re

    if url.startswith("s3://"):
        parts = url.replace("s3://", "").split("/", 1)
        if len(parts) == 2:
            return parts[0], parts[1]

    # https://bucket.s3.region.amazonaws.com/key (쿼리 파라미터 제거)
    match = re.match(r"https://([^.]+)\.s3[.\w-]*\.amazonaws\.com/([^?]+)", url)
    if match:
        return match.group(1), match.group(2)

    raise ValueError(f"S3 URL 파싱 실패: {url}")


def get_presigned_url(url: str, expiration: int = 604800) -> Optional[str]:
    """S3 URL(s3:// 또는 https://)을 presigned URL로 변환. 실패 시 None 반환."""
    if not url or not s3_client:
        return None
    try:
        bucket_name, s3_key = _parse_s3_url(url)
        return s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': s3_key},
            ExpiresIn=expiration,
        )
    except Exception:
        # s3:// URL은 브라우저에서 로드할 수 없으므로 반환하지 않음
        if url.startswith("s3://"):
            return None
        return url


def generate_presigned_url(s3_url: str, expiration: int = 604800) -> str:
    """
    Pre-signed URL 생성 (임시 다운로드 링크)

    Args:
        s3_url: S3 URL (s3://bucket/key 또는 https://bucket.s3...amazonaws.com/key)
        expiration: 유효 기간 (초, 기본 7일)

    Returns:
        Pre-signed URL (https://...)

    Raises:
        Exception: URL 생성 실패 시
    """
    if not s3_client:
        raise Exception("S3 클라이언트가 초기화되지 않았습니다.")

    try:
        bucket_name, s3_key = _parse_s3_url(s3_url)
        
        # Pre-signed URL 생성
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': s3_key
            },
            ExpiresIn=expiration
        )
        
        logger.info(f"✅ Pre-signed URL 생성 성공 (유효기간: {expiration}초)")
        
        return presigned_url
    
    except ClientError as e:
        error_message = e.response['Error']['Message']
        logger.error(f"❌ Pre-signed URL 생성 실패: {error_message}")
        raise Exception(f"Pre-signed URL 생성 실패: {error_message}")
    
    except Exception as e:
        logger.error(f"❌ Pre-signed URL 생성 중 오류 발생: {str(e)}")
        raise


# ============================================
# 파일 삭제
# ============================================
def delete_file_from_s3(s3_url: str) -> bool:
    """
    S3에서 파일 삭제
    
    Args:
        s3_url: S3 URL (s3://bucket/key)
    
    Returns:
        삭제 성공 여부
    """
    if not s3_client:
        logger.warning("S3 클라이언트가 초기화되지 않았습니다.")
        return False
    
    try:
        # S3 URL 파싱
        if not s3_url.startswith("s3://"):
            raise ValueError("올바른 S3 URL 형식이 아닙니다")
        
        parts = s3_url.replace("s3://", "").split("/", 1)
        if len(parts) != 2:
            raise ValueError("S3 URL 파싱 실패")
        
        bucket_name, s3_key = parts
        
        # 파일 삭제
        s3_client.delete_object(
            Bucket=bucket_name,
            Key=s3_key
        )
        
        logger.info(f"✅ S3 파일 삭제 성공: {s3_url}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ S3 파일 삭제 실패: {str(e)}")
        return False


# ============================================
# 파일 검증
# ============================================
def validate_file_size(file_size: int, max_size_mb: int = 50) -> bool:
    """파일 크기 검증"""
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes


def validate_file_format(filename: str, allowed_formats: list) -> bool:
    """파일 포맷 검증"""
    file_ext = os.path.splitext(filename)[1].lower()
    return file_ext in allowed_formats


# 파일 타입별 검증 규칙
IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.webp']
AUDIO_FORMATS = ['.mp3', '.wav', '.m4a']
VIDEO_FORMATS = ['.mp4', '.mov', '.avi']

MAX_IMAGE_SIZE_MB = 10
MAX_AUDIO_SIZE_MB = 50
MAX_VIDEO_SIZE_MB = 500


def validate_character_image(filename: str, file_size: int) -> Tuple[bool, str]:
    """캐릭터 이미지 검증"""
    if not validate_file_format(filename, IMAGE_FORMATS):
        return False, f"지원하지 않는 이미지 형식입니다. 허용: {', '.join(IMAGE_FORMATS)}"
    
    if not validate_file_size(file_size, MAX_IMAGE_SIZE_MB):
        return False, f"이미지 크기가 너무 큽니다. 최대: {MAX_IMAGE_SIZE_MB}MB"
    
    return True, "OK"


def validate_character_voice(filename: str, file_size: int) -> Tuple[bool, str]:
    """캐릭터 음성 검증"""
    if not validate_file_format(filename, AUDIO_FORMATS):
        return False, f"지원하지 않는 음성 형식입니다. 허용: {', '.join(AUDIO_FORMATS)}"
    
    if not validate_file_size(file_size, MAX_AUDIO_SIZE_MB):
        return False, f"음성 파일 크기가 너무 큽니다. 최대: {MAX_AUDIO_SIZE_MB}MB"
    
    return True, "OK"


def validate_product_image(filename: str, file_size: int) -> Tuple[bool, str]:
    """제품 이미지 검증"""
    if not validate_file_format(filename, IMAGE_FORMATS):
        return False, f"지원하지 않는 이미지 형식입니다. 허용: {', '.join(IMAGE_FORMATS)}"
    
    if not validate_file_size(file_size, MAX_IMAGE_SIZE_MB):
        return False, f"이미지 크기가 너무 큽니다. 최대: {MAX_IMAGE_SIZE_MB}MB"
    
    return True, "OK"


def validate_output_video(filename: str, file_size: int) -> Tuple[bool, str]:
    """최종 영상 검증"""
    if not validate_file_format(filename, VIDEO_FORMATS):
        return False, f"지원하지 않는 영상 형식입니다. 허용: {', '.join(VIDEO_FORMATS)}"
    
    if not validate_file_size(file_size, MAX_VIDEO_SIZE_MB):
        return False, f"영상 파일 크기가 너무 큽니다. 최대: {MAX_VIDEO_SIZE_MB}MB"
    
    return True, "OK"


# ============================================
# S3 연결 테스트
# ============================================
def test_s3_connection() -> Tuple[bool, str]:
    """
    S3 연결 테스트
    
    Returns:
        (성공 여부, 메시지)
    """
    if not s3_client:
        return False, "S3 클라이언트가 초기화되지 않았습니다."
    
    if not settings.S3_BUCKET_NAME:
        return False, "S3_BUCKET_NAME이 설정되지 않았습니다."
    
    try:
        # 버킷 존재 확인
        s3_client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
        return True, f"S3 연결 성공: {settings.S3_BUCKET_NAME}"
    
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            return False, f"버킷을 찾을 수 없습니다: {settings.S3_BUCKET_NAME}"
        elif error_code == '403':
            return False, "버킷 접근 권한이 없습니다."
        else:
            return False, f"S3 연결 실패: {e.response['Error']['Message']}"
    
    except Exception as e:
        return False, f"S3 연결 테스트 중 오류: {str(e)}"
