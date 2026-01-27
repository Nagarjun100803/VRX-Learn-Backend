from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    name: str
    host: str
    port: int 
    password: str
    user: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DATABASE_",
        extra="ignore"
    )


class LocalDatabaseSettings(DatabaseSettings):
    
    model_config = SettingsConfigDict(
        env_file="src/.env",
        env_prefix="LOCAL_DATABASE_",
        extra="ignore"
    )
    



# settings = DatabaseSettings()
settings = LocalDatabaseSettings()

