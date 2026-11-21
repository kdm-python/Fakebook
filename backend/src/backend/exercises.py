import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Exercise:
    exercise_id: str
    title: str
    description: str
    entrypoint: Path
    result_variable: str
    success_path: str | None

    def public_dict(self) -> dict[str, str]:
        return {
            "id": self.exercise_id,
            "title": self.title,
            "description": self.description,
        }


class ExerciseRegistry:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def list(self) -> list[Exercise]:
        if not self.root.is_dir():
            return []

        exercises: list[Exercise] = []
        for metadata_path in sorted(self.root.glob("*/exercise.toml")):
            exercises.append(self._load(metadata_path))
        return exercises

    def get(self, exercise_id: str) -> Exercise | None:
        if not exercise_id or not exercise_id.replace("-", "").isalnum():
            return None

        metadata_path = self.root / exercise_id / "exercise.toml"
        if not metadata_path.is_file():
            return None

        exercise = self._load(metadata_path)
        return exercise if exercise.exercise_id == exercise_id else None

    def _load(self, metadata_path: Path) -> Exercise:
        exercise_dir = metadata_path.parent.resolve()
        if exercise_dir.parent != self.root:
            raise ValueError("Exercise metadata is outside the exercise directory")

        with metadata_path.open("rb") as metadata_file:
            data = tomllib.load(metadata_file)

        entrypoint = (exercise_dir / data.get("entrypoint", "exercise.py")).resolve()
        if entrypoint.parent != exercise_dir or not entrypoint.is_file():
            raise ValueError(f"Invalid entrypoint for {exercise_dir.name}")

        return Exercise(
            exercise_id=exercise_dir.name,
            title=str(data["title"]),
            description=str(data.get("description", "")),
            entrypoint=entrypoint,
            result_variable=str(data.get("result_variable", "login_success")),
            success_path=data.get("success_path"),
        )
