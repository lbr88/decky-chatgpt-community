import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from backend.compatibility import VOICE_MARKERS


ROOT = Path(__file__).parents[1]


class ReleaseScriptTests(unittest.TestCase):
    def test_verifier_exit_code_tracks_real_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            app_asar = Path(directory, "app.asar")
            app_asar.write_bytes(b"|".join(VOICE_MARKERS))

            compatible = subprocess.run(
                [sys.executable, "scripts/verify-installed-app.py", str(app_asar)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            app_asar.write_bytes(VOICE_MARKERS[0])
            incompatible = subprocess.run(
                [sys.executable, "scripts/verify-installed-app.py", str(app_asar)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(compatible.returncode, 0)
        self.assertIn("compatible", compatible.stdout.lower())
        self.assertEqual(incompatible.returncode, 1)
        self.assertIn("missing", incompatible.stderr.lower())

    def test_release_archive_contains_only_runtime_allowlist(self):
        build = subprocess.run(
            ["bash", "scripts/package-release.sh"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(build.returncode, 0, build.stderr)
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        archive = (
            ROOT
            / "dist-release"
            / f"decky-chatgpt-community-{package['version']}.zip"
        )
        self.assertTrue(archive.is_file())

        with zipfile.ZipFile(archive) as bundle:
            names = set(bundle.namelist())

        prefix = "decky-chatgpt-community/"
        required = {
            f"{prefix}dist/index.js",
            f"{prefix}main.py",
            f"{prefix}backend/controller.py",
            f"{prefix}plugin.json",
            f"{prefix}package.json",
            f"{prefix}README.md",
            f"{prefix}LICENSE",
        }
        self.assertTrue(required.issubset(names))
        self.assertFalse(any("node_modules" in name for name in names))
        self.assertFalse(any("__pycache__" in name for name in names))
        self.assertTrue(all(name.startswith(prefix) for name in names))

    def test_local_installer_rejects_an_unexpected_home(self):
        with tempfile.TemporaryDirectory() as directory:
            environment = os.environ.copy()
            environment["HOME"] = directory
            result = subprocess.run(
                ["bash", "scripts/install-local.sh"],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("/home/deck", result.stderr)


if __name__ == "__main__":
    unittest.main()
