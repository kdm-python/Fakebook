import re
import tomllib
from dataclasses import dataclass
from pathlib import Path


SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


@dataclass(frozen=True)
class School:
    school_id: str
    title: str
    directory: Path

    def public_dict(self) -> dict[str, str]:
        return {"id": self.school_id, "title": self.title}


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

    def school(self, school_id: str) -> School | None:
        if not SLUG.fullmatch(school_id):
            return None
        directory = (self.root / school_id).resolve()
        if directory.parent != self.root:
            return None
        metadata_path = directory / "school.toml"
        if not metadata_path.is_file():
            return None
        with metadata_path.open("rb") as metadata_file:
            data = tomllib.load(metadata_file)
        return School(school_id, str(data["title"]), directory)

    def list(self, school_id: str) -> list[Exercise]:
        school = self.school(school_id)
        if school is None:
            return []
        exercises: list[Exercise] = []
        for metadata_path in sorted(school.directory.glob("*/exercise.toml")):
            exercise = self.get(school_id, metadata_path.parent.name)
            if exercise is not None:
                exercises.append(exercise)
        return exercises

    def get(self, school_id: str, exercise_id: str) -> Exercise | None:
        school = self.school(school_id)
        if school is None or not SLUG.fullmatch(exercise_id):
            return None
        exercise_dir = (school.directory / exercise_id).resolve()
        if exercise_dir.parent != school.directory:
            return None
        metadata_path = exercise_dir / "exercise.toml"
        if not metadata_path.is_file():
            return None
        with metadata_path.open("rb") as metadata_file:
            data = tomllib.load(metadata_file)
        entrypoint = (exercise_dir / data.get("entrypoint", "exercise.py")).resolve()
        if entrypoint.parent != exercise_dir or not entrypoint.is_file():
            raise ValueError(f"Invalid entrypoint for {exercise_dir.name}")
        return Exercise(
            exercise_id=exercise_id,
            title=str(data["title"]),
            description=str(data.get("description", "")),
            entrypoint=entrypoint,
            result_variable=str(data.get("result_variable", "login_success")),
            success_path=data.get("success_path"),
        )
