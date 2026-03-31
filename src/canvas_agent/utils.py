from __future__ import annotations

import re
from pathlib import Path


def slugify(value: str, max_length: int = 80) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", value, flags=re.ASCII).strip().lower()
    slug = re.sub(r"[-\s]+", "-", cleaned).strip("-")
    return slug[:max_length] or "item"


def truncate_text(text: str, max_chars: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 3].rstrip() + "..."


def safe_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

