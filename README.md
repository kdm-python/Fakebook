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

Open <http://miltoncross.localhost:8000/> or
<http://school-test.localhost:8000/>. The school subdomain selects the exercise
set. Some local DNS setups do not resolve `*.localhost`; if yours does not, add
the particular names to your hosts file or use a local proxy that resolves them.

The original exercise accepts:

```text
Username: george
Password: RedSimpsons
```

Two variations are included in Miltoncross's exercise selector:

```text
Alternative: lisa / PurpleDonuts
Three attempts: bart / BlueSkateboard
```

These values are sample exercise answers. Deployment settings belong in an
environment file and should not be committed.

If the exercise answers must remain private, keep this Git repository private as
well as keeping the backend directory outside the public web root.

## Add an exercise

Create a school directory under `backend/exercises/` matching its subdomain,
with a `school.toml` containing a display title. Within it, create one directory
per exercise, containing `exercise.py` and `exercise.toml`:

```text
backend/exercises/miltoncross/
├── school.toml
└── example-exercise/
    ├── exercise.py
    └── exercise.toml
```

The school metadata is `title = "Miltoncross"`. The exercise metadata is:

```toml
title = "Example Exercise"
description = "A short description shown in the browser."
entrypoint = "exercise.py"
result_variable = "login_success"
success_path = "/rewards/fakebook/"
```

`https://miltoncross.bytelets.org/example-exercise` opens the exercise directly;
the school root shows the selector. The Python file can use ordinary `print()` and `input()`. Set the configured
result variable to `True` when the exercise succeeds. Only the TOML title and
description are returned by the public API.

Restart the application after adding or changing an exercise. The test school
under `backend/exercises/school-test/` is a small example of a separate school.

## Checks

```sh
cd backend
uv run pytest
```

## LXC deployment

The application LXC runs one systemd service and exposes one HTTP port to the
separate reverse-proxy LXC. See [deploy/README.md](deploy/README.md).

The main Nginx server must preserve the original Host header and proxy normal
HTTP requests and WebSocket upgrades to the application LXC.
`deploy/reverse-proxy.example.conf` is a reference for the person managing that
server; the deployment script does not modify it.

## Boundaries of this version

This version runs the configured, server-owned exercises. It does not accept
arbitrary uploaded Python files yet. The Fakebook reward page is a static page
and its URL can be visited directly; it is not an authentication boundary.
