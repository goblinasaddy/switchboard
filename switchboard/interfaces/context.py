from typing import Protocol, Any
from switchboard.interfaces.service import IService
from switchboard.types.context import RepositoryModel, ContextPackage, Symbol

class IParser(Protocol):
    """Protocol for AST symbol extraction for specific programming languages."""
    
    def parse(self, file_content: str, file_path: str) -> list[Symbol]:
        """
        Parse raw source code content and return a list of defined symbols.
        
        Args:
            file_content: Raw string content of the source file.
            file_path: Relative path to the source file.
            
        Returns:
            List of Symbol objects.
        """
        ...


class IContextEngine(IService, Protocol):
    """Subsystem responsible for static analysis and repository structure indexing."""
    
    async def scan(self) -> RepositoryModel:
        """
        Recursively scan the local repository root path, ignoring blacklisted path files,
        parsing AST symbols, and assembling dependencies.
        
        Returns:
            The complete parsed RepositoryModel snapshot.
        """
        ...
        
    async def get_dependency_graph(self) -> Any:
        """
        Get the internal directed dependency graph representation.
        
        Returns:
            NetworkX DiGraph of files and symbols.
        """
        ...
        
    async def build_package(self, query: str, file_paths: list[str] | None = None) -> ContextPackage:
        """
        Synthesize a task-specific ContextPackage minimized to contain only the files,
        symbols, and relation metadata relevant to the target query.
        
        Args:
            query: String describing target engineering task or query.
            file_paths: Optional manual checklist of files to include.
            
        Returns:
            Compiled ContextPackage layer.
        """
        ...
        
    async def invalidate_cache(self, file_path: str) -> None:
        """
        Mark a file as modified, invalidating its cache, and re-calculating AST
        symbols and relation sub-graphs.
        
        Args:
            file_path: Target relative file path to invalidate.
        """
        ...
