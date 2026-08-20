import logging
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class PluginImportTests(unittest.TestCase):
    def test_main_loads_when_decky_uses_a_foreign_working_directory(self):
        loader = textwrap.dedent(
            """
            import logging
            import runpy
            import sys
            import types

            decky = types.ModuleType("decky")
            decky.logger = logging.getLogger("decky-import-test")
            sys.modules["decky"] = decky
            runpy.run_path(sys.argv[1], run_name="decky_plugin_main")
            """
        )
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-c", loader, str(ROOT / "main.py")],
                cwd=directory,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
