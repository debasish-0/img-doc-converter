# Book Image to Editable Word Converter

Converts a folder of book-page images into an editable Word document using Surya OCR.

The pipeline preserves page order and approximate layout, including OCR text, headings, numbered or bulleted lists, page boundaries, and OCR confidence information.

## Setup

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Place page images in `book_pages/`. Supported formats:

`jpg`, `jpeg`, `png`, `bmp`, `tif`, `tiff`

## Convert

```powershell
python run_all.py
```

Surya is the default backend. To compare with the retained PaddleOCR adapter:

```powershell
$env:OCR_BACKEND = "paddle"
python -m pip install paddlepaddle paddleocr
python run_all.py
```

The final document is created at:

```text
final_book.docx
```

Intermediate page documents and the conversion manifest are stored in `page_docx_files/`.

## Tests

```powershell
python -m unittest -v test_pipeline.py
```

## Notes

- PaddleOCR downloads its models the first time it runs.
- Surya 2.x uses a local inference server: `llama.cpp` for CPU/Apple Silicon or
  `vLLM` with an NVIDIA GPU. Surya downloads model files on first use.
- Surya is Apache-2.0 licensed. Its local inference runtime may have separate
  licensing terms; review those terms before redistribution.
- OCR output is editable but cannot guarantee pixel-perfect reproduction of photographed pages.
- Complex tables, unusual typography, poor lighting, skew, and handwriting may require manual review.
- Failed pages stop the merge and are recorded in `page_docx_files/conversion_manifest.json`.
- `OCR_LANGUAGE` in `convert_book.py` can be changed for another supported PaddleOCR language.
