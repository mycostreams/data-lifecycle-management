from typing import Sequence, TypeVar

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from prince_archiver.models import read

ReadT = TypeVar("ReadT", bound=read.ReadBase)


async def get_pagininated_results(
    session: AsyncSession,
    model: type[ReadT],
    *,
    filter_params: list[ColumnElement] | None = None,
    offset: int = 0,
    limit: int = 100,
) -> tuple[int, Sequence[ReadT]]:
    filter_params = filter_params or []

    count_stmt = select(func.count()).select_from(model).where(*filter_params)

    read_stmt = select(model).where(*filter_params).limit(limit).offset(offset)

    count = await session.scalar(count_stmt)
    results = await session.scalars(read_stmt)

    return count or 0, results.all()
