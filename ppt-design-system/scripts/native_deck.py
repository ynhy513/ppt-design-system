"""Write the supported design layers as editable PowerPoint objects."""

from base64 import b64decode
from io import BytesIO

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

from design_replay import require


def write_pptx(system, pages, boxes, asset, output):
    deck = Presentation()
    deck.slide_width, deck.slide_height = Inches(40 / 3), Inches(7.5)
    width, height = deck.slide_width, deck.slide_height
    tokens = system["tokens"]
    colors = tokens["colors"]

    def frame(box, region):
        x, y, w, h = box
        left, top, rw, rh = region
        return (left + rw * x / 100, top + rh * y / 100, rw * w / 100, rh * h / 100)

    def emu(values):
        return tuple(round(value) for value in values)

    def picture(shapes, url, bounds, fit, position):
        data = b64decode(url.split(",", 1)[1])
        left, top, w, h = bounds
        with Image.open(BytesIO(data)) as image:
            iw, ih = image.size
            if image.format == "WEBP":
                buffer = BytesIO()
                image.save(buffer, "PNG")
                data = buffer.getvalue()
        if fit == "contain":
            scale = min(w / iw, h / ih)
            sw, sh = iw * scale, ih * scale
            left += (w - sw) * position[0] / 100
            top += (h - sh) * position[1] / 100
            w, h = sw, sh
        obj = shapes.add_picture(BytesIO(data), *emu((left, top, w, h)))
        if fit == "cover":
            crop_x, crop_y = max(0, 1 - w / h / (iw / ih)), max(0, 1 - h / w / (ih / iw))
            obj.crop_left, obj.crop_right = crop_x * position[0] / 100, crop_x * (1 - position[0] / 100)
            obj.crop_top, obj.crop_bottom = crop_y * position[1] / 100, crop_y * (1 - position[1] / 100)
        return obj

    def color(name, paint):
        return RGBColor.from_string(colors[paint.get(name, name)].lstrip("#"))

    def line_style(obj, layer, paint, region_width):
        obj.line.color.rgb = color(layer["stroke"], paint)
        obj.line.width = Pt(region_width / 12700 * tokens["strokes"][layer["weight"]] / 1600)

    def text(shapes, layer, bounds, slots, paint, font_width):
        obj = shapes.add_textbox(*emu(bounds))
        tf = obj.text_frame
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.word_wrap, tf.vertical_anchor, tf.auto_size = True, MSO_ANCHOR.MIDDLE, MSO_AUTO_SIZE.NONE
        style = tokens["type"][layer["type"]]
        fonts = [name.strip() for name in style["font"].split(",")]
        font = next((name for name in fonts if name not in {"sans-serif", "serif", "monospace"}), "Arial")
        east_asian = next((name for name in fonts if name.startswith(("PingFang", "Microsoft YaHei", "Noto Sans CJK",
                                                                        "Hiragino", "SimHei", "SimSun"))), font)
        value = slots[layer["slot"]] if "slot" in layer else layer["value"]
        phrase = slots.get(layer.get("underline_slot"), "")
        start = value.find(phrase) if phrase else -1
        end = start + len(phrase)
        offset = 0
        for i, row in enumerate(value.split("\n")):
            para = tf.add_paragraph() if i else tf.paragraphs[0]
            para.space_before = para.space_after = Pt(0)
            para.line_spacing = style["leading"]
            para.alignment = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}[layer["align"]]
            marks = sorted({0, len(row), *(index - offset for index in (start, end)
                                           if start >= 0 and offset < index < offset + len(row))})
            for a, b in zip(marks, marks[1:]):
                run = para.add_run()
                run.text = row[a:b]
                run.font.name, run.font.bold = font, style["weight"] >= 600
                run.font.size = Pt(font_width / 12700 * style["size"] / 100)
                run.font.color.rgb = color(layer["ink"], paint)
                if start >= 0 and start <= offset + a < end:
                    run.font.underline = True
                east_asian_font = OxmlElement("a:ea")
                east_asian_font.set("typeface", east_asian)
                run._r.get_or_add_rPr().append(east_asian_font)
            offset += len(row) + 1
        return obj

    def draw(shapes, layer, slots, region, font_width, paint):
        kind, identifier = layer["kind"], layer["id"]
        if kind == "motif":
            obj = shapes.add_group_shape()
            nested = frame(layer["box"], region)
            bindings = layer.get("bindings", {})
            for part in system["motifs"][layer["motif"]]:
                draw(obj.shapes, part, {k: slots[v] for k, v in bindings.items()}, nested,
                     font_width if bindings else nested[2], layer.get("paint", {}))
        elif kind in {"line", "curve"}:
            require(kind == "line", f"Native PPTX does not support curve {identifier}; use --html-only")
            points = [frame([x, y, 0, 0], region)[:2] for x, y in layer["points"]]
            obj = shapes.add_connector(MSO_CONNECTOR.STRAIGHT, *emu(points[0] + points[1]))
            line_style(obj, layer, paint, region[2])
            if layer.get("arrow"):
                tail = OxmlElement("a:tailEnd")
                tail.set("type", "triangle")
                obj._element.spPr.get_or_add_ln().append(tail)
        else:
            bounds = frame(layer["box"], region)
            if kind == "text":
                obj = text(shapes, layer, bounds, slots, paint, font_width)
            elif kind == "box":
                obj = shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if "radius" in layer else MSO_SHAPE.RECTANGLE,
                                       *emu(bounds))
                obj.fill.solid()
                obj.fill.fore_color.rgb = color(layer["fill"], paint)
                if "radius" in layer:
                    obj.adjustments[0] = min(.5, font_width * tokens["radii"][layer["radius"]] / 100 / min(bounds[2:]))
                if "stroke" in layer:
                    line_style(obj, layer, paint, font_width)
                else:
                    obj.line.fill.background()
            else:
                if "asset" in layer:
                    fixed = system["fixed_assets"][layer["asset"]]
                    url = asset(fixed["file"], fixed["sha256"])
                else:
                    url = asset(slots[layer["slot"]])
                obj = picture(shapes, url, bounds, layer["fit"], layer["position"])
                if "radius" in layer:
                    obj._element.spPr.prstGeom.set("prst", "roundRect")
            obj.rotation = layer.get("rotation", 0)
        if kind in {"line", "box"}:
            for theme_style in obj._element.xpath("./p:style"):
                obj._element.remove(theme_style)
        obj.name = identifier

    for page in pages:
        slide = deck.slides.add_slide(deck.slide_layouts[6])
        pattern = system["patterns"][page["pattern"]]
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = color(pattern["background"], {})
        backdrop = system["families"][pattern["family"]].get("backdrop")
        if backdrop:
            obj = picture(slide.shapes, asset(backdrop["file"], backdrop["sha256"], backdrop=True),
                          (0, 0, width, height), "fill", (50, 50))
            obj.name = "background-artwork"
        for layer in pattern["layers"]:
            change = boxes.get(page["id"], {}).get(layer["id"])
            draw(slide.shapes, {**layer, "box": change} if change else layer, page["slots"], (0, 0, width, height), width, {})
    deck.save(output)
