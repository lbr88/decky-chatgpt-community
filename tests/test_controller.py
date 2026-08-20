import subprocess
import unittest
from pathlib import Path

from backend.compatibility import VoiceContract
from backend.controller import ChatGPTController
from backend.processes import AppProcess


class XdotoolRunner:
    def __init__(self, windows=("10", "20")):
        self.windows = windows
        self.calls = []

    def __call__(self, args, **kwargs):
        command = tuple(args)
        self.calls.append(command)
        if command[:4] == (
            "/usr/bin/xdotool",
            "search",
            "--onlyvisible",
            "--class",
        ):
            return subprocess.CompletedProcess(args, 0, "\n".join(self.windows) + "\n", "")
        if command == ("/usr/bin/xdotool", "getwindowgeometry", "--shell", "10"):
            return subprocess.CompletedProcess(args, 0, "WIDTH=100\nHEIGHT=100\n", "")
        if command == ("/usr/bin/xdotool", "getwindowgeometry", "--shell", "20"):
            return subprocess.CompletedProcess(args, 0, "WIDTH=640\nHEIGHT=480\n", "")
        return subprocess.CompletedProcess(args, 0, "", "")


class FakePopen:
    def __init__(self):
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append((tuple(args), kwargs))
        return object()


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.process = AppProcess(
            88,
            "/opt/codex-desktop/ChatGPT",
            {"DISPLAY": ":8", "XAUTHORITY": "/tmp/xauth", "HOME": "/home/deck"},
        )

    def _controller(self, *, runner=None, processes=None, contract=None, popen=None):
        return ChatGPTController(
            runner=runner or XdotoolRunner(),
            process_finder=lambda: [self.process] if processes is None else processes(),
            contract_checker=lambda _: contract
            or VoiceContract(True, (), "Realtime Voice Mode is compatible"),
            popen=popen or FakePopen(),
            sleep=lambda _: None,
            launch_attempts=2,
            app_asar=Path("/fake/app.asar"),
            uid=1000,
        )

    def test_voice_fails_closed_before_input_when_contract_is_missing(self):
        runner = XdotoolRunner()
        controller = self._controller(
            runner=runner,
            contract=VoiceContract(False, ("Ctrl+Shift+V",), "incompatible bundle"),
        )

        result = controller.toggle_voice()

        self.assertFalse(result.ok)
        self.assertIn("incompatible bundle", result.message)
        self.assertEqual(runner.calls, [])

    def test_voice_focuses_largest_exact_window_before_sending_shortcut(self):
        runner = XdotoolRunner()
        controller = self._controller(runner=runner)

        result = controller.toggle_voice()

        self.assertTrue(result.ok)
        self.assertIn(
            (
                "/usr/bin/xdotool",
                "search",
                "--onlyvisible",
                "--class",
                "^codex-desktop$",
            ),
            runner.calls,
        )
        focus = ("/usr/bin/xdotool", "windowactivate", "--sync", "20")
        key = (
            "/usr/bin/xdotool",
            "key",
            "--window",
            "20",
            "--clearmodifiers",
            "ctrl+shift+v",
        )
        self.assertLess(runner.calls.index(focus), runner.calls.index(key))

    def test_missing_verified_window_never_sends_key(self):
        runner = XdotoolRunner(windows=())
        controller = self._controller(runner=runner)

        result = controller.toggle_voice()

        self.assertFalse(result.ok)
        self.assertIn("window", result.message.lower())
        self.assertFalse(any("key" in call for call in runner.calls))

    def test_open_launches_app_then_focuses_discovered_window(self):
        sightings = iter(([], [self.process]))
        popen = FakePopen()
        runner = XdotoolRunner(windows=("20",))
        controller = self._controller(
            runner=runner,
            processes=lambda: next(sightings, [self.process]),
            popen=popen,
        )

        result = controller.open_app()

        self.assertTrue(result.ok)
        self.assertEqual(popen.calls[0][0], ("/usr/bin/codex-desktop",))
        self.assertTrue(popen.calls[0][1]["start_new_session"])
        self.assertEqual(popen.calls[0][1]["env"]["HOME"], "/home/deck")

    def test_new_chat_uses_the_apps_fixed_shortcut(self):
        runner = XdotoolRunner(windows=("20",))
        controller = self._controller(runner=runner)

        result = controller.new_chat()

        self.assertTrue(result.ok)
        self.assertIn(
            (
                "/usr/bin/xdotool",
                "key",
                "--window",
                "20",
                "--clearmodifiers",
                "ctrl+n",
            ),
            runner.calls,
        )


if __name__ == "__main__":
    unittest.main()
