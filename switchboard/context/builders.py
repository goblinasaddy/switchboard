import os
from switchboard.context.models import RepositoryModel, ContextPackage, SourceFile, Symbol
from switchboard.context.graph import DependencyGraph

class ContextBuilder:
    """
    Subsystem component responsible for extracting task-specific file subsets
    and compiling the final ContextPackage payload.
    """

    def __init__(self, repo_model: RepositoryModel, dep_graph: DependencyGraph) -> None:
        self.repo_model = repo_model
        self.dep_graph = dep_graph

    def build(self, query: str, file_paths: list[str] | None = None) -> ContextPackage:
        """
        Builds a ContextPackage containing relevant files and symbols based on the query.
        
        Args:
            query: User's task description or keywords.
            file_paths: Optional explicit file checklist to include.
            
        Returns:
            Compiled ContextPackage.
        """
        matched_files: dict[str, SourceFile] = {}
        matched_symbols: list[Symbol] = []
        
        # 1. Match explicit files if provided
        if file_paths:
            for fp in file_paths:
                normalized = fp.replace("\\", "/")
                if normalized in self.repo_model.files:
                    matched_files[normalized] = self.repo_model.files[normalized]

        # 2. Heuristic query-matching
        # Search for file names or symbol names matching query words
        query_words = set(query.lower().replace("_", " ").replace("-", " ").split())
        
        for fp, src_file in self.repo_model.files.items():
            # If file path segment matches query
            base = os.path.basename(fp).lower()
            if any(word in base for word in query_words):
                matched_files[fp] = src_file
                
            # If symbol names match query
            for sym in src_file.symbols:
                if sym.name.lower() in query_words or any(word in sym.name.lower() for word in query_words):
                    matched_files[fp] = src_file
                    if sym not in matched_symbols:
                        matched_symbols.append(sym)

        # 3. Pull in immediate dependencies (using the dependency graph)
        # Ensure imports/dependencies of matched files are also loaded for context
        dependencies_to_add = []
        for fp in matched_files.keys():
            deps = self.dep_graph.get_dependencies(fp)
            for d in deps:
                if d not in matched_files and d not in dependencies_to_add:
                    dependencies_to_add.append(d)
                    
        for d in dependencies_to_add:
            matched_files[d] = self.repo_model.files[d]

        # 4. Assemble symbols and calculate token estimations
        # Gather all symbols from the compiled file list
        all_symbols = list(matched_symbols)
        total_chars = 0
        
        for fp, src_file in matched_files.items():
            for sym in src_file.symbols:
                if sym not in all_symbols:
                    all_symbols.append(sym)
            total_chars += src_file.size_bytes

        # Standard token heuristic: ~4 characters per token
        token_estimate = int(total_chars / 4.0)

        return ContextPackage(
            task_query=query,
            files=list(matched_files.values()),
            symbols=all_symbols,
            token_estimate=token_estimate,
            metadata={
                "matched_count": len(matched_files),
                "total_symbols_count": len(all_symbols)
            }
        )
