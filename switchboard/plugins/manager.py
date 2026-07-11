import asyncio
import importlib.util
import json
import os
from typing import Any
from switchboard.interfaces.service import IService
from switchboard.logging.config import get_logger
from switchboard.exceptions.base import PluginError

logger = get_logger("plugin_manager")

class PluginManager(IService):
    """
    Subsystem responsible for discovering, validating, loading, and managing
    lifecycle states of external platform extensions (plugins).
    """

    def __init__(self, plugin_dir: str = "plugins") -> None:
        self._plugin_dir = plugin_dir
        self._plugins: dict[str, dict[str, Any]] = {}

    @property
    def name(self) -> str:
        return "plugin_manager"

    @property
    def dependencies(self) -> list[str]:
        # Independent core platform manager
        return []

    async def initialize(self) -> None:
        """Ensure the target plugins directory exists."""
        logger.info("Initializing Plugin Manager", plugin_dir=self._plugin_dir)
        if not os.path.exists(self._plugin_dir):
            try:
                os.makedirs(self._plugin_dir, exist_ok=True)
                logger.info("Created plugin directory", path=self._plugin_dir)
            except Exception as e:
                raise PluginError(f"Failed to create plugins directory '{self._plugin_dir}': {e}") from e

    async def start(self) -> None:
        """Scan, validate, and load all discovered plugins."""
        logger.info("Starting Plugin Manager scanning")
        await self.discover_and_load_plugins()

    async def shutdown(self) -> None:
        """Safely shut down and release plugin allocations."""
        logger.info("Shutting down Plugin Manager, unloading active plugins")
        # Clear module references
        self._plugins.clear()

    async def discover_and_load_plugins(self) -> None:
        """
        Scan directory entries, locating directories with a `plugin.json` manifest.
        """
        if not os.path.exists(self._plugin_dir):
            return

        for entry in os.scandir(self._plugin_dir):
            if entry.is_dir():
                manifest_path = os.path.join(entry.path, "plugin.json")
                if os.path.exists(manifest_path):
                    try:
                        await self.load_plugin(entry.path, manifest_path)
                    except Exception as e:
                        logger.error(
                            "Failed to load plugin", 
                            directory=entry.name, 
                            error=str(e)
                        )

    async def load_plugin(self, plugin_path: str, manifest_path: str) -> None:
        """
        Read manifest, import module dynamically, and trigger its registration.
        """
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
        except Exception as e:
            raise PluginError(f"Failed to read plugin manifest at {manifest_path}: {e}") from e

        # Validate manifest properties
        plugin_name = manifest.get("name")
        version = manifest.get("version")
        entry_point = manifest.get("entry_point")

        if not plugin_name or not version or not entry_point:
            raise PluginError(
                f"Invalid plugin manifest at {manifest_path}. "
                "Must include 'name', 'version', and 'entry_point'."
            )

        if plugin_name in self._plugins:
            logger.warning("Plugin already loaded, skipping import", plugin=plugin_name)
            return

        entry_file = os.path.join(plugin_path, entry_point)
        if not os.path.exists(entry_file):
            raise PluginError(f"Entry point file '{entry_point}' not found at {entry_file}")

        # Construct unique python module path
        module_name = f"switchboard.plugins.loaded.{plugin_name}"
        spec = importlib.util.spec_from_file_location(module_name, entry_file)
        if spec is None or spec.loader is None:
            raise PluginError(f"Could not build execution spec for plugin '{plugin_name}'")

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            logger.info("Loaded plugin module", plugin=plugin_name, version=version)

            # Trigger plugin registration hook if available
            if hasattr(module, "register_plugin"):
                register_hook = getattr(module, "register_plugin")
                if asyncio.iscoroutinefunction(register_hook):
                    await register_hook(self)
                else:
                    register_hook(self)

            self._plugins[plugin_name] = {
                "manifest": manifest,
                "module": module,
                "enabled": True,
                "path": plugin_path
            }
        except Exception as e:
            raise PluginError(f"Runtime execution failed for plugin module '{plugin_name}': {e}") from e

    def get_loaded_plugins(self) -> dict[str, dict[str, Any]]:
        """Return references to all loaded plugins."""
        return self._plugins

    def enable_plugin(self, name: str) -> None:
        """Enable plugin by name."""
        if name not in self._plugins:
            raise PluginError(f"Cannot enable plugin '{name}'. Plugin is not loaded.")
        self._plugins[name]["enabled"] = True
        logger.info("Plugin enabled", plugin=name)

    def disable_plugin(self, name: str) -> None:
        """Disable plugin by name."""
        if name not in self._plugins:
            raise PluginError(f"Cannot disable plugin '{name}'. Plugin is not loaded.")
        self._plugins[name]["enabled"] = False
        logger.info("Plugin disabled", plugin=name)
