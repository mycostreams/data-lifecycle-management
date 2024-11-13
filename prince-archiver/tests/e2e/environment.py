from behave.fixture import use_fixture_by_tag

from tests.e2e.fixtures import client, get_exports

fixture_registry = {
    "fixture.client": client,
    "fixture.get_exports": get_exports,
}


def before_tag(context, tag):
    if tag.startswith("fixture."):
        return use_fixture_by_tag(tag, context, fixture_registry)
