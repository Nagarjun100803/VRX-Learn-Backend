from functools import lru_cache
from urllib.parse import quote

import aioboto3
from aioboto3 import Session
from mypy_boto3_s3 import S3Client

from src.settings import settings

DEFAULT_EXPIRE_SECONDS = 5 * 60  # Later this will come from settings.


class FileMetadata:
    def __init__(self, key: str, filename: str, content_type: str) -> None:
        self.filename = filename
        self.key = key
        self.content_type = content_type


@lru_cache
def get_session() -> aioboto3.Session:
    return aioboto3.Session(
        aws_access_key_id=settings.aws_s3.access_key_id.get_secret_value(),
        aws_secret_access_key=settings.aws_s3.secret_access_key.get_secret_value(),
        region_name=settings.aws_s3.region.get_secret_value(),
    )


class S3Bucket:
    def __init__(self, bucket_name: str, session: Session) -> None:
        self.bucket_name = bucket_name
        self.session = session

    async def get_view_url(
        self, metadata: FileMetadata, expires_in_seconds: int = DEFAULT_EXPIRE_SECONDS
    ) -> str:

        async with self.session.client("s3") as s3:  # type: ignore[reportGeneralTypeIssues]
            s3: S3Client
            return await s3.generate_presigned_url(  # type: ignore[reportGeneralTypeIssues]
                ClientMethod="get_object",
                Params={
                    "Key": metadata.key,
                    "Bucket": self.bucket_name,
                    "ResponseContentDisposition": f"inline; filename={quote(metadata.filename)}",
                    "ResponseContentType": metadata.content_type,
                },
                ExpiresIn=expires_in_seconds,
            )

    async def get_upload_url(
        self, metadata: FileMetadata, expires_in_seconds: int = DEFAULT_EXPIRE_SECONDS
    ) -> str:
        async with self.session.client("s3") as s3:  # type: ignore[reportGeneralTypeIssues]
            s3: S3Client
            return await s3.generate_presigned_url(  # type: ignore[reportGeneralTypeIssues]
                ClientMethod="put_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": metadata.key,
                    "ContentType": metadata.content_type,
                },
                ExpiresIn=expires_in_seconds,
            )
