"""Internal child-process wrapper for a private exercise script."""

import json
import runpy
import sys
from pathlib import Path


def write_result(path: Path, result: dict[str, object]) -> None:
    path.write_text(json.dumps(result), encoding="utf-8")


def main() -> int:
    exercise_path = Path(sys.argv[1])
    result_path = Path(sys.argv[2])
    result_variable = sys.argv[3]

    try:
        namespace = runpy.run_path(str(exercise_path), run_name="__exercise__")
    except BaseException as error:
        error_name = type(error).__name__
        print(f"\nPython error:\n{error_name}: {error}", flush=True)
        write_result(
            result_path,
            {"success": False, "error": error_name},
        )
        return 1

    write_result(
        result_path,
        {"success": namespace.get(result_variable) is True},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
