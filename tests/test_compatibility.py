import tempfile
import unittest
from pathlib import Path

from backend.compatibility import VOICE_MARKERS, check_voice_contract


class VoiceCompatibilityTests(unittest.TestCase):
    def test_all_markers_make_bundle_compatible(self):
        with tempfile.TemporaryDirectory() as directory:
            app_asar = Path(directory, "app.asar")
            app_asar.write_bytes(b" prefix ".join(VOICE_MARKERS))

            result = check_voice_contract(app_asar)

        self.assertTrue(result.compatible)
        self.assertEqual(result.missing, ())
        self.assertEqual(result.message, "Realtime Voice Mode is compatible")

    def test_missing_markers_are_reported_without_guessing(self):
        with tempfile.TemporaryDirectory() as directory:
            app_asar = Path(directory, "app.asar")
            app_asar.write_bytes(VOICE_MARKERS[0] + b" and nothing else")

            result = check_voice_contract(app_asar)

        self.assertFalse(result.compatible)
        self.assertEqual(
            result.missing,
            ("Ctrl+Shift+V", "Start or stop voice chat", "realtimeVoiceRuntime"),
        )
        self.assertIn("3 required markers", result.message)

    def test_marker_split_across_chunk_boundary_is_found(self):
        chunk_size = 1024 * 1024
        payload = bytearray(b"x" * (chunk_size - 5))
        payload.extend(VOICE_MARKERS[0])
        for marker in VOICE_MARKERS[1:]:
            payload.extend(b"|")
            payload.extend(marker)

        with tempfile.TemporaryDirectory() as directory:
            app_asar = Path(directory, "app.asar")
            app_asar.write_bytes(payload)

            result = check_voice_contract(app_asar)

        self.assertTrue(result.compatible)

    def test_missing_bundle_is_an_incompatible_result(self):
        result = check_voice_contract(Path("/definitely/missing/app.asar"))

        self.assertFalse(result.compatible)
        self.assertEqual(result.missing, tuple(marker.decode() for marker in VOICE_MARKERS))
        self.assertIn("not found", result.message)


if __name__ == "__main__":
    unittest.main()
