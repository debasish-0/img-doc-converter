from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docxcompose.composer import Composer

from pipeline_utils import discover_page_docx, validate_page_numbers

PROJECT_DIR = Path(__file__).resolve().parent
PAGE_DOCX_FOLDER = PROJECT_DIR / "page_docx_files"
FINAL_DOCX = PROJECT_DIR / "final_book.docx"


def main() -> None:
    manifest_path = PAGE_DOCX_FOLDER / "conversion_manifest.json"
    expected_count = None
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected_count = manifest.get("input_count")
        if manifest.get("failures"):
            raise RuntimeError("Cannot merge: conversion manifest contains failed pages.")

    page_data = discover_page_docx(PAGE_DOCX_FOLDER)
    validate_page_numbers((number for number, _path in page_data), expected_count)
    print("Merging pages in order:", ", ".join(str(number) for number, _ in page_data))

    master = Document(page_data[0][1])
    composer = Composer(master)
    for _number, path in page_data[1:]:
        composer.append(Document(path))
    temporary_path = FINAL_DOCX.with_suffix(".tmp.docx")
    composer.save(temporary_path)
    temporary_path.replace(FINAL_DOCX)
    print(f"Final document created: {FINAL_DOCX}")


if __name__ == "__main__":
    main()
