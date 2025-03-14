from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    JWT_SECRET: str
    GOOGLE_REFRESH_TOKEN: str
    DATABASE_URL: str
    DATABASE_NAME: str
    JWT_ALGORITHM: str
    JWT_EXP_MINUTES: int
    GOOGLE_REDIRECT_URI: str
    
    class Config:
        env_file = ".env"

settings = Settings()