from pydantic_settings import BaseSettings, SettingsConfigDict


class BrokerSettings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


class Settings(BaseSettings):

    USERNAME: str
    PASSWORD: str
    HOST: str
    PORT: int = 22

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
