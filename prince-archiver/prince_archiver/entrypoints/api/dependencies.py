from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, AsyncGenerator

from fastapi import Depends
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
from s3fs import S3FileSystem
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from prince_archiver.config import AWSSettings
from prince_archiver.service_layer.uow import get_session_maker

SessionmakerT = async_sessionmaker[AsyncSession]


class Settings(AWSSettings, BaseSettings):
    POSTGRES_DSN: PostgresDsn

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def file_system_factory(settings: Settings) -> S3FileSystem:
    client_kwargs = {}
    if settings.AWS_REGION_NAME:
        client_kwargs["region_name"] = settings.AWS_REGION_NAME

    return S3FileSystem(
        key=settings.AWS_ACCESS_KEY_ID,
        secret=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=settings.AWS_ENDPOINT_URL,
        client_kwargs=client_kwargs,
        asynchronous=True,
        max_concurrency=settings.UPLOAD_MAX_CONCURRENCY,
    )


@dataclass
class AppState:
    settings: Settings
    file_system: S3FileSystem
    sessionmaker: SessionmakerT


@lru_cache
def get_app_state() -> AppState:
    settings = Settings()
    return AppState(
        settings=settings,
        file_system=file_system_factory(settings),
        sessionmaker=get_session_maker(str(settings.POSTGRES_DSN)),
    )


async def get_file_system(
    state: Annotated[AppState, Depends(get_app_state)],
) -> S3FileSystem:
    return state.file_system


async def get_session(
    state: Annotated[AppState, Depends(get_app_state)],
) -> AsyncGenerator[AsyncSession, None]:
    async with state.sessionmaker() as session:
        yield session
