from typing import Generic, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")

@runtime_checkable
class IRegistry(Protocol, Generic[T]):
    """
    Generic registry interface defining standard storage, retrieval, and check operations
    for managed platform components (services, models, runtimes, etc.).
    """

    def register(self, name: str, item: T) -> None:
        """
        Register a new item with a unique identifier name.
        
        Args:
            name: Unique name identifier.
            item: Component instance to register.
            
        Raises:
            RegistryError: If an item is already registered under this name.
        """
        ...

    def get(self, name: str) -> T:
        """
        Retrieve an item by its identifier name.
        
        Args:
            name: The target unique identifier.
            
        Returns:
            The registered component instance.
            
        Raises:
            RegistryError: If no item is found under this name.
        """
        ...

    def has(self, name: str) -> bool:
        """
        Check if an item exists under the given name.
        
        Args:
            name: Unique identifier to verify.
        """
        ...

    def list_keys(self) -> list[str]:
        """Return a list of all registered identifier keys."""
        ...
