import os
import pwd
from collections.abc import Mapping
from pathlib import Path


_EXPLICIT_KEYS = {
    "DBUS_SESSION_BUS_ADDRESS",
    "DESKTOP_SESSION",
    "DISPLAY",
    "GDK_BACKEND",
    "HOME",
    "LANG",
    "LC_ALL",
    "LOGNAME",
    "PATH",
    "PULSE_SERVER",
    "SHELL",
    "USER",
    "WAYLAND_DISPLAY",
    "XAUTHORITY",
}
_PREFIXES = ("GAMESCOPE_", "GTK_", "QT_", "SDL_", "STEAM_", "XDG_")


def parse_environment(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}

    result: dict[str, str] = {}
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key:
            result[key] = value
    return result


def _allowed(key: str) -> bool:
    return key in _EXPLICIT_KEYS or key.startswith(_PREFIXES)


def graphical_environment(
    uid: int,
    inherited: Mapping[str, str] | None = None,
    *,
    runtime_dir: Path | None = None,
    gamescope_environment: Path | None = None,
) -> dict[str, str]:
    inherited = os.environ if inherited is None else inherited
    try:
        account = pwd.getpwuid(uid)
        default_home = account.pw_dir
        default_user = account.pw_name
    except KeyError:
        default_home = inherited.get("HOME", f"/home/{uid}")
        default_user = inherited.get("USER", str(uid))

    runtime = runtime_dir or Path(f"/run/user/{uid}")
    gamescope = gamescope_environment or runtime / "gamescope-environment"
    result = {key: value for key, value in inherited.items() if _allowed(key)}
    result.update(
        {
            key: value
            for key, value in parse_environment(gamescope).items()
            if _allowed(key)
        }
    )
    result.setdefault("HOME", default_home)
    result.setdefault("USER", default_user)
    result.setdefault("LOGNAME", default_user)
    result.setdefault("PATH", "/usr/local/bin:/usr/bin:/bin")
    result.setdefault("XDG_RUNTIME_DIR", str(runtime))

    if "XAUTHORITY" not in result:
        candidates = sorted(
            runtime.glob("xauth_*"),
            key=lambda candidate: candidate.stat().st_mtime,
            reverse=True,
        )
        if candidates:
            result["XAUTHORITY"] = str(candidates[0])
    return result
