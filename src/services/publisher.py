"""Event publisher messaging protocol."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class EventPublisher(Protocol):
    """Protocol defining asynchronous message publishing contracts."""

    def publish(self, topic: str, event: dict[str, Any]) -> None:
        """Publish an event payload to the specified topic."""
        ...

    def close(self) -> None:
        """Flush and release publisher connections and resources."""
        ...
