import pytest
from switchboard.interfaces.service import IService
from switchboard.registry.service import ServiceRegistry
from switchboard.exceptions.base import RegistryError

class MockService(IService):
    def __init__(self, name: str, deps: list[str] | None = None) -> None:
        self._name = name
        self._deps = deps or []
        self.initialized = False
        self.started = False
        self.stopped = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def dependencies(self) -> list[str]:
        return self._deps

    async def initialize(self) -> None:
        self.initialized = True

    async def start(self) -> None:
        self.started = True

    async def shutdown(self) -> None:
        self.stopped = True


def test_service_registration_and_lookup() -> None:
    registry = ServiceRegistry()
    service = MockService("test_service")
    
    registry.register("test_service", service)
    
    assert registry.has("test_service") is True
    assert registry.get("test_service") is service
    assert "test_service" in registry.list_keys()


def test_duplicate_registration_fails() -> None:
    registry = ServiceRegistry()
    service1 = MockService("dup")
    service2 = MockService("dup")
    
    registry.register("dup", service1)
    with pytest.raises(RegistryError):
        registry.register("dup", service2)


def test_missing_registration_fails() -> None:
    registry = ServiceRegistry()
    with pytest.raises(RegistryError):
        registry.get("nonexistent")


def test_topological_sorting_order() -> None:
    registry = ServiceRegistry()
    
    # Dependencies: s3 depends on s2; s2 depends on s1; s1 has no deps.
    s1 = MockService("s1", deps=[])
    s2 = MockService("s2", deps=["s1"])
    s3 = MockService("s3", deps=["s2"])
    
    # Register in mixed order
    registry.register("s3", s3)
    registry.register("s1", s1)
    registry.register("s2", s2)
    
    ordered = registry.get_ordered_services()
    assert [s.name for s in ordered] == ["s1", "s2", "s3"]


def test_circular_dependency_fails() -> None:
    registry = ServiceRegistry()
    
    s1 = MockService("s1", deps=["s2"])
    s2 = MockService("s2", deps=["s1"])
    
    registry.register("s1", s1)
    registry.register("s2", s2)
    
    with pytest.raises(RegistryError):
        registry.get_ordered_services()


def test_missing_dependency_fails() -> None:
    registry = ServiceRegistry()
    
    s1 = MockService("s1", deps=["unregistered_dep"])
    registry.register("s1", s1)
    
    with pytest.raises(RegistryError):
        registry.get_ordered_services()
