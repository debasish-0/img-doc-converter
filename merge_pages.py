import re
from pathlib import Path

from docx import Document
from docxcompose.composer import Composer

# ================= SETTINGS =================

PAGE_DOCX_FOLDER = Path("page_docx_files")
FINAL_DOCX = Path("final_book.docx")

# ============================================


def get_page_number(docx_path: Path):
    """
    Gets page number from filename.

    Supported names:
    001.docx, 002.docx
    page_001.docx
    page 001.docx
    """

    match = re.search(
        r"(?:page[_\- ]?)?(\d{1,4})",
        docx_path.stem,
        re.IGNORECASE
    )

    if match:
        return int(match.group(1))

    return None


def main():
    docx_files = [
        path for path in PAGE_DOCX_FOLDER.glob("*.docx")
        if path.name != FINAL_DOCX.name
    ]

    if not docx_files:
        raise FileNotFoundError(
            f"No DOCX files found in: {PAGE_DOCX_FOLDER.resolve()}"
        )

    page_data = []

    for docx_path in docx_files:
        page_number = get_page_number(docx_path)

        if page_number is None:
            # Unknown page numbers are placed at the end
            page_number = 100000 + len(page_data)

        page_data.append((page_number, docx_path))

    # Sort by page number
    page_data.sort(key=lambda item: item[0])

    print("Merging pages in this order:\n")

    for page_number, docx_path in page_data:
        print(f"Page {page_number}: {docx_path.name}")

    # Use the first page as the base document
    first_page_path = page_data[0][1]
    master_document = Document(first_page_path)

    composer = Composer(master_document)

    # Append remaining pages
    for _, docx_path in page_data[1:]:
        composer.append(Document(docx_path))

    composer.save(FINAL_DOCX)

    print(f"\nFinal document created:")
    print(FINAL_DOCX.resolve())


if __name__ == "__main__":
    main()