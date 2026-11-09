"""OCR backend adapters with one normalized line format for DOCX generation."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class OCRLine:
    y: float
    x: float
    text: str
    confidence: float
    label: str = "Text"


def _box_position(box, fallback_y: float = 0.0) -> tuple[float, float]:
    if box is None:
        return 0.0, fallback_y
    values = box.tolist() if hasattr(box, "tolist") else box
    if values and isinstance(values[0], (int, float)):
        return float(values[0]), float(values[1])
    if values and len(values[0]) >= 2:
        return min(float(point[0]) for point in values), min(float(point[1]) for point in values)
    return 0.0, fallback_y


def _plain_text(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value or "", flags=re.IGNORECASE)
    value = re.sub(r"</(p|div|li|tr|h[1-6])>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\n{2,}", "\n", value)
    return html.unescape(value).strip()


class SuryaBackend:
    """Surya 2.x/2.5 backend using its shared inference manager."""

    def __init__(self) -> None:
        try:
            from surya.inference import SuryaInferenceManager
            from surya.recognition import RecognitionPredictor
        except ImportError as error:
            raise RuntimeError(
                "Surya is not installed. Run: python -m pip install -r requirements.txt"
            ) from error
        try:
            manager = SuryaInferenceManager()
            self.predictor = RecognitionPredictor(manager)
        except Exception as error:
            raise RuntimeError(
                "Surya could not start its inference backend. Surya 2.x requires "
                "llama.cpp for CPU or vLLM for NVIDIA GPU."
            ) from error

    def recognize(self, image_path: Path) -> list[OCRLine]:
        from PIL import Image

        image = Image.open(image_path).convert("RGB")
        page = self.predictor([image])[0]
        lines = []
        for index, block in enumerate(getattr(page, "blocks", [])):
            text = _plain_text(getattr(block, "html", "") or getattr(block, "text", ""))
            if not text:
                continue
            x, y = _box_position(getattr(block, "bbox", None), index * 20)
            lines.append(OCRLine(
                y=y,
                x=x,
                text=text,
                confidence=float(getattr(block, "confidence", 1.0) or 1.0),
                label=str(getattr(block, "label", "Text")),
            ))
        return sorted(lines, key=lambda line: (line.y, line.x))


class PaddleBackend:
    """Compatibility backend for comparing against the existing PaddleOCR path."""

    def __init__(self, language: str = "en") -> None:
        try:
            from paddleocr import PaddleOCR
            self.ocr = PaddleOCR(
                lang=language,
                use_doc_orientation_classify=True,
                use_doc_unwarping=True,
                use_textline_orientation=True,
                enable_mkldnn=False,
            )
        except ImportError as error:
            raise RuntimeError(
                "PaddleOCR is not installed. Run: python -m pip install -r requirements.txt"
            ) from error
        except TypeError as error:
            raise RuntimeError("The installed PaddleOCR does not provide the 3.x interface.") from error

    def recognize(self, image_path: Path) -> list[OCRLine]:
        import numpy as np
        from PIL import Image

        image = np.asarray(Image.open(image_path).convert("RGB"))[:, :, ::-1]
        result = next(iter(self.ocr.predict(image)), None)
        if result is None:
            return []
        data = result if isinstance(result, dict) else getattr(result, "json", {})
        if callable(data):
            data = data()
        texts = data.get("rec_texts", [])
        scores = data.get("rec_scores", [1.0] * len(texts))
        boxes = data.get("rec_boxes", data.get("dt_polys", []))
        lines = []
        for index, text in enumerate(texts):
            x, y = _box_position(boxes[index] if index < len(boxes) else None, index * 20)
            lines.append(OCRLine(y, x, str(text).strip(), float(scores[index])))
        return sorted((line for line in lines if line.text), key=lambda line: (line.y, line.x))


def build_backend(name: str, language: str = "en"):
    if name.casefold() == "surya":
        return SuryaBackend()
    if name.casefold() == "paddle":
        return PaddleBackend(language)
    raise ValueError(f"Unsupported OCR backend {name!r}; choose 'surya' or 'paddle'.")
