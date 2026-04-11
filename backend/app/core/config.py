from pydantic_settings import BaseSettings, SettingsConfigDict

from app.ml.model_config import MODEL_NAME as DEFAULT_MODEL_NAME


class Settings(BaseSettings):
    HF_TOKEN: str = ""
    BACKEND_PORT: int = 8000
    MODEL_NAME: str = DEFAULT_MODEL_NAME
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    UPSTASH_REDIS_REST_URL: str = ""
    UPSTASH_REDIS_REST_TOKEN: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()