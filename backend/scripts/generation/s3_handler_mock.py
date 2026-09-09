"""
Mock S3 Handler - 테스트용
실제 S3 없이 API 테스트 가능
"""
from datetime import datetime


# ============================================
# Mock S3 파일 경로 생성
# ============================================
def get_s3_path(file_type: str, company_id: int, filename: str) -> str:
    """
    S3 파일 경로 생성 (Mock)
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
# Mock 파일 업로드
# ============================================
def upload_file_to_s3(file_content: bytes, file_type: str, company_id: int, 
                     filename: str, content_type: str = None) -> str:
    """
    파일을 S3에 업로드 (Mock - 실제 업로드 안 함)
    
    Returns:
        Mock S3 URL
    """
    # S3 경로 생성
    s3_key = get_s3_path(file_type, company_id, filename)
    
    # Mock S3 URL 생성
    s3_url = f"s3://mock-bucket/{s3_key}"
    
    print(f"✅ Mock S3 업로드: {s3_url} (크기: {len(file_content)} bytes)")
    
    return s3_url


# ============================================
# Mock Pre-signed URL 생성
# ============================================
def generate_presigned_url(s3_url: str, expiration: int = 3600) -> str:
    """
    Pre-signed URL 생성 (Mock)
    
    Returns:
        Mock Pre-signed URL
    """
    # Mock URL 생성
    mock_url = s3_url.replace("s3://", "https://mock-s3.amazonaws.com/")
    mock_url += f"?expires={expiration}"
    
    print(f"✅ Mock Pre-signed URL 생성: {mock_url}")
    
    return mock_url


# ============================================
# 파일 검증 (실제 검증 로직 유지)
# ============================================
def validate_file_size(file_size: int, max_size_mb: int = 50) -> bool:
    """파일 크기 검증"""
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes


def validate_file_format(filename: str, allowed_formats: list) -> bool:
    """파일 포맷 검증"""
    import os
    file_ext = os.path.splitext(filename)[1].lower()
    return file_ext in allowed_formats


# 파일 타입별 검증 규칙
IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.webp']
AUDIO_FORMATS = ['.mp3', '.wav', '.m4a']
VIDEO_FORMATS = ['.mp4', '.mov', '.avi']

MAX_IMAGE_SIZE_MB = 10
MAX_AUDIO_SIZE_MB = 50
MAX_VIDEO_SIZE_MB = 500


def validate_character_image(filename: str, file_size: int) -> tuple[bool, str]:
    """캐릭터 이미지 검증"""
    if not validate_file_format(filename, IMAGE_FORMATS):
        return False, f"지원하지 않는 이미지 형식입니다. 허용: {', '.join(IMAGE_FORMATS)}"
    
    if not validate_file_size(file_size, MAX_IMAGE_SIZE_MB):
        return False, f"이미지 크기가 너무 큽니다. 최대: {MAX_IMAGE_SIZE_MB}MB"
    
    return True, "OK"


def validate_character_voice(filename: str, file_size: int) -> tuple[bool, str]:
    """캐릭터 음성 검증"""
    if not validate_file_format(filename, AUDIO_FORMATS):
        return False, f"지원하지 않는 음성 형식입니다. 허용: {', '.join(AUDIO_FORMATS)}"
    
    if not validate_file_size(file_size, MAX_AUDIO_SIZE_MB):
        return False, f"음성 파일 크기가 너무 큽니다. 최대: {MAX_AUDIO_SIZE_MB}MB"
    
    return True, "OK"


def validate_product_image(filename: str, file_size: int) -> tuple[bool, str]:
    """제품 이미지 검증"""
    if not validate_file_format(filename, IMAGE_FORMATS):
        return False, f"지원하지 않는 이미지 형식입니다. 허용: {', '.join(IMAGE_FORMATS)}"
    
    if not validate_file_size(file_size, MAX_IMAGE_SIZE_MB):
        return False, f"이미지 크기가 너무 큽니다. 최대: {MAX_IMAGE_SIZE_MB}MB"
    
    return True, "OK"
