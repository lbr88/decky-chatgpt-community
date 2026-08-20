import asyncio
import importlib.util
import logging
import sys
import types
import unittest
from pathlib import Path

from backend.models import OperationResult


class ControllerStub:
    def status(self):
        return {
            "installed": True,
            "version": "1.2.3",
            "running": True,
            "voiceCompatible": True,
            "voiceMessage": "compatible",
            "updater": {"state": "idle"},
        }

    def open_app(self):
        return OperationResult(True, "opened")

    def toggle_voice(self):
        return OperationResult(True, "voice")

    def new_chat(self):
        return OperationResult(True, "new chat")

    def check_updates(self):
        return OperationResult(False, "offline")


class PluginBridgeTests(unittest.TestCase):
    def _load_plugin(self):
        decky = types.ModuleType("decky")
        decky.logger = logging.getLogger("decky-test")
        previous = sys.modules.get("decky")
        sys.modules["decky"] = decky
        try:
            path = Path(__file__).parents[1] / "main.py"
            spec = importlib.util.spec_from_file_location("decky_chatgpt_main", path)
            module = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(module)
            return module
        finally:
            if previous is None:
                sys.modules.pop("decky", None)
            else:
                sys.modules["decky"] = previous

    def test_bridge_returns_json_compatible_status_and_operations(self):
        module = self._load_plugin()
        plugin = module.Plugin(controller=ControllerStub())

        async def exercise():
            return {
                "status": await plugin.get_status(),
                "open": await plugin.open_app(),
                "voice": await plugin.toggle_voice(),
                "chat": await plugin.new_chat(),
                "updates": await plugin.check_updates(),
            }

        result = asyncio.run(exercise())

        self.assertEqual(result["status"]["version"], "1.2.3")
        self.assertEqual(result["open"], {"ok": True, "message": "opened"})
        self.assertEqual(result["voice"], {"ok": True, "message": "voice"})
        self.assertEqual(result["chat"], {"ok": True, "message": "new chat"})
        self.assertEqual(result["updates"], {"ok": False, "message": "offline"})


if __name__ == "__main__":
    unittest.main()
