from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

from .canvas_api import CanvasClient, ReadingItem
from .config import AppConfig
from .extractors import (
    extract_links,
    extract_external_text,
    extract_pdf_text,
    guess_extension,
    html_to_text,
)
from .summarizer import Summarizer
from .scaffold import ensure_session_dirs
from .utils import safe_write_text, slugify


@dataclass
class ProcessingResult:
    title: str
    item_type: str
    module_name: str
    source_url: str
    status: str
    notes: str = ""
    raw_text_path: str | None = None
    summary_path: str | None = None
    asset_path: str | None = None


class Pipeline:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.canvas = CanvasClient(config)
        self.summarizer = Summarizer(config)

    def run(self) -> list[ProcessingResult]:
        items = self.canvas.list_module_items()
        results: list[ProcessingResult] = []

        for item in items:
            try:
                results.append(self._process_item(item))
            except Exception as exc:
                results.append(
                    ProcessingResult(
                        title=item.title,
                        item_type=item.item_type,
                        module_name=item.module_name,
                        source_url=item.source_url,
                        status="failed",
                        notes=str(exc),
                    )
                )

        manifest_path = self.config.course_root / "run_manifest.json"
        manifest_path.write_text(
            json.dumps([asdict(result) for result in results], indent=2),
            encoding="utf-8",
        )
        return results

    def _process_item(self, item: ReadingItem) -> ProcessingResult:
        slug = slugify(item.title)
        if item.item_type == "Page" and item.page_url:
            return self._process_page(item, slug)
        if item.item_type == "File" and item.file_id:
            return self._process_file(item, slug)
        if item.item_type in {"ExternalUrl", "ExternalTool"} and item.external_url:
            return self._process_link(item, slug)
        raise ValueError("Unsupported or incomplete module item")

    def _process_page(self, item: ReadingItem, slug: str) -> ProcessingResult:
        session_root = self.config.session_root(item.title)
        ensure_session_dirs(session_root)
        page = self.canvas.get_page(item.page_url or "")
        html = page.get("body", "")
        text = html_to_text(html)
        raw_path = session_root / "pages" / "session-page.txt"
        summary_path = session_root / "summaries" / "session-summary.md"
        safe_write_text(raw_path, text)
        summary = self.summarizer.summarize(item.title, text)
        safe_write_text(summary_path, summary)
        nested_notes = self._process_page_links(item.title, slug, html, session_root)
        notes = "; ".join(nested_notes)
        return ProcessingResult(
            title=item.title,
            item_type=item.item_type,
            module_name=item.module_name,
            source_url=item.source_url,
            status="ok",
            notes=notes,
            raw_text_path=str(raw_path),
            summary_path=str(summary_path),
        )

    def _process_file(self, item: ReadingItem, slug: str) -> ProcessingResult:
        session_root = self.config.session_root(item.title)
        ensure_session_dirs(session_root)
        file_info = self.canvas.get_file(item.file_id or 0)
        file_url = file_info.get("url")
        if not file_url:
            raise ValueError("Canvas file is missing a download URL")

        filename = file_info.get("display_name") or file_info.get("filename") or slug
        content_type = file_info.get("content-type") or item.content_type
        extension = guess_extension(filename, content_type)
        asset_path = session_root / "files" / f"{slug}{extension}"
        raw_text_path = session_root / "files" / f"{slug}.txt"
        summary_path = session_root / "summaries" / f"{slug}.summary.md"

        payload = self.canvas.download_file(file_url)
        asset_path.write_bytes(payload)

        if extension.lower() == ".pdf" or (content_type and "pdf" in content_type.lower()):
            text = extract_pdf_text(payload)
        else:
            text = ""
            try:
                text = payload.decode("utf-8")
            except UnicodeDecodeError:
                text = ""

        if not text.strip():
            notes = "Downloaded file but could not extract readable text for summarization."
            return ProcessingResult(
                title=item.title,
                item_type=item.item_type,
                module_name=item.module_name,
                source_url=item.source_url,
                status="partial",
                notes=notes,
                asset_path=str(asset_path),
            )

        safe_write_text(raw_text_path, text)
        summary = self.summarizer.summarize(item.title, text)
        safe_write_text(summary_path, summary)
        return ProcessingResult(
            title=item.title,
            item_type=item.item_type,
            module_name=item.module_name,
            source_url=item.source_url,
            status="ok",
            raw_text_path=str(raw_text_path),
            summary_path=str(summary_path),
            asset_path=str(asset_path),
        )

    def _process_link(self, item: ReadingItem, slug: str) -> ProcessingResult:
        session_root = self.config.session_root(item.title)
        ensure_session_dirs(session_root)
        link_url = item.external_url or ""
        raw_text_path = session_root / "links" / f"{slug}.txt"
        summary_path = session_root / "summaries" / f"{slug}.summary.md"
        metadata_path = session_root / "links" / f"{slug}.url.txt"

        safe_write_text(metadata_path, link_url)
        text, content_type = extract_external_text(link_url)
        if not text.strip():
            raise ValueError("External link was reachable but no readable text was extracted")

        safe_write_text(raw_text_path, text)
        summary = self.summarizer.summarize(item.title, text)
        safe_write_text(summary_path, summary)
        return ProcessingResult(
            title=item.title,
            item_type=item.item_type,
            module_name=item.module_name,
            source_url=item.source_url,
            status="ok",
            notes=f"Fetched external content type: {content_type or 'unknown'}",
            raw_text_path=str(raw_text_path),
            summary_path=str(summary_path),
        )

    def _process_page_links(self, page_title: str, slug: str, html: str, session_root: Path) -> list[str]:
        notes: list[str] = []
        seen_urls: set[str] = set()
        links = extract_links(html)
        link_count = 0

        for index, (label, href) in enumerate(links, start=1):
            absolute_url = urljoin(self.config.canvas_base_url.rstrip("/") + "/", href)
            parsed = urlparse(absolute_url)
            if absolute_url in seen_urls or parsed.scheme not in {"http", "https"}:
                continue
            seen_urls.add(absolute_url)

            link_slug = f"resource-{index:02d}-{slugify(label, max_length=20)}"
            try:
                if parsed.netloc.endswith("instructure.com"):
                    link_result = self._process_canvas_link(page_title, label, absolute_url, link_slug, session_root)
                else:
                    link_result = self._process_external_page_link(page_title, label, absolute_url, link_slug, session_root)
                if link_result:
                    link_count += 1
            except Exception as exc:
                notes.append(f"Link '{label}' skipped: {exc}")

        if link_count:
            notes.insert(0, f"Processed {link_count} link(s) embedded in the page")
        return notes

    def _process_canvas_link(self, page_title: str, label: str, url: str, slug: str, session_root: Path) -> bool:
        response = self.canvas.session.get(url, timeout=60)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").lower()
        base_name = f"{page_title} - {label}"

        if "pdf" in content_type or url.lower().endswith(".pdf"):
            asset_path = session_root / "files" / f"{slug}.pdf"
            asset_path.write_bytes(response.content)
            text = extract_pdf_text(response.content)
            if not text.strip():
                return False
            raw_text_path = session_root / "files" / f"{slug}.txt"
            summary_path = session_root / "summaries" / f"{slug}.summary.md"
            safe_write_text(raw_text_path, text)
            safe_write_text(summary_path, self.summarizer.summarize(base_name, text))
            return True

        if "html" in content_type:
            download_url = self._find_canvas_download_url(response.text, response.url)
            if download_url:
                download_response = self.canvas.session.get(download_url, timeout=60)
                download_response.raise_for_status()
                download_type = download_response.headers.get("content-type", "").lower()
                if "pdf" in download_type or download_url.lower().endswith(".pdf"):
                    asset_path = session_root / "files" / f"{slug}.pdf"
                    asset_path.write_bytes(download_response.content)
                    text = extract_pdf_text(download_response.content)
                    if not text.strip():
                        return False
                    raw_text_path = session_root / "files" / f"{slug}.txt"
                    summary_path = session_root / "summaries" / f"{slug}.summary.md"
                    safe_write_text(raw_text_path, text)
                    safe_write_text(summary_path, self.summarizer.summarize(base_name, text))
                    return True

            text = html_to_text(response.text)
            if not text.strip():
                return False
            raw_text_path = session_root / "links" / f"{slug}.txt"
            summary_path = session_root / "summaries" / f"{slug}.summary.md"
            safe_write_text(raw_text_path, text)
            safe_write_text(summary_path, self.summarizer.summarize(base_name, text))
            return True

        return False

    def _process_external_page_link(self, page_title: str, label: str, url: str, slug: str, session_root: Path) -> bool:
        text, _ = extract_external_text(url)
        if not text.strip():
            return False
        raw_text_path = session_root / "links" / f"{slug}.txt"
        summary_path = session_root / "summaries" / f"{slug}.summary.md"
        metadata_path = session_root / "links" / f"{slug}.url.txt"
        safe_write_text(metadata_path, url)
        safe_write_text(raw_text_path, text)
        safe_write_text(summary_path, self.summarizer.summarize(f"{page_title} - {label}", text))
        return True

    def _find_canvas_download_url(self, html: str, base_url: str) -> str | None:
        for label, href in extract_links(html):
            full_url = urljoin(base_url, href)
            lowered = f"{label} {href}".lower()
            if "download" in lowered or "/download" in href.lower():
                return full_url
        return None
