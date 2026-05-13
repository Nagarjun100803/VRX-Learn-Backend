"""
Module providing email sending functionality using AWS SES.
"""

from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Self, Union

import aioboto3
from mypy_boto3_ses import SESClient
from mypy_boto3_ses.type_defs import (
    BodyTypeDef,
    ContentTypeDef,
    DestinationTypeDef,
    MessageTypeDef,
    SendEmailRequestTypeDef,
)
from pydantic import EmailStr, model_validator
from pydantic.main import BaseModel

from src.settings import settings


class EmailBody(BaseModel):
    text: Union[str, None] = None
    html: Union[str, None] = None

    @model_validator(mode="after")
    def validate_body(self) -> Self:
        if self.text is None and self.html is None:
            raise ValueError("Either text or html must be provided")

        return self


class EmailMessage(BaseModel):
    """
    Represents an email message to be sent.
    """

    to: list[EmailStr]
    """The list of email addresses to send the message to."""
    subject: str
    """The subject of the email."""
    body: EmailBody
    """The body of the email."""


# Base Email Service Provider.
class BaseEmailServiceProvider(ABC):
    """
    Abstract base class for email service providers.
    """

    @abstractmethod
    async def send(self, message: EmailMessage) -> None:
        raise NotImplementedError


@lru_cache
def get_session() -> aioboto3.Session:
    """
    Returns an aioboto3 session configured with AWS SES credentials.
    """
    return aioboto3.Session(
        aws_access_key_id=settings.aws_ses.access_key_id.get_secret_value(),
        aws_secret_access_key=settings.aws_ses.secret_access_key.get_secret_value(),
        region_name=settings.aws_ses.region.get_secret_value(),
    )


class SES(BaseEmailServiceProvider):
    """
    SES email service provider implementation.
    """

    def __init__(self, session: aioboto3.Session):
        self.session = session

    async def send(self, message: EmailMessage) -> None:
        """
        Sends an email using the AWS SES client.
        """

        async with self.session.client("ses") as client:  # type: ignore[reportGeneralTypeIssues]
            client: SESClient

            text = message.body.text or ""
            html = message.body.html or ""

            await client.send_email(  # type: ignore[reportGeneralTypeIssues]
                **SendEmailRequestTypeDef(
                    Source=settings.aws_ses.from_email.get_secret_value(),
                    Destination=DestinationTypeDef(ToAddresses=message.to),
                    Message=MessageTypeDef(
                        Subject=ContentTypeDef(Data=message.subject),
                        Body=BodyTypeDef(
                            Text=ContentTypeDef(Data=text),
                            Html=ContentTypeDef(Data=html),
                        ),
                    ),
                )
            )
