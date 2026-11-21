from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

from check_color_fields import check_color_fields


class ColorFieldTests(unittest.TestCase):
    def test_area_and_location_reject_accent_only_and_moved_field(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = Image.new("RGB", (100, 100), "white")
            image.paste("#FFE01B", (0, 0, 50, 100))
            image.save(root / "slide.png")
            review = {"pages": [{"id": "cover", "screenshot": "slide.png", "fields": [{
                "role": "chapter-field", "color": "#FFE01B", "min_fraction": .95,
                "max_fraction": 1, "region": [0, 0, .5, 1],
                "evidence": "reference hero", "basis": "Reviewed left-half field adaptation"
            }]}]}
            self.assertTrue(check_color_fields(review, root)["passed"])
            moved = deepcopy(review)
            moved["pages"][0]["fields"][0]["region"] = [.5, 0, 1, 1]
            self.assertFalse(check_color_fields(moved, root)["passed"])
            excessive = deepcopy(review)
            excessive["pages"][0]["fields"][0].update(region=[0, 0, 1, 1], min_fraction=0, max_fraction=.4)
            self.assertFalse(check_color_fields(excessive, root)["passed"])
            image = Image.new("RGB", (100, 100), "white")
            image.paste("#FFE01B", (0, 0, 3, 100))
            image.save(root / "slide.png")
            self.assertFalse(check_color_fields(review, root)["passed"])
            path = root / "review.json"
            path.write_text(json.dumps(review))
            result = subprocess.run([sys.executable, str(Path(__file__).with_name("check_color_fields.py")),
                                     str(path), "--out", str(root / "result.json")], capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(json.loads((root / "result.json").read_text())["passed"])

    def test_invalid_or_empty_reviews_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new("RGB", (10, 10), "white").save(root / "slide.png")
            field = {"role": "canvas", "color": "#FFFFFF", "min_fraction": 0,
                     "max_fraction": 1, "evidence": "source", "basis": "reviewed"}
            review = {"pages": [{"id": "cover", "screenshot": "slide.png", "fields": [field]}]}
            for changes in ({"min_fraction": float("nan")}, {"max_fraction": True},
                            {"region": [0, 0, 0, 1]}, {"color": "white"}, {"basis": ""}):
                invalid = deepcopy(review)
                invalid["pages"][0]["fields"][0].update(changes)
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    check_color_fields(invalid, root)
            for invalid in ({"pages": []}, {"pages": [{**review["pages"][0], "fields": []}]},
                            {"pages": review["pages"] * 2}):
                with self.assertRaises(ValueError):
                    check_color_fields(invalid, root)


if __name__ == "__main__":
    unittest.main()
