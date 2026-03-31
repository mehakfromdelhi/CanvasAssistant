from __future__ import annotations

import io
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from readability import Document


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())


def extract_links(html: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[tuple[str, str]] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        label = " ".join(anchor.get_text(" ", strip=True).split()) or href
        if href:
            links.append((label, href))
    return links


def extract_pdf_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages.append(page_text.strip())
    return "\n\n".join(pages)


def extract_external_text(url: str) -> tuple[str, str]:
    response = requests.get(
        url,
        headers={"User-Agent": "CanvasAcademicAssistant/0.1"},
        timeout=45,
    )
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()
    if "pdf" in content_type or url.lower().endswith(".pdf"):
        text = extract_pdf_text(response.content)
        return text, content_type

    html = response.text
    document = Document(html)
    cleaned_html = document.summary()
    text = html_to_text(cleaned_html)
    if not text.strip():
        text = html_to_text(html)
    return text, content_type


def guess_extension(filename: str | None, content_type: str | None, fallback: str = ".bin") -> str:
    if filename and "." in filename:
        return Path(filename).suffix
    if content_type:
        if "pdf" in content_type:
            return ".pdf"
        if "html" in content_type:
            return ".html"
        if "text" in content_type:
            return ".txt"
    return fallback


def filename_from_url(url: str) -> str:
    parsed = urlparse(url)
    name = Path(parsed.path).name
    return name or "downloaded-file"
