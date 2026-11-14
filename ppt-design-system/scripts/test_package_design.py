import json
from hashlib import sha256
from types import SimpleNamespace

from PIL import Image
from pptx import Presentation
from pptx.util import Inches
import pytest

from design_replay import check_source, make_renderer
from make_deck import make
from package_design import check_directory, check_zip
from style_catalog import catalog
from test_design_replay import design_system


def test_package_keeps_native_tiff_with_png_derivative(tmp_path, design_system):
    original = tmp_path / "original.tiff"
    image = Image.new("RGBA", (12, 8), (0, 171, 200, 120))
    image.save(original)
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    picture = slide.shapes.add_picture(str(original), Inches(1), Inches(1))
    source = tmp_path / "reference.pptx"
    presentation.save(source)

    object_id = f"p1-o{picture.shape_id}"
    pack = tmp_path / "pack"
    assets = pack / "assets"
    element_catalog = catalog(source, asset_objects=[object_id], assets_out=assets)
    manifest_path = assets / "assets-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    native = manifest["objects"][0]["media"][0]
    rendered = assets / "accent.png"
    image.save(rendered)
    derivative = {"file": rendered.name, "sha256": sha256(rendered.read_bytes()).hexdigest(),
                  "sources": [object_id], "treatment": "TIFF to PNG"}
    manifest["derivatives"] = [derivative]
    manifest_path.write_text(json.dumps(manifest))

    design_system["source"] = {"kind": "pptx", "pages": 1, "sha256": manifest["source_sha256"]}
    for key, identifier in (("families", "guest"), ("evidence", "guest-page"), ("rules", "guest-rule")):
        del design_system[key][identifier]
    design_system["evidence"]["main-page"]["objects"] = [picture.shape_id]
    design_system["fixed_assets"] = {"accent": {
        "file": rendered.name, "sha256": derivative["sha256"], "source_sha256": native["sha256"],
        "evidence": "main-page",
    }}
    design_system["patterns"]["editorial"]["layers"].append({
        "kind": "image", "id": "accent", "asset": "accent", "fit": "contain",
        "position": [50, 50], "box": [70, 30, 20, 20],
    })
    grammar = {"version": 1, "source_sha256": manifest["source_sha256"], "elements": {
        "accent": {"kind": "image", "family": "main", "status": "inherited", "objects": [object_id],
                   "tokens": element_catalog["objects"][object_id]["tokens"], "relations": ["comparison"],
                   "use": "Place the accent next to the title."}},
        "recipes": {"editorial": {
            "pattern": "editorial", "relation": "comparison", "focus": "title",
            "use_elements": {"accent": ["title", "accent"]},
            "fields": {"title": "title"}, "items": [], "limits": {"title": 30},
        }}}
    for name, data in (("design-system", design_system), ("style-grammar", grammar), ("element-catalog", element_catalog)):
        (pack / f"{name}.json").write_text(json.dumps(data))
    (pack / "STYLE.md").write_text("# Style\n")

    target = tmp_path / "pack.zip"
    assert check_directory(pack, target) == []
    assert check_zip(target) == []
    check_source(design_system, source)
    _, load_asset, _ = make_renderer(design_system, assets, {native["sha256"]})
    assert load_asset(rendered.name, derivative["sha256"]).startswith("data:image/png;")
    (assets / native["file"]).unlink()
    assert f"Missing manifest asset: assets/{native['file']}" in check_directory(pack, None)
    (pack / "manuscript.json").write_text("{}")
    assert "Unexpected top-level file: manuscript.json" in check_directory(pack, None)


def test_make_reuses_a_registered_photo_from_the_zip_without_content_assets(tmp_path, design_system):
    pack = tmp_path / "pack"
    assets = pack / "assets"
    assets.mkdir(parents=True)
    file = assets / "photo.jpg"
    Image.new("RGB", (20, 15), "green").save(file)
    record = {"file": file.name, "sha256": sha256(file.read_bytes()).hexdigest(), "creator": "Photographer",
              "source_url": "https://example.com/photo", "license": "CC0 1.0",
              "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
              "role": "Photo", "reuse": "Center crop", "distribution_basis": "CC0 permits redistribution"}
    fingerprint = design_system["source"]["sha256"]
    design_system["evidence"]["main-page"]["catalog_refs"] = ["p1-photo"]
    layers = design_system["patterns"]["editorial"]["layers"]
    layers.append({"kind": "image", "id": "photo", "slot": "photo", "fit": "cover",
                   "position": [50, 50], "box": [10, 30, 80, 60]})
    catalog = {"version": 1, "source_sha256": fingerprint, "pages": 2, "objects": {
        "p1-photo": {"page": 1, "object": 1, "tokens": ["visual"]}},
        "tokens": {"visual": {"kind": "raster-frame", "value": {"pixel_size": [20, 15]}}}}
    grammar = {"version": 1, "source_sha256": fingerprint, "elements": {
        "photo": {"kind": "image", "family": "main", "status": "inherited", "objects": ["p1-photo"],
                  "tokens": ["visual"], "relations": ["comparison"], "use": "An image next to the title."}},
        "recipes": {"editorial": {"pattern": "editorial", "relation": "comparison", "focus": "title",
                                 "density": "medium", "weight": "medium", "layout": "Photo and title",
                                 "use_elements": {"photo": ["title", "photo"]},
                                 "fields": {"title": "title", "photo": "photo"}, "items": [],
                                 "limits": {"title": 50, "photo": 50}}}}
    for name, value in (("design-system", design_system), ("style-grammar", grammar), ("element-catalog", catalog)):
        (pack / f"{name}.json").write_text(json.dumps(value))
    (pack / "STYLE.md").write_text("# Style\n")
    manifest = {"version": 1, "source_sha256": fingerprint, "objects": [], "stock_photos": [record]}
    manifest_path = assets / "assets-manifest.json"
    manifest_path.write_text(json.dumps(manifest))
    target = tmp_path / "pack.zip"
    assert check_directory(pack, target) == []
    chapter = {"id": "first", "relation": "comparison", "intent": "Show the photo",
               "fields": {"title": "Photo", "photo": "pack:photo.jpg"}, "items": []}
    manuscript = tmp_path / "manuscript.json"
    manuscript.write_text(json.dumps({"version": 1, "chapters": [chapter]}))
    args = SimpleNamespace(pack=target, manuscript=manuscript, assets=None, source=None, edits=None, html_only=False)
    stage = tmp_path / "job/result"
    stage.mkdir(parents=True)
    assert make(args, stage)
    assert Presentation(stage / "deck.pptx").slides[0].shapes[1].image.blob == file.read_bytes()
    report = json.loads((stage / "make-report.json").read_text())
    assert report["stock_photos"] == {"photo.jpg": record["sha256"]}

    Image.new("RGB", (20, 15), "blue").save(file)
    assert any("SHA-256 mismatch" in error for error in check_directory(pack, None))
    record["sha256"] = sha256(file.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    args.pack = pack
    assert make(args, stage)
    assert json.loads((stage / "make-report.json").read_text())["base"] != report["base"]

    chapter["fields"]["photo"] = "pack:unregistered.jpg"
    manuscript.write_text(json.dumps({"version": 1, "chapters": [chapter]}))
    with pytest.raises(ValueError, match="not a registered stock photo"):
        make(args, stage)
    record["distribution_basis"] = ""
    manifest_path.write_text(json.dumps(manifest))
    assert any("distribution basis" in error for error in check_directory(pack, None))
