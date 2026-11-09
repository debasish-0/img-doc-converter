import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from pipeline_utils import discover_images, discover_page_docx, natural_key, validate_page_numbers


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


if __name__ == "__main__":
    unittest.main()
