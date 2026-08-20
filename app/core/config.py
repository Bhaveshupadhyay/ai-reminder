from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Project metadata
    PROJECT_NAME: str = "AI Open-Loop Reminder Backend"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/openloops",
        description="Async PostgreSQL connection string",
    )

    # AI Configuration
    AI_PROVIDER: str = Field(
        default="mock",
        description="AI Provider to use: 'mock', 'openai', 'gemini'",
    )
    AI_API_KEY: Optional[str] = Field(default=None, description="API Key for AI provider")
    AI_MODEL: Optional[str] = Field(
        default=None, description="Model identifier (e.g. gpt-4o-mini, gemini-1.5-flash)"
    )
    AI_REQUEST_TIMEOUT_SECONDS: float = 30.0

    # Notification Filtering
    IGNORED_NOTIFICATION_PACKAGES: List[str] = Field(
        default=[
            "android",
            "com.android.systemui",
            "com.google.android.gms",
            "com.android.vending",
            "com.sec.android.app.samsungapps",
            "com.spotify.music",
            "com.google.android.apps.photos",
            "com.apple.shortcuts",
        ],
        description="List of Android/iOS package names to ignore by default",
    )

    # Open Loop Deduplication Settings
    DEDUPLICATION_WINDOW_DAYS: int = 14
    DEDUPLICATION_SIMILARITY_THRESHOLD: float = 0.55

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str]) -> str:
        if not v:
            return "postgresql+asyncpg://postgres:postgres@localhost:5432/openloops"
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


settings = Settings()
