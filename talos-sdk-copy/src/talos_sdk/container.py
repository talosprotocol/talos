from collections.abc import Callable
from typing import Any, TypeVar, cast

T = TypeVar("T")


class Container:
    """A simple thread-safe Dependency Injection container."""

    def __init__(self) -> None:
        self._services: dict[type[Any], Any] = {}
        self._factories: dict[type[Any], Callable[[], Any]] = {}

    def register(self, interface: type[T], implementation: T) -> None:
        """Register a singleton instance for an interface."""
        self._services[interface] = implementation

    def register_factory(self, interface: type[T], factory: Callable[[], T]) -> None:
        """Register a factory for an interface (lazy or transient)."""
        self._factories[interface] = factory

    def resolve(self, interface: type[T]) -> T:
        """Resolve an implementation for an interface."""
        if interface in self._services:
            return cast(T, self._services[interface])

        if interface in self._factories:
            instance = self._factories[interface]()
            # Optionally cache if singleton desired, but keeping simple
            return cast(T, instance)

        raise ValueError(f"No registration found for {interface}")


# Global instance for easy access if needed
_global_container = Container()


def get_container() -> Container:
    return _global_container
