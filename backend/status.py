import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .models import OperationResult


Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class PackageInfo:
    installed: bool
    version: str | None


def _run(runner: Runner, command: tuple[str, ...]) -> subprocess.CompletedProcess[str] | None:
    try:
        return runner(command, capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError):
        return None


def read_package_info(runner: Runner = subprocess.run) -> PackageInfo:
    result = _run(runner, ("/usr/bin/pacman", "-Q", "codex-desktop"))
    if result is None or result.returncode != 0:
        return PackageInfo(False, None)
    fields = result.stdout.strip().split()
    if len(fields) != 2 or fields[0] != "codex-desktop":
        return PackageInfo(False, None)
    return PackageInfo(True, fields[1])


def read_updater_status(runner: Runner = subprocess.run) -> dict[str, Any] | None:
    result = _run(
        runner,
        ("/usr/bin/codex-update-manager", "status", "--json"),
    )
    if result is None or result.returncode != 0:
        return None
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def request_update_check(runner: Runner = subprocess.run) -> OperationResult:
    result = _run(runner, ("/usr/bin/codex-update-manager", "check-now"))
    if result is None:
        return OperationResult(False, "Could not run the ChatGPT Community updater")
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown updater error"
        return OperationResult(False, f"Update check failed: {detail}")
    message = result.stdout.strip() or "Update check requested"
    return OperationResult(True, message)
