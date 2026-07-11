import os
import tempfile
import pytest
from switchboard.context.models import Language, SymbolType
from switchboard.context.scanner import GitignoreMatcher, RepositoryScanner, detect_language
from switchboard.context.parsers.python import PythonASTParser
from switchboard.context.graph import DependencyGraph
from switchboard.context.builders import ContextBuilder
from switchboard.kernel.bootstrap import bootstrap_platform
from switchboard.types.events import (
    IndexStartedEvent,
    IndexCompletedEvent,
    ContextBuiltEvent,
)

def test_language_detection() -> None:
    assert detect_language("foo.py") == Language.PYTHON
    assert detect_language("bar.JS") == Language.JAVASCRIPT
    assert detect_language("baz.tsx") == Language.TYPESCRIPT
    assert detect_language("hello.rs") == Language.RUST
    assert detect_language("world.go") == Language.GO
    assert detect_language("README.md") == Language.MARKDOWN
    assert detect_language("unknown.txt") == Language.UNKNOWN


def test_gitignore_matcher_and_scanner() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create directories
        os.makedirs(os.path.join(tmp_dir, "src"))
        os.makedirs(os.path.join(tmp_dir, "tests"))
        os.makedirs(os.path.join(tmp_dir, "__pycache__"))
        os.makedirs(os.path.join(tmp_dir, ".git"))

        # Create files
        with open(os.path.join(tmp_dir, "src", "main.py"), "w") as f:
            f.write("print('hello')")
        with open(os.path.join(tmp_dir, "tests", "test_main.py"), "w") as f:
            f.write("def test(): pass")
        with open(os.path.join(tmp_dir, "__pycache__", "main.pyc"), "w") as f:
            f.write("binary")
        with open(os.path.join(tmp_dir, ".gitignore"), "w") as f:
            f.write("tests/\n")

        # Scan without gitignore first (uses default patterns in matcher)
        scanner = RepositoryScanner(tmp_dir)
        files = scanner.scan()
        rel_paths = {f[0] for f in files}
        
        # 'tests/test_main.py' should be ignored because of gitignore rule "tests/"
        assert "src/main.py" in rel_paths
        assert "tests/test_main.py" not in rel_paths
        assert "__pycache__/main.pyc" not in rel_paths


def test_python_ast_parser() -> None:
    code = """
import os
from sys import exit

class Database:
    \"\"\"Simulated DB class.\"\"\"
    def __init__(self) -> None:
        pass
        
    def query(self, sql: str) -> None:
        \"\"\"Query method.\"\"\"
        pass

def top_level_func():
    return 42
"""
    parser = PythonASTParser()
    symbols = parser.parse(code, "db.py")
    
    # Assert import symbols
    imports = [s for s in symbols if s.type == SymbolType.IMPORT]
    assert len(imports) == 2
    assert {i.name for i in imports} == {"os", "sys.exit"}
    
    # Assert class symbol
    classes = [s for s in symbols if s.type == SymbolType.CLASS]
    assert len(classes) == 1
    assert classes[0].name == "Database"
    assert classes[0].docstring == "Simulated DB class."
    
    # Assert method symbol
    methods = [s for s in symbols if s.type == SymbolType.METHOD]
    assert len(methods) == 2
    assert {m.name for m in methods} == {"Database.__init__", "Database.query"}
    assert methods[1].docstring == "Query method."
    
    # Assert function symbol
    funcs = [s for s in symbols if s.type == SymbolType.FUNCTION]
    assert len(funcs) == 1
    assert funcs[0].name == "top_level_func"


@pytest.mark.asyncio
async def test_context_manager_lifecycle_and_invalidation() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create temp python files referencing each other
        file_a = os.path.join(tmp_dir, "module_a.py")
        file_b = os.path.join(tmp_dir, "module_b.py")
        
        with open(file_a, "w") as f:
            f.write("import module_b\nclass A:\n    pass\n")
        with open(file_b, "w") as f:
            f.write("def b_func():\n    pass\n")
            
        kernel = await bootstrap_platform(overrides={"ollama_url": "http://localhost:11434"})
        await kernel.initialize()
        
        # Get context manager (point it to tmp_dir instead of repo root for testing)
        context_manager = kernel.get_service("context_manager")
        context_manager._root_path = os.path.abspath(tmp_dir)
        context_manager._repo_model.root_path = os.path.abspath(tmp_dir)
        
        # Scan
        repo_model = await context_manager.scan()
        assert repo_model.total_files == 2
        assert "module_a.py" in repo_model.files
        assert "module_b.py" in repo_model.files
        
        # Validate Dependency Graph links
        dep_graph = await context_manager.get_dependency_graph()
        assert dep_graph.get_dependencies("module_a.py") == ["module_b.py"]
        
        # Test Cache Invalidation: Modify module_b.py to define a new function
        with open(file_b, "w") as f:
            f.write("def b_func():\n    pass\ndef new_func():\n    pass\n")
            
        await context_manager.invalidate_cache("module_b.py")
        
        # Reparse should update the symbols count
        updated_model = context_manager._repo_model
        assert updated_model.total_symbols == 4  # module_a: import module_b + class A (2), module_b: b_func + new_func (2)
        
        await kernel.shutdown()


@pytest.mark.asyncio
async def test_context_builder() -> None:
    kernel = await bootstrap_platform()
    await kernel.initialize()
    await kernel.start()
    
    # Test built packages on the active SwitchBoard repo
    context_manager = kernel.get_service("context_manager")
    
    # Compile package for query 'bootstrap'
    package = await context_manager.build_package(query="bootstrap")
    
    # The scanner should have matched switchboard/kernel/bootstrap.py and pulled its imports
    matched_paths = [f.path for f in package.files]
    assert any("bootstrap.py" in p for p in matched_paths)
    
    # Assert token estimates exist
    assert package.token_estimate > 0
    assert package.task_query == "bootstrap"
    
    await kernel.shutdown()
