#!/usr/bin/env bash
set -euo pipefail

repository="LBR88/decky-chatgpt-community"
release_base="${CHATGPT_DECKY_RELEASE_BASE_URL:-https://github.com/${repository}/releases/latest/download}"
plugin_parent="${CHATGPT_DECKY_PLUGIN_ROOT:-/home/deck/homebrew/plugins}"
plugin_name="decky-chatgpt-community"
plugin_target="${plugin_parent}/${plugin_name}"
plugin_home="$(dirname "${plugin_parent}")"
staging_parent="${plugin_home}/.${plugin_name}-staging"
backup_parent="${plugin_home}/.${plugin_name}-backups"
temporary_root="$(mktemp -d /tmp/decky-chatgpt-community-install.XXXXXX)"
incoming=""
previous=""
replacement_state="staging"

run_privileged() {
    if [[ -n "${CHATGPT_DECKY_TEST_MODE:-}" ]]; then
        "$@"
    else
        sudo "$@"
    fi
}

cleanup() {
    rm -rf -- "${temporary_root}"
    if [[ -n "${incoming}" && -e "${incoming}" ]]; then
        if [[ "${replacement_state}" == "exchanged" \
            && -n "${previous}" && ! -e "${previous}" ]]; then
            run_privileged mv -- "${incoming}" "${previous}"
        else
            run_privileged rm -rf -- "${incoming}"
        fi
    fi
}
trap cleanup EXIT

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

if [[ "$(id -u)" -eq 0 ]]; then
    fail "Run this installer as the deck user, not root."
fi
if [[ -z "${CHATGPT_DECKY_TEST_MODE:-}" ]]; then
    [[ "${HOME:-}" == "/home/deck" ]] \
        || fail "This installer supports the deck user on SteamOS."
    [[ "${plugin_parent}" == "/home/deck/homebrew/plugins" ]] \
        || fail "Refusing unexpected Decky plugin directory: ${plugin_parent}"
fi

required_commands=(python3 sha256sum)
if [[ -z "${CHATGPT_DECKY_TEST_MODE:-}" ]]; then
    required_commands+=(curl sudo)
fi
for command in "${required_commands[@]}"; do
    command -v "${command}" >/dev/null || fail "Missing required command: ${command}"
done
[[ -d "${plugin_parent}" ]] || fail "Decky Loader was not found at ${plugin_parent}"

assets=("decky-chatgpt-community.zip" "SHA256SUMS")
for asset in "${assets[@]}"; do
    echo "Downloading ${asset}"
    if [[ -n "${CHATGPT_DECKY_TEST_MODE:-}" ]]; then
        install -m 0600 "${release_base}/${asset}" "${temporary_root}/${asset}"
    else
        curl --proto '=https' --tlsv1.2 --fail --location --silent --show-error \
            --retry 3 --output "${temporary_root}/${asset}" \
            "${release_base}/${asset}"
    fi
done

expected="$(awk '$2 == "decky-chatgpt-community.zip" { print $1 }' \
    "${temporary_root}/SHA256SUMS")"
[[ "${expected}" =~ ^[0-9a-f]{64}$ ]] \
    || fail "Missing checksum for decky-chatgpt-community.zip"
actual="$(sha256sum "${temporary_root}/decky-chatgpt-community.zip" | awk '{ print $1 }')"
[[ "${actual}" == "${expected}" ]] \
    || fail "Checksum mismatch for decky-chatgpt-community.zip"

python3 - "${temporary_root}/decky-chatgpt-community.zip" \
    "${temporary_root}/plugin" <<'PY'
import pathlib
import stat
import sys
import zipfile

archive = pathlib.Path(sys.argv[1])
destination = pathlib.Path(sys.argv[2])
destination.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(archive) as source:
    for entry in source.infolist():
        path = pathlib.PurePosixPath(entry.filename)
        mode = entry.external_attr >> 16
        if path.is_absolute() or ".." in path.parts or stat.S_ISLNK(mode):
            raise SystemExit(f"Unsafe archive entry: {entry.filename}")
    source.extractall(destination)
