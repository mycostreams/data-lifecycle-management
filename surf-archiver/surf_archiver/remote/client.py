import logging
import textwrap
from contextlib import asynccontextmanager
from datetime import date
from typing import Any, AsyncGenerator, Optional
from uuid import UUID, uuid4

import asyncssh

from surf_archiver.definitions import Mode

LOGGER = logging.getLogger(__name__)


class ArchiveClient:
    COMMAND = textwrap.dedent(
        """\
        nohup surf-archiver-cli archive \\
            --job-id={job_id} --mode={mode} {date} > /dev/null 2>&1 &
        """
    )

    def __init__(self, conn: asyncssh.SSHClientConnection):
        self.conn = conn

    async def archive(
        self,
        date_: date,
        job_id: Optional[UUID] = None,
        mode: Mode = Mode.STITCH,
        *,
        timeout: float = 30,
    ):
        job_id = job_id or uuid4()

        LOGGER.info("[%s] Archiving %s", job_id, date_)
        cmd = self._build_command(
            date=date_.isoformat(),
            mode=mode.value,
            job_id=job_id.hex,
        )
        await self.conn.run(cmd, check=True, timeout=timeout)

    def _build_command(self, **kwargs: Any) -> str:
        return self.COMMAND.format(**kwargs)


class ArchiveClientFactory:
    def __init__(
        self,
        username: str,
        password: str,
        host: str,
        port: int = 22,
    ):
        self.username = username
        self.password = password
        self.host = host
        self.port = port

    @asynccontextmanager
    async def get_managed_client(self) -> AsyncGenerator[ArchiveClient, None]:
        managed_conn = asyncssh.connect(
            username=self.username,
            password=self.password,
            host=self.host,
            port=self.port,
            known_hosts=None,
        )
        async with managed_conn as conn:
            yield ArchiveClient(conn)
