from pathlib import Path
from typing import Generator

import pytest
import yaml
from mypy_boto3_s3 import S3Client
from typer.testing import CliRunner

from surf_archiver.cli import app
from surf_archiver.config import Config
from surf_archiver.test_utils import MessageWaiter


@pytest.fixture(name="object_store_data")
def fixture_object_store_data(
    s3_client: S3Client,
    random_str: str,
) -> Generator[None, None, None]:
    s3_client.create_bucket(
        Bucket=random_str,
        CreateBucketConfiguration={"LocationConstraint": "us-west-1"},
    )

    s3_client.put_object(
        Body=b"test",
        Bucket=random_str,
        Key="images/test-id/20000101/0000.tar",
    )
    yield

    s3_client.delete_object(
        Bucket=random_str,
        Key="images/test-id/20000101/0000.tar",
    )

    s3_client.delete_bucket(Bucket=random_str)


@pytest.fixture(name="config")
def fixture_config(
    connection_url: str,
    random_str: str,
    tmp_path: Path,
) -> Config:
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
    config_dir.mkdir(parents=True, exist_ok=True)

    config_file = config_dir / "config.yaml"
    with config_file.open("w") as file:
        yaml.dump(config.model_dump(mode="json"), file)

    return config_file


@pytest.fixture(name="runner")
def fixture_runner(s3_endpoint_url: str) -> CliRunner:
    env = {
        "AWS_ACCESS_KEY_ID": "test",
        "AWS_SECRET_ACCESS_KEY": "test",
        "AWS_ENDPOINT_URL": s3_endpoint_url,
        "AWS_DEFAULT_REGION": "us-west-1",
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
    assert (config.target_dir / "images" / "test-id" / "20000101.tar").exists()

    message_waiter.wait()
    assert message_waiter.message
