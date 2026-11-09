from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

from paddleocr import (
    PPStructure,
    DocImgOrientationClassification,
    save_structure_res
)
from paddleocr.ppstructure.recovery.recovery_to_doc import (
    sorted_layout_boxes,
    convert_info_docx
)

# ================= SETTINGS =================

INPUT_FOLDER = Path("book_pages")
OUTPUT_FOLDER = Path("page_docx_files")

# Change to your book language:
# English: "en"
# Hindi + English: "hi+en"
# Bengali + English: "bn+en"
OCR_LANGUAGE = "en"

# ============================================

OUTPUT_FOLDER.mkdir(exist_ok=True)

orientation_model = DocImgOrientationClassification(
    model_name="PP-LCNet_x1_0_doc_ori"
)

layout_engine = PPStructure(
    recovery=True,
    lang=OCR_LANGUAGE,
    show_log=False
)

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"
}


def correct_phone_rotation(image_path: Path):
    """
    Corrects:
    1. Phone EXIF rotation metadata
    2. Sideways / upside-down book-page photos
    """
    pil_image = Image.open(image_path)

    # Fix rotation stored by the mobile camera
    pil_image = ImageOps.exif_transpose(pil_image)

    image = cv2.cvtColor(
        np.array(pil_image.convert("RGB")),
        cv2.COLOR_RGB2BGR
    )

    # Detect whether the page itself is rotated
    result = orientation_model.predict(image, batch_size=1)

    for res in result:
        orientation = int(res["class_ids"][0])

        # 0 = 0 degrees, 1 = 90 degrees, 2 = 180 degrees, 3 = 270 degrees
        if orientation == 1:
            image = cv2.rotate(
                image,
                cv2.ROTATE_90_COUNTERCLOCKWISE
            )
        elif orientation == 2:
            image = cv2.rotate(
                image,
                cv2.ROTATE_180
            )
        elif orientation == 3:
            image = cv2.rotate(
                image,
                cv2.ROTATE_90_CLOCKWISE
            )

    return image


def convert_single_page(image_path: Path):
    print(f"Processing: {image_path.name}")

    image = correct_phone_rotation(image_path)

    result = layout_engine(image)

    page_name = image_path.stem

    # Save OCR/layout results and cropped figures/tables
    save_structure_res(
        result,
        str(OUTPUT_FOLDER),
        page_name
    )

    height, width, _ = image.shape

    # Sort detected regions in reading order
    ordered_result = sorted_layout_boxes(result, width)

    # Create an editable DOCX for this page
    convert_info_docx(
        image,
        ordered_result,
        str(OUTPUT_FOLDER),
        page_name
    )


def main():
    image_files = [
        path for path in INPUT_FOLDER.iterdir()
        if path.suffix.lower() in IMAGE_EXTENSIONS
    ]

    if not image_files:
        raise FileNotFoundError(
            f"No images found in: {INPUT_FOLDER.resolve()}"
        )

    print(f"Found {len(image_files)} images.")
    print("Starting bulk conversion...\n")

    for image_path in sorted(image_files):
        try:
            convert_single_page(image_path)
        except Exception as error:
            print(f"ERROR processing {image_path.name}: {error}")

    print(f"\nDone. Individual page DOCX files are in:")
    print(OUTPUT_FOLDER.resolve())


if __name__ == "__main__":
    main()