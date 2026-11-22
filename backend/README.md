# Fakebook backend

The backend serves the static frontend, lists public exercise metadata, and runs
private Python exercises over WebSockets.

From this directory:

```sh
uv sync
uv run fakebook-backend
```

Then open <http://miltoncross.localhost:8000/> or
<http://school-test.localhost:8000/>. The hostname selects the school, and
`/<exercise-id>` opens an exercise directly.

Configuration uses environment variables beginning with `FAKEBOOK_`. See
`.env.example` for the available local settings.
`FAKEBOOK_SCHOOL_DOMAINS` lists accepted parent domains; production should set
it to `bytelets.org`.
