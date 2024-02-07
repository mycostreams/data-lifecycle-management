
from io import BytesIO
from uuid import uuid4

from .config import Settings
from .client import SFTPClient
from .slurm import SlurmGenerator, SlurmTemplate


def generate_id() -> str:
    return uuid4().hex[:6]


def main(*, _settings: Settings | None =  None):

    settings = _settings or Settings()

    slurm_script = SlurmGenerator().render_slurm(SlurmTemplate.HELLO_WORLD)

    client = SFTPClient(
        username=settings.SFTP_USERNAME,
        password=settings.SFTP_PASSWORD,
        host=settings.SFTP_HOST,
        port=settings.SFTP_PORT,
    )

    target_path = f"tmp/slurm/{generate_id()}.sh"

    with client:
        client.sftp_client.putfo(
            BytesIO(slurm_script.encode()),
            target_path,
        )


main()

