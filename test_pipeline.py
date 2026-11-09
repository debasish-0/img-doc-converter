import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pipeline_utils import discover_images, discover_page_docx, natural_key, validate_page_numbers
from ocr_backends import OCRLine, _box_position, _plain_text


class PipelineTests(unittest.TestCase):
    def test_natural_sort(self):
        names = [Path("page_10.jpg"), Path("page_2.jpg"), Path("page_1.jpg")]
        self.assertEqual([path.name for path in sorted(names, key=natural_key)], [
            "page_1.jpg", "page_2.jpg", "page_10.jpg"
        ])

    def test_discover_images_filters_and_sorts(self):
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            for name in ("page_10.jpg", "page_2.png", "notes.txt", "page_1.jpeg"):
                (folder / name).touch()
            self.assertEqual(
                [path.name for path in discover_images(folder)],
                ["page_1.jpeg", "page_2.png", "page_10.jpg"],
            )

    def test_page_validation_rejects_gaps(self):
        with self.assertRaises(ValueError):
            validate_page_numbers([1, 3])

    def test_page_docx_discovery_ignores_stale_names(self):
        with TemporaryDirectory() as directory:
            folder = Path(directory)
            for name in ("page_0002.docx", "page_0001.docx", "old.docx"):
                (folder / name).touch()
            self.assertEqual(
                [number for number, _ in discover_page_docx(folder)],
                [1, 2],
            )

    def test_box_position_accepts_flat_and_polygon_boxes(self):
        self.assertEqual(_box_position([10, 20, 30, 40]), (10.0, 20.0))
        self.assertEqual(_box_position([[10, 20], [30, 40]]), (10.0, 20.0))

    def test_surya_html_is_normalized_to_editable_text(self):
        self.assertEqual(_plain_text("<p>Chapter 1</p><br>Text"), "Chapter 1\nText")

    def test_normalized_line_keeps_list_marker_and_confidence(self):
        line = OCRLine(20, 10, "1. First item", 0.94, "ListGroup")
        self.assertEqual(line.text, "1. First item")
        self.assertEqual(line.confidence, 0.94)


if __name__ == "__main__":
    unittest.main()
