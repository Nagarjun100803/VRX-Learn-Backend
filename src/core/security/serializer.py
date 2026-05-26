from itsdangerous import URLSafeTimedSerializer

from src.settings import settings

verify_email_serializer = URLSafeTimedSerializer(
    secret_key=settings.email_verification.secret_key.get_secret_value(),
    salt=settings.email_verification.salt.get_secret_value(),
)


reset_password_serializer = URLSafeTimedSerializer(
    secret_key=settings.password_reset.secret_key.get_secret_value(),
    salt=settings.password_reset.salt.get_secret_value(),
)
