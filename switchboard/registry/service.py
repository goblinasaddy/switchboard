import networkx as nx
from switchboard.interfaces.service import IService
from switchboard.interfaces.registry import IRegistry
from switchboard.exceptions.base import RegistryError

class ServiceRegistry(IRegistry[IService]):
    """
    Concrete registry implementation managing SwitchBoard service lifecycles 
    and resolving dependencies using topological sorting.
    """

    def __init__(self) -> None:
        self._services: dict[str, IService] = {}

    def register(self, name: str, item: IService) -> None:
        """
        Register an IService implementation.
        
        Args:
            name: The service identifier name.
            item: The service instance.
            
        Raises:
            RegistryError: If service is already registered under this name.
        """
        if name in self._services:
            raise RegistryError(f"Service with name '{name}' already registered.")
        self._services[name] = item

    def get(self, name: str) -> IService:
        """
        Retrieve a registered service by its name.
        
        Args:
            name: Service identifier name.
            
        Raises:
            RegistryError: If service is not registered.
        """
        if name not in self._services:
            raise RegistryError(f"Service '{name}' is not registered.")
        return self._services[name]

    def has(self, name: str) -> bool:
        """Check if a service is registered under the given name."""
        return name in self._services

    def list_keys(self) -> list[str]:
        """List names of all registered services."""
        return list(self._services.keys())

    def get_ordered_services(self) -> list[IService]:
        """
        Perform a topological sort on registered services based on their dependencies.
        
        Returns:
            A list of IService instances ordered such that dependencies appear 
            before the services that depend on them.
            
        Raises:
            RegistryError: If circular dependencies are detected or a dependency is missing.
        """
        graph = nx.DiGraph()
        
        # Add all nodes
        for name in self._services:
            graph.add_node(name)
            
        # Add edges for dependencies
        for name, service in self._services.items():
            for dep in service.dependencies:
                if dep not in self._services:
                    raise RegistryError(
                        f"Service '{name}' depends on unregistered service '{dep}'."
                    )
                # dep must be resolved/started BEFORE name, so dep -> name
                graph.add_edge(dep, name)
                
        try:
            ordered_names = list(nx.topological_sort(graph))
            return [self._services[name] for name in ordered_names]
        except nx.NetworkXUnfeasible as e:
            raise RegistryError(f"Circular dependency detected in service tree: {e}") from e
