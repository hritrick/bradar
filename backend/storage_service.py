"""Pluggable storage for report artefacts.

Supported providers:
  - 'local' : stores files under STORAGE_LOCAL_DIR
  - 's3'    : stores files in any S3-compatible bucket (AWS S3, MinIO, Cloudflare R2,
              DigitalOcean Spaces, etc.) via boto3.

URIs returned:
  - local : 'file:///abs/path/to/file.pdf'
  - s3    : 's3://bucket/key'
"""
import io
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

log = logging.getLogger(__name__)


class StorageProvider(ABC):
    name: str = "base"

    @abstractmethod
    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Store bytes at logical key; returns the URI."""

    @abstractmethod
    def get(self, uri: str) -> bytes:
        """Read bytes for a given URI previously returned by put()."""

    @abstractmethod
    def exists(self, uri: str) -> bool:
        ...

    @abstractmethod
    def delete(self, uri: str) -> None:
        ...

    def signed_url(self, uri: str, expires_seconds: int = 600) -> Optional[str]:
        """Return a signed URL where the underlying provider supports it; otherwise None."""
        return None


class LocalDiskStorage(StorageProvider):
    name = "local"

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _abs(self, key: str) -> Path:
        p = (self.base_dir / key.lstrip("/")).resolve()
        if not str(p).startswith(str(self.base_dir)):
            raise ValueError("path traversal blocked")
        return p

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        path = self._abs(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return f"file://{path}"

    def _path_from_uri(self, uri: str) -> Path:
        if uri.startswith("file://"):
            return Path(uri[len("file://"):])
        # legacy: bare path stored by older code
        return Path(uri)

    def get(self, uri: str) -> bytes:
        with open(self._path_from_uri(uri), "rb") as f:
            return f.read()

    def exists(self, uri: str) -> bool:
        return self._path_from_uri(uri).exists()

    def delete(self, uri: str) -> None:
        try:
            self._path_from_uri(uri).unlink()
        except FileNotFoundError:
            pass


class S3CompatibleStorage(StorageProvider):
    """Works with AWS S3, MinIO, Cloudflare R2, DigitalOcean Spaces, etc."""
    name = "s3"

    def __init__(self, bucket: str, region: str, endpoint_url: Optional[str],
                 access_key: str, secret_key: str, public_url_prefix: Optional[str] = None):
        import boto3
        from botocore.config import Config
        self.bucket = bucket
        self.region = region
        self.endpoint_url = endpoint_url or None
        self.public_url_prefix = (public_url_prefix or "").rstrip("/") or None
        self._client = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=endpoint_url or None,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4", retries={"max_attempts": 3, "mode": "standard"}),
        )

    @staticmethod
    def _parse(uri: str) -> tuple[str, str]:
        u = urlparse(uri)
        if u.scheme != "s3":
            raise ValueError("not an s3 URI")
        return u.netloc, u.path.lstrip("/")

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        key = key.lstrip("/")
        self._client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        return f"s3://{self.bucket}/{key}"

    def get(self, uri: str) -> bytes:
        bucket, key = self._parse(uri)
        resp = self._client.get_object(Bucket=bucket, Key=key)
        return resp["Body"].read()

    def exists(self, uri: str) -> bool:
        try:
            bucket, key = self._parse(uri)
            self._client.head_object(Bucket=bucket, Key=key)
            return True
        except Exception:
            return False

    def delete(self, uri: str) -> None:
        bucket, key = self._parse(uri)
        self._client.delete_object(Bucket=bucket, Key=key)

    def signed_url(self, uri: str, expires_seconds: int = 600) -> Optional[str]:
        bucket, key = self._parse(uri)
        try:
            return self._client.generate_presigned_url("get_object",
                                                       Params={"Bucket": bucket, "Key": key},
                                                       ExpiresIn=expires_seconds)
        except Exception as e:
            log.warning("signed_url failed: %s", e)
            return None


# Singleton built lazily from env vars.
_storage: Optional[StorageProvider] = None


def get_storage() -> StorageProvider:
    global _storage
    if _storage is not None:
        return _storage
    provider = (os.environ.get("STORAGE_PROVIDER") or "local").lower()
    if provider == "s3":
        bucket = os.environ.get("STORAGE_S3_BUCKET") or ""
        region = os.environ.get("STORAGE_S3_REGION") or "ap-south-1"
        endpoint = os.environ.get("STORAGE_S3_ENDPOINT_URL") or None
        ak = os.environ.get("STORAGE_S3_ACCESS_KEY") or ""
        sk = os.environ.get("STORAGE_S3_SECRET_KEY") or ""
        public_prefix = os.environ.get("STORAGE_S3_PUBLIC_URL_PREFIX") or ""
        if not (bucket and ak and sk):
            log.warning("STORAGE_PROVIDER=s3 but credentials/bucket missing — falling back to local disk.")
        else:
            try:
                _storage = S3CompatibleStorage(bucket, region, endpoint, ak, sk, public_prefix)
                log.info("Storage: S3-compatible (bucket=%s, endpoint=%s)", bucket, endpoint or "aws")
                return _storage
            except Exception as e:
                log.warning("Could not initialise S3 storage (%s) — falling back to local.", e)
    base_dir = os.environ.get("STORAGE_LOCAL_DIR") or "/app/backend/reports_out"
    _storage = LocalDiskStorage(base_dir)
    log.info("Storage: LocalDiskStorage at %s", base_dir)
    return _storage


def reset_for_tests():
    global _storage
    _storage = None
