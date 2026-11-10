"""Tokenize the native visual objects in a local PPTX, without reading their copy into the catalog."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from lxml import etree
from pptx.enum.shapes import MSO_SHAPE_TYPE

from pptx_source import background, bounds, load_source, text_style, theme_for


def local(node):
    return etree.QName(node).localname


def paint(node):
    return {"mode": local(node), "attributes": dict(node.attrib),
            "settings": [{"mode": local(part), "attributes": dict(part.attrib)}
                         for part in node.iterdescendants()]}


def catalog(source):
    deck, fingerprint = load_source(source)
    tokens, objects, surfaces = {}, {}, {}

    def token(kind, value):
        encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
        identifier = f"{kind}-{sha256(encoded).hexdigest()[:16]}"
        tokens[identifier] = {"kind": kind, "value": value}
        return identifier

    def collect(shapes, page, theme, parent=None):
        for index, shape in enumerate(shapes):
            identifier = f"p{page}-o{shape.shape_id}"
            frame = bounds(shape, deck.slide_width, deck.slide_height)
            references = []
            props = shape._element.xpath("./p:spPr | ./p:grpSpPr")
            if props:
                geometry = props[0].xpath("./a:prstGeom | ./a:custGeom")
                if geometry:
                    node = geometry[0]
                    value = {"preset": node.get("prst", "custom"),
                             "adjustments": {g.get("name"): g.get("fmla") for g in node.xpath("./a:avLst/a:gd")}}
                    if local(node) == "custGeom":
                        value["geometry_sha256"] = sha256(etree.tostring(node, method="c14n", exclusive=True)).hexdigest()
                    references.append(token("geometry", value))
                for node in props[0].xpath("./a:solidFill | ./a:gradFill | ./a:blipFill | ./a:pattFill | ./a:noFill | ./a:ln | ./a:effectLst | ./a:effectDag"):
                    # A color transform or gradient stop is part of the paint, not a new asset.
                    kind = {"ln": "stroke", "effectLst": "effect", "effectDag": "effect"}.get(local(node), "fill")
                    references.append(token(kind, paint(node)))
            for node in shape._element.xpath("./p:spPr//a:srgbClr | ./p:spPr//a:schemeClr | ./p:txBody//a:srgbClr | ./p:txBody//a:schemeClr"):
                raw = node.get("val")
                color = theme[0].get(theme[1].get(raw, raw)) if local(node) == "schemeClr" else raw
                if color:
                    references.append(token("color", color))
            if shape.has_text_frame:
                style = text_style(shape, theme, deck)
                references.append(token("type", {k: v for k, v in style.items() if k != "insets"}))
                references.append(token("insets", style["insets"]))
                for node in shape._element.xpath("./p:txBody//a:rPr | ./p:txBody//a:defRPr"):
                    value = {"attributes": dict(node.attrib),
                             "fonts": {local(part): part.get("typeface")
                                       for part in node.xpath("./a:latin | ./a:ea | ./a:cs")}}
                    if value["attributes"] or value["fonts"]:
                        references.append(token("type-detail", value))
            for rel_id in shape._element.xpath(
                "./p:blipFill//a:blip/@r:embed | ./p:spPr/a:blipFill//a:blip/@r:embed | "
                "./p:blipFill//*[local-name()='svgBlip']/@r:embed | "
                "./p:spPr/a:blipFill//*[local-name()='svgBlip']/@r:embed"
            ):
                rel = shape.part.rels.get(rel_id)
                if rel and not rel.is_external and rel.reltype.endswith(("/image", "/hdphoto")):
                    crops = shape._element.xpath("./p:blipFill/a:srcRect | ./p:spPr/a:blipFill/a:srcRect")
                    references.append(token("asset", {"sha256": sha256(rel.target_part.blob).hexdigest(),
                                                       "mime": rel.target_part.content_type,
                                                       "crop": dict(crops[0].attrib) if crops else {}}))
            objects[identifier] = {
                "page": page, "object": shape.shape_id, "parent": parent, "layer": index,
                "kind": shape.shape_type.name if shape.shape_type is not None else "UNKNOWN",
                "bounds": frame, "rotation": shape.rotation, "tokens": list(dict.fromkeys(references)),
            }
            if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
                collect(shape.shapes, page, theme, identifier)

    for page, slide in enumerate(deck.slides, 1):
        theme = theme_for(slide)
        color, origin = background(slide, theme)
        native_backgrounds = {}
        for scope, owner in (("slide", slide), ("layout", slide.slide_layout),
                             ("master", slide.slide_layout.slide_master)):
            backgrounds = owner._element.xpath("./p:cSld/p:bg/*")
            if backgrounds:
                native_backgrounds[scope] = token("fill", paint(backgrounds[0]))
        surfaces[f"p{page}"] = {
            "background_color": token("color", color), "origin": origin,
            "native_backgrounds": native_backgrounds,
            "palette": {name: token("color", value) for name, value in theme[0].items()},
            "theme_fonts": {name: token("typeface", value) for name, value in theme[2].items() if value},
        }
        collect(slide.shapes, page, theme)
    return {"version": 1, "source_sha256": fingerprint, "pages": len(deck.slides),
            "objects": objects, "tokens": tokens, "surfaces": surfaces}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = catalog(args.source)
    with args.out.open("x", encoding="utf-8") as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
        output.write("\n")


if __name__ == "__main__":
    main()
