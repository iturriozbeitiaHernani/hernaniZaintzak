from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    DATABASE_URL: str
    ANTHROPIC_API_KEY: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # SMTP — dejar vacíos para deshabilitar el envío real (fallback a log)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""      # "hernaniZaintzak <noreply@ikastola.eus>"
    SMTP_TLS: bool = True    # STARTTLS; False para SSL directo (puerto 465)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
