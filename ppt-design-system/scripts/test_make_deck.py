from base64 import b64encode
from io import BytesIO

from PIL import Image
import pytest

from make_deck import apply_edits


def test_edits_are_page_specific_and_keep_the_confirmed_manuscript():
    plan = {"version": 1, "pages": [{"id": "first", "slots": {"title": "Old phrase", "emphasis": "phrase", "photo": "a.png"}},
                                    {"id": "second", "slots": {"title": "Other page"}}]}
    model = {"base": "confirmed", "pages": {"first": {"layers": [
        {"slot": "title", "kind": "text", "limit": 20, "underline": "emphasis"},
        {"slot": "photo", "kind": "image", "limit": 40},
    ], "boxes": {"cards": [3, 4, 50, 25]}}, "second": {"layers": [], "boxes": {}}}}
    png = BytesIO()
    Image.new("RGB", (2, 3), "white").save(png, "PNG")
    url = "data:image/png;base64," + b64encode(png.getvalue()).decode()
    edits = {"version": 1, "base": "confirmed", "pages": {"first": {
        "slots": {"title": "New wording"}, "boxes": {"cards": [4, 5, 51, 25]}, "images": {"photo": url},
    }}}
    adjusted, boxes, images = apply_edits(plan, model, edits, set())
    assert adjusted["pages"][0]["slots"]["title"] == "New wording"
    assert adjusted["pages"][0]["slots"]["emphasis"] == ""
    assert images[adjusted["pages"][0]["slots"]["photo"]] == url
    assert adjusted["pages"][1] == plan["pages"][1]
    assert plan["pages"][0]["slots"]["title"] == "Old phrase"
    assert boxes == {"first": {"cards": [4, 5, 51, 25]}}

    with pytest.raises(ValueError, match="different deck"):
        apply_edits(plan, model, {**edits, "base": "other"}, set())
    edits["pages"]["first"]["boxes"]["cards"] = [90, 5, 51, 25]
    with pytest.raises(ValueError, match="Invalid layer position"):
        apply_edits(plan, model, edits, set())
    edits["pages"]["first"]["boxes"] = {"fixed-art": [1, 1, 20, 20]}
    with pytest.raises(ValueError, match="fixed-art"):
        apply_edits(plan, model, edits, set())
