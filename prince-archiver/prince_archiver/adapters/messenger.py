import json
from enum import StrEnum
from typing import Any

import httpx
from jinja2 import Environment, PackageLoader


class Message(StrEnum):
    DAILY_REPORT = "daily-report.json.jinja"
    DAILY_STATS = "daily-stats.json.jinja"


class Messenger:
    def __init__(
        self,
        client: httpx.AsyncClient,
        url: str,
        *,
        _env: Environment | None = None,
    ):
        self.client = client
        self.url = url

        self.env = _env or Environment(
            loader=PackageLoader("prince_archiver"),
            enable_async=True,
        )

    async def publish(self, message: Message, **kwargs: Any):
        await self.client.post(
            self.url,
            json=json.loads(
                await self._render_message(message, **kwargs),
            ),
        )

    async def _render_message(self, message: Message, **kwargs: Any):
        template = self.env.get_template(message.value)
        return await template.render_async(**kwargs)
