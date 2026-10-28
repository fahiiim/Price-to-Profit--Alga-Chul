"""S3 Storage Service for business logos and generated document PDFs.

Supports object tagging (type=quote, type=invoice, type=internal_revenue, type=logo)
and graceful local fallback when S3 is not configured.
"""

import logging
from collections.abc import Mapping
from urllib.parse import urlencode

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import Settings

logger = logging.getLogger(__name__)


def _build_s3_client(settings: Settings):
    kwargs: dict = {"region_name": settings.s3_region}
    key_id = settings.aws_access_key_id.strip() if settings.aws_access_key_id else None
    secret = (
        settings.aws_secret_access_key.strip()
        if settings.aws_secret_access_key
        else None
    )
    if key_id and secret:
        kwargs["aws_access_key_id"] = key_id
        kwargs["aws_secret_access_key"] = secret
    if settings.s3_endpoint_url:
        kwargs["endpoint_url"] = settings.s3_endpoint_url
    return boto3.client("s3", **kwargs)


def upload_to_s3(
    settings: Settings,
    *,
    key: str,
    data: bytes,
    content_type: str,
    tags: Mapping[str, str] | None = None,
) -> bool:
    """Upload data to S3 with object tagging and metadata.

    Returns True if successfully uploaded, False if S3 is not configured
    or an error occurred.
    """
    if not settings.s3_bucket_name:
        return False

    try:
        client = _build_s3_client(settings)
        params: dict = {
            "Bucket": settings.s3_bucket_name,
            "Key": key,
            "Body": data,
            "ContentType": content_type,
        }

        if tags:
            # S3 put_object accepts Tagging as a URL-encoded string: key1=val1&key2=val2
            params["Tagging"] = urlencode(tags)
            # Metadata keys in S3 must be strings
            params["Metadata"] = {k: str(v) for k, v in tags.items()}

        client.put_object(**params)
        logger.info(
            "Uploaded %s (%d bytes) to s3://%s with tags %s",
            key,
            len(data),
            settings.s3_bucket_name,
            tags,
        )
        return True
    except (BotoCoreError, ClientError) as exc:
        logger.warning(
            "Failed to upload %s to s3://%s: %s", key, settings.s3_bucket_name, exc
        )
        return False


def delete_from_s3(settings: Settings, *, key: str) -> bool:
    """Delete an object from S3.

    Returns True if deleted or S3 not configured, False on failure.
    """
    if not settings.s3_bucket_name or not key:
        return True

    try:
        client = _build_s3_client(settings)
        client.delete_object(Bucket=settings.s3_bucket_name, Key=key)
        logger.info("Deleted %s from s3://%s", key, settings.s3_bucket_name)
        return True
    except (BotoCoreError, ClientError) as exc:
        logger.warning(
            "Failed to delete %s from s3://%s: %s", key, settings.s3_bucket_name, exc
        )
        return False


def download_from_s3(settings: Settings, *, key: str) -> bytes | None:
    """Download an object from S3 if available."""
    if not settings.s3_bucket_name or not key:
        return None

    try:
        client = _build_s3_client(settings)
        response = client.get_object(Bucket=settings.s3_bucket_name, Key=key)
        return response["Body"].read()
    except (BotoCoreError, ClientError) as exc:
        logger.warning(
            "Failed to download %s from s3://%s: %s", key, settings.s3_bucket_name, exc
        )
        return None
