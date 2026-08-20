import os
import tempfile
import unittest
from pathlib import Path

from backend.processes import find_app_processes


class AppProcessTests(unittest.TestCase):
    def _process(
        self,
        root: Path,
        pid: int,
        *,
        executable: str,
        cmdline: tuple[str, ...],
        environment: dict[str, str],
    ) -> None:
        process = root / str(pid)
        process.mkdir()
        (process / "exe").symlink_to(executable)
        (process / "cmdline").write_bytes(
            b"\0".join(item.encode() for item in cmdline) + b"\0"
        )
        (process / "environ").write_bytes(
            b"\0".join(f"{key}={value}".encode() for key, value in environment.items())
            + b"\0"
        )

    def test_finds_only_exact_app_executable_and_filters_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            proc = Path(directory)
            self._process(
                proc,
                200,
                executable="/opt/codex-desktop/ChatGPT",
                cmdline=("/opt/codex-desktop/ChatGPT", "--type=browser"),
                environment={
                    "DISPLAY": ":4",
                    "XAUTHORITY": "/run/user/1000/xauth",
                    "HOME": "/home/deck",
                    "ACCOUNT_TOKEN": "must-not-leave-proc",
                },
            )
            self._process(
                proc,
                201,
                executable="/opt/codex-desktop/browser_crashpad_handler",
                cmdline=("/opt/codex-desktop/browser_crashpad_handler",),
                environment={"DISPLAY": ":4"},
            )

            result = find_app_processes(proc)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].pid, 200)
        self.assertEqual(result[0].executable, "/opt/codex-desktop/ChatGPT")
        self.assertEqual(
            result[0].environment,
            {
                "DISPLAY": ":4",
                "XAUTHORITY": "/run/user/1000/xauth",
                "HOME": "/home/deck",
            },
        )

    def test_launcher_cmdline_is_recognized_without_substring_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            proc = Path(directory)
            self._process(
                proc,
                300,
                executable="/usr/bin/bash",
                cmdline=("/usr/bin/codex-desktop",),
                environment={"DISPLAY": ":1"},
            )
            self._process(
                proc,
                301,
                executable="/usr/bin/bash",
                cmdline=("/tmp/not-codex-desktop",),
                environment={"DISPLAY": ":1"},
            )

            result = find_app_processes(proc)

        self.assertEqual([process.pid for process in result], [300])

    def test_racing_or_incomplete_process_entries_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            proc = Path(directory)
            (proc / "400").mkdir()
            (proc / "not-a-pid").mkdir()

            result = find_app_processes(proc)

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
