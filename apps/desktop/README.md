# pmgo Desktop

The desktop client owns the primary user experience. It starts a loopback-only
Python sidecar, stores SQLite and Markdown data in Electron's platform-specific
`userData` directory, and keeps provider keys in Electron `safeStorage`.

The renderer depends on `window.pmgoPlatform`, a deliberately small bridge that
future Android, iOS, and HarmonyOS shells can implement without changing product
screens. The current desktop scope includes multiple projects, task lifecycle,
local Markdown notes, and consent-based AI project context.

Development:

```bash
npm install
npm run desktop:dev
```

Release builds use `scripts/build-sidecar.py` first, then electron-builder. The
sidecar is compiled for each target operating system by the release workflow;
cross-compiling a Python executable is intentionally avoided.
