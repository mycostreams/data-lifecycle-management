import httpx
from behave.fixture import use_fixture_by_tag
from sqlalchemy import create_engine


def db_conn(context):

    dsn = "postgresql+psycopg2://postgres:postgres@localhost:5431/postgres"
    engine = create_engine(dsn)

    with engine.begin() as conn:
        context.db_conn = conn
        yield context.db_conn


def client(context):
    with httpx.Client() as client:
        context.client = client
        yield context.client


fixture_registry = {
    "fixture.db_conn": db_conn,
    "fixture.client": client,
}


def before_tag(context, tag):
    if tag.startswith("fixture."):
        return use_fixture_by_tag(tag, context, fixture_registry)
