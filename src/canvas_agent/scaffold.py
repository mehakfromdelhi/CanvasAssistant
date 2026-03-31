from __future__ import annotations

from pathlib import Path

from .config import AppConfig


SESSION_FOLDERS = ("pages", "files", "links", "summaries")


def ensure_local_project_dirs(project_root: Path) -> None:
    for relative in ("data/browser", "data/downloads", "logs"):
        (project_root / relative).mkdir(parents=True, exist_ok=True)


def ensure_course_dirs(config: AppConfig) -> list[Path]:
    created: list[Path] = []

    config.course_root.mkdir(parents=True, exist_ok=True)
    created.append(config.course_root)

    return created


def ensure_session_dirs(session_root: Path) -> list[Path]:
    created = [session_root]
    session_root.mkdir(parents=True, exist_ok=True)
    for name in SESSION_FOLDERS:
        path = session_root / name
        path.mkdir(parents=True, exist_ok=True)
        created.append(path)
    return created
