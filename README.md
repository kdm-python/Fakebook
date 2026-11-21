# Python Exercise Runner

A small browser interface for interactive Python classroom exercises. Python runs
on the server, so exercise source and answers are not delivered to the browser.

The project uses plain HTML, CSS and JavaScript in `frontend/`, and FastAPI with
Uvicorn in `backend/`. One application process serves both parts on the same port.

## Run locally

Install [uv](https://docs.astral.sh/uv/), then run:

```sh
cd backend
uv sync
uv run fakebook-backend
```

Open <http://127.0.0.1:8000>.

The original exercise accepts:

```text
Username: george
Password: RedSimpsons
```

Two variations are included in the exercise selector:

```text
Alternative: lisa / PurpleDonuts
Three attempts: bart / BlueSkateboard
```

These values are sample exercise answers. Deployment settings belong in an
environment file and should not be committed.

If the exercise answers must remain private, keep this Git repository private as
well as keeping the backend directory outside the public web root.

## Add an exercise

Create a directory under `backend/exercises/` containing `exercise.py` and
`exercise.toml`:

```toml
title = "Example Exercise"
description = "A short description shown in the browser."
entrypoint = "exercise.py"
result_variable = "login_success"
success_path = "/fakebook/"
```

The Python file can use ordinary `print()` and `input()`. Set the configured
result variable to `True` when the exercise succeeds. Only the TOML title and
description are returned by the public API.

Restart the application after adding or changing an exercise.

## Checks

```sh
cd backend
uv run pytest
```

## LXC deployment

The application LXC runs one systemd service and exposes one HTTP port to the
separate reverse-proxy LXC. See [deploy/README.md](deploy/README.md).

The main Nginx server must proxy normal HTTP requests and WebSocket upgrades to
the application LXC. `deploy/reverse-proxy.example.conf` is a reference for the
person managing that server; the deployment script does not modify it.

## Boundaries of this version

This version runs the configured, server-owned exercises. It does not accept
arbitrary uploaded Python files yet. The Fakebook reward page is a static page
and its URL can be visited directly; it is not an authentication boundary.
