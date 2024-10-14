from uuid import uuid4

import pytest


@pytest.fixture(name="random_str")
def fixture_random_str() -> str:
    return uuid4().hex
