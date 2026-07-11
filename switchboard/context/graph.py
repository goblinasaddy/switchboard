import networkx as nx
from switchboard.context.models import RepositoryModel

class DependencyGraph:
    """
    Subsystem component utilizing networkx to map codebase dependency networks.
    """

    def __init__(self) -> None:
        self._graph = nx.DiGraph()

    @property
    def graph(self) -> nx.DiGraph:
        return self._graph

    def build(self, repo_model: RepositoryModel) -> None:
        """
        Build the directed relation graph from the RepositoryModel.
        """
        self._graph.clear()
        
        # 1. Add file nodes and symbol nodes
        for file_path, source_file in repo_model.files.items():
            self._graph.add_node(file_path, type="file", lang=source_file.language.value)
            
            for sym in source_file.symbols:
                sym_id = f"{file_path}::{sym.name}"
                self._graph.add_node(
                    sym_id, 
                    type="symbol", 
                    sym_type=sym.type.value,
                    file=file_path,
                    name=sym.name
                )
                # Draw containment relation
                self._graph.add_edge(file_path, sym_id, relation="contains")

        # Helper map of symbol name to their containing files/symbol IDs
        symbol_map: dict[str, list[str]] = {}
        for file_path, source_file in repo_model.files.items():
            for sym in source_file.symbols:
                symbol_map.setdefault(sym.name, []).append(f"{file_path}::{sym.name}")

        # 2. Resolve imports and connect edges
        for file_path, source_file in repo_model.files.items():
            for imp in source_file.imports:
                # Resolve package imports to files
                # e.g., "switchboard.kernel.bootstrap" -> check if switchboard/kernel/bootstrap.py exists
                inferred_file = imp.replace(".", "/") + ".py"
                if inferred_file in repo_model.files:
                    self._graph.add_edge(file_path, inferred_file, relation="imports_file")
                else:
                    # check sub-packages or folders
                    inferred_init = imp.replace(".", "/") + "/__init__.py"
                    if inferred_init in repo_model.files:
                        self._graph.add_edge(file_path, inferred_init, relation="imports_file")

                # Resolve imported symbol links
                # e.g., if we import a name, link the importing file to that symbol node
                parts = imp.split(".")
                last_part = parts[-1]
                if last_part in symbol_map:
                    for dest_sym_id in symbol_map[last_part]:
                        self._graph.add_edge(file_path, dest_sym_id, relation="imports_symbol")

    def get_dependencies(self, file_path: str) -> list[str]:
        """Get file paths that the target file depends on."""
        if not self._graph.has_node(file_path):
            return []
        
        deps = []
        # outgoing edges with relation "imports_file"
        for _, target, data in self._graph.out_edges(file_path, data=True):
            if data.get("relation") == "imports_file":
                deps.append(target)
        return deps

    def get_dependents(self, file_path: str) -> list[str]:
        """Get files that depend on the target file."""
        if not self._graph.has_node(file_path):
            return []
            
        dependents = []
        # incoming edges to target file
        for source, _, data in self._graph.in_edges(file_path, data=True):
            if data.get("relation") == "imports_file":
                dependents.append(source)
        return dependents
