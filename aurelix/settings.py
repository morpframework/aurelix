from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='aurelix_')

    database_url: str = 'sqlite:///./database.sqlite'

settings = Settings()
