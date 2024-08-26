from prince_archiver.domain.models import ImagingEvent
from prince_archiver.service_layer.handlers.utils import get_target_key


def test_get_target_key(unexported_imaging_event: ImagingEvent):
    output = get_target_key(unexported_imaging_event, "test-bucket")

    assert output == "test-bucket/images/test_experiment_id/20000101/000000.tar"
