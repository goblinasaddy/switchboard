from switchboard.interfaces.provider import IProvider
from switchboard.interfaces.registry import IRegistry
from switchboard.exceptions.base import RegistryError

class ProviderRegistry(IRegistry[IProvider]):
    """
    Concrete registry implementation for discovering, registering, and retrieving
    compute provider backends.
    """

    def __init__(self) -> None:
        self._providers: dict[str, IProvider] = {}

    def register(self, name: str, item: IProvider) -> None:
        """
        Register an IProvider instance.
        
        Args:
            name: Unique identifier name of the provider.
            item: The provider instance.
            
        Raises:
            RegistryError: If a provider is already registered under this name.
        """
        if name in self._providers:
            raise RegistryError(f"Compute provider '{name}' is already registered.")
        self._providers[name] = item

    def get(self, name: str) -> IProvider:
        """
        Retrieve a registered provider by name.
        
        Args:
            name: The target provider identifier.
            
        Returns:
            The registered provider instance.
            
        Raises:
            RegistryError: If no provider is registered under this name.
        """
        if name not in self._providers:
            raise RegistryError(f"Compute provider '{name}' is not registered.")
        return self._providers[name]

    def has(self, name: str) -> bool:
        """Check if a provider exists under the given name."""
        return name in self._providers

    def list_keys(self) -> list[str]:
        """List names of all registered providers."""
        return list(self._providers.keys())
