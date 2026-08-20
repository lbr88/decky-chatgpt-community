# ChatGPT Community for Decky

A Steam Deck Quick Access plugin for the installed **ChatGPT Community** Linux
app. It opens ChatGPT, starts a new chat, checks for updates, and toggles
ChatGPT's real live Voice Mode.

This is not an API client. It uses the ChatGPT app already signed in on your
Steam Deck. There is no API key, separate account, transcription service, or
replacement voice implementation.

## Related project

This plugin controls an existing ChatGPT Community installation. Install the
app first with
**[ChatGPT Community for Steam Deck](https://github.com/LBR88/chatgpt-steam-deck)**,
then install this Decky plugin for Gaming Mode Quick Access controls. The two
repositories remain separate so the app installer and optional Decky
integration can be installed or updated independently.

## Current status

Version 0.1.6 is the current Steam Deck release. It is verified against ChatGPT
Community built from official Linux app 26.814.41957.

The official bundle already contains:

- `composer.startVoiceMode`
- the Linux shortcut `Ctrl+Shift+V`
- the description `Start or stop voice chat`
- the bundled `realtimeVoiceRuntime`

Because that is a complete callable contract, this release applies **zero app
patches**. See [the patch policy](patches/README.md).

## Requirements

- SteamOS on Steam Deck
- Decky Loader
- ChatGPT Community installed as the native `codex-desktop` package
- `/usr/bin/xdotool` (present on the tested SteamOS installation)

## Install

1. Switch the Steam Deck to **Desktop Mode**.
2. Download **[Install ChatGPT Community for Decky][desktop-installer]**.
3. Open the downloaded file and choose **Execute** if SteamOS asks.
4. Enter the Deck user's sudo password in the visible terminal when prompted.
5. Return to Gaming Mode, open Quick Access, and select **ChatGPT Community**.

The desktop installer downloads the latest plugin release, verifies its SHA-256
checksum, safely extracts it, preserves the previous plugin as a backup, and
restarts Decky Loader. It does not clone this repository.

For manual installation, download `decky-chatgpt-community.zip` and install it
with Decky Loader's plugin/developer installer.

The plugin does not uninstall or replace your working ChatGPT Community app.

## Use

- **Open ChatGPT** creates or reuses a Steam shortcut and switches to the app.
- **Toggle Voice Mode** remembers the game you are playing, briefly switches to
  ChatGPT, starts or stops its live Voice Mode, and returns to your game.
- **Check for Updates** asks the existing `codex-update-manager` to check.
- **Refresh Status** rechecks the package, process, updater, and Voice Mode
  compatibility contract.

ChatGPT remains running as a background companion after the plugin returns to
your game, so the voice session can continue while you play. Steam does not
close the original game. The Quick Access menu closes before focus-sensitive
commands. Voice Mode is disabled if the installed app no longer contains the
verified command contract. The plugin never falls back to screen coordinates.

## Local development

Use pnpm 9, matching Decky's official plugin template:

```bash
corepack pnpm@9.15.9 install --frozen-lockfile
corepack pnpm@9.15.9 run build
python -m unittest discover -s tests -v
python scripts/verify-installed-app.py
bash scripts/package-release.sh
bash scripts/install-local.sh
```

The last command only accepts the `deck` user and only writes to
`/home/deck/homebrew/plugins/decky-chatgpt-community`.

## How it works

The Decky frontend creates one native non-Steam shortcut for
`/usr/bin/codex-desktop` and launches it with `SteamClient.Apps.RunGame`. This
keeps ChatGPT in Steam's process tree, allowing Gamescope to focus its window.
The shortcut clears Steam's `LD_PRELOAD` only for the ChatGPT launch because
Steam's overlay library crashes Electron child processes on the tested SteamOS
version. Gamescope still owns and presents the app normally.
For an in-game Voice Mode toggle, the plugin records Steam's currently running
game, focuses the already-running ChatGPT shortcut without relaunching it,
invokes the verified app shortcut, then restores the recorded game even when
the operation fails.

The unprivileged Python backend finds the exact
`/opt/codex-desktop/ChatGPT` process, reads only its display-related process
environment, locates the largest visible window whose class is exactly
`codex-desktop`, focuses that window, and sends the app's own shortcut through
`xdotool`. It never launches a hidden ChatGPT process itself.

SteamOS can use multiple Xwayland displays in Gaming Mode, so the plugin uses
the display belonging to ChatGPT rather than assuming `DISPLAY=:0`. When
SteamOS masks a sibling process's environment, the backend checks only numeric
Xwayland sockets available to the session and still requires the exact
`codex-desktop` window class. If the app is not running, it launches it with
SteamOS's Gamescope environment and waits for the verified window.

## Privacy and security

- No OpenAI API calls or API keys
- No conversation, audio, or account-data access
- No shell commands supplied by the frontend
- No root Decky backend
- No screen-coordinate automation
- No copied OpenAI application payload in this repository or release zip
- Release ZIP verification before the desktop installer changes Decky files

## Troubleshooting

If Voice Mode says **Unavailable**, run:

```bash
python scripts/verify-installed-app.py /opt/codex-desktop/resources/app.asar
```

If the verifier reports missing markers, update this plugin and ChatGPT
Community. Do not force the shortcut: the compatibility gate is intentionally
fail closed.

If the first Voice Mode toggle takes several seconds, let ChatGPT finish
starting. The plugin waits up to 30 seconds for its Steam-owned window and then
returns to the game that was already running.

## License

MIT. ChatGPT, the official Linux application, and OpenAI services remain the
property of their respective owners. This is an independent community plugin.

[desktop-installer]: https://github.com/LBR88/decky-chatgpt-community/releases/latest/download/Install-ChatGPT-Community-Decky.desktop
