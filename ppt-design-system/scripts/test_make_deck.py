from base64 import b64encode
from io import BytesIO

from PIL import Image
import pytest
from pptx import Presentation

from make_deck import apply_edits
from native_deck import write_pptx


def test_native_curve_preserves_control_points_and_arrow(tmp_path):
    curve = {"kind": "curve", "id": "return-arc", "stroke": "ink", "weight": "edge", "arrow": True,
             "points": [[75, 20], [75, 60], [25, 60], [25, 20]]}
    system = {
        "tokens": {"colors": {"paper": "#FFFFFF", "ink": "#222222"}, "radii": {}, "strokes": {"edge": 5}},
        "families": {"main": {}},
        "patterns": {"cycle": {"family": "main", "background": "paper", "layers": [curve]}},
    }
    file = tmp_path / "curve.pptx"
    write_pptx(system, [{"id": "page", "pattern": "cycle", "slots": {}}], {}, None, file)
    deck = Presentation(file)
    shape = deck.slides[0].shapes[0]
    path = shape._element.xpath("./p:spPr/a:custGeom/a:pathLst/a:path")[0]
    assert shape.name == "return-arc"
    assert path.get("fill") == "none"
    assert [(int(p.get("x")), int(p.get("y"))) for p in path.xpath(".//a:pt")] == [
        (deck.slide_width // 2, 0), (deck.slide_width // 2, deck.slide_height * 2 // 5),
        (0, deck.slide_height * 2 // 5), (0, 0),
    ]
    assert len(path.xpath("./a:cubicBezTo/a:pt")) == 3
    assert shape._element.xpath("./p:spPr/a:ln/a:tailEnd")[0].get("type") == "triangle"


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
