"""PDF upload, validation, and text extraction service.
Uses pypdf (already installed) for extraction.  No extra native deps required.
"""
from __future__ import annotations

import logging
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

logger = logging.getLogger(__name__)

MAX_BYTES = 20 * 1024 * 1024  # 20 MB
PDF_EXTENSIONS = (".pdf",)


def validate_file(file_path: Path, max_bytes: int = MAX_BYTES) -> None:
    """Validate that *file_path* is a non‐empty, reasonably‑sized PDF."""
    if not file_path.exists():
        raise ValueError("File does not exist")
    if not file_path.suffix.lower() in PDF_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")
    size_bytes = file_path.stat().st_size
    if size_bytes == 0:
        raise ValueError("File is empty")
    if size_bytes > max_bytes:
        raise ValueError(
            f"File size {size_bytes / 1024 / 1024:.2f} MB exceeds limit "
            f"{max_bytes / 1024 / 1024:.0f} MB"
        )


def extract_text(file_path: Path) -> tuple[str, int]:
    """Extract page‐ordered text from ``file_path``.

    Returns ``(full_text, page_count)``.  *full_text* is the concatenation
    of all pages with ``\n\n`` separators.  If no text can be extracted an
    empty string is returned.
    """
    try:
        reader = PdfReader(str(file_path))
    except PdfReadError as exc:
        logger.warning("Cannot read PDF: %s", file_path, exc_info=exc)
        raise ValueError("Invalid or corrupted PDF file")
    except Exception as exc:
        logger.warning("Unexpected error reading PDF: %s", file_path, exc_info=exc)
        raise ValueError(f"Could not read PDF: {exc}")

    page_count = len(reader.pages)
    if page_count == 0:
        raise ValueError("PDF contains no pages")

    full_parts: list[str] = []
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text()
            if text:
                text = "\n".join(line for line in text.split("\n") if line.strip())
                full_parts.append(f"--- PAGE {i + 1} ---\n{text}")
        except Exception as exc:
            logger.warning("Failed to extract page %d: %s", i + 1, exc)
            full_parts.append(f"--- PAGE {i + 1} --- [extraction error]")

    full_text = "\n\n".join(full_parts).strip()
    return full_text, page_count
