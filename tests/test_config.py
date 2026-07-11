import os
from unittest import mock
import pytest
from switchboard.config.loader import load_config
from switchboard.exceptions.base import ConfigError

def test_load_config_defaults() -> None:
    # Ensure default settings load without error
    settings = load_config(config_path=None)
    assert settings.env == "development"
    assert settings.log_level == "INFO"


def test_load_config_toml(tmp_path) -> None:
    # Create temp TOML config file
    config_file = tmp_path / "settings.toml"
    config_content = """
    [switchboard]
    env = "staging"
    log_level = "WARNING"
    max_vram_gb = 8.0
    """
    config_file.write_text(config_content)

    settings = load_config(config_path=str(config_file))
    assert settings.env == "staging"
    assert settings.log_level == "WARNING"
    assert settings.max_vram_gb == 8.0


def test_load_config_env_priority(tmp_path) -> None:
    config_file = tmp_path / "settings.toml"
    config_content = """
    [switchboard]
    env = "staging"
    log_level = "WARNING"
    """
    config_file.write_text(config_content)

    # Env vars should override TOML configuration values
    with mock.patch.dict(os.environ, {"SWITCHBOARD_LOG_LEVEL": "ERROR", "SWITCHBOARD_ENV": "production"}):
        settings = load_config(config_path=str(config_file))
        assert settings.env == "production"
        assert settings.log_level == "ERROR"


def test_load_config_cli_overrides_priority(tmp_path) -> None:
    config_file = tmp_path / "settings.toml"
    config_content = """
    [switchboard]
    env = "staging"
    log_level = "WARNING"
    """
    config_file.write_text(config_content)

    # CLI overrides should take highest priority over env and TOML
    with mock.patch.dict(os.environ, {"SWITCHBOARD_LOG_LEVEL": "ERROR"}):
        overrides = {"log_level": "DEBUG", "env": "testing"}
        settings = load_config(config_path=str(config_file), overrides=overrides)
        assert settings.log_level == "DEBUG"
        assert settings.env == "testing"


def test_invalid_toml_raises_config_error(tmp_path) -> None:
    bad_config = tmp_path / "bad.toml"
    bad_config.write_text("invalid_toml = {unclosed")
    
    with pytest.raises(ConfigError):
        load_config(config_path=str(bad_config))
