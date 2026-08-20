# ChatGPT Community for Decky

A Steam Deck Quick Access plugin for the installed **ChatGPT Community** Linux
app. It opens ChatGPT, starts a new chat, checks for updates, and toggles
ChatGPT's real live Voice Mode.

This is not an API client. It uses the ChatGPT app already signed in on your
Steam Deck. There is no API key, separate account, transcription service, or
replacement voice implementation.

## Current status

Version 0.1.1 is the initial Steam Deck release. It is verified against ChatGPT
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

The installer for ChatGPT Community is maintained separately at
[LBR88/chatgpt-steam-deck](https://github.com/LBR88/chatgpt-steam-deck).

## Install

1. Download the `decky-chatgpt-community-*.zip` file from the latest GitHub release.
2. Install the zip with Decky Loader's plugin/developer installer.
3. Restart Decky Loader if the plugin does not appear immediately.
4. Open Quick Access and select **ChatGPT Community**.

The plugin does not uninstall or replace your working ChatGPT Community app.

## Use

- **Open ChatGPT** launches or focuses the installed app.
- **Toggle Voice Mode** starts or stops ChatGPT's live Voice Mode.
- **New Chat** opens a new ChatGPT conversation.
- **Check for Updates** asks the existing `codex-update-manager` to check.
- **Refresh Status** rechecks the package, process, updater, and Voice Mode
  compatibility contract.

The Quick Access menu closes before focus-sensitive commands. Voice Mode is
disabled if the installed app no longer contains the verified command contract.
The plugin never falls back to screen coordinates.

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

The unprivileged Python backend finds the exact
`/opt/codex-desktop/ChatGPT` process, reads only its display-related process
environment, locates the largest visible window whose class is exactly
`codex-desktop`, focuses that window, and sends the app's own shortcut through
`xdotool`.

SteamOS can use multiple Xwayland displays in Gaming Mode, so the plugin uses
the display belonging to ChatGPT rather than assuming `DISPLAY=:0`. If the app
is not running, it launches it with SteamOS's Gamescope environment and waits
for the verified window.

## Privacy and security

- No OpenAI API calls or API keys
- No conversation, audio, or account-data access
- No shell commands supplied by the frontend
- No root Decky backend
- No screen-coordinate automation
- No copied OpenAI application payload in this repository or release zip

## Troubleshooting

If Voice Mode says **Unavailable**, run:

```bash
python scripts/verify-installed-app.py /opt/codex-desktop/resources/app.asar
```

If the verifier reports missing markers, update this plugin and ChatGPT
Community. Do not force the shortcut: the compatibility gate is intentionally
fail closed.

If ChatGPT opens but is not visible in Gaming Mode, add ChatGPT Community as a
non-Steam shortcut and launch it once from Steam so Gamescope owns its window.

## License

MIT. ChatGPT, the official Linux application, and OpenAI services remain the
property of their respective owners. This is an independent community plugin.
