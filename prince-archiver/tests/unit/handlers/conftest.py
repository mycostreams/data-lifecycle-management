import pytest

from prince_archiver.domain.models import StitchEvent

from .utils import MockImagingEventRepo, MockUnitOfWork


@pytest.fixture(name="uow")
def fixture_uow(
    exported_stitch_event: StitchEvent,
    unexported_stitch_event: StitchEvent,
):
    return MockUnitOfWork(
        imaging_event_repo=MockImagingEventRepo(
            imaging_events=[exported_stitch_event, unexported_stitch_event],
        ),
    )
