class SwitchBoardError(Exception):
    """Base exception for all SwitchBoard errors."""
    pass


class KernelError(SwitchBoardError):
    """Raised when an error occurs during Kernel bootstrapping or lifecycle transitions."""
    pass


class RegistryError(SwitchBoardError):
    """Raised when service registration, dependency injection, or lookup fails."""
    pass


class EventBusError(SwitchBoardError):
    """Raised when event publishing, subscription, or handler execution fails."""
    pass


class PluginError(SwitchBoardError):
    """Raised when plugin discovery, validation, or loading fails."""
    pass


class ConfigError(SwitchBoardError):
    """Raised when configuration validation or environment parsing fails."""
    pass
