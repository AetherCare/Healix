"""
Storage abstraction with factory pattern supporting local filesystem and AWS S3.
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError

from app.core.config import Settings, get_settings


class StorageBackend(ABC):
    """Abstract storage interface for file persistence."""

    @abstractmethod
    async def save(self, content: bytes, filename: str, folder: str) -> str:
        """Persist file content and return its accessible URL/path."""

    @abstractmethod
    async def delete(self, file_url: str) -> bool:
        """Remove a stored file by its URL/path."""

    @abstractmethod
    async def read(self, file_url: str) -> bytes:
        """Read file content from storage."""


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage for development and on-prem deployments."""

    def __init__(self, base_path: str) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, file_url: str) -> Path:
        """Convert stored URL to local filesystem path."""
        relative = file_url.replace("local://", "")
        return self.base_path / relative

    async def save(self, content: bytes, filename: str, folder: str) -> str:
        target_dir = self.base_path / folder
        target_dir.mkdir(parents=True, exist_ok=True)
        unique_name = f"{uuid4().hex}_{filename}"
        target_path = target_dir / unique_name
        target_path.write_bytes(content)
        return f"local://{folder}/{unique_name}"

    async def delete(self, file_url: str) -> bool:
        path = self._resolve_path(file_url)
        if path.exists():
            path.unlink()
            return True
        return False

    async def read(self, file_url: str) -> bytes:
        return self._resolve_path(file_url).read_bytes()


class S3StorageBackend(StorageBackend):
    """AWS S3 storage backend for production cloud deployments."""

    def __init__(
        self,
        bucket: str,
        region: str,
        access_key: str,
        secret_key: str,
    ) -> None:
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=access_key or None,
            aws_secret_access_key=secret_key or None,
        )

    async def save(self, content: bytes, filename: str, folder: str) -> str:
        key = f"{folder}/{uuid4().hex}_{filename}"
        self.client.put_object(Bucket=self.bucket, Key=key, Body=content)
        return f"s3://{self.bucket}/{key}"

    async def delete(self, file_url: str) -> bool:
        key = file_url.replace(f"s3://{self.bucket}/", "")
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    async def read(self, file_url: str) -> bytes:
        key = file_url.replace(f"s3://{self.bucket}/", "")
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()


def create_storage_backend(settings: Optional[Settings] = None) -> StorageBackend:
    """
    Factory function returning the configured storage backend.

    Hot-swappable via STORAGE_BACKEND environment variable.
    """
    cfg = settings or get_settings()
    backend = cfg.storage_backend.lower()

    if backend == "s3":
        return S3StorageBackend(
            bucket=cfg.aws_s3_bucket,
            region=cfg.aws_s3_region,
            access_key=cfg.aws_access_key_id,
            secret_key=cfg.aws_secret_access_key,
        )
    return LocalStorageBackend(base_path=cfg.storage_local_path)
