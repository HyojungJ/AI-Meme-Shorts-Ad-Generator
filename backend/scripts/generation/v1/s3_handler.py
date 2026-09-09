"""
AWS S3 ?뚯씪 ?낅줈??諛?愿由??묒뾽 ?댁슜 2踰? ?뚯씪 ?낅줈??泥섎━
蹂댁븞 ?ы빆 (UMS-AUT-04): AWS Access Key? Secret Key???섍꼍 蹂?섎줈 愿由?"""
import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from datetime import datetime, timedelta
import mimetypes

load_dotenv()

# AWS ?ㅼ젙 (UMS-AUT-04: ?섍꼍 蹂?섎줈 愿由?
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# S3 ?대씪?댁뼵???앹꽦
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)


# ============================================
# S3 ?뚯씪 寃쎈줈 洹쒖튃 (?묒뾽 ?댁슜 2踰?
# ============================================
def get_s3_path(file_type: str, company_id: int, filename: str) -> str:
    """
    S3 ?뚯씪 寃쎈줈 ?앹꽦
    
    寃쎈줈 洹쒖튃:
    - 罹먮┃???대?吏: characters/{company_id}/{timestamp}_{filename}
    - 罹먮┃???뚯꽦: voices/{company_id}/{timestamp}_{filename}
    - ?쒗뭹 ?대?吏: products/{company_id}/{timestamp}_{filename}
    - 異쒕젰 ?곸긽: videos/{company_id}/{job_id}/{filename}
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
# ?뚯씪 ?낅줈??# ============================================
def upload_file_to_s3(file_content: bytes, file_type: str, company_id: int, 
                     filename: str, content_type: str = None) -> str:
    """
    ?뚯씪??S3???낅줈??    
    Args:
        file_content: ?뚯씪 諛붿씠?덈━ ?곗씠??        file_type: ?뚯씪 ???(character_image, character_voice, product_image)
        company_id: ?뚯궗 ID
        filename: ?뚯씪紐?        content_type: MIME ???(?좏깮)
    
    Returns:
        S3 URL
    """
    try:
        # S3 寃쎈줈 ?앹꽦
        s3_key = get_s3_path(file_type, company_id, filename)
        
        # Content-Type ?먮룞 媛먯?
        if not content_type:
            content_type, _ = mimetypes.guess_type(filename)
            if not content_type:
                content_type = 'application/octet-stream'
        
        # S3 ?낅줈??        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_content,
            ContentType=content_type
        )
        
        # S3 URL ?앹꽦
        s3_url = f"s3://{S3_BUCKET_NAME}/{s3_key}"
        print(f"S3 ?낅줈???깃났: {s3_url}")
        
        return s3_url
        
    except ClientError as e:
        print(f"S3 ?낅줈???ㅽ뙣: {e}")
        raise Exception(f"S3 ?낅줈???ㅽ뙣: {str(e)}")


# ============================================
# Pre-signed URL ?앹꽦 (蹂댁븞)
# ============================================
def generate_presigned_url(s3_url: str, expiration: int = 3600) -> str:
    """
    Pre-signed URL ?앹꽦 (蹂댁븞???꾪븳 ?꾩떆 URL)
    
    Args:
        s3_url: S3 URL (s3://bucket/key ?뺤떇)
        expiration: ?좏슚 ?쒓컙 (珥? 湲곕낯 1?쒓컙)
    
    Returns:
        Pre-signed URL
    """
    try:
        # S3 URL?먯꽌 bucket怨?key 異붿텧
        if not s3_url.startswith("s3://"):
            raise ValueError("Invalid S3 URL format")
        
        parts = s3_url.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""
        
        # Pre-signed URL ?앹꽦
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expiration
        )
        
        return presigned_url
        
    except ClientError as e:
        print(f"Pre-signed URL ?앹꽦 ?ㅽ뙣: {e}")
        raise Exception(f"Pre-signed URL ?앹꽦 ?ㅽ뙣: {str(e)}")


# ============================================
# ?뚯씪 寃利?# ============================================
def validate_file_size(file_size: int, max_size_mb: int = 50) -> bool:
    """
    ?뚯씪 ?ш린 寃利?    
    Args:
        file_size: ?뚯씪 ?ш린 (bytes)
        max_size_mb: 理쒕? ?ш린 (MB)
    
    Returns:
        寃利?寃곌낵
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes


def validate_file_format(filename: str, allowed_formats: list) -> bool:
    """
    ?뚯씪 ?щ㎎ 寃利?    
    Args:
        filename: ?뚯씪紐?        allowed_formats: ?덉슜???뺤옣??由ъ뒪??(?? ['.jpg', '.png'])
    
    Returns:
        寃利?寃곌낵
    """
    file_ext = os.path.splitext(filename)[1].lower()
    return file_ext in allowed_formats


# ============================================
# ?뚯씪 ??낅퀎 寃利?洹쒖튃
# ============================================
IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.webp']
AUDIO_FORMATS = ['.mp3', '.wav', '.m4a']
VIDEO_FORMATS = ['.mp4', '.mov', '.avi']

MAX_IMAGE_SIZE_MB = 10  # ?대?吏 理쒕? 10MB
MAX_AUDIO_SIZE_MB = 50  # ?뚯꽦 理쒕? 50MB
MAX_VIDEO_SIZE_MB = 500  # ?곸긽 理쒕? 500MB


def validate_character_image(filename: str, file_size: int) -> tuple[bool, str]:
    """罹먮┃???대?吏 寃利?""
    if not validate_file_format(filename, IMAGE_FORMATS):
        return False, f"吏?먰븯吏 ?딅뒗 ?대?吏 ?뺤떇?낅땲?? ?덉슜: {', '.join(IMAGE_FORMATS)}"
    
    if not validate_file_size(file_size, MAX_IMAGE_SIZE_MB):
        return False, f"?대?吏 ?ш린媛 ?덈Т ?쎈땲?? 理쒕?: {MAX_IMAGE_SIZE_MB}MB"
    
    return True, "OK"


def validate_character_voice(filename: str, file_size: int) -> tuple[bool, str]:
    """罹먮┃???뚯꽦 寃利?""
    if not validate_file_format(filename, AUDIO_FORMATS):
        return False, f"吏?먰븯吏 ?딅뒗 ?뚯꽦 ?뺤떇?낅땲?? ?덉슜: {', '.join(AUDIO_FORMATS)}"
    
    if not validate_file_size(file_size, MAX_AUDIO_SIZE_MB):
        return False, f"?뚯꽦 ?뚯씪 ?ш린媛 ?덈Т ?쎈땲?? 理쒕?: {MAX_AUDIO_SIZE_MB}MB"
    
    return True, "OK"


def validate_product_image(filename: str, file_size: int) -> tuple[bool, str]:
    """?쒗뭹 ?대?吏 寃利?""
    if not validate_file_format(filename, IMAGE_FORMATS):
        return False, f"吏?먰븯吏 ?딅뒗 ?대?吏 ?뺤떇?낅땲?? ?덉슜: {', '.join(IMAGE_FORMATS)}"
    
    if not validate_file_size(file_size, MAX_IMAGE_SIZE_MB):
        return False, f"?대?吏 ?ш린媛 ?덈Т ?쎈땲?? 理쒕?: {MAX_IMAGE_SIZE_MB}MB"
    
    return True, "OK"
