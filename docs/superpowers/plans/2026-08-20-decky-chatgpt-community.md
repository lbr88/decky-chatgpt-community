# Decky ChatGPT Community Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish a Decky Loader plugin that controls the installed ChatGPT Community app and toggles its bundled Realtime Voice Mode without an API or upstream fork.

**Architecture:** An unprivileged Python backend discovers the app's graphical session, verifies the official Voice Mode command contract, and invokes fixed app shortcuts through `xdotool`. A TypeScript Decky panel exposes those operations and status. The repository carries no ASAR patch while the upstream contract exists, but reserves a tested fail-closed patch layer for future drift.

**Tech Stack:** Python 3.11 standard library, pytest-compatible unittest tests, TypeScript 5, React 19 types, `@decky/api`, `@decky/ui`, Rollup, pnpm, Bash release packaging.

**Spec:** `docs/superpowers/specs/2026-08-20-decky-chatgpt-community-design.md`

## Global Constraints

- Use the installed ChatGPT Community app and the user's existing account; never call the OpenAI API.
- Keep `codex-desktop-linux` upstream history out of this repository.
- Apply no ASAR patch while `composer.startVoiceMode` and its `Ctrl+Shift+V` binding exist.
- Fail closed before sending keyboard input if the Voice Mode contract or exact `codex-desktop` window cannot be verified.
- Run the Decky backend without `_root` and never invoke a shell with frontend-controlled text.
- Do not uninstall, replace, or rebuild the working ChatGPT Community package.

---

### Task 1: Compatibility and environment core

**Files:**
- Create: `backend/__init__.py`
- Create: `backend/compatibility.py`
- Create: `backend/desktop.py`
- Test: `tests/test_compatibility.py`
- Test: `tests/test_desktop.py`

**Interfaces:**
- Produces: `check_voice_contract(path: Path) -> VoiceContract`
- Produces: `parse_environment(path: Path) -> dict[str, str]`
- Produces: `graphical_environment(uid: int, inherited: Mapping[str, str]) -> dict[str, str]`

- [ ] **Step 1: Write failing compatibility tests**

Create tests asserting that all four markers return a compatible result,
missing markers are listed, chunk boundaries are handled, and a missing file
returns an incompatible result.

- [ ] **Step 2: Run compatibility tests and verify RED**

Run: `python -m unittest tests.test_compatibility -v`

Expected: import failure because `backend.compatibility` does not exist.

- [ ] **Step 3: Implement bounded marker scanning**

Implement immutable `VoiceContract(compatible: bool, missing: tuple[str, ...], message: str)` and scan the ASAR in 1 MiB chunks with enough overlap for the longest marker.

- [ ] **Step 4: Run compatibility tests and verify GREEN**

Run: `python -m unittest tests.test_compatibility -v`

Expected: all compatibility tests pass.

- [ ] **Step 5: Write failing environment tests**

Create tests for comments and blank lines, values containing `=`, Gamescope
overrides, fallback inheritance, and Xauthority discovery.

- [ ] **Step 6: Run environment tests and verify RED**

Run: `python -m unittest tests.test_desktop -v`

Expected: import failure because `backend.desktop` does not exist.

- [ ] **Step 7: Implement environment discovery and verify GREEN**

Parse fixed key/value files without evaluating them. Copy only graphical and
session variables into a new environment and discover `xauth_*` under the
matching runtime directory when `XAUTHORITY` is absent.

- [ ] **Step 8: Commit the core**

Stage only the task files and commit `feat: verify ChatGPT voice compatibility`.

### Task 2: Process, window, and updater controller

**Files:**
- Create: `backend/processes.py`
- Create: `backend/controller.py`
- Create: `backend/status.py`
- Test: `tests/test_processes.py`
- Test: `tests/test_controller.py`
- Test: `tests/test_status.py`

**Interfaces:**
- Produces: `find_app_processes(proc_root: Path = Path('/proc')) -> list[AppProcess]`
- Produces: `ChatGPTController.status() -> dict[str, object]`
- Produces: `ChatGPTController.open_app() -> OperationResult`
- Produces: `ChatGPTController.toggle_voice() -> OperationResult`
- Produces: `ChatGPTController.new_chat() -> OperationResult`
- Produces: `ChatGPTController.check_updates() -> OperationResult`

- [ ] **Step 1: Write and run failing process tests**

Use a fake proc tree to cover exact executable matching, NUL-separated
environment parsing, inaccessible entries, and helper-process exclusion. Run
`python -m unittest tests.test_processes -v` and confirm the missing-module
failure.

- [ ] **Step 2: Implement exact process discovery and verify GREEN**

Match `/opt/codex-desktop/ChatGPT` and `/usr/bin/codex-desktop`, expose only
PID plus display variables, and tolerate races while processes exit.

- [ ] **Step 3: Write and run failing controller tests**

