# Patch policy

There is currently **no ChatGPT application patch** in this repository.

The official Linux bundle already exposes its real Realtime Voice Mode through
the application command `composer.startVoiceMode`, bound to `Ctrl+Shift+V`.
The Decky plugin verifies that semantic contract and invokes the command in the
exact `codex-desktop` window.

If an upstream release removes the shortcut while retaining Voice Mode, this
directory may contain a minimal `linux-features/` overlay plus fail-closed tests
for the latest official ASAR. It must not contain an upstream source mirror,
generated app bundle, account data, or copied proprietary payload.
