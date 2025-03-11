from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    JWT_SECRET: str
    GOOGLE_REFRESH_TOKEN: str
    DATABASE_URL: str
    DATABASE_NAME: str
    
    class Config:
        env_file = ".env"

settings = Settings()