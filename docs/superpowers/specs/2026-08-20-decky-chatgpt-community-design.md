# Decky ChatGPT Community Design

## Goal

Provide a Decky Loader panel that controls the locally installed **ChatGPT
Community** application on Steam Deck, including the application's real
Realtime Voice Mode. The plugin uses the user's existing ChatGPT sign-in and
never calls the OpenAI API or asks for an API key.

## Scope

The first release provides:

- installed, running, version, and Voice Mode compatibility status;
- open/focus ChatGPT Community;
- toggle the application's real Voice Mode;
- open a new ChatGPT conversation;
- request an update check through `codex-update-manager`;
- a distributable Decky plugin zip and a local installation helper.

The first release does not add a separate chat client, transcribe audio,
synthesize speech, automate ChatGPT's web UI, install ChatGPT Community, or
replace the application's updater.

## Upstream Contract

The signed official Linux bundle in ChatGPT Community 26.814.41957 contains
the application command `composer.startVoiceMode`. Its Linux Electron default
keybinding is `Ctrl+Shift+V`, and its user-facing description is `Start or stop
voice chat`. The command calls the bundled `realtimeVoiceRuntime`; it is not
dictation.

Version 1 uses this existing app command and therefore applies no ASAR patch.
The repository contains a compatibility verifier that checks the installed
`app.asar` for all four semantic markers before the plugin sends input:

- `composer.startVoiceMode`
- `Ctrl+Shift+V`
- `Start or stop voice chat`
- `realtimeVoiceRuntime`

Missing markers make Voice Mode unavailable and return a clear error. The
plugin must never fall back to screen coordinates or send the shortcut to an
unverified window.

`patches/` is intentionally empty except for documentation. If upstream later
removes the shortcut but retains Voice Mode, a narrowly scoped, fail-closed
overlay may be added there. The overlay must be tested against the current
official ASAR and remain separate from the upstream repository; this project
will not fork or mirror `codex-desktop-linux`.

## Architecture

### Decky frontend

`src/index.tsx` renders a compact Quick Access panel using `@decky/ui`. It
calls the Python backend through `@decky/api`, shows operation results as Decky
toasts, and refreshes status after each operation. The primary action is
labelled **Toggle Voice Mode** because the application command starts or stops
an active call.

### Python backend

`main.py` is an unprivileged Decky backend. It delegates platform mechanics to
small modules under `backend/`:

- `compatibility.py` scans `app.asar` in bounded chunks for the Voice Mode
  contract;
- `processes.py` finds the exact ChatGPT Community executable and reads only
  the display variables needed to address its X11 window;
- `desktop.py` loads the SteamOS Gamescope environment when launching the app;
- `controller.py` locates a visible `codex-desktop` window with `xdotool`,
  chooses the largest matching window, focuses it, and sends application
  shortcuts;
- `status.py` reads package and updater state with fixed argument arrays.

No backend method accepts a command, executable, environment variable name, or
shell fragment from the frontend. Subprocesses use argument arrays with
`shell=False`.

### Window and display selection

When ChatGPT is running, the controller reads `DISPLAY` and `XAUTHORITY` from
the app process environment and runs `xdotool` in that same display. This
works with SteamOS multiple-Xwayland Gamescope sessions. If the app is not yet
running, the launcher uses `/run/user/<uid>/gamescope-environment` when
available and otherwise inherits the Decky user's graphical environment.

Only visible windows whose WM class matches `codex-desktop` are candidates.
The largest candidate is selected. Voice input is never sent if compatibility,
display discovery, window discovery, or focus fails.

### Application and updater commands

- Open/focus: `/usr/bin/codex-desktop`
- Voice Mode: `Ctrl+Shift+V`
- New conversation: `Ctrl+N`
- Update state: `/usr/bin/codex-update-manager status --json`
- Update check: `/usr/bin/codex-update-manager check-now`

The plugin never uninstalls or replaces the working application. Building,
installing, and using the Decky plugin leaves the native package untouched.

## Error Handling

Backend calls return a stable object containing `ok`, `message`, and optional
status data. Expected problems—missing package, incompatible bundle, missing
`xdotool`, absent display, absent window, launch timeout, or updater failure—
are user-facing failures rather than Python exceptions crossing the Decky
bridge. Detailed diagnostics go to Decky's plugin log without logging account
data, conversation text, or process environments.

## Testing

Python unit tests use temporary fake ASAR files, process directories, Gamescope
environment files, and executable shims. Tests assert command arguments and
fail-closed behavior without controlling the real desktop.

Frontend verification consists of strict TypeScript compilation and a Rollup
production build. Release verification checks the zip layout and executes the
compatibility verifier against the installed ChatGPT Community bundle. A real
Voice Mode toggle remains an explicit manual smoke test because automated
activation would start a microphone session in the user's account.

## Distribution

GitHub releases attach `decky-chatgpt-community-<version>.zip`. The archive has
one top-level `decky-chatgpt-community/` directory containing `dist/index.js`,
`main.py`, `backend/`, `plugin.json`, `package.json`, `README.md`, and `LICENSE`.
The repository is public under `LBR88/decky-chatgpt-community`, with a clean
local clone at `/home/deck/git/decky-chatgpt-community`.
