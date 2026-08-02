# Platform strategy

pmgo ships desktop-first while keeping its product protocol portable to mobile.
The goal is to reuse domain behavior and UI flows without forcing every platform
to run the current Python sidecar.

## Product surfaces

| Phase | Shell | Local core | Status |
| --- | --- | --- | --- |
| macOS / Windows / Linux | Electron | Bundled Python sidecar + SQLite | Current focus |
| Android / iOS | Web UI in a native shell | Native SQLite bridge implementing the same contract | Future |
| HarmonyOS | Responsive Web UI in a native web shell | Native bridge implementing the same contract | Future |

The responsive client calls `window.pmgoPlatform`, not Electron directly.
Desktop implements that bridge in `apps/desktop/renderer/platform.js`. A future
mobile shell can expose the same methods for requests, secure credentials,
filesystem access, sharing, and notifications.

## Stable contract

The portable boundary is the versioned product contract:

- projects, tasks, risks, and Markdown notes;
- context preview and explicit context consent;
- provider configuration without plaintext secrets;
- import, export, backup, and migration behavior.

Contract fixtures should run against both the desktop Python core and every
future native implementation. If duplicated business rules become expensive,
the core can later move to a shared Rust library with C-compatible bindings;
the UI protocol remains unchanged.

## Desktop-first scope

Before beginning mobile shells, the desktop release should support:

1. signed installers and safe upgrades on all three desktop systems;
2. multi-project task and note workflows;
3. backup, restore, and Obsidian directory selection;
4. contextual AI with a visible consent preview;
5. stable migrations and recovery from an interrupted write.

Mobile work should then start with read/capture/sync workflows rather than copy
every desktop administration screen. Optional encrypted device-to-device sync
must be designed separately; local-first does not imply automatic cloud upload.
