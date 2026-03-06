from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./medireview.db"
    GEMINI_API_KEY: str = ""
    SYNC_INTERVAL_MINUTES: int = 5
    NAVER_PLACE_ID: str = ""  # 네이버 지도 Place ID
    CHROME_HEADLESS: bool = True
    CHROME_USER_DATA_DIR: str = "/home/chlwnsguru/.config/google-chrome-selenium"  # Chrome 사용자 데이터 디렉토리 (예: ~/.config/google-chrome)
    CHROME_PROFILE_NAME: str = "Default"  # Chrome 프로필 이름

    class Config:
        env_file = ".env"


settings = Settings()
