from datetime import UTC, datetime

from prince_archiver.adapters.streams import get_id


def test_get_id():
    assert get_id(datetime(1970, 1, 1, 1, tzinfo=UTC)) == 3600000
