from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./medireview.db"

    # LLM Provider 설정
    LLM_PROVIDER: str = "gemini"                     # "gemini" | "ollama"
    GEMINI_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma4:latest"
    OLLAMA_TIMEOUT_SEC: int = 60

    SYNC_INTERVAL_MINUTES: int = 60 # 리뷰 동기화 간격 (분)
    NAVER_PLACE_ID: str = ""  # 네이버 지도 Place ID
    CHROME_HEADLESS: bool = True
    CHROME_USER_DATA_DIR: str = "/home/chlwnsguru/.config/google-chrome-selenium"  # Chrome 사용자 데이터 디렉토리 (예: ~/.config/google-chrome)
    CHROME_PROFILE_NAME: str = "Default"  # Chrome 프로필 이름

    # 카카오 API
    KAKAO_CLIENT_ID: str = ""          # REST API 키
    KAKAO_CLIENT_SECRET: str = ""      # Client Secret
    KAKAO_REDIRECT_URI: str = "http://localhost:9001/api/kakao/redirect"

    # 토큰 암호화 키 (Fernet)
    TOKEN_ENCRYPTION_KEY: str = ""     # 비어 있으면 앱 시작 시 자동 생성

    class Config:
        env_file = ".env"


settings = Settings()
