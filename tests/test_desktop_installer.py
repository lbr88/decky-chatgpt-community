from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DesktopInstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.release = self.root / "release"
        self.plugin_parent = self.root / "plugins"
        self.release.mkdir()
        self.plugin_parent.mkdir()
        self.version = "0.1.3"
        self._create_release(self.version)
        self.environment = {
            **os.environ,
            "CHATGPT_DECKY_TEST_MODE": "1",
            "CHATGPT_DECKY_RELEASE_BASE_URL": str(self.release),
            "CHATGPT_DECKY_PLUGIN_ROOT": str(self.plugin_parent),
            "CHATGPT_DECKY_SKIP_SERVICE_RESTART": "1",
        }

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _create_release(self, version: str) -> None:
        stage = self.root / "stage/decky-chatgpt-community"
        (stage / "backend").mkdir(parents=True)
        (stage / "dist").mkdir()
        (stage / "plugin.json").write_text(
            json.dumps({"name": "ChatGPT Community", "flags": []}),
            encoding="utf-8",
        )
        (stage / "package.json").write_text(
            json.dumps({"version": version}), encoding="utf-8"
        )
        (stage / "main.py").write_text("class Plugin: pass\n", encoding="utf-8")
        (stage / "dist/index.js").write_text(
            "export default {};\n", encoding="utf-8"
        )
        (stage / "backend/__init__.py").write_text("", encoding="utf-8")

        archive = self.release / "decky-chatgpt-community.zip"
        with zipfile.ZipFile(archive, "w") as bundle:
            for path in sorted(stage.parent.rglob("*")):
                bundle.write(path, path.relative_to(stage.parent))
        (self.release / "SHA256SUMS").write_text(
            f"{sha256(archive)} decky-chatgpt-community.zip\n",
            encoding="utf-8",
        )

    def _run_installer(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(ROOT / "scripts/install.sh")],
            env=self.environment,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_install_and_repeat_are_safe_and_idempotent(self) -> None:
        first = self._run_installer()
        self.assertEqual(first.returncode, 0, first.stderr)
        installed = self.plugin_parent / "decky-chatgpt-community"
        self.assertEqual(
            json.loads((installed / "package.json").read_text())["version"],
            self.version,
        )
        self.assertTrue((installed / "dist/index.js").is_file())

        second = self._run_installer()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn(f"plugin {self.version} is already installed", second.stdout)
        self.assertIn("Everything is already up to date", second.stdout)
        self.assertFalse((self.plugin_parent / ".backups").exists())

    def test_same_version_with_missing_runtime_file_is_repaired(self) -> None:
        first = self._run_installer()
        self.assertEqual(first.returncode, 0, first.stderr)
        installed = self.plugin_parent / "decky-chatgpt-community"
        (installed / "dist/index.js").unlink()

        repaired = self._run_installer()

        self.assertEqual(repaired.returncode, 0, repaired.stderr)
        self.assertTrue((installed / "dist/index.js").is_file())
        self.assertNotIn("already installed", repaired.stdout)

    def test_unsafe_archive_entry_is_rejected(self) -> None:
        archive = self.release / "decky-chatgpt-community.zip"
        with zipfile.ZipFile(archive, "w") as bundle:
            bundle.writestr("../outside-plugin", "unsafe")
        (self.release / "SHA256SUMS").write_text(
            f"{sha256(archive)} decky-chatgpt-community.zip\n",
            encoding="utf-8",
        )

        result = self._run_installer()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unsafe archive entry", result.stderr)
        self.assertFalse((self.root / "outside-plugin").exists())

    def test_checksum_mismatch_is_rejected_before_installation(self) -> None:
        (self.release / "SHA256SUMS").write_text(
            f"{'0' * 64} decky-chatgpt-community.zip\n", encoding="utf-8"
        )

        result = self._run_installer()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Checksum mismatch", result.stderr)
        self.assertFalse(
            (self.plugin_parent / "decky-chatgpt-community").exists()
        )

    def test_existing_older_plugin_is_preserved_as_a_backup(self) -> None:
        installed = self.plugin_parent / "decky-chatgpt-community"
        installed.mkdir()
        (installed / "package.json").write_text(
            json.dumps({"version": "0.1.2"}), encoding="utf-8"
        )
        (installed / "old-marker").write_text("previous", encoding="utf-8")

        result = self._run_installer()

        self.assertEqual(result.returncode, 0, result.stderr)
        backup_parent = self.root / ".decky-chatgpt-community-backups"
        backups = list(backup_parent.iterdir())
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / "old-marker").read_text(), "previous")
        self.assertEqual(
            {path.name for path in self.plugin_parent.iterdir()},
            {"decky-chatgpt-community"},
        )

    def test_desktop_bootstrapper_downloads_matching_versioned_installer(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        desktop = ROOT / "Install-ChatGPT-Community-Decky.desktop"
        contents = desktop.read_text(encoding="utf-8")

        self.assertIn("Terminal=false", contents)
        self.assertIn(
            f"decky-chatgpt-community/v{package['version']}/scripts/install.sh",
            contents,
        )
        self.assertNotIn("| bash", contents)


if __name__ == "__main__":
    unittest.main()