Use an injected command runner and clock to assert largest-window selection,
exact class search, focus-before-key ordering, launch polling, compatibility
gating, and fixed shortcuts. Confirm failure because the controller is absent.

- [ ] **Step 4: Implement the minimal controller and verify GREEN**

Run `xdotool` with argument arrays, select the largest visible candidate, and
return `OperationResult(ok: bool, message: str)` for expected failures.

- [ ] **Step 5: Write and run failing updater tests**

Assert package-version parsing, JSON updater status parsing, missing commands,
nonzero exits, and fixed `check-now` arguments.

- [ ] **Step 6: Implement updater status and verify GREEN**

Use `pacman -Q codex-desktop`, `codex-update-manager status --json`, and
`codex-update-manager check-now` with timeouts and no shell.

- [ ] **Step 7: Run the complete Python suite and commit**

Run: `python -m unittest discover -s tests -v`

Expected: all tests pass. Commit `feat: control ChatGPT from Decky`.

### Task 3: Decky backend bridge and panel

**Files:**
- Create: `main.py`
- Create: `src/index.tsx`
- Create: `src/types.d.ts`
- Create: `plugin.json`
- Create: `package.json`
- Create: `tsconfig.json`
- Create: `rollup.config.js`
- Create: `tests/test_plugin_bridge.py`

**Interfaces:**
- Consumes: `ChatGPTController` public methods from Task 2
- Produces: Decky callable methods `get_status`, `open_app`, `toggle_voice`, `new_chat`, and `check_updates`

- [ ] **Step 1: Write and run failing bridge tests**

Load `main.py` with a temporary `decky` stub and assert each async bridge
method returns the controller result as JSON-compatible dictionaries. Confirm
the missing-file failure.

- [ ] **Step 2: Implement the backend bridge and verify GREEN**

Instantiate one controller in `_main`, log only operation names and results,
and expose the five fixed methods.

- [ ] **Step 3: Add the Decky manifest and build configuration**

Use plugin name `ChatGPT Community`, author `LBR88`, API version 1, no `_root`
flag, strict TypeScript, and the official `@decky/rollup` configuration.

- [ ] **Step 4: Implement the typed panel**

Render status, Open ChatGPT, Toggle Voice Mode, New Chat, Check for Updates,
and Refresh controls. Disable Voice Mode when compatibility is false, close
the Quick Access menu before focus-sensitive actions, and show result toasts.

- [ ] **Step 5: Install dependencies and build**

Run: `pnpm install --frozen-lockfile` after generating the lockfile once.

Run: `pnpm run build`

Expected: `dist/index.js` builds with no TypeScript or Rollup errors.

- [ ] **Step 6: Run all tests and commit**

Run the Python suite and frontend build, then commit `feat: add Decky control panel`.

### Task 4: Packaging, documentation, and publication

**Files:**
- Create: `scripts/verify-installed-app.py`
- Create: `scripts/package-release.sh`
- Create: `scripts/install-local.sh`
- Create: `tests/test_release_scripts.py`
- Create: `patches/README.md`
- Create: `README.md`
- Create: `LICENSE`
- Create: `.gitignore`
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: built `dist/index.js` and backend files
- Produces: `dist-release/decky-chatgpt-community-<version>.zip`

- [ ] **Step 1: Write and run failing release tests**

Assert the compatibility CLI exit codes, release zip allowlist and top-level
directory, safe local install target validation, and absence of generated
dependencies from the archive.

- [ ] **Step 2: Implement verification and packaging scripts**

The verifier calls the same Python contract code. The packager uses an
explicit allowlist. The local installer copies only into
`$HOME/homebrew/plugins/decky-chatgpt-community` and refuses root or an
unexpected home path.

- [ ] **Step 3: Document installation and the zero-patch design**

Explain prerequisites, GitHub zip installation, local development, real Voice
Mode behavior, current compatibility markers, troubleshooting, privacy, and
why `patches/` is empty.

- [ ] **Step 4: Add continuous integration**

Run Python tests, dependency installation, TypeScript build, release packaging,
and archive layout verification on pushes and pull requests.

- [ ] **Step 5: Verify the installed official bundle**

Run: `python scripts/verify-installed-app.py /opt/codex-desktop/resources/app.asar`

Expected: compatible with all four Voice Mode markers.

- [ ] **Step 6: Perform complete release verification**

Run: `python -m unittest discover -s tests -v`, `pnpm run build`,
`bash scripts/package-release.sh`, `git diff --check`, and inspect the zip
listing. Do not automatically toggle Voice Mode.

- [ ] **Step 7: Commit, publish, and install locally**

Inspect staged scope, commit `chore: prepare initial Decky release`, fast-forward
`main`, create public `LBR88/decky-chatgpt-community`, push `main`, publish an
initial release with the verified zip, clone it to
`/home/deck/git/decky-chatgpt-community`, and install the same archive into the
local Decky plugin directory without changing ChatGPT Community.
