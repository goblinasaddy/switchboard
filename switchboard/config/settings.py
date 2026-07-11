from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Pydantic Settings model defining configuration schemas and default values
    for the SwitchBoard runtime environment.
    """
    model_config = SettingsConfigDict(
        env_prefix="SWITCHBOARD_", 
        env_file=".env", 
        extra="ignore"
    )
    
    env: str = "development"
    log_level: str = "INFO"
    version: str = "0.1.0"
    plugin_dir: str = "plugins"
    
    # Inference engine connections (future-proofing Phase 1)
    ollama_url: str = "http://localhost:11434"
    
    # Resource management defaults (future-proofing Phase 2)
    max_vram_gb: float = 12.0
    max_ram_gb: float = 16.0
