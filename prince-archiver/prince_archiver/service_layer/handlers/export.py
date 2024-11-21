import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Callable

import s3fs

from prince_archiver.adapters.file import ArchiveFile, MetaData, PathManager
from prince_archiver.adapters.streams import MessageInfo, Stream
from prince_archiver.domain.value_objects import Checksum
from prince_archiver.service_layer import dto
from prince_archiver.service_layer.streams import OutgoingExportMessage
from prince_archiver.utils import now

LOGGER = logging.getLogger(__name__)


@dataclass
class _ExportInfo:
    key: str
    size: str
    checksum: Checksum
    timestamp: datetime = field(default_factory=now)


SchemaMapperT = Callable[[dto.ExportImagingEvent], dto.BaseSchema]


def default_schema_mapper(msg: dto.ExportImagingEvent) -> dto.BaseSchema:
    return dto.Schema(**dict(msg))


class Exporter:
    """
    Class to handle export from local to s3
    """

    def __init__(
        self,
        s3: s3fs.S3FileSystem,
        key_generator: Callable[[dto.ExportImagingEvent], str],
        path_manager: PathManager,
        *,
        schema_mapper: SchemaMapperT = default_schema_mapper,
        timeout: int = 120,
    ):
        self.s3 = s3
        self.key_generator = key_generator
        self.path_manager = path_manager
        self.schema_mapper = schema_mapper
        self.timeout = timeout

    async def export(self, message: dto.ExportImagingEvent) -> _ExportInfo:
        LOGGER.info("[%s] Exporting", message.ref_id)

        key = self.key_generator(message)

        async with (
            self._get_temp_archive(message) as archive_file,
            asyncio.TaskGroup() as tg,
        ):
            t1 = tg.create_task(archive_file.get_info())
            tg.create_task(self._upload(archive_file.path, key))

        return _ExportInfo(key=key, **asdict(t1.result()))

    @asynccontextmanager
    async def _get_temp_archive(
        self,
        message: dto.ExportImagingEvent,
    ) -> AsyncGenerator[ArchiveFile, None]:
        src_dir = self.path_manager.get_src_dir(message.system, message.local_path)
        metadata = self._get_metadata(message)
        async with src_dir.get_temp_archive(metadata=metadata) as archive_file:
            yield archive_file

    async def _upload(self, path: Path, key: str, *, timeout: int | None = None):
        async with asyncio.timeout(timeout or self.timeout):
            await self.s3._put_file(path, key)

    def _get_metadata(self, message: dto.ExportImagingEvent) -> MetaData:
        schema = self.schema_mapper(message)
        return MetaData(schema.model_dump_json(indent=4).encode())


class Publisher:
    """
    Class to handle to the publishing of export result
    """

    def __init__(self, stream: Stream):
        self.stream = stream

    async def publish(self, message: dto.ExportedImagingEvent):
        LOGGER.info("[%s] Publishing export", message.ref_id)
        await self.stream.add(OutgoingExportMessage(message))


class ExportHandler:
    """
    Class to handle to the publishing of export result
    """

    def __init__(
        self,
        stream: Stream,
        exporter: Exporter,
        publisher: Publisher,
    ):
        self.exporter = exporter
        self.publisher = publisher
        self.stream = stream

    async def process(self, message: dto.ExportImagingEvent):
        upload_info = await self.exporter.export(message)

        kwargs: dict[str, Any] = {**dict(message), **upload_info.__dict__}

        await self.publisher.publish(
            dto.ExportedImagingEvent(**kwargs),
        )
        await self.stream.ack(MessageInfo(**dict(message.message_info)))
