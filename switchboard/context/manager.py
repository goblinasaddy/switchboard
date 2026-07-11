import os
from typing import Any
from switchboard.interfaces.context import IContextEngine
from switchboard.interfaces.service import IService
from switchboard.interfaces.event_bus import IEventBus
from switchboard.context.models import RepositoryModel, ContextPackage, SourceFile, Language
from switchboard.context.scanner import RepositoryScanner, compute_file_hash
from switchboard.context.parser import ParserRegistry
from switchboard.context.parsers.python import PythonASTParser
from switchboard.context.graph import DependencyGraph
from switchboard.context.builders import ContextBuilder
from switchboard.types.events import (
    IndexStartedEvent,
    IndexCompletedEvent,
    IndexFailedEvent,
    FileParsedEvent,
    ContextBuiltEvent,
)
from switchboard.logging.config import get_logger

logger = get_logger("context_manager")

class ContextManager(IContextEngine, IService):
    """
    Subsystem coordinator managing scans, AST parsers, dependency graphs,
    and compiling context packages.
    """

    def __init__(self, root_path: str = ".", event_bus: IEventBus | None = None) -> None:
        self._root_path = os.path.abspath(root_path)
        self._event_bus = event_bus
        self._parser_registry = ParserRegistry()
        self._dep_graph = DependencyGraph()
        self._repo_model: RepositoryModel | None = None

    @property
    def name(self) -> str:
        return "context_manager"

    @property
    def dependencies(self) -> list[str]:
        return ["event_bus"]

    async def initialize(self) -> None:
        logger.info("Initializing Context Manager", root_path=self._root_path)
        # Register default native Python parser
        self._parser_registry.register(Language.PYTHON, PythonASTParser())
        self._repo_model = RepositoryModel(root_path=self._root_path)

    async def start(self) -> None:
        logger.info("Context Manager started. Performing initial codebase index...")
        await self.scan()

    async def shutdown(self) -> None:
        logger.info("Shutting down Context Manager")
        self._repo_model = None

    # IContextEngine Interface

    async def scan(self) -> RepositoryModel:
        """Scan directory structure, execute AST parsing, and build relation graph."""
        if self._event_bus:
            await self._event_bus.publish(IndexStartedEvent(self._root_path))
            
        logger.debug("Starting directory scan")
        scanner = RepositoryScanner(self._root_path)
        
        try:
            scan_results = scanner.scan()
            files_dict = {}
            lang_counts = {}
            total_symbols = 0
            
            for rel_path, abs_path, lang in scan_results:
                # Track language counts
                lang_counts[lang] = lang_counts.get(lang, 0) + 1
                
                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                except Exception as ex:
                    logger.warning("Failed to read file", path=rel_path, error=str(ex))
                    continue
                    
                file_hash = compute_file_hash(content)
                symbols = []
                imports = []
                
                # Check if a parser is available
                if self._parser_registry.has(lang):
                    parser = self._parser_registry.get(lang)
                    symbols = parser.parse(content, rel_path)
                    total_symbols += len(symbols)
                    
                    # Extract imports to feed dependency resolutions
                    for s in symbols:
                        if s.type.value == "import":
                            imports.append(s.name)

                    if self._event_bus:
                        await self._event_bus.publish(FileParsedEvent(rel_path, len(symbols)))
                
                files_dict[rel_path] = SourceFile(
                    path=rel_path,
                    language=lang,
                    size_bytes=len(content.encode("utf-8")),
                    hash=file_hash,
                    symbols=symbols,
                    imports=imports
                )

            # Assemble model
            self._repo_model = RepositoryModel(
                root_path=self._root_path,
                files=files_dict,
                total_files=len(files_dict),
                total_symbols=total_symbols,
                languages=lang_counts
            )

            # Assemble graph
            self._dep_graph.build(self._repo_model)
            
            logger.info(
                "Codebase indexing completed", 
                files=len(files_dict), 
                symbols=total_symbols
            )
            
            if self._event_bus:
                await self._event_bus.publish(
                    IndexCompletedEvent(self._root_path, len(files_dict), total_symbols)
                )
                
            return self._repo_model
            
        except Exception as e:
            logger.error("Codebase scan failed", error=str(e))
            if self._event_bus:
                await self._event_bus.publish(IndexFailedEvent(self._root_path, str(e)))
            raise

    async def get_dependency_graph(self) -> Any:
        return self._dep_graph

    async def build_package(self, query: str, file_paths: list[str] | None = None) -> ContextPackage:
        """Compile a query-specific task package."""
        if not self._repo_model:
            raise ValueError("Repository index is empty. Call scan() first.")
            
        builder = ContextBuilder(self._repo_model, self._dep_graph)
        package = builder.build(query, file_paths)
        
        logger.debug(
            "ContextPackage built", 
            query=query, 
            matched_files=len(package.files),
            estimated_tokens=package.token_estimate
        )
        
        if self._event_bus:
            await self._event_bus.publish(
                ContextBuiltEvent(query, len(package.files), len(package.symbols))
            )
            
        return package

    async def invalidate_cache(self, file_path: str) -> None:
        """Mark single file modified and re-calculate imports/symbols."""
        if not self._repo_model:
            return
            
        normalized = file_path.replace("\\", "/")
        abs_path = os.path.join(self._root_path, normalized)
        
        if not os.path.exists(abs_path):
            # File deleted
            self._repo_model.files.pop(normalized, None)
            logger.info("Cached file deleted, invalidated from model", file=normalized)
        else:
            # File updated
            try:
                with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                lang = self._repo_model.files[normalized].language if normalized in self._repo_model.files else Language.UNKNOWN
                file_hash = compute_file_hash(content)
                
                symbols = []
                imports = []
                if self._parser_registry.has(lang):
                    parser = self._parser_registry.get(lang)
                    symbols = parser.parse(content, normalized)
                    for s in symbols:
                        if s.type.value == "import":
                            imports.append(s.name)
                            
                # Update file in repository model
                self._repo_model.files[normalized] = SourceFile(
                    path=normalized,
                    language=lang,
                    size_bytes=len(content.encode("utf-8")),
                    hash=file_hash,
                    symbols=symbols,
                    imports=imports
                )
                logger.info("Cached file modified, re-parsed successfully", file=normalized)
            except Exception as e:
                logger.warning("Failed to update file cache", file=normalized, error=str(e))
                return
                
        # Recalculate totals
        self._repo_model.total_files = len(self._repo_model.files)
        self._repo_model.total_symbols = sum(len(f.symbols) for f in self._repo_model.files.values())
        
        # Rebuild relationship graph
        self._dep_graph.build(self._repo_model)
