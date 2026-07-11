import json
import pytest
from switchboard.plugins.manager import PluginManager
from switchboard.exceptions.base import PluginError

@pytest.mark.asyncio
async def test_plugin_discovery_and_loading(tmp_path) -> None:
    # 1. Scaffolding a dummy plugin directory structure
    plugin_folder = tmp_path / "my_test_plugin"
    plugin_folder.mkdir()

    manifest = {
        "name": "test_plugin",
        "version": "1.0.0",
        "entry_point": "main.py"
    }
    
    # Write plugin.json
    manifest_file = plugin_folder / "plugin.json"
    manifest_file.write_text(json.dumps(manifest))

    # Write main.py entrypoint with hook
    entrypoint_file = plugin_folder / "main.py"
    entrypoint_code = """
def register_plugin(manager):
    manager.test_hook_called = True
"""
    entrypoint_file.write_text(entrypoint_code)

    # 2. Instantiate and run PluginManager on the temp path
    pm = PluginManager(plugin_dir=str(tmp_path))
    await pm.initialize()
    await pm.start()

    # 3. Assertions
    loaded_plugins = pm.get_loaded_plugins()
    assert "test_plugin" in loaded_plugins
    assert loaded_plugins["test_plugin"]["enabled"] is True
    assert getattr(pm, "test_hook_called", False) is True

    # 4. Check disable/enable
    pm.disable_plugin("test_plugin")
    assert loaded_plugins["test_plugin"]["enabled"] is False

    pm.enable_plugin("test_plugin")
    assert loaded_plugins["test_plugin"]["enabled"] is True

    await pm.shutdown()
    assert len(pm.get_loaded_plugins()) == 0


@pytest.mark.asyncio
async def test_plugin_missing_entrypoint_raises(tmp_path) -> None:
    plugin_folder = tmp_path / "broken_plugin"
    plugin_folder.mkdir()

    manifest = {
        "name": "broken_plugin",
        "version": "1.0.0",
        "entry_point": "missing.py"
    }
    
    manifest_file = plugin_folder / "plugin.json"
    manifest_file.write_text(json.dumps(manifest))

    pm = PluginManager(plugin_dir=str(tmp_path))
    await pm.initialize()
    
    # The start/scan should log the error but not crash the whole scan process
    await pm.start()
    assert len(pm.get_loaded_plugins()) == 0
