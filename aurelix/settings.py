from pydantic_settings import BaseSettings, SettingsConfigDict
import pydantic
import enum 

class OIDCScheme(enum.StrEnum):
    PASSWORD = 'password'

class Settings(BaseSettings, case_sensitive=True):
    model_config = SettingsConfigDict(env_prefix='AURELIX_')
    CONFIG: str | None = None
    OIDC_SCHEME: str | None = None
    OIDC_DISCOVERY_ENDPOINT: str | None = None