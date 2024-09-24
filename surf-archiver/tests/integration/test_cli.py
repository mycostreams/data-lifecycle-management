from io import BytesIO
from pathlib import Path

import pytest
from httpx import Client
from typer.testing import CliRunner

from surf_archiver.cli import app
from surf_archiver.config import Config
from surf_archiver.test_utils import MessageWaiter


@pytest.fixture(name="object_store_data")
def fixture_object_store_data(random_str: str):
    bucket_url = f"http://localhost:9091/{random_str}"
    file_url = f"{bucket_url}/images/test-id/20000101_0000.tar"

    with Client() as client:
        client.put(bucket_url)
        client.put(file_url, files={"upload-file": BytesIO(b"test")})

        yield

        client.delete(file_url)
        client.delete(bucket_url)


@pytest.fixture(name="config")
def fixture_config(connection_url: str, random_str: str, tmp_path: Path) -> Config:
    return Config(
        target_dir=tmp_path,
        connection_url=connection_url,
        bucket=random_str,
        exchange_name=random_str,
        log_file=tmp_path / "test.log",
    )


@pytest.fixture(name="config_file")
def fixture_config_file(config: Config, tmp_path: Path) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    config_file = config_dir / "config.yaml"
    config_file.write_text(config.model_dump_json())

    return config_file


@pytest.fixture(name="runner")
def fixture_runner() -> CliRunner:
    env = {
        "AWS_ACCESS_KEY_ID": "aws-access-key-id",
        "AWS_SECRET_ACCESS_KEY": "aws-access-key-id",
        "AWS_ENDPOINT_URL": "http://localhost:9091",
    }
    return CliRunner(env=env)


@pytest.mark.usefixtures("object_store_data")
def test_app(
    runner: CliRunner,
    config_file: Path,
    config: Config,
    message_waiter: MessageWaiter,
):
    cmd = ["archive", "2000-01-01", "--mode=images", f"--config-path={config_file}"]
    result = runner.invoke(app, cmd)

    assert result.exit_code == 0

    assert config.log_file and config.log_file.exists()
    assert (config.target_dir / "images" / "test-id" / "2000-01-01.tar").exists()

    message_waiter.wait()
    assert message_waiter.message
    print(message_waiter.message)
