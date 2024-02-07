from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    SFTP_USERNAME: str
    SFTP_PASSWORD: str
    SFTP_HOST: str
    SFTP_PORT: int = 22

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')
