from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # AI API Keys
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # Gemini
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_MAX_TOKENS: int = 8192

    # OpenAI
    OPENAI_CHAT_MODEL: str = "gpt-4o"
    OPENAI_TTS_MODEL: str = "tts-1-hd"
    OPENAI_TTS_VOICE: str = "alloy"
    OPENAI_IMAGE_MODEL: str = "dall-e-3"
    OPENAI_IMAGE_SIZE: str = "1792x1024"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/video_pipeline"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Object Storage (MinIO / S3)
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_ASSETS_BUCKET: str = "video-pipeline-assets"
    S3_OUTPUTS_BUCKET: str = "video-pipeline-outputs"

    # App
    TEMP_DIR: str = "./temp"
    MAX_CONCURRENT_IMAGE_REQUESTS: int = 5
    LOG_LEVEL: str = "INFO"

    # Storage TTL
    OUTPUT_TTL_HOURS: int = 24
    FAILED_TEMP_TTL_HOURS: int = 6

    # Cost
    DEFAULT_COST_BUDGET_USD: float = 2.0
    DALLE_COST_PER_IMAGE: float = 0.08
    TTS_COST_PER_1K_CHARS: float = 0.03

    # Auth
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # Quota
    DEFAULT_DAILY_QUOTA: int = 5


settings = Settings()