PY

staged_plugin="${temporary_root}/plugin/${plugin_name}"
[[ -f "${staged_plugin}/plugin.json" \
    && -f "${staged_plugin}/package.json" \
    && -f "${staged_plugin}/main.py" \
    && -f "${staged_plugin}/dist/index.js" ]] \
    || fail "Plugin archive is incomplete"

staged_version="$(python3 -c \
    'import json,sys; print(json.load(open(sys.argv[1]))["version"])' \
    "${staged_plugin}/package.json")"
installed_version=""
if [[ -f "${plugin_target}/package.json" ]]; then
    installed_version="$(python3 -c \
        'import json,sys; print(json.load(open(sys.argv[1])).get("version", ""))' \
        "${plugin_target}/package.json" 2>/dev/null || true)"
fi

plugin_trees_match() {
    python3 - "$1" "$2" <<'PY'
import hashlib
import pathlib
import sys

expected_root = pathlib.Path(sys.argv[1])
installed_root = pathlib.Path(sys.argv[2])
for expected in expected_root.rglob("*"):
    if not expected.is_file():
        continue
    relative = expected.relative_to(expected_root)
    installed = installed_root / relative
    if installed.is_symlink() or not installed.is_file():
        raise SystemExit(1)
    expected_hash = hashlib.sha256(expected.read_bytes()).digest()
    installed_hash = hashlib.sha256(installed.read_bytes()).digest()
    if installed_hash != expected_hash:
        raise SystemExit(1)
PY
}

if [[ "${installed_version}" == "${staged_version}" ]] \
    && plugin_trees_match "${staged_plugin}" "${plugin_target}"; then
    echo "ChatGPT Community plugin ${staged_version} is already installed; skipping."
    echo "Everything is already up to date."
    exit 0
fi

if [[ -z "${CHATGPT_DECKY_TEST_MODE:-}" ]]; then
    sudo -v
fi
incoming="${staging_parent}/${plugin_name}.installing.$$"
run_privileged install -d -m 0755 "${staging_parent}"
run_privileged install -d -m 0755 "${incoming}"
run_privileged cp -a "${staged_plugin}/." "${incoming}/"
if [[ -z "${CHATGPT_DECKY_TEST_MODE:-}" ]]; then
    run_privileged chown -R root:root "${incoming}"
fi
run_privileged find "${incoming}" -type d -exec chmod 0755 '{}' +
run_privileged find "${incoming}" -type f -exec chmod 0644 '{}' +

if [[ -e "${plugin_target}" ]]; then
    run_privileged install -d -m 0755 "${backup_parent}"
    previous="${backup_parent}/${plugin_name}-$(date -u +%Y%m%dT%H%M%SZ)-$$"
    if ! run_privileged python3 - "${incoming}" "${plugin_target}" <<'PY'
import ctypes
import os
import sys

source = os.fsencode(sys.argv[1])
target = os.fsencode(sys.argv[2])
libc = ctypes.CDLL(None, use_errno=True)
renameat2 = libc.renameat2
renameat2.argtypes = [
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_uint,
]
renameat2.restype = ctypes.c_int
if renameat2(-100, source, -100, target, 2) != 0:
    error = ctypes.get_errno()
    raise OSError(error, os.strerror(error))
PY
    then
        fail "Could not atomically replace the Decky plugin"
    fi
    replacement_state="exchanged"
    run_privileged mv -- "${incoming}" "${previous}"
else
    run_privileged mv -- "${incoming}" "${plugin_target}"
fi
incoming=""
replacement_state="complete"
echo "Installed ChatGPT Community plugin ${staged_version} at ${plugin_target}"
if [[ -n "${previous}" ]]; then
    echo "Previous plugin preserved at ${previous}"
fi

if [[ -z "${CHATGPT_DECKY_SKIP_SERVICE_RESTART:-}" ]]; then
    sudo systemctl restart plugin_loader.service
    echo "Restarted Decky Loader."
fi
echo "Installation complete. Return to Gaming Mode and open ChatGPT Community in Quick Access."
