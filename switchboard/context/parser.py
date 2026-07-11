from switchboard.interfaces.context import IParser
from switchboard.context.models import Language
from switchboard.exceptions.base import RegistryError

class ParserRegistry:
    """
    Registry for loading and accessing programming language AST parsers.
    """

    def __init__(self) -> None:
        self._parsers: dict[Language, IParser] = {}

    def register(self, language: Language, parser: IParser) -> None:
        """Register a parser implementation for a target programming language."""
        if language in self._parsers:
            raise RegistryError(f"AST parser for language '{language.value}' already registered.")
        self._parsers[language] = parser

    def get(self, language: Language) -> IParser:
        """Get the registered parser instance for a language."""
        if language not in self._parsers:
            raise RegistryError(f"AST parser for language '{language.value}' is not registered.")
        return self._parsers[language]

    def has(self, language: Language) -> bool:
        """Check if a parser is registered for a language."""
        return language in self._parsers
