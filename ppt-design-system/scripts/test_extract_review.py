from PIL import Image
import pytest

from compile_story import compile_story
from extract_review import coverage, scan_source
from test_design_replay import design_system


def test_pdf_scan_keeps_original_jpeg_and_occurrences(tmp_path):
    picture = Image.new("RGB", (20, 12), "#7D61A2")
    source = tmp_path / "repeated.pdf"
    picture.save(source, save_all=True, append_images=[picture])
    output = tmp_path / "scan"
    output.mkdir()

    catalog, manifest = scan_source(source, output)
    assert catalog["pages"] == 2
    assert [item["id"] for item in manifest["objects"]] == ["p1-image-1", "p2-image-1"]
    one, two = [item["media"][0] for item in manifest["objects"]]
    assert one["part"] != two["part"]
    assert one["file"] == two["file"]
    assert one["mime"] == "image/jpeg" and not one["needs_context"]
    assert len(list((output / "assets").glob("*.jpg"))) == 1
    with Image.open(output / "assets" / one["file"]) as original:
        assert original.size == (20, 12)


def test_flat_raster_scan_does_not_make_up_assets_or_recipe_matches(tmp_path):
    source = tmp_path / "screenshot.jpg"
    Image.new("RGBA", (20, 12), "#7D61A2").save(source, format="PNG")
    output = tmp_path / "scan"
    output.mkdir()

    catalog, manifest = scan_source(source, output)
    assert catalog["tokens"]["raster-frame"]["value"] == {"pixel_size": [20, 12], "format": "PNG"}
    assert manifest["objects"] == []
    probe = {"chapters": [{"id": "compare", "relation": "before-after", "fields": {"title": "Before and after"},
                           "items": []}]}
    initial = coverage(catalog, probe, "probe")["rows"][0]
    assert initial["status"] == "pending" and initial["match"] is None
    review = {"compare": {"decision": "adapt", "evidence": ["p1-frame"], "note": "Rebuild the visual pair."}}
    assessed = coverage(catalog, probe, "probe", review=review)["rows"][0]
    assert assessed["status"] == "adapt" and assessed["match"] is None


def test_scan_accepts_a_single_jpeg_without_frame_metadata(tmp_path):
    source = tmp_path / "reference.jpg"
    Image.new("RGB", (12, 8)).save(source, format="JPEG")
    output = tmp_path / "scan"
    output.mkdir()
    catalog, manifest = scan_source(source, output)
    assert catalog["tokens"]["raster-frame"]["value"] == {"pixel_size": [12, 8], "format": "JPEG"}
    assert manifest["objects"] == []


def test_partial_coverage_still_validates_matched_slots(design_system):
    catalog = {"version": 1, "pages": 2, "source_sha256": "0" * 64,
               "objects": {"p1-text": {"page": 1, "tokens": ["type"]}}, "tokens": {"type": {}}}
    recipe = {"pattern": "editorial", "relation": "comparison", "focus": "title",
              "weight": "high", "density": "low", "layout": "Title",
              "use_elements": {"headline": ["title"]}, "fields": {"title": "title"},
              "items": [], "limits": {"title": 15}}
    grammar = {"version": 1, "source_sha256": "0" * 64, "recipes": {"editorial": recipe},
               "elements": {"headline": {"kind": "type", "status": "inherited", "family": "main",
                                         "objects": ["p1-text"], "tokens": ["type"],
                                         "relations": ["comparison"], "use": "Title"}}}
    chapter = {"id": "comparison", "relation": "comparison", "intent": "Compare",
               "fields": {"title": ""}, "items": []}
    probe = {"version": 1, "chapters": [chapter, {**chapter, "id": "other", "relation": "other"}]}
    with pytest.raises(ValueError, match="Invalid slot title"):
        compile_story(design_system, catalog, grammar, probe)
    chapter["fields"]["title"] = "Compare"
    plan, report = compile_story(design_system, catalog, grammar, probe)
    assert plan is None
    assert [row["chapter"] for row in report["compiled"]] == ["comparison"]
    assert [row["chapter"] for row in report["extensions_needed"]] == ["other"]
