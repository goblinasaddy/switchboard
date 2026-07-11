import ast
from switchboard.interfaces.context import IParser
from switchboard.context.models import Symbol, SymbolType

class PythonASTVisitor(ast.NodeVisitor):
    """AST node visitor to extract structured class, function, method, and import symbols."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.symbols: list[Symbol] = []
        self.imports: list[str] = []
        self._current_class: str | None = None

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(alias.name)
            # Record symbol
            self.symbols.append(
                Symbol(
                    name=alias.name,
                    type=SymbolType.IMPORT,
                    file_path=self.file_path,
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    docstring=None
                )
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            full_name = f"{module}.{alias.name}" if module else alias.name
            self.imports.append(full_name)
            # Record symbol
            self.symbols.append(
                Symbol(
                    name=full_name,
                    type=SymbolType.IMPORT,
                    file_path=self.file_path,
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    docstring=None
                )
            )
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        docstring = ast.get_docstring(node)
        class_name = node.name
        
        # Build symbol
        self.symbols.append(
            Symbol(
                name=class_name,
                type=SymbolType.CLASS,
                file_path=self.file_path,
                start_line=node.lineno,
                end_line=node.end_lineno or node.lineno,
                docstring=docstring
            )
        )
        
        # Track class scope to classify inner methods
        old_class = self._current_class
        self._current_class = class_name
        self.generic_visit(node)
        self._current_class = old_class

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        docstring = ast.get_docstring(node)
        func_name = node.name
        
        if self._current_class:
            name = f"{self._current_class}.{func_name}"
            sym_type = SymbolType.METHOD
        else:
            name = func_name
            sym_type = SymbolType.FUNCTION

        self.symbols.append(
            Symbol(
                name=name,
                type=sym_type,
                file_path=self.file_path,
                start_line=node.lineno,
                end_line=node.end_lineno or node.lineno,
                docstring=docstring
            )
        )
        # Function body can contain nested definitions but we do not recurse deep to avoid duplicate definitions
        # However, we still visit children to find imports inside functions
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)


class PythonASTParser(IParser):
    """
    Python language parser utilizing the built-in ast module.
    """

    def parse(self, file_content: str, file_path: str) -> list[Symbol]:
        """Parse Python source content and extract classes, functions, and imports."""
        if not file_content.strip():
            return []
            
        try:
            tree = ast.parse(file_content, filename=file_path)
            visitor = PythonASTVisitor(file_path)
            visitor.visit(tree)
            return visitor.symbols
        except SyntaxError:
            # Code contains errors, return empty definitions gracefully
            return []
        except Exception:
            return []
