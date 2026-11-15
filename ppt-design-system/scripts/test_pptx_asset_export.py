import json

from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE
from pptx.opc.package import Part
from pptx.opc.packuri import PackURI
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches

from style_catalog import catalog


def test_exports_svg_and_original_alpha_fallback_from_group(tmp_path):
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    group = slide.shapes.add_group_shape()
    png = tmp_path / "accent.png"
    Image.new("RGBA", (10, 10), (4, 18, 54, 64)).save(png)
    picture = group.shapes.add_picture(str(png), Inches(1), Inches(1))
    picture.crop_left = 0.15
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"/>'
    svg_part = Part(PackURI("/ppt/media/accent.svg"), "image/svg+xml", slide.part.package, svg)
    relationship = slide.part.relate_to(svg_part, RELATIONSHIP_TYPE.IMAGE)
    blip = picture._element.xpath("./p:blipFill/a:blip")[0]
    ext = etree.SubElement(etree.SubElement(blip, "{http://schemas.openxmlformats.org/drawingml/2006/main}extLst"),
                           "{http://schemas.openxmlformats.org/drawingml/2006/main}ext")
    etree.SubElement(ext, "{http://schemas.microsoft.com/office/drawing/2016/SVG/main}svgBlip", attrib={
        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed": relationship,
    })
    source = tmp_path / "reference.pptx"
    presentation.save(source)
    object_id = f"p1-o{picture.shape_id}"
    group_id = f"p1-o{group.shape_id}"
    destination = tmp_path / "assets"
    result = catalog(source, asset_objects=[object_id, group_id], assets_out=destination)
    assert result == catalog(source)

    manifest = json.loads((destination / "assets-manifest.json").read_text())
    exported, unresolved = manifest["objects"]
    assert manifest["source_sha256"] == result["source_sha256"]
    assert exported["parent"] == group_id
    assert unresolved["status"] == "no-embedded-image"
    files = {entry["mime"]: entry for entry in exported["media"]}
    assert (destination / files["image/png"]["file"]).read_bytes() == png.read_bytes()
    assert (destination / files["image/svg+xml"]["file"]).read_bytes() == svg
    assert files["image/png"]["crop"] == {"l": "15000"}

    all_assets = tmp_path / "all"
    assert catalog(source, assets_out=all_assets) == result
    automatically_exported = json.loads((all_assets / "assets-manifest.json").read_text())
    assert automatically_exported["objects"] == [exported]


def test_empty_title_placeholder_records_layout_and_master_type_evidence(tmp_path):
    presentation = Presentation()
    layout = presentation.slide_layouts[0]
    title = layout.placeholders.get(idx=0)
    text_styles = title._element.xpath("./p:txBody/a:lstStyle")[0]
    level = OxmlElement("a:lvl1pPr")
    level.set("algn", "ctr")
    run = OxmlElement("a:defRPr")
    run.set("sz", "3700")
    run.set("i", "1")
    latin = OxmlElement("a:latin")
    latin.set("typeface", "Arial")
    run.append(latin)
    level.append(run)
    text_styles.append(level)
    slide = presentation.slides.add_slide(layout)
    assert not slide.shapes.title.text
    source = tmp_path / "empty-title.pptx"
    presentation.save(source)

    result = catalog(source)
    obj = result["objects"][f"p1-o{slide.shapes.title.shape_id}"]
    values = [result["tokens"][key]["value"] for key in obj["tokens"] if key.startswith("placeholder-type-")]
    assert {"origin": "layout", "font": "Arial", "pt": 37, "italic": True, "align": "center"} in values
    assert any(value["origin"] == "master-text-style" for value in values)
