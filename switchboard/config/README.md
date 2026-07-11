# config Subsystem

## Purpose
The `config` subsystem manages the loading, validation, and parsing of system configuration parameters from environment variables, local `.env` files, static configurations, and command-line overrides.

## Responsibilities
- Declare system configuration options and defaults using `pydantic-settings`.
- Implement `loader.py` to prioritize and merge configuration sources (.env -> settings.toml -> CLI parameters).

## Public APIs
- `Settings`: Pydantic validation class containing settings like `env`, `log_level`, etc.
- `load_config(config_path: str | None = None, overrides: dict[str, Any] | None = None) -> Settings`: Standard loader returning validated configuration.

## Future Work
- Support multi-profile configurations (development, test, production).
- Add support for encrypted configuration secrets.
