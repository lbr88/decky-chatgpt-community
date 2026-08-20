import asyncio

import decky

from backend.controller import ChatGPTController


class Plugin:
    def __init__(self, controller=None):
        self._controller = controller or ChatGPTController()

    async def _main(self):
        decky.logger.info("ChatGPT Community controller loaded")

    async def _unload(self):
        decky.logger.info("ChatGPT Community controller unloaded")

    async def get_status(self):
        try:
            return await asyncio.to_thread(self._controller.status)
        except Exception:
            decky.logger.exception("Status request failed")
            return {
                "installed": False,
                "version": None,
                "running": False,
                "voiceCompatible": False,
                "voiceMessage": "Could not inspect ChatGPT Community",
                "updater": None,
            }

    async def open_app(self):
        return await self._operation("open_app")

    async def toggle_voice(self):
        return await self._operation("toggle_voice")

    async def new_chat(self):
        return await self._operation("new_chat")

    async def check_updates(self):
        return await self._operation("check_updates")

    async def _operation(self, name):
        try:
            operation = getattr(self._controller, name)
            result = await asyncio.to_thread(operation)
            decky.logger.info("Operation %s finished: ok=%s", name, result.ok)
            return result.to_dict()
        except Exception:
            decky.logger.exception("Operation %s failed", name)
            return {"ok": False, "message": "Unexpected plugin error"}
