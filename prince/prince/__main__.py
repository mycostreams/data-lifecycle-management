from .celery_app import create_archived_timestep
from .config import Settings
from .file import get_plate_timesteps


def main(*, _settings: Settings | None = None):

    settings = _settings or Settings()

    for plate_timestep in get_plate_timesteps(settings.DATA_DIR):

        serialized_timestep = plate_timestep.model_dump(mode="json")

        create_archived_timestep.delay(
            serialized_timestep,
            str(settings.ARCHIVE_DIR),
        )


main()
