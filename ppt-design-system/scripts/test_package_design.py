import json
from hashlib import sha256

from PIL import Image
from pptx import Presentation
from pptx.util import Inches

from design_replay import check_source, make_renderer
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
