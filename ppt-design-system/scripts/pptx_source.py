"""Read native PPTX geometry, typography and provenance for the design catalog."""

from hashlib import sha256
from io import BytesIO
from pathlib import PurePosixPath
from zipfile import ZipFile

from lxml import etree
from pptx import Presentation
from pptx.enum.dml import MSO_COLOR_TYPE, MSO_FILL_TYPE
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.oxml.ns import qn


THEME_ALIASES = {
    "BACKGROUND_1": "bg1", "TEXT_1": "tx1", "BACKGROUND_2": "bg2", "TEXT_2": "tx2",
    "DARK_1": "dk1", "DARK_2": "dk2", "LIGHT_1": "lt1", "LIGHT_2": "lt2",
}


def _walk(shapes):
    for shape in shapes:
        yield shape
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from _walk(shape.shapes)


def load_source(path):
    if path.suffix.lower() != ".pptx" or path.stat().st_size > 200 * 1024**2:
        raise ValueError("请使用 200 MB 以内的本机 PPTX。")
    data = path.read_bytes()
    with ZipFile(BytesIO(data)) as package:
        entries = package.infolist()
        names = [entry.filename for entry in entries]
        if (len(entries) > 4500 or len(set(names)) != len(names)
                or sum(entry.file_size for entry in entries) > 450 * 1024**2
                or any(entry.flag_bits & 1 or name.startswith("/") or "\\" in name
                       or ".." in PurePosixPath(name).parts or "vbaproject" in name.lower()
                       for entry, name in zip(entries, names))):
            raise ValueError("参考稿包含不支持的文件结构。")
    deck = Presentation(BytesIO(data))
    if not 1 <= len(deck.slides) <= 120:
        raise ValueError("候选 Skill 支持 1–120 页。")
    return deck, sha256(data).hexdigest()


def source_shape(deck, page, obj):
    if not 1 <= page <= len(deck.slides):
        raise ValueError("引用页码超出参考稿。")
    found = next((s for s in _walk(deck.slides[page-1].shapes) if s.shape_id == obj), None)
    if found is None:
        raise ValueError(f"找不到源稿第 {page} 页对象 {obj}。")
    return found


def theme_for(slide):
    master = slide.slide_layout.slide_master
    rel = next((rel for rel in master.part.rels.values() if rel.reltype.endswith("/theme")), None)
    if not rel:
        return {}, {}, {}
    theme = etree.fromstring(rel.target_part.blob, etree.XMLParser(resolve_entities=False))
    colors = {}
    for slot in theme.iter(qn("a:clrScheme")):
        for item in slot:
            if len(item):
                value = item[0].get("lastClr") or item[0].get("val")
                if value and len(value) == 6:
                    colors[etree.QName(item).localname] = value.upper()
    fonts = {}
    for group, key in (("majorFont", "title"), ("minorFont", "body")):
        parent = next(theme.iter(qn(f"a:{group}")), None)
        if parent is not None:
            latin = parent.find(qn("a:latin"))
            if latin is not None:
                fonts[key] = latin.get("typeface")
    mapping = master._element.find(qn("p:clrMap"))
    color_map = dict(mapping.attrib) if mapping is not None else {}
    for owner in (slide.slide_layout, slide):
        override = owner._element.find(qn("p:clrMapOvr"))
        child = override.find(qn("a:overrideClrMapping")) if override is not None else None
        if child is not None:
            color_map.update(child.attrib)
    return colors, color_map, fonts


def color_of(color, theme):
    colors, mapping, _ = theme
    if color.type == MSO_COLOR_TYPE.RGB:
        value = str(color.rgb)
    elif color.type == MSO_COLOR_TYPE.SCHEME:
        key = color.theme_color.name
        slot = THEME_ALIASES.get(key, key.lower())
        value = colors.get(mapping.get(slot, slot))
    else:
        return None
    if not value or not color.brightness:
        return value
    brightness = color.brightness
    return "".join(f"{round((c + (255-c)*brightness) if brightness > 0 else c*(1+brightness)):02X}"
                   for c in rgb(value))


def fill_of(fill, theme):
    return color_of(fill.fore_color, theme) if fill.type == MSO_FILL_TYPE.SOLID else None


def rgb(value):
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))


def bounds(shape, width, height):
    return [round(value / dimension, 4) for value, dimension in
            zip((shape.left, shape.top, shape.width, shape.height), (width, height, width, height))]


def background(slide, theme):
    for kind, owner in (("slide", slide), ("layout", slide.slide_layout), ("master", slide.slide_layout.slide_master)):
        value = fill_of(owner.background.fill, theme)
        if value:
            return value, kind
    return "FFFFFF", "default"


def _type_style(shape, theme):
    paragraphs = shape.text_frame.paragraphs
    hits = []
    for para in paragraphs:
        for run in para.runs:
            weight = len(run.text.strip())
            if weight:
                font = run.font
                hits.append((weight, font.name or para.font.name,
                             font.size or para.font.size, color_of(font.color, theme) or color_of(para.font.color, theme)))
    if not hits:
        return None, None, None
    _, name, size, color = max(hits, key=lambda x: x[0])
    return name.strip() if name else None, round(size.pt, 2) if size else None, color


def align_of(shape):
    align = next((p.alignment for p in shape.text_frame.paragraphs if p.text.strip()), None)
    return {"LEFT": "left", "CENTER": "center", "RIGHT": "right"}.get(align.name if align else "")


def text_style(shape, theme, deck):
    font, pt, color = _type_style(shape, theme)
    presets = shape._element.xpath(".//a:rPr/a:solidFill/a:prstClr/@val")
    if color is None and presets and len(set(presets)) == 1:
        color = {"white": "FFFFFF", "black": "000000"}.get(presets[0])
    tf = shape.text_frame
    return {"align": align_of(shape), "font": font, "pt": pt, "color": color,
            "insets": [round(tf.margin_left / deck.slide_width, 4),
                       round(tf.margin_top / deck.slide_height, 4),
                       round(tf.margin_right / deck.slide_width, 4),
                       round(tf.margin_bottom / deck.slide_height, 4)]}
