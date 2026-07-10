"""File storage abstraction (S3 / MinIO)."""
from __future__ import annotations

import os
import uuid
from io import BytesIO
from typing import Any

import boto3
from minio import Minio

from app.core.config import settings


def _get_minio_client() -> Minio:
    endpoint = settings.s3_endpoint.replace("https://", "").replace("http://", "")
    secure = settings.s3_endpoint.startswith("https://")
    return Minio(
        endpoint,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        secure=secure,
    )


def _get_s3_client() -> Any:
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint or None,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
    )


def upload_file(file_bytes: bytes, original_name: str, mime_type: str) -> str:
    ext = os.path.splitext(original_name)[1]
    key = f"resumes/{uuid.uuid4()}{ext}"

    if settings.use_minio:
        client = _get_minio_client()
        if not client.bucket_exists(settings.s3_bucket):
            client.make_bucket(settings.s3_bucket)
        client.put_object(
            settings.s3_bucket,
            key,
            BytesIO(file_bytes),
            length=len(file_bytes),
            content_type=mime_type,
        )
    else:
        client = _get_s3_client()
        client.put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=file_bytes,
            ContentType=mime_type,
        )
    return key


def get_file_url(key: str) -> str:
    if settings.use_minio:
        return f"{settings.s3_endpoint}/{settings.s3_bucket}/{key}"
    return f"https://{settings.s3_bucket}.s3.{settings.s3_region}.amazonaws.com/{key}"
