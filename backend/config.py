from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./medireview.db"
    GEMINI_API_KEY: str = ""
    SYNC_INTERVAL_MINUTES: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
