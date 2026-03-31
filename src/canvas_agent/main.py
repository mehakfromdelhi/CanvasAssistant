from __future__ import annotations

from pathlib import Path

from .config import load_config
from .pipeline import Pipeline
from .scaffold import ensure_course_dirs, ensure_local_project_dirs


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    ensure_local_project_dirs(project_root)

    config = load_config()
    created_paths = ensure_course_dirs(config)
    pipeline = Pipeline(config)
    results = pipeline.run()

    print("Canvas Academic Assistant run complete.")
    print(f"Course: {config.course_name}")
    print(f"Canvas course id: {config.canvas_course_id}")
    print(f"Course folder: {config.course_root}")
    print("Prepared course folders:")
    for path in created_paths:
        print(f" - {path}")
    print("Processing results:")
    for result in results:
        note = f" ({truncate_result_note(result.notes)})" if result.notes else ""
        print(f" - [{result.status}] {result.item_type}: {result.title}{note}")


def truncate_result_note(note: str) -> str:
    note = " ".join(note.split())
    return note[:100] + ("..." if len(note) > 100 else "")
