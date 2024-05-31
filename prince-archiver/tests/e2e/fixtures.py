import httpx
from sqlalchemy.ext.asyncio import create_async_engine


def db_engine(context):

    dsn = "postgresql+asyncpg://postgres:postgres@localhost:5431/postgres"

    context.db_engine = create_async_engine(dsn)

    return context.db_engine


def client(context):
    with httpx.Client() as client:
        context.client = client
        yield context.client
