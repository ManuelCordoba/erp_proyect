"""
S3 service utilities for generating pre-signed URLs.
"""
import boto3
from botocore.exceptions import ClientError
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Cached S3 client instance
_s3_client = None


def get_s3_client():
    """
    Get S3 client configured with AWS credentials.
    The client is created once and reused for futures calls.
    """
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            config=boto3.session.Config(signature_version=settings.AWS_S3_SIGNATURE_VERSION)
        )
    return _s3_client


def check_object_exists(bucket_key: str) -> bool:
    """
    Check if an object exists in S3.
    
    Args:
        bucket_key: The S3 key (path) of the file to check
    
    Returns:
        True if the object exists, False otherwise
    """
    try:
        s3_client = get_s3_client()
        s3_client.head_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=bucket_key
        )
        return True
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == '404' or error_code == 'NoSuchKey':
            return False
        # For other errors, log and re-raise
        logger.error(f"Error checking if object exists in S3: {e}")
        raise


def generate_presigned_upload_url(bucket_key: str, content_type: str, expiration: int = None) -> dict:
    """
    Generate a pre-signed URL for uploading a file to S3.
    
    Args:
        bucket_key: The S3 key (path) where the file will be uploaded
        content_type: The MIME type of the file
        expiration: URL expiration time in seconds (defaults to AWS_S3_PRESIGNED_URL_EXPIRATION)
    
    Returns:
        dict with 'upload_url' and 'bucket_key'
    """
    try:
        s3_client = get_s3_client()
        expiration = expiration or settings.AWS_S3_PRESIGNED_URL_EXPIRATION

        # Generate pre-signed POST URL for upload (more reliable than PUT)
        presigned_post = s3_client.generate_presigned_post(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=bucket_key,
            Fields={'Content-Type': content_type},
            Conditions=[
                {'Content-Type': content_type},
                ['content-length-range', 1, 10 * 1024 * 1024 * 1024]  # Max 10GB
            ],
            ExpiresIn=expiration
        )
        
        return {
            'upload_url': presigned_post['url'],
            'fields': presigned_post['fields'],
            'bucket_key': bucket_key
        }
    except ClientError as e:
        logger.error(f"Error generating presigned upload URL: {e}")
        raise


def generate_presigned_download_url(bucket_key: str, expiration: int = None) -> str:
    """
    Generate a pre-signed URL for downloading a file from S3.
    
    Args:
        bucket_key: The S3 key (path) of the file to download
        expiration: URL expiration time in seconds (defaults to AWS_S3_PRESIGNED_URL_EXPIRATION)
    
    Returns:
        Pre-signed URL string
    """
    try:
        s3_client = get_s3_client()
        expiration = expiration or settings.AWS_S3_PRESIGNED_URL_EXPIRATION
        
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': bucket_key
            },
            ExpiresIn=expiration
        )
        
        return presigned_url
    except ClientError as e:
        logger.error(f"Error generating presigned download URL: {e}")
        raise