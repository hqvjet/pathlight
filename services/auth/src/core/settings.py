from functools import lru_cache
from pydantic import BaseSettings

class Settings(BaseSettings):
    postgres_dsn: str
    secret_key: str
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings() -> Settings:
    return Settings()
