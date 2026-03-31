from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    canvas_base_url: str
    canvas_api_token: str
    canvas_course_id: str
    academics_root: Path
    course_name: str
    openai_api_key: str
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    openai_model: str = "gpt-4.1-mini"

    @property
    def course_root(self) -> Path:
        return self.academics_root / self.course_name

    def session_root(self, title: str) -> Path:
        match = re.search(r"session\s+(\d+)", title, flags=re.IGNORECASE)
        if not match:
            return self.course_root / "General"
        return self.course_root / f"Session {int(match.group(1))}"


def load_config() -> AppConfig:
    load_dotenv()

    required = {
        "CANVAS_BASE_URL": os.getenv("CANVAS_BASE_URL", "").strip(),
        "CANVAS_API_TOKEN": os.getenv("CANVAS_API_TOKEN", "").strip(),
        "CANVAS_COURSE_ID": os.getenv("CANVAS_COURSE_ID", "").strip(),
        "ACADEMICS_ROOT": os.getenv("ACADEMICS_ROOT", "").strip(),
        "COURSE_NAME": os.getenv("COURSE_NAME", "").strip(),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "").strip(),
    }

    missing = [key for key, value in required.items() if not value]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Missing required .env values: {missing_text}")

    return AppConfig(
        canvas_base_url=required["CANVAS_BASE_URL"],
        canvas_api_token=required["CANVAS_API_TOKEN"],
        canvas_course_id=required["CANVAS_COURSE_ID"],
        academics_root=Path(required["ACADEMICS_ROOT"]),
        course_name=required["COURSE_NAME"],
        openai_api_key=required["OPENAI_API_KEY"],
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash",
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini",
    )
