import logging
from contextlib import asynccontextmanager
from functools import partial
from typing import AsyncGenerator, Callable

import asyncssh

from .api_client.models import ArchiveModel, ArchivesList, ExportList, ExportModel


class SSHClient:
    def __init__(self, conn: asyncssh.SSHClientConnection):
        self.conn = conn

    async def remote_sbatch(self, sbatch_command: str) -> str:
        """Executes the sbatch command on the remote server."""
        try:
            result = await self.conn.run(f"{sbatch_command}", check=True)
            return str(result.stdout)  # Return the output of the sbatch command
        except asyncssh.Error as e:
            logging.warning(f"Error running sbatch command: {str(e)}")
            return ""

    async def pipe_exports(
        self,
        path: str,
        exports: list[ExportModel],
        *,
        _mapper: Callable[[list[ExportModel]], bytes] | None = None,
    ):
        mapper = _mapper or partial(ExportList.dump_json, indent=4)
        async with self.conn.start_sftp_client() as sftp_client:
            async with sftp_client.open(path, "wb") as f:
                await f.write(mapper(exports))


    async def pipe_exports_archive(
        self,
        path: str,
        exports: list[ArchiveModel],
        *,
        _mapper: Callable[[list[ArchiveModel]], bytes] | None = None,
    ):
        mapper = _mapper or partial(ArchivesList.dump_json, indent=4)
        async with self.conn.start_sftp_client() as sftp_client:
            async with sftp_client.open(path, "wb") as f:
                await f.write(mapper(exports))


class SSHClientFactory:
    def __init__(
        self,
        username: str,
        password: str,
        host: str,
    ):
        self.username = username
        self.host = host
        self.password = password

    @asynccontextmanager
    async def get_ssh_client(self) -> AsyncGenerator[SSHClient, None]:
        """Context manager to manage the SSH connection."""
        managed_conn = asyncssh.connect(
            host=self.host,
            username=self.username,
            password=self.password,
            known_hosts=None,
        )
        async with managed_conn as conn:
            yield SSHClient(conn)
