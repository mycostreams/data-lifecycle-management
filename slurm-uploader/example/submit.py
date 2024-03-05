from datetime import date

from slurm_uploader.client import Client
from slurm_uploader.config import Settings


def main(*, _settings: Settings | None = None):

    settings = _settings or Settings()

    client = Client(
        username=settings.USERNAME,
        password=settings.PASSWORD,
        host=settings.HOST,
    )

    with client:
        job_id = client.submit_job(date.today())
        print(job_id)


if __name__ == "__main__":
    main()
