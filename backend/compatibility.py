from dataclasses import dataclass
from pathlib import Path


VOICE_MARKERS = (
    b"composer.startVoiceMode",
    b"Ctrl+Shift+V",
    b"Start or stop voice chat",
    b"realtimeVoiceRuntime",
)


@dataclass(frozen=True)
class VoiceContract:
    compatible: bool
    missing: tuple[str, ...]
    message: str


def check_voice_contract(app_asar: Path) -> VoiceContract:
    marker_names = tuple(marker.decode("utf-8") for marker in VOICE_MARKERS)
    try:
        source = app_asar.open("rb")
    except OSError:
        return VoiceContract(False, marker_names, f"App bundle not found: {app_asar}")

    found: set[bytes] = set()
    chunk_size = 1024 * 1024
    overlap_size = max(map(len, VOICE_MARKERS)) - 1
    tail = b""

    try:
        with source:
            while chunk := source.read(chunk_size):
                window = tail + chunk
                for marker in VOICE_MARKERS:
                    if marker not in found and marker in window:
                        found.add(marker)
                if len(found) == len(VOICE_MARKERS):
                    break
                tail = window[-overlap_size:]
    except OSError as error:
        return VoiceContract(False, marker_names, f"Could not read app bundle: {error}")

    missing = tuple(
        marker.decode("utf-8") for marker in VOICE_MARKERS if marker not in found
    )
    if missing:
        return VoiceContract(
            False,
            missing,
            f"Realtime Voice Mode is incompatible: missing {len(missing)} required markers",
        )
    return VoiceContract(True, (), "Realtime Voice Mode is compatible")
