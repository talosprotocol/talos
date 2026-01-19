from abc import ABC, abstractmethod

import pytest

from talos_sdk.container import Container


class IService(ABC):
    @abstractmethod
    def do(self) -> str: ...


class ServiceImpl(IService):
    def do(self) -> str:
        return "done"


def test_container_singleton() -> None:
    c = Container()
    impl = ServiceImpl()
    c.register(IService, impl)  # type: ignore[type-abstract]

    assert c.resolve(IService) is impl  # type: ignore[type-abstract]
    assert c.resolve(IService).do() == "done"  # type: ignore[type-abstract]


def test_container_factory() -> None:
    c = Container()
    c.register_factory(IService, lambda: ServiceImpl())  # type: ignore[type-abstract]

    s1 = c.resolve(IService)  # type: ignore[type-abstract]
    s2 = c.resolve(IService)  # type: ignore[type-abstract]
    assert s1 is not s2
    assert s1.do() == "done"


def test_resolve_missing() -> None:
    c = Container()
    with pytest.raises(ValueError, match="No registration found"):
        c.resolve(IService)  # type: ignore[type-abstract]
