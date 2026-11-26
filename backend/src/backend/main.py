import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .exercises import ExerciseRegistry
from .runner import ExerciseRunner
from .settings import get_settings

settings = get_settings()
registry = ExerciseRegistry(settings.exercise_dir)

app = FastAPI(
    title=settings.app_name,
    docs_url=None,
    redoc_url=None,
)


def school_id_from_host(host: str) -> str | None:
    hostname = host.split(":", 1)[0].lower().rstrip(".")
    for domain in (part.strip().lower() for part in settings.school_domains.split(",")):
        if domain and hostname.endswith("." + domain):
            school_id = hostname[: -(len(domain) + 1)]
            if registry.school(school_id) is not None:
                return school_id
    return None


def request_school(request: Request) -> str:
    school_id = school_id_from_host(request.headers.get("host", ""))
    if school_id is None:
        raise HTTPException(status_code=404, detail="Unknown school")
    return school_id


def school_not_found_response(host: str) -> HTMLResponse:
    hostname = host.split(":", 1)[0].lower().rstrip(".")
    parent_domains = {
        domain.strip().lower()
        for domain in settings.school_domains.split(",")
        if domain.strip()
    }
    if not hostname or hostname in parent_domains:
        heading = "No school specified"
        message = (
            "Add your school prefix to the address. For local development, "
            "try miltoncross.localhost:8000."
        )
    else:
        heading = "School not found"
        message = (
            "The school prefix in this address is not configured. "
            "Check the address and try again."
        )

    return HTMLResponse(
        status_code=404,
        content=f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{heading} · Python Exercise Runner</title>
    <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
    <link rel="stylesheet" href="/style.css" />
  </head>
  <body>
    <header class="site-header">
      <div class="brand">
        <span class="brand-mark" aria-hidden="true">&gt;_</span>
        <div>
          <div class="brand-title">Python Exercise Runner</div>
          <div class="brand-subtitle">Interactive classroom exercises</div>
        </div>
      </div>
      <div class="status-pill" data-state="error">404</div>
    </header>
    <main class="page-shell error-shell">
      <section class="error-card">
        <p class="eyebrow">School</p>
        <h1>{heading}</h1>
        <p class="exercise-description">{message}</p>
      </section>
    </main>
  </body>
</html>""",
    )


@app.middleware("http")
async def reject_unknown_school(request: Request, call_next):
    public_paths = {"/api/health", "/style.css", "/favicon.svg"}
    if (
        request.url.path not in public_paths
        and school_id_from_host(request.headers.get("host", "")) is None
    ):
        return school_not_found_response(request.headers.get("host", ""))
    return await call_next(request)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/exercises")
async def list_exercises(request: Request) -> dict[str, object]:
    school_id = request_school(request)
    school = registry.school(school_id)
    assert school is not None
    return {
        "school": school.public_dict(),
        "exercises": [exercise.public_dict() for exercise in registry.list(school_id)],
    }


@app.websocket("/api/runs/{exercise_id}")
async def run_exercise(websocket: WebSocket, exercise_id: str) -> None:
    school_id = school_id_from_host(websocket.headers.get("host", ""))
    exercise = registry.get(school_id, exercise_id) if school_id else None
    if exercise is None or not exercise.include:
        await websocket.close(code=1008, reason="Unknown exercise")
        return

    await websocket.accept()
    runner = ExerciseRunner(
        exercise=exercise,
        websocket=websocket,
        max_output_bytes=settings.max_output_bytes,
    )
    await runner.run()


frontend_dir = settings.frontend_dir.resolve()
if not (frontend_dir / "index.html").is_file():
    raise RuntimeError(f"Frontend not found at {frontend_dir}")


@app.get("/", include_in_schema=False)
async def school_home(request: Request) -> FileResponse:
    request_school(request)
    return FileResponse(frontend_dir / "index.html")


@app.get("/style.css", include_in_schema=False)
async def stylesheet() -> FileResponse:
    return FileResponse(frontend_dir / "style.css")


@app.get("/app.js", include_in_schema=False)
async def javascript() -> FileResponse:
    return FileResponse(frontend_dir / "app.js")


@app.get("/favicon.svg", include_in_schema=False)
async def favicon() -> FileResponse:
    return FileResponse(frontend_dir / "favicon.svg")


@app.get("/{exercise_id}", include_in_schema=False)
async def exercise_page(request: Request, exercise_id: str) -> FileResponse:
    school_id = request_school(request)
    exercise = registry.get(school_id, exercise_id)
    if exercise is None or not exercise.include:
        raise HTTPException(status_code=404, detail="Unknown exercise")
    return FileResponse(frontend_dir / "index.html")


app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


def run() -> None:
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        proxy_headers=True,
        forwarded_allow_ips=settings.forwarded_allow_ips,
    )
