# pmgo Desktop Architecture

The desktop client is the primary product surface. OpenClaw and Hermes are
optional adapters for channels and unattended automation.

The client uses a small platform bridge so its responsive project-management UI
can later be embedded in Android, iOS, and HarmonyOS shells. See
[PLATFORMS.md](./PLATFORMS.md).

## Runtime boundary

```text
Electron desktop shell
  ├─ renderer: focus, board, risks, assistant, settings
  ├─ OS secure storage: model API key
  └─ native Python sidecar (127.0.0.1 + random bearer token)
       ├─ LocalCore
       ├─ Provider interface
       └─ userData/
            ├─ pmgo.db
            └─ projects/<slug>/*.md
```

The renderer has no Node access and cannot call the network directly. Electron's
isolated preload exposes a narrow request bridge. The Python API binds only to
loopback and requires a random per-process bearer token. API keys are injected
into model calls for that request and are never written to SQLite.

## Provider contract

The first implementation supports OpenAI-compatible chat-completions endpoints
and Ollama's compatible local endpoint. Provider configuration contains only an
identifier, base URL, and model name. The next adapters can add Anthropic and
Gemini without changing task persistence or the UI-to-core protocol.

Before a contextual request is sent, the UI previews how many tasks, risks, and
Markdown notes will be included. Users can omit notes or disable project context
entirely.

## Data locations

- macOS: `~/Library/Application Support/pmgo`
- Windows: `%LOCALAPPDATA%\\pmgo`
- Linux: `$XDG_DATA_HOME/pmgo`, otherwise `~/.local/share/pmgo`

Installed Electron builds use Electron's equivalent `userData` directory. Users
can export the Markdown tree to an Obsidian vault; direct vault selection and
attachment indexing are planned next.

## Packaging

`scripts/build-sidecar.py` compiles the Python API with PyInstaller. The GitHub
Actions desktop workflow builds this sidecar and Electron installer on each
target OS. This avoids unsupported Python cross-compilation and produces DMG/ZIP,
NSIS/portable, and AppImage/DEB artifacts.
