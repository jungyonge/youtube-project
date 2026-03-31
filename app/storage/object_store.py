from __future__ import annotations

import asyncio
from functools import partial
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from loguru import logger

from app.config import settings


class ObjectStore:
    def __init__(self) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )

    def _run_sync(self, func: partial[Any]) -> Any:
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, func)

    async def ensure_bucket(self, bucket: str) -> None:
        try:
            await self._run_sync(partial(self._client.head_bucket, Bucket=bucket))
        except ClientError:
            logger.info("Creating bucket: {}", bucket)
            await self._run_sync(partial(self._client.create_bucket, Bucket=bucket))

    async def upload(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        await self._run_sync(
            partial(
                self._client.put_object,
                Bucket=bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
        )
        logger.debug("Uploaded s3://{}/{} ({} bytes)", bucket, key, len(data))
        return key

    async def download(self, bucket: str, key: str) -> bytes:
        response = await self._run_sync(
            partial(self._client.get_object, Bucket=bucket, Key=key)
        )
        body = response["Body"].read()
        logger.debug("Downloaded s3://{}/{} ({} bytes)", bucket, key, len(body))
        return body

    async def presigned_url(
        self, bucket: str, key: str, expires_in: int = 3600
    ) -> str:
        url: str = self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        if settings.S3_PUBLIC_URL:
            url = url.replace(settings.S3_ENDPOINT_URL, settings.S3_PUBLIC_URL)
        return url

    async def delete(self, bucket: str, key: str) -> None:
        await self._run_sync(
            partial(self._client.delete_object, Bucket=bucket, Key=key)
        )
        logger.debug("Deleted s3://{}/{}", bucket, key)

    async def exists(self, bucket: str, key: str) -> bool:
        try:
            await self._run_sync(
                partial(self._client.head_object, Bucket=bucket, Key=key)
            )
            return True
        except ClientError:
            return False

    async def list_objects(self, bucket: str, prefix: str = "") -> list[str]:
        response = await self._run_sync(
            partial(self._client.list_objects_v2, Bucket=bucket, Prefix=prefix)
        )
        contents = response.get("Contents", [])
        return [obj["Key"] for obj in contents]


object_store = ObjectStore()
