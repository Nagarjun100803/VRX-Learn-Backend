import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any, BinaryIO, List, Self
from urllib.parse import quote

# AWS SDK
import aioboto3
from mypy_boto3_s3 import S3Client
from mypy_boto3_s3.type_defs import DeleteObjectOutputTypeDef, DeleteTypeDef
from pydantic import BaseModel, Field, model_validator

from src.command.commands.media import AllowedContentTypes
from src.settings import settings


class FileMetadata(BaseModel):
    filename: str
    content_type: AllowedContentTypes
    size: Annotated[int, Field(gt=0, examples=[1024])]

    @model_validator(mode="after")
    def validate_filename(self) -> Self:
        self.filename = Path(self.filename).name
        return self

    def to_dict(self) -> dict:
        # NOTE: Implement this helper not to break previous
        # dataclass version of this class.
        return self.model_dump()


class StorageMetadata(BaseModel):
    key: str
    content_type: AllowedContentTypes
    size: Annotated[int, Field(gt=0, examples=[1024])]


@dataclass
class BaseObjectStorageService(ABC):
    @abstractmethod
    async def get_presigned_url(self, *args, **kwargs) -> str:
        """Generates a Presigned URL to view or download a file."""

    @abstractmethod
    async def generate_presigned_url(self, *args, **kwargs) -> str:
        """Generates a Presigned URL to upload a single file."""

    @abstractmethod
    async def generate_presigned_urls(self, *args, **kwargs) -> list[str]:
        """Generates a Presigned URL to upload multiple files."""

    @abstractmethod
    async def upload_file(self, *args, **kwargs) -> Any:
        """Used to upload a file directly to object storage"""

    @abstractmethod
    async def delete_files(self, *args, **kwargs) -> Any:
        "Used to delete a files from the object storage"


# Global session configuration to connect with the Cloud Service.

PRESIGNED_URL_EXPIRE_MINS = 120  # 2 Hour


@lru_cache
def get_session() -> aioboto3.Session:
    return aioboto3.Session(
        aws_access_key_id=settings.aws.access_key_id.get_secret_value(),
        aws_secret_access_key=settings.aws.secret_access_key.get_secret_value(),
        region_name=settings.aws.region.get_secret_value(),
    )


@dataclass
class S3(BaseObjectStorageService):
    bucket: str
    session: aioboto3.Session

    # NOTE: All the filenames refers the Key, So Appropriate Service eg. LessonService
    # AssignmentService handles adding the prefix to the filename.
    # For example. filename="assignments/{Nagarjun}/{Assignment1.pdf}"

    async def get_presigned_url(
        self,
        key: str,
        filename: str,
        mime_type: str,
        expire_mins: int = PRESIGNED_URL_EXPIRE_MINS,
    ) -> str:

        async with self.session.client("s3") as s3:  # type: ignore
            s3: S3Client
            return await s3.generate_presigned_url(  # type: ignore
                ClientMethod="get_object",
                Params={
                    "Key": key,
                    "Bucket": self.bucket,
                    "ResponseContentDisposition": f"inline; filename={quote(filename)}",
                    "ResponseContentType": mime_type,
                },
                ExpiresIn=(expire_mins * 60),
            )

    async def generate_presigned_url(
        self,
        file_metadata: StorageMetadata,
        expire_mins: int = PRESIGNED_URL_EXPIRE_MINS,
    ) -> str:

        async with self.session.client("s3") as s3:  # type: ignore
            s3: S3Client
            return await s3.generate_presigned_url(  # type: ignore
                ClientMethod="put_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": file_metadata.key,
                    "ContentType": file_metadata.content_type,
                },
                ExpiresIn=(expire_mins * 60),
            )

    async def generate_presigned_urls(
        self,
        files_metadata: List[StorageMetadata],
        expire_mins: int = PRESIGNED_URL_EXPIRE_MINS,
    ) -> List[str]:

        return await asyncio.gather(
            *(self.generate_presigned_url(fm, expire_mins) for fm in files_metadata)
        )

    async def upload_file(
        self, key: str, fileobj: BinaryIO, content_type: AllowedContentTypes
    ) -> dict[str, str]:

        async with get_session().client("s3") as s3:  # type: ignore
            s3: S3Client
            await s3.upload_fileobj(  # type: ignore
                Fileobj=fileobj,
                Bucket=self.bucket,
                Key=key,
                ExtraArgs={"ContentType": content_type},
            )
        return {"key": key, "status": "uploaded"}

    async def delete_files(self, filenames: List[str]) -> DeleteObjectOutputTypeDef:

        async with self.session.client("s3") as s3:  # type: ignore
            s3: S3Client
            return await s3.delete_objects(  # type: ignore
                Bucket=self.bucket,
                Delete=DeleteTypeDef(
                    Objects=[{"Key": filename} for filename in filenames], Quiet=True
                ),
            )
