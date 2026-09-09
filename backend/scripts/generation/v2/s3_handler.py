"""
AWS S3 파일 업로드 및 관리
작업 내용 2번: 파일 업로드 처리
보안 사항 (UMS-AUT-04): AWS Access Key와 Secret Key는 환경 변수로 관리
"""
import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from datetime import datetime, timedelta
import mimetypes

load_dotenv()

# AWS 설정 (UMS-AUT-04: 환경 변수로 관리)
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# S3 클라이언트 생성
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)


# ============================================
# S3 파일 경로 규칙 (작업 내용 2번)
# ============================================
def get_s3_path(file_type: str, company_id: int, filename: str) -> str:
    """
    S3 파일 경로 생성
    
    경로 규칙:
    - 캐릭터 이미지: characters/{company_id}/{timestamp}_{filename}
    - 캐릭터 음성: voices/{company_id}/{timestamp}_{filename}
    - 제품 이미지: products/{company_id}/{timestamp}_{filename}
    - 출력 영상: videos/{company_id}/{job_id}/{filename}
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
def upload_file_to_s3(file_content: bytes, file_type: str, company_id: int, 
                     filename: str, content_type: str = None) -> str:
    """
    파일을 S3에 업로드
    
    Args:
        file_content: 파일 바이너리 데이터
        file_type: 파일 타입 (character_image, character_voice, product_image)
        company_id: 회사 ID
        filename: 파일명
        content_type: MIME 타입 (선택)
    
    Returns:
        S3 URL
    """
    try:
        # S3 경로 생성
        s3_key = get_s3_path(file_type, company_id, filename)
        
        # Content-Type 자동 감지
        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
            if not content_type:
                content_type = 'application/octet-stream'
        
        # S3 업로드
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_content,
            ContentType=content_type
        )
        
        # S3 URL 생성
        s3_url = f"s3://{S3_BUCKET_NAME}/{s3_key}"
        print(f"S3 업로드 성공: {s3_url}")
        
        return s3_url
        
    except ClientError as e:
        print(f"S3 업로드 실패: {e}")
        raise Exception(f"S3 업로드 실패: {str(e)}")


# ============================================
# Pre-signed URL 생성 (보안)
# ============================================
def generate_presigned_url(s3_url: str, expiration: int = 3600) -> str:
    """
    Pre-signed URL 생성 (보안을 위한 임시 URL)
    
    Args:
        s3_url: S3 URL (s3://bucket/key 형식)
        expiration: 유효 시간 (초, 기본 1시간)
    
    Returns:
        Pre-signed URL
    """
    try:
        # S3 URL에서 bucket과 key 추출
        if not s3_url.startswith("s3://"):
            raise ValueError("Invalid S3 URL format")
        
        parts = s3_url.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""
        
        # Pre-signed URL 생성
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expiration
        )
        
        return presigned_url
        
    except ClientError as e:
        print(f"Pre-signed URL 생성 실패: {e}")
        raise Exception(f"Pre-signed URL 생성 실패: {str(e)}")


# ============================================
# 파일 검증
# ============================================
def validate_file_size(file_size: int, max_size_mb: int = 50) -> bool:
    """
    파일 크기 검증
    
    Args:
        file_size: 파일 크기 (bytes)
        max_size_mb: 최대 크기 (MB)
    
    Returns:
        검증 결과
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes


def validate_file_format(filename: str, allowed_formats: list) -> bool:
    """
    파일 포맷 검증
    
    Args:
        filename: 파일명
        allowed_formats: 허용된 확장자 리스트 (예: ['.jpg', '.png'])
    
    Returns:
        검증 결과
    """
    file_ext = os.path.splitext(filename)[1].lower()
    return file_ext in allowed_formats


# ============================================
# 파일 타입별 검증 규칙
# ============================================
IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.webp']
AUDIO_FORMATS = ['.mp3', '.wav', '.m4a']
VIDEO_FORMATS = ['.mp4', '.mov', '.avi']

MAX_IMAGE_SIZE_MB = 10  # 이미지 최대 10MB
MAX_AUDIO_SIZE_MB = 50  # 음성 최대 50MB
MAX_VIDEO_SIZE_MB = 500  # 영상 최대 500MB


def validate_product_image(filename: str, file_size: int) -> tuple[bool, str]:
    """제품 이미지 검증"""
    if not validate_file_format(filename, IMAGE_FORMATS):
        return False, f"지원하지 않는 이미지 형식입니다. 허용: {', '.join(IMAGE_FORMATS)}"
    
    if not validate_file_size(file_size, MAX_IMAGE_SIZE_MB):
        return False, f"이미지 크기가 너무 큽니다. 최대: {MAX_IMAGE_SIZE_MB}MB"
    
    return True, "OK"
