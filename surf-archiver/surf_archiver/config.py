from pathlib import Path
from typing import Optional, Tuple, Type

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

HOME_PATH = Path.home()

DEFAULT_CONFIG_DIR = HOME_PATH / ".surf-archiver"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"


class Config(BaseSettings):
    log_file: Optional[Path] = DEFAULT_CONFIG_DIR / "app.log"

    bucket: str = "prince-archiver-dev"
    target_dir: Path = HOME_PATH / "prince"

    connection_url: str = "amqp://guest:guest@localhost:5672"
    exchange_name: str = "surf-data-archive"

    model_config = SettingsConfigDict(env_prefix="surf_archiver_")


def get_config(config_path: Path) -> Config:
    class _Config(Config):
        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls: Type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
        ) -> Tuple[PydanticBaseSettingsSource, ...]:
            return (
                init_settings,
                YamlConfigSettingsSource(settings_cls, yaml_file=config_path),
                env_settings,
            )

    return _Config()
