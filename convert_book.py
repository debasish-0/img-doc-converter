from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps
from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.shared import Inches, Pt

from pipeline_utils import discover_images

PROJECT_DIR = Path(__file__).resolve().parent
INPUT_FOLDER = PROJECT_DIR / "book_pages"
OUTPUT_FOLDER = PROJECT_DIR / "page_docx_files"
MANIFEST_FILE = OUTPUT_FOLDER / "conversion_manifest.json"
OCR_LANGUAGE = "en"


def build_ocr():
    try:
        from paddleocr import PaddleOCR
    except ImportError as error:
        raise RuntimeError(
            "PaddleOCR is not installed. Run: python -m pip install -r requirements.txt"
        ) from error
    try:
        return PaddleOCR(
            lang=OCR_LANGUAGE,
            use_doc_orientation_classify=True,
            use_doc_unwarping=True,
            use_textline_orientation=True,
        )
    except TypeError as error:
        raise RuntimeError(
            "The installed PaddleOCR does not provide the PaddleOCR 3.x interface."
        ) from error


def load_image(path: Path):
    image = ImageOps.exif_transpose(Image.open(path))
    return cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)


def result_as_dict(result):
    if isinstance(result, dict):
        return result
    value = getattr(result, "json", None)
    if callable(value):
        value = value()
    if isinstance(value, str):
        return json.loads(value)
    if isinstance(value, dict):
        return value
    raise TypeError(f"Unsupported PaddleOCR result type: {type(result)!r}")


def first_result_value(data, keys, default):
    """Return the first non-empty result field without boolean-testing arrays."""
    for key in keys:
        value = data.get(key)
        if value is None:
            continue
        if hasattr(value, "size") and value.size == 0:
            continue
        if not hasattr(value, "size") and len(value) == 0:
            continue
        return value
    return default


def extract_lines(result):
    data = result_as_dict(result)
    texts = first_result_value(data, ("rec_texts", "texts"), [])
    scores = first_result_value(data, ("rec_scores", "scores"), [1.0] * len(texts))
    boxes = first_result_value(data, ("rec_boxes", "dt_polys", "boxes"), [])
    lines = []
    for index, text in enumerate(texts):
        text = str(text).strip()
        if not text:
            continue
        box = np.asarray(boxes[index]) if index < len(boxes) else np.array([[0, index * 20]])
        lines.append((
            float(np.min(box[:, 1])),
            float(np.min(box[:, 0])),
            text,
            float(scores[index]) if index < len(scores) else 1.0,
        ))
    return sorted(lines, key=lambda item: (item[0], item[1]))


def configure_styles(document: Document) -> None:
    normal = document.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(11)
    for name, size in (("Book Heading", 16), ("Book Subheading", 13)):
        style = document.styles[name] if name in document.styles else document.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        style.font.name = "Arial"
        style.font.size = Pt(size)
        style.font.bold = True


def write_editable_page(document: Document, lines) -> float:
    if not lines:
        document.add_paragraph("[No text detected on this page.]")
        return 0.0
    average_confidence = sum(item[3] for item in lines) / len(lines)
    previous_y = None
    for y, _x, text, _score in lines:
        paragraph = document.add_paragraph()
        if previous_y is not None and y - previous_y > 45:
            paragraph.paragraph_format.space_before = Pt(8)
        previous_y = y
        marker = re.match(r"^\s*((?:\d+|[A-Za-z])[.)]|[•●▪◦*-])\s+", text)
        if marker:
            paragraph.style = "List Number" if marker.group(1)[0].isdigit() else "List Bullet"
        elif len(text) <= 90 and (text.isupper() or text.endswith(":")):
            paragraph.style = "Book Heading"
        paragraph.add_run(text)
    return average_confidence


def convert_page(image_path: Path, page_number: int, ocr) -> dict:
    print(f"Processing page {page_number}: {image_path.name}", flush=True)
    result = next(iter(ocr.predict(load_image(image_path))), None)
    lines = extract_lines(result) if result is not None else []
    document = Document()
    configure_styles(document)
    section = document.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)
    confidence = write_editable_page(document, lines)
    output_path = OUTPUT_FOLDER / f"page_{page_number:04d}.docx"
    temporary_path = output_path.with_suffix(".tmp.docx")
    document.save(temporary_path)
    temporary_path.replace(output_path)
    return {
        "page": page_number,
        "source": str(image_path.relative_to(PROJECT_DIR)),
        "output": output_path.name,
        "line_count": len(lines),
        "average_confidence": round(confidence, 4),
        "status": "ok",
    }


def main() -> None:
    image_files = discover_images(INPUT_FOLDER)
    if OUTPUT_FOLDER.exists():
        shutil.rmtree(OUTPUT_FOLDER)
    OUTPUT_FOLDER.mkdir(parents=True)
    ocr = build_ocr()
    manifest = {"input_count": len(image_files), "pages": [], "failures": []}
    for page_number, image_path in enumerate(image_files, start=1):
        try:
            manifest["pages"].append(convert_page(image_path, page_number, ocr))
        except Exception as error:
            manifest["failures"].append({
                "page": page_number,
                "source": image_path.name,
                "error": str(error),
            })
            print(f"ERROR processing page {page_number}: {error}")
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if manifest["failures"]:
        raise RuntimeError(f"{len(manifest['failures'])} page(s) failed; see {MANIFEST_FILE}")
    print(f"Converted {len(image_files)} pages to {OUTPUT_FOLDER}")


if __name__ == "__main__":
    main()
