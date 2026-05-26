from src.notifications.provider import BaseEmailServiceProvider, EmailBody, EmailMessage
from src.notifications.renderer import render_template
from src.settings import settings


class EmailTemplates:
    """
    Factory class responsible for creating email templates.
    """

    def reset_password(self, to: str, username: str, reset_link: str) -> EmailMessage:
        token_expire_mins = int(settings.password_reset.token_expire_seconds / 60)

        html = render_template(
            "reset_password.html",
            **{
                "reset_link": reset_link,
                "username": username,
                "token_expire_mins": token_expire_mins,
            },
        )
        fallback_text = f"Hi {username}\n\n, Reset your password by clicking the link below:\n {reset_link}"

        return EmailMessage(
            to=[to],
            subject="Reset Password Request",
            body=EmailBody(html=html, text=fallback_text),
        )

    def verify_email(self, to: str, username: str, verify_link: str) -> EmailMessage:
        html = render_template(
            "verify_email.html",
            **{
                "verify_link": verify_link,
                "username": username,
                "token_expire_mins": 30,
            },
        )
        fallback_text = f"Hi {username}\n\n, Verify your email by clicking the link below:\n {verify_link}"

        return EmailMessage(
            to=[to],
            subject="Verify Email",
            body=EmailBody(html=html, text=fallback_text),
        )


class NotificationSender:
    """
    High-level class for sending notifications using the configured email service provider and template.
    """

    def __init__(
        self, provider: BaseEmailServiceProvider, template: EmailTemplates
    ) -> None:
        self.provider = provider
        self.template = template

    async def send_reset_password_email(
        self, to: str, username: str, reset_link: str
    ) -> None:
        message = self.template.reset_password(to, username, reset_link)
        await self.provider.send(message)

    async def send_verify_email(self, to: str, username: str, verify_link: str) -> None:
        message = self.template.verify_email(to, username, verify_link)
        await self.provider.send(message)
