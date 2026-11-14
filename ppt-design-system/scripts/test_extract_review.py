from io import BytesIO
import json

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
    report = json.loads((output / "image-decisions.json").read_text())
    assert report["pages"][0]["decisions"][0]["action"] == "review"


def test_pdf_scan_pairs_spread_captions_and_routes_with_target_subjects(tmp_path):
    streams = [
        b"q 290 0 0 220 0 180 cm /Im0 Do Q",
        b"q 290 0 0 160 0 0 cm /Im0 Do Q",
        b"q 290 0 0 220 310 180 cm /Im0 Do Q",
        b"q 290 0 0 160 310 0 cm /Im0 Do Q",
    ]
    for x, top, bottom in [(32,b"Map of North Bay",b"Cartographic diagram"),(346,b"Illustration in watercolor",b"Photo of Pine Park")]:
        for y, label in [(350,b"IMAGE AT TOP"),(337,top),(310,b"IMAGE BELOW"),(297,bottom)]:
            streams.append(b"BT /F1 10 Tf %d %d Td (%s) Tj ET" % (x,y,label))
    data = b"\n".join(streams)
    source_image = BytesIO()
    Image.new("RGB", (10, 10), "green").save(source_image, format="JPEG")
    image = source_image.getvalue()
    # A generated minimal PDF exercises the scanner's actual text and object pairing.
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Count 1 /Kids [3 0 R] >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 400] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> /XObject << /Im0 6 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(data),data),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /XObject /Subtype /Image /Width 10 /Height 10 /ColorSpace /DeviceRGB "
        b"/BitsPerComponent 8 /Filter /DCTDecode /Length %d >>\nstream\n%s\nendstream" % (len(image),image),
    ]
    pdf = b"%PDF-1.4\n"
    offsets = []
    for index, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf += b"%d 0 obj\n%s\nendobj\n" % (index, obj)
    startxref = len(pdf)
    pdf += b"xref\n0 7\n0000000000 65535 f \n"
    pdf += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    pdf += b"trailer\n<< /Size 7 /Root 1 0 R >>\nstartxref\n%d\n%%EOF\n" % startxref
    source = tmp_path / "spread.pdf"
    source.write_bytes(pdf)
    output = tmp_path / "scan"
    output.mkdir()
    context = {"regions":[
        {"page":1,"region":[0,0,50,50],"subject":"North Bay"},
        {"page":1,"region":[50,50,50,50],"subject":"Oak Park"},
    ]}
    scan_source(source, output, image_context=context, context_sha="context")
    report = json.loads((output / "image-decisions.json").read_text())
    rows = report["pages"][0]["decisions"]
    assert report["context_sha256"] == "context"
    assert [(r["caption"],r["action"]) for r in rows] == [
        ("Map of North Bay","reuse"),("Cartographic diagram","redraw"),
        ("Illustration in watercolor","extend"),("Photo of Pine Park","search"),
    ]
    assert "不确定项" in (output / "image-decisions.md").read_text()

    context["regions"].append({"page": 1, "region": [50, 50, 50, 50], "subject": "Pine Park"})
    overlap = tmp_path / "overlap"
    overlap.mkdir()
    scan_source(source, overlap, image_context=context)
    decisions = json.loads((overlap / "image-decisions.json").read_text())["pages"][0]["decisions"]
    assert decisions[-1]["action"] == "review"
    assert any("多个新稿目标" in note for note in decisions[-1]["uncertainty"])


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
