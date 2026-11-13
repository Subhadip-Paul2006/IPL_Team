"""Service boundary abstract base class."""

from abc import ABC, abstractmethod
from typing import Any


class ServiceBoundary(ABC):
    """Abstract service boundary establishing identity and lifecycle contracts."""

    @abstractmethod
    def get_service_name(self) -> str:
        """Return the canonical service identifier."""
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """Perform service health inspection and return diagnostic status dictionary."""
        raise NotImplementedError
