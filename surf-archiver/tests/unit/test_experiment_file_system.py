from datetime import date
from unittest.mock import AsyncMock

from s3fs import S3FileSystem

from surf_archiver.file import ExperimentFileSystem


async def test_list_files_by_date():
    mock_s3 = AsyncMock(S3FileSystem)
    mock_s3._glob.return_value = [
        "test-bucket/images/id-1/20000101_0000.tar",
        "test-bucket/images/id-2/20000101_0000.tar",
        "test-bucket/images/id-2/20000101_0100.tar",
    ]

    file_system = ExperimentFileSystem(s3=mock_s3, bucket_name="test-bucket")

    expected = {
        "id-1": ["test-bucket/images/id-1/20000101_0000.tar"],
        "id-2": [
            "test-bucket/images/id-2/20000101_0000.tar",
            "test-bucket/images/id-2/20000101_0100.tar",
        ],
    }

    output = await file_system.list_files_by_date(date(2000, 1, 1))
    assert output == expected
