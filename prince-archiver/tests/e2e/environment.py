from behave.fixture import use_fixture_by_tag

from tests.e2e.fixtures import db_engine, client


fixture_registry = {
    "fixture.db_engine": db_engine,
    "fixture.client": client,
}


def before_tag(context, tag):
    if tag.startswith("fixture."):
        return use_fixture_by_tag(tag, context, fixture_registry)
