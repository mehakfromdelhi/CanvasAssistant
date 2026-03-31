from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

import requests

from .config import AppConfig


@dataclass(frozen=True)
class ReadingItem:
    module_name: str
    item_id: int | None
    title: str
    item_type: str
    source_url: str
    page_url: str | None = None
    file_id: int | None = None
    external_url: str | None = None
    content_type: str | None = None


class CanvasClient:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {config.canvas_api_token}",
                "User-Agent": "CanvasAcademicAssistant/0.1",
            }
        )
        self.base_api = urljoin(config.canvas_base_url.rstrip("/") + "/", "api/v1/")

    def _get(self, path: str, **kwargs: Any) -> requests.Response:
        response = self.session.get(urljoin(self.base_api, path), timeout=30, **kwargs)
        response.raise_for_status()
        return response

    def _paginate(self, path: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        response = self._get(path, params=params)
        items = response.json()
        if not isinstance(items, list):
            return []

        results = items[:]
        while response.links.get("next"):
            response = self.session.get(response.links["next"]["url"], timeout=30)
            response.raise_for_status()
            page_items = response.json()
            if not isinstance(page_items, list):
                break
            results.extend(page_items)
        return results

    def list_module_items(self) -> list[ReadingItem]:
        modules = self._paginate(
            f"courses/{self.config.canvas_course_id}/modules",
            params={"include[]": ["items", "content_details"], "per_page": 100},
        )
        readings: list[ReadingItem] = []

        for module in modules:
            module_name = module.get("name", "Untitled Module")
            for item in module.get("items", []):
                item_type = item.get("type") or "Unknown"
                if item_type not in {"Page", "File", "ExternalUrl", "ExternalTool"}:
                    continue

                source_url = item.get("html_url") or item.get("url") or ""
                readings.append(
                    ReadingItem(
                        module_name=module_name,
                        item_id=item.get("id"),
                        title=item.get("title") or "Untitled Item",
                        item_type=item_type,
                        source_url=source_url,
                        page_url=item.get("page_url"),
                        file_id=item.get("content_id"),
                        external_url=item.get("external_url"),
                        content_type=(item.get("content_details") or {}).get("content_type"),
                    )
                )

        return readings

    def get_page(self, page_url: str) -> dict[str, Any]:
        response = self._get(
            f"courses/{self.config.canvas_course_id}/pages/{page_url}",
            params={"include[]": ["body"]},
        )
        return response.json()

    def get_file(self, file_id: int) -> dict[str, Any]:
        response = self._get(f"courses/{self.config.canvas_course_id}/files/{file_id}")
        return response.json()

    def download_file(self, url: str) -> bytes:
        response = self.session.get(url, timeout=60)
        response.raise_for_status()
        return response.content

