from hashlib import sha256
from typing import AsyncGenerator, Callable, Protocol

from prince_archiver.domain.value_objects import Algorithm, Checksum


class _HashProtocol(Protocol):
    def update(self, data: bytes): ...

    def hexdigest(self) -> str: ...


class ChecksumFactory:
    """
    Class for generating checksums.
    """

    HASH_MAPPING: dict[Algorithm, Callable[[], _HashProtocol]] = {
        Algorithm.SHA256: sha256,
    }

    @classmethod
    async def get_checksum(
        cls,
        bytes_iterator: AsyncGenerator[bytes, None],
        *,
        algorithm: Algorithm = Algorithm.SHA256,
    ) -> Checksum:
        hash = cls.HASH_MAPPING[algorithm]()
        async for chunk in bytes_iterator:
            hash.update(chunk)

        return Checksum(
            algorithm=algorithm,
            hex=hash.hexdigest(),
        )
