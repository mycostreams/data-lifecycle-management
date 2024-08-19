import pytest

from prince_archiver.domain.models import ImagingEvent

from .utils import MockImagingEventRepo, MockUnitOfWork


@pytest.fixture(name="uow")
def fixture_uow(
    exported_imaging_event: ImagingEvent,
    unexported_imaging_event: ImagingEvent,
):
    return MockUnitOfWork(
        imaging_event_repo=MockImagingEventRepo(
            imaging_events=[exported_imaging_event, unexported_imaging_event],
        ),
    )
