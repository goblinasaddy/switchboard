from enum import Enum
from pydantic import BaseModel, Field
from typing import Any

class Language(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    RUST = "rust"
    GO = "go"
    MARKDOWN = "markdown"
    UNKNOWN = "unknown"

class SymbolType(str, Enum):
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    IMPORT = "import"
    VARIABLE = "variable"

class Symbol(BaseModel):
    name: str
    type: SymbolType
    file_path: str
    start_line: int
    end_line: int
    docstring: str | None = None
    dependencies: list[str] = Field(default_factory=list)

class SourceFile(BaseModel):
    path: str
    language: Language
    size_bytes: int
    hash: str
    symbols: list[Symbol] = Field(default_factory=list)
    imports: list[str] = Field(default_factory=list)

class RepositoryModel(BaseModel):
    root_path: str
    files: dict[str, SourceFile] = Field(default_factory=dict)
    total_files: int = 0
    total_symbols: int = 0
    languages: dict[Language, int] = Field(default_factory=dict)

class ContextPackage(BaseModel):
    task_query: str
    files: list[SourceFile] = Field(default_factory=list)
    symbols: list[Symbol] = Field(default_factory=list)
    token_estimate: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)
