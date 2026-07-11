import os
import tomllib
from typing import Any
from switchboard.config.settings import Settings
from switchboard.exceptions.base import ConfigError

def load_config(
    config_path: str | None = None, 
    overrides: dict[str, Any] | None = None
) -> Settings:
    """
    Load, validate, and merge configuration from TOML files, environment variables, 
    and CLI overrides.
    
    Priority Order (Highest to Lowest):
    1. CLI Overrides
    2. Environment Variables (prefixed with SWITCHBOARD_)
    3. TOML configuration file
    4. Settings model defaults
    
    Args:
        config_path: Absolute or relative path to a settings.toml file.
        overrides: Dictionary of config values from CLI inputs.
        
    Raises:
        ConfigError: If config file is missing, invalid TOML, or validation fails.
    """
    toml_data: dict[str, Any] = {}

    # 1. Load TOML configuration if path specified or default file exists
    target_path = config_path or "switchboard.toml"
    
    if os.path.exists(target_path):
        try:
            with open(target_path, "rb") as f:
                raw_data = tomllib.load(f)
                # Expecting top-level or [switchboard] table
                toml_data = raw_data.get("switchboard", raw_data)
        except Exception as e:
            raise ConfigError(f"Failed to parse TOML configuration from {target_path}: {e}") from e
    elif config_path is not None:
        raise ConfigError(f"Config file not found at: {config_path}")

    # 2. Extract environment variables prefixed with SWITCHBOARD_
    env_data: dict[str, Any] = {}
    prefix = "SWITCHBOARD_"
    for key, val in os.environ.items():
        if key.startswith(prefix):
            field_name = key[len(prefix):].lower()
            env_data[field_name] = val

    # Merge toml_data and env_data (env_data overrides toml_data)
    merged_data = {**toml_data, **env_data}

    # 3. Instantiate settings
    try:
        settings = Settings(**merged_data)
    except Exception as e:
        raise ConfigError(f"Configuration validation failed: {e}") from e

    # 4. Apply CLI overrides
    if overrides:
        try:
            settings = settings.model_copy(update={k: v for k, v in overrides.items() if v is not None})
            # Re-validate settings after updates
            settings = Settings(**settings.model_dump())
        except Exception as e:
            raise ConfigError(f"CLI override validation failed: {e}") from e

    return settings
