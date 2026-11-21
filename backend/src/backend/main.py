import uvicorn
from fastapi import FastAPI, WebSocket
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


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/exercises")
async def list_exercises() -> dict[str, list[dict[str, str]]]:
    return {"exercises": [exercise.public_dict() for exercise in registry.list()]}


@app.websocket("/api/runs/{exercise_id}")
async def run_exercise(websocket: WebSocket, exercise_id: str) -> None:
    exercise = registry.get(exercise_id)
    if exercise is None:
        await websocket.close(code=1008, reason="Unknown exercise")
        return

    await websocket.accept()
    runner = ExerciseRunner(
        exercise=exercise,
        websocket=websocket,
        timeout_seconds=settings.run_timeout_seconds,
        max_output_bytes=settings.max_output_bytes,
    )
    await runner.run()


frontend_dir = settings.frontend_dir.resolve()
if not (frontend_dir / "index.html").is_file():
    raise RuntimeError(f"Frontend not found at {frontend_dir}")

app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


def run() -> None:
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        proxy_headers=True,
        forwarded_allow_ips=settings.forwarded_allow_ips,
    )
