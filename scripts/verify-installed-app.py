#!/usr/bin/env python3
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from backend.compatibility import check_voice_contract  # noqa: E402


def main() -> int:
    app_asar = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("/opt/codex-desktop/resources/app.asar")
    )
    result = check_voice_contract(app_asar)
    if result.compatible:
        print(f"OK: {result.message}: {app_asar}")
        return 0
    print(f"ERROR: {result.message}: {app_asar}", file=sys.stderr)
    if result.missing:
        print(f"Missing: {', '.join(result.missing)}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
