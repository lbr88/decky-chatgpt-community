#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
version="$(node -p "require('${repo_root}/package.json').version")"
release_root="${repo_root}/dist-release"
archive="${release_root}/decky-chatgpt-community-${version}.zip"
stage_root="$(mktemp -d /tmp/decky-chatgpt-community-release.XXXXXX)"
plugin_root="${stage_root}/decky-chatgpt-community"

cleanup() {
    rm -rf -- "${stage_root}"
}
trap cleanup EXIT

if [[ ! -f "${repo_root}/dist/index.js" ]]; then
    echo "Missing dist/index.js; run pnpm run build first." >&2
    exit 1
fi

mkdir -p "${plugin_root}/backend" "${plugin_root}/dist" "${plugin_root}/assets" "${release_root}"

install -m 0644 "${repo_root}/dist/index.js" "${plugin_root}/dist/index.js"
install -m 0644 "${repo_root}/main.py" "${plugin_root}/main.py"
install -m 0644 "${repo_root}/plugin.json" "${plugin_root}/plugin.json"
install -m 0644 "${repo_root}/package.json" "${plugin_root}/package.json"
install -m 0644 "${repo_root}/README.md" "${plugin_root}/README.md"
install -m 0644 "${repo_root}/LICENSE" "${plugin_root}/LICENSE"
install -m 0644 "${repo_root}/assets/logo.svg" "${plugin_root}/assets/logo.svg"

for module in __init__ compatibility controller desktop models processes status; do
    install -m 0644 "${repo_root}/backend/${module}.py" "${plugin_root}/backend/${module}.py"
done

(cd "${stage_root}" && python -m zipfile -c "${archive}" decky-chatgpt-community)
printf '%s\n' "${archive}"
