"""Shared, dependency-light helpers for the book conversion pipeline."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"})
PAGE_DOCX_RE = re.compile(r"^page_(\d{4,})\.docx$", re.IGNORECASE)


def natural_key(path: Path) -> tuple[object, ...]:
    """Sort names naturally, so page_2 comes before page_10."""
    parts = re.split(r"(\d+)", path.stem.casefold())
    return tuple(int(part) if part.isdigit() else part for part in parts)


def discover_images(folder: Path) -> list[Path]:
    if not folder.is_dir():
        raise FileNotFoundError(f"Input folder does not exist: {folder.resolve()}")
    images = sorted(
        (path for path in folder.iterdir() if path.is_file() and path.suffix.casefold() in IMAGE_EXTENSIONS),
        key=natural_key,
    )
    if not images:
        raise FileNotFoundError(f"No supported images found in: {folder.resolve()}")
    return images


def discover_page_docx(folder: Path) -> list[tuple[int, Path]]:
    if not folder.is_dir():
        raise FileNotFoundError(f"Output folder does not exist: {folder.resolve()}")
    pages: list[tuple[int, Path]] = []
    for path in folder.glob("*.docx"):
        match = PAGE_DOCX_RE.match(path.name)
        if match:
            pages.append((int(match.group(1)), path))
    return sorted(pages, key=lambda item: item[0])


def validate_page_numbers(page_numbers: Iterable[int], expected_count: int | None = None) -> None:
    numbers = list(page_numbers)
    if len(numbers) != len(set(numbers)):
        raise ValueError(f"Duplicate page numbers found: {numbers}")
    if expected_count is not None and len(numbers) != expected_count:
        raise ValueError(
            f"Expected {expected_count} converted pages, found {len(numbers)}."
        )
    expected = list(range(1, len(numbers) + 1))
    if numbers != expected:
        raise ValueError(f"Converted pages are incomplete or out of order: {numbers}")
