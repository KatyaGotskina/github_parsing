from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../../.env")

    SERVICE_NAME: str = 'github_parsing'

    DB_HOST: str
    DB_PORT: str
    DB_PASSWORD: str
    DB_USER: str
    DB_NAME: str


settings = Settings()
