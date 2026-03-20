from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, SecretStr, Field
from typing import Annotated, Literal



class DatabaseSettings(BaseSettings):
    name: SecretStr
    host: SecretStr
    port: int 
    password: SecretStr
    user: SecretStr

    model_config = SettingsConfigDict(
        env_file="src/.env",
        env_prefix="DATABASE_",
        extra="ignore"
    )


class LocalDatabaseSettings(DatabaseSettings):
    
    model_config = SettingsConfigDict(
        env_file="src/.env",
        env_prefix="LOCAL_DATABASE_",
        extra="ignore"
    )
    
    
class AWSS3Settings(BaseSettings):
    access_key_id: SecretStr
    secret_access_key: SecretStr
    region: SecretStr
    s3_bucket: SecretStr    

    model_config = SettingsConfigDict(
        env_file="src/.env",
        extra="ignore",
        env_prefix="AWS_"
    )

class CORSSettings(BaseSettings):
    allowed_origins: list[str]

    model_config = SettingsConfigDict(
        env_file="src/.env",
        extra="ignore",
        env_prefix="CORS_"
    )

class Settings(BaseModel):
    database: Annotated[DatabaseSettings, Field(default_factory=DatabaseSettings)]
    aws: Annotated[AWSS3Settings, Field(default_factory=AWSS3Settings)]
    cors: Annotated[CORSSettings, Field(default_factory=CORSSettings)]
    

settings = Settings()

if __name__ == "__main__":
    print(settings.model_dump_json(indent=4))
    

