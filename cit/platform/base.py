from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class CredentialStore(ABC):
    @abstractmethod
    def read(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def write(self, payload: dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def validate_access(self) -> None:
        raise NotImplementedError
