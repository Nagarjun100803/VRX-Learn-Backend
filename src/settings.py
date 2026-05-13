from typing import Annotated

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    name: SecretStr
    host: SecretStr
    port: int
    password: SecretStr
    user: SecretStr
    min_conn: int
    max_conn: int

    model_config = SettingsConfigDict(
        env_file="src/.env", env_prefix="DATABASE_", extra="ignore"
    )


class AWSS3Settings(BaseSettings):
    access_key_id: SecretStr
    secret_access_key: SecretStr
    region: SecretStr
    bucket: SecretStr

    model_config = SettingsConfigDict(
        env_file="src/.env", extra="ignore", env_prefix="AWS_S3_"
    )


class AWSSESSettings(BaseSettings):
    access_key_id: SecretStr
    secret_access_key: SecretStr
    region: SecretStr
    from_email: SecretStr

    model_config = SettingsConfigDict(
        env_file="src/.env", extra="ignore", env_prefix="AWS_SES_"
    )


class JWTSettings(BaseSettings):
    secret_key: SecretStr
    algorithm: str = "HS256"
    expire_mins: int = 4320  # 3 days.

    model_config = SettingsConfigDict(
        env_file="src/.env", extra="ignore", env_prefix="JWT_"
    )


class CORSSettings(BaseSettings):
    allowed_origins: list[str]

    model_config = SettingsConfigDict(
        env_file="src/.env", extra="ignore", env_prefix="CORS_"
    )


class PasswordResetSettings(BaseSettings):
    frontend_base_url: str
    reset_path: str
    secret_key: SecretStr
    salt: SecretStr
    token_expire_seconds: int

    model_config = SettingsConfigDict(
        env_file="src/.env", extra="ignore", env_prefix="PASSWORD_RESET_"
    )


class Settings(BaseModel):
    database: Annotated[DatabaseSettings, Field(default_factory=DatabaseSettings)]  # type: ignore[arg-type]
    jwt: Annotated[JWTSettings, Field(default_factory=JWTSettings)]  # type: ignore[arg-type]
    aws_s3: Annotated[AWSS3Settings, Field(default_factory=AWSS3Settings)]  # type: ignore[arg-type]
    aws_ses: Annotated[AWSSESSettings, Field(default_factory=AWSSESSettings)]  # type: ignore[arg-type]
    cors: Annotated[CORSSettings, Field(default_factory=CORSSettings)]  # type: ignore[arg-type]
    password_reset: Annotated[
        PasswordResetSettings, Field(default_factory=PasswordResetSettings)  # type: ignore[arg-type]
    ]


settings = Settings()  # type: ignore[reportCallIssue]

if __name__ == "__main__":
    print(settings.model_dump_json(indent=4))
