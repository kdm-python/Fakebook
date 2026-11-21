# Fakebook backend

The backend serves the static frontend, lists public exercise metadata, and runs
private Python exercises over WebSockets.

From this directory:

```sh
uv sync
uv run fakebook-backend
```

Then open <http://127.0.0.1:8000>.

Configuration uses environment variables beginning with `FAKEBOOK_`. See
`.env.example` for the available local settings.
