from typing import Generator

import boto3
import pytest
from mypy_boto3_s3 import S3Client
from testcontainers.localstack import LocalStackContainer


@pytest.fixture(name="localstack", scope="session")
def fixture_localstack() -> Generator[LocalStackContainer, None, None]:
    localstack = LocalStackContainer("localstack/localstack:2.0.1").with_services("s3")
    localstack.region_name = None

    localstack.start()

    yield localstack

    localstack.stop()


@pytest.fixture(name="s3_endpoint_url", scope="session")
def fixture_s3_endpoint_url(localstack: LocalStackContainer) -> str:
    return localstack.get_url()


@pytest.fixture(scope="session", name="s3_client")
def fixture_s3_client(
    s3_endpoint_url: str,
) -> Generator[S3Client, None, None]:
    client = boto3.client(
        "s3",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        endpoint_url=s3_endpoint_url,
        region_name="us-west-1",
    )

    yield client

    client.close()
