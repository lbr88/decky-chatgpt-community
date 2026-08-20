import tempfile
import unittest
from pathlib import Path

from backend.desktop import graphical_environment, parse_environment


class DesktopEnvironmentTests(unittest.TestCase):
    def test_parse_environment_does_not_evaluate_values(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "environment")
            source.write_text(
                "\n# ignored\nDISPLAY=:3\nDBUS_SESSION_BUS_ADDRESS=unix:path=/run/a=b\nINVALID\n",
                encoding="utf-8",
            )

            result = parse_environment(source)

        self.assertEqual(
            result,
            {
                "DISPLAY": ":3",
                "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/a=b",
            },
        )

    def test_gamescope_values_override_inherited_graphics_without_copying_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            gamescope = runtime / "gamescope-environment"
            gamescope.write_text(
                "DISPLAY=:7\nXDG_RUNTIME_DIR=/run/user/1000\nSTEAM_GAMESCOPE_HDR_SUPPORTED=1\nUNRELATED_SECRET=do-not-copy\n",
                encoding="utf-8",
            )
            xauth = runtime / "xauth_current"
            xauth.write_text("cookie", encoding="utf-8")

            result = graphical_environment(
                1000,
                {
                    "HOME": "/home/deck",
                    "PATH": "/usr/bin",
                    "DISPLAY": ":0",
                    "UNRELATED_SECRET": "also-do-not-copy",
                },
                runtime_dir=runtime,
                gamescope_environment=gamescope,
            )

        self.assertEqual(result["DISPLAY"], ":7")
        self.assertEqual(result["HOME"], "/home/deck")
        self.assertEqual(result["PATH"], "/usr/bin")
        self.assertEqual(result["XAUTHORITY"], str(xauth))
        self.assertEqual(result["STEAM_GAMESCOPE_HDR_SUPPORTED"], "1")
        self.assertNotIn("UNRELATED_SECRET", result)

    def test_inherited_graphical_environment_is_used_without_gamescope_file(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            result = graphical_environment(
                1000,
                {
                    "HOME": "/home/deck",
                    "PATH": "/usr/bin",
                    "DISPLAY": ":2",
                    "XAUTHORITY": "/tmp/auth",
                    "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/1000/bus",
                },
                runtime_dir=runtime,
                gamescope_environment=runtime / "missing",
            )

        self.assertEqual(result["DISPLAY"], ":2")
        self.assertEqual(result["XAUTHORITY"], "/tmp/auth")
        self.assertEqual(
            result["DBUS_SESSION_BUS_ADDRESS"], "unix:path=/run/user/1000/bus"
        )


if __name__ == "__main__":
    unittest.main()
