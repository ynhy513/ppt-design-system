"""Replay a reviewed visual system and an approved page plan into offline HTML."""

import argparse
from base64 import b64encode
from functools import cache
from hashlib import file_digest, sha256
from html import escape
from io import BytesIO
import json
from pathlib import Path
import re
from zipfile import ZipFile

from jsonschema import ValidationError, validate
from PIL import Image

SCHEMA = Path(__file__).resolve().parents[1] / "references/design-system.schema.json"
FIELDS = {
    "box": ({"box", "fill"}, {"radius", "stroke", "weight", "rotation"}),
    "text": ({"box", "type", "ink", "align"}, {"slot", "value", "rotation", "underline_slot"}),
    "image": ({"box", "fit", "position"}, {"slot", "asset", "radius", "rotation"}),
    "line": ({"points", "stroke", "weight"}, {"arrow"}),
    "curve": ({"points", "stroke", "weight"}, {"arrow"}),
    "motif": ({"box", "motif"}, {"paint", "bindings"}),
}
TOKEN_GROUPS = {
    "fill": "colors", "ink": "colors", "stroke": "colors", "type": "type",
    "radius": "radii", "weight": "strokes",
}
PAGE_FIELDS = {"id", "role", "pattern", "focus", "density", "weight", "slots"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"Invalid JSON number: {value}")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates,
                      parse_constant=reject_constant)


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def box_ok(box):
    x, y, w, h = box
    return w > 0 and h > 0 and x + w <= 100.001 and y + h <= 100.001


def check_layers(layers, system, motif_slots=None):
    inside_motif = motif_slots is None
    ids, slots = set(), {}
    for layer in layers:
        kind, identifier = layer["kind"], layer["id"]
        required, optional = FIELDS[kind]
        fields = layer.keys() - {"kind", "id"}
        require(required <= fields <= required | optional, f"Invalid fields for {identifier}")
        require(identifier not in ids, f"Duplicate layer: {identifier}")
        ids.add(identifier)
        if "box" in layer:
            require(box_ok(layer["box"]), f"Out-of-canvas layer: {identifier}")
        for field, group in TOKEN_GROUPS.items():
            if field in layer:
                require(layer[field] in system["tokens"][group], f"Unknown {field} token on {identifier}")
        require(("stroke" in layer) == ("weight" in layer), f"Incomplete stroke on {identifier}")
        if kind == "curve":
            require(len(layer["points"]) == 4, f"Curve {identifier} needs four points")
        if kind == "text":
            require(("slot" in layer) != ("value" in layer), f"Supply text or a slot on {identifier}")
        if kind == "image":
            require(not inside_motif, f"Image in motif: {identifier}")
            require(("slot" in layer) != ("asset" in layer), f"Supply a fixed asset or image slot on {identifier}")
            if "asset" in layer:
                require(layer["asset"] in system.get("fixed_assets", {}), f"Unknown fixed image on {identifier}")
        if "slot" in layer:
            name = layer["slot"]
            require(name not in slots, f"Unavailable or repeated slot: {name}")
            slots[name] = kind
        if "underline_slot" in layer:
            name = layer["underline_slot"]
            require(not inside_motif and "slot" in layer and name not in slots,
                    f"Unavailable or repeated underline slot: {name}")
            slots[name] = "text"
        if kind == "motif":
            name = layer["motif"]
            require(not inside_motif and name in motif_slots, f"Unknown or nested motif: {identifier}")
            bindings = layer.get("bindings", {})
            inner_slots = motif_slots[name]
            require(bindings.keys() == inner_slots.keys(), f"Motif slot bindings do not match on {identifier}")
            page_slots = set(bindings.values())
            require(len(page_slots) == len(bindings) and page_slots.isdisjoint(slots),
                    f"Repeated page slot on motif {identifier}")
            slots.update((page_slot, inner_slots[inner_slot]) for inner_slot, page_slot in bindings.items())
            colors = system["tokens"]["colors"]
            for key, value in layer.get("paint", {}).items():
                used = {part[field] for part in system["motifs"][name]
                        for field in ("fill", "ink", "stroke") if field in part}
                require(key in used and value in colors, f"Invalid motif color override: {key}")
    return ids, slots


def used_tokens(layers, system, paint=None):
    paint = paint or {}
    for layer in layers:
        for field, group in TOKEN_GROUPS.items():
            if field in layer:
                name = layer[field]
                yield f"{group}.{paint.get(name, name) if group == 'colors' else name}"
        if layer["kind"] == "motif":
            yield from used_tokens(system["motifs"][layer["motif"]], system, layer.get("paint"))


def check_system(system):
    validate(system, load(SCHEMA))
    family = system["primary_family"]
    families, evidence, rules = (system[key] for key in ("families", "evidence", "rules"))
    require([name for name, item in families.items() if item["scope"] == "primary"] == [family],
            "Select exactly one primary family")
    assigned = [p for item in families.values() for p in item["pages"]]
    require(len(set(assigned)) == len(assigned), "A source page may be assigned to only one family")
    require(all(p <= system["source"]["pages"] for p in assigned), "Family page out of bounds")
    for key, item in evidence.items():
        require(item["page"] in assigned and box_ok(item["region"]), f"Unassigned page or invalid region: {key}")
    for name, item in families.items():
        if backdrop := item.get("backdrop"):
            reference = evidence.get(backdrop["evidence"])
            require(item["scope"] != "excluded" and reference is not None and reference["page"] in item["pages"],
                    f"Background must cite its own approved family: {name}")
    for key, rule in rules.items():
        require(all(ref in evidence for ref in rule["evidence"]), f"Missing evidence for rule {key}")
    fixed_assets = system.get("fixed_assets", {})
    require(not fixed_assets or system["source"]["kind"] == "pptx", "Fixed image verification requires a PPTX source")
    for key, asset in fixed_assets.items():
        ref = evidence.get(asset["evidence"])
        require(ref and len(ref.get("objects", [])) == 1, f"Fixed image requires one source object: {key}")
    token_keys = {f"{group}.{name}" for group, items in system["tokens"].items() for name in items}
    require(system["token_rules"].keys() == token_keys, "Every token needs exactly one provenance rule")
    for name, rule in system["token_rules"].items():
        require(rule in rules, f"Unknown token rule on {name}")
    motif_slots = {name: check_layers(layers, system)[1] for name, layers in system["motifs"].items()}
    contracts = {}
    allowed = {page for item in families.values() if item["scope"] != "excluded" for page in item["pages"]}
    for key, pattern in system["patterns"].items():
        name = pattern["family"]
        require(name in families and families[name]["scope"] != "excluded", f"Disallowed family on {key}")
        require(pattern["background"] in system["tokens"]["colors"], f"Unknown background on {key}")
        require(all(ref in rules for ref in pattern["rules"]), f"Unknown rule on {key}")
        contracts[key] = check_layers(pattern["layers"], system, motif_slots)
        token_names = {f'colors.{pattern["background"]}', *used_tokens(pattern["layers"], system)}
        rule_ids = {*pattern["rules"], *(system["token_rules"][name] for name in token_names)}
        pages = {evidence[ev]["page"] for ref in rule_ids for ev in rules[ref]["evidence"]}
        require(pages.intersection(families[name]["pages"]), f"No same-family evidence on {key}")
        require(pages <= allowed, f"Excluded source evidence used on {key}")
        for layer in pattern["layers"]:
            if layer["kind"] == "image" and "asset" in layer:
                ref = evidence[fixed_assets[layer["asset"]]["evidence"]]
                require(ref["page"] in families[name]["pages"], f"Fixed image uses a different source family: {layer['id']}")
    for name, steps in system.get("sequences", {}).items():
        for step in steps:
            require(all(pattern in contracts and step["focus"] in contracts[pattern][0]
                        for pattern in step["patterns"]), f"Invalid pattern or focus in sequence {name}")
            require(len({system["patterns"][p]["role"] for p in step["patterns"]}) == 1,
                    f"Sequence variants must serve the same role: {name}")
    return contracts


def check_source(system, source):
    kind = system["source"]["kind"]
    require(digest(source) == system["source"]["sha256"], "Source SHA-256 does not match")
    if kind == "pptx":
        from pptx_source import load_source, source_shape
        from style_catalog import embedded_images

        deck, _ = load_source(source)
        count = len(deck.slides)
        for item in system["evidence"].values():
            for obj in item.get("objects", []):
                source_shape(deck, item["page"], obj)
        for key, asset in system.get("fixed_assets", {}).items():
            ref = system["evidence"][asset["evidence"]]
            obj = source_shape(deck, ref["page"], ref["objects"][0])
            expected = asset.get("source_sha256", asset["sha256"])
            require(any(sha256(part.blob).hexdigest() == expected for _, part, _ in embedded_images(obj)),
                    f"Fixed image does not match its source object: {key}")
    elif kind == "pdf":
        import pdfplumber
        with pdfplumber.open(source) as pdf:
            count = len(pdf.pages)
    else:
        count = 1
    require(count == system["source"]["pages"], "Source page count does not match")


def check_plan(plan, system, contracts):
    require(isinstance(plan, dict) and {"version", "pages"} <= plan.keys() <= {"version", "pages", "sequence"}
            and type(plan["version"]) is int
            and plan["version"] == 1, "Invalid plan version or fields")
    pages = plan["pages"]
    require(isinstance(pages, list) and 1 <= len(pages) <= 120, "Expected 1–120 pages")
    sequences = system.get("sequences", {})
    require(not sequences or "sequence" in plan, "This design system requires an approved sequence")
    seen = set()
    for page in pages:
        require(isinstance(page, dict) and page.keys() == PAGE_FIELDS, "Invalid page fields")
        identifier = page["id"]
        require(isinstance(identifier, str) and re.fullmatch(r"[a-z][a-z0-9-]{0,49}", identifier)
                and identifier not in seen, "Invalid or repeated page ID")
        seen.add(identifier)
        pattern = page["pattern"]
        require(isinstance(pattern, str) and pattern in contracts, f"Unapproved pattern on {identifier}")
        require(page["role"] == system["patterns"][pattern]["role"], f"Wrong layout role on {identifier}")
        ids, slots = contracts[pattern]
        require(isinstance(page["focus"], str) and page["focus"] in ids, f"Unknown focus on {identifier}")
        for key in ("density", "weight"):
            require(page[key] in ("low", "medium", "high"), f"Invalid {key} on {identifier}")
        require(isinstance(page["slots"], dict) and page["slots"].keys() == slots.keys(), f"Slot mismatch on {identifier}")
        underlines = {layer["underline_slot"]: layer for layer in system["patterns"][pattern]["layers"]
                      if "underline_slot" in layer}
        for name, value in page["slots"].items():
            require(isinstance(value, str) and (0 < len(value.strip()) <= 600 or (name in underlines and value == "")),
                    f"Invalid slot {name} on {identifier}")
        for name, layer in underlines.items():
            fragment = page["slots"][name]
            if not fragment:
                continue
            value = page["slots"][layer["slot"]]
            start = value.find(fragment)
            require(fragment == fragment.strip() and start >= 0 and value.find(fragment, start + 1) < 0,
                    f"Underline must match one exact phrase on {identifier}/{layer['id']}")
    if "sequence" in plan:
        name = plan["sequence"]
        require(isinstance(name, str) and name in sequences, "Unknown sequence")
        steps = sequences[name]
        require(len(steps) == len(pages), f"Unexpected page count for sequence {name}")
        for page, step in zip(pages, steps):
            require(page["pattern"] in step["patterns"] and all(page[k] == step[k]
                    for k in ("focus", "density", "weight")), f"Sequence drift on {page['id']}")
    return pages


def source_media(source):
    with ZipFile(source) as package:
        hashes = set()
        for item in package.infolist():
            if item.filename.startswith("ppt/media/") and not item.is_dir():
                with package.open(item) as stream:
                    hashes.add(file_digest(stream, "sha256").hexdigest())
        return hashes


def make_renderer(system, assets, original_media):
    tokens = system["tokens"]
    colors = tokens["colors"]
    asset_hashes = {}

    @cache
    def asset(name, expected_sha256=None, *, backdrop=False):
        require(assets is not None, f"Raster asset requires --assets: {name}")
        path = (assets / name).resolve()
        require(not Path(name).is_absolute() and path.is_relative_to(assets.resolve()) and path.is_file(),
                f"Image must resolve to a local file under --assets: {name}")
        require(path.stat().st_size <= 12 * 1024**2, f"Image exceeds 12 MiB: {name}")
        data = path.read_bytes()
        fingerprint = sha256(data).hexdigest()
        if expected_sha256 is None:
            require(fingerprint not in original_media, f"Original source media is present in the swap test: {name}")
        else:
            label = "background" if backdrop else "image"
            require(fingerprint == expected_sha256, f"Approved {label} SHA-256 does not match: {name}")
        with Image.open(BytesIO(data)) as im:
            require(im.format in {"PNG", "JPEG", "WEBP"} and im.width * im.height <= 16_000_000
                    and not getattr(im, "is_animated", False), f"Unsupported raster asset: {name}")
            if backdrop:
                require(im.width * 9 == im.height * 16, f"Background must fill the 16:9 canvas: {name}")
            mime = Image.MIME[im.format]
            im.verify()
        asset_hashes[name] = fingerprint
        return f"data:{mime};base64,{b64encode(data).decode()}"

    def draw(layer, slots, prefix, paint=None):
        paint = paint or {}
        kind, identifier = layer["kind"], layer["id"]
        attr = f'data-layer="{identifier}"'
        color = lambda field: colors[paint.get(layer[field], layer[field])]
        radius = f'{tokens["radii"][layer["radius"]]}cqw' if "radius" in layer else "0"
        if kind in {"line", "curve"}:
            points = [f"{x * 16:g},{y * 9:g}" for x, y in layer["points"]]
            path = f"M{points[0]} {'C' if kind == 'curve' else 'L'}{' '.join(points[1:])}"
            stroke = color("stroke")
            marker = f"{prefix}-{identifier}-arrow"
            tip = (f'<defs><marker id="{marker}" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">'
                   f'<path d="M0 0 L6 3 L0 6Z" fill="{stroke}"/></marker></defs>') if layer.get("arrow") else ""
            end = f' marker-end="url(#{marker})"' if tip else ""
            return (f'<svg class="vector" {attr} viewBox="0 0 1600 900" preserveAspectRatio="none" aria-hidden="true">{tip}'
                    f'<path d="{path}" fill="none" stroke="{stroke}" stroke-linecap="round" '
                    f'stroke-width="{tokens["strokes"][layer["weight"]]}"{end}/></svg>')
        x, y, w, h = layer["box"]
        pos = f"left:{x}%;top:{y}%;width:{w}%;height:{h}%"
        if rotation := layer.get("rotation"):
            pos += f";transform:rotate({rotation}deg)"
        if kind == "box":
            border = (f'border:{tokens["strokes"][layer["weight"]] / 16:g}cqw solid {color("stroke")};'
                      if "stroke" in layer else "")
            return f'<div {attr} style="{pos};background:{color("fill")};border-radius:{radius};{border}"></div>'
        if kind == "text":
            t = tokens["type"][layer["type"]]
            value = slots[layer["slot"]] if "slot" in layer else layer["value"]
            content = escape(value)
            phrase = slots[layer["underline_slot"]] if "underline_slot" in layer else ""
            if phrase:
                before, phrase, after = value.partition(phrase)
                content = (f'{escape(before)}<u style="text-underline-offset:.12em;'
                           f'text-decoration-thickness:.052em">{escape(phrase)}</u>{escape(after)}')
            style = (f'{pos};font:{t["weight"]} {t["size"]}cqw/{t["leading"]} {t["font"]};'
                     f'color:{color("ink")};text-align:{layer["align"]}')
            return f'<div class="text" {attr} style="{style}"><span>{content}</span></div>'
        if kind == "image":
            image_x, image_y = layer["position"]
            if "asset" in layer:
                fixed = system["fixed_assets"][layer["asset"]]
                url = asset(fixed["file"], fixed["sha256"])
            else:
                url = asset(slots[layer["slot"]])
            return (f'<img {attr} src="{url}" alt="" style="{pos};object-fit:{layer["fit"]};'
                    f'object-position:{image_x}% {image_y}%;border-radius:{radius}">')
        bindings = layer.get("bindings", {})
        component_slots = {inner: slots[outer] for inner, outer in bindings.items()}
        if bindings:
            # Bound text uses the slide's typography while the motif region controls its geometry.
            pos += ";container-type:normal"
        body = "".join(draw(part, component_slots, f"{prefix}-{identifier}", layer.get("paint"))
                       for part in system["motifs"][layer["motif"]])
        return f'<div class="motif" {attr} data-motif="{layer["motif"]}" style="{pos}">{body}</div>'

    return draw, asset, asset_hashes


def render(system, pages, draw, asset):
    cards = []
    for page in pages:
        pattern = system["patterns"][page["pattern"]]
        layers = "".join(draw(layer, page["slots"], page["id"]) for layer in pattern["layers"])
        surface = system["tokens"]["colors"][pattern["background"]]
        backdrop = system["families"][pattern["family"]].get("backdrop")
        background = ""
        if backdrop:
            url = asset(backdrop["file"], backdrop["sha256"], backdrop=True)
            background = f'<img class="backdrop" src="{url}" alt="">'
        cards.append(f'<article id="{page["id"]}" data-pattern="{page["pattern"]}" data-focus="{page["focus"]}"'
                     f' style="background:{surface}">{background}{layers}</article>')
    return ("""<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Design system replay</title><style>
*{box-sizing:border-box}body{margin:0;background:#e9e7e7}
article{position:relative;container-type:inline-size;width:min(100%,1200px);aspect-ratio:16/9;margin:18px auto;overflow:hidden}
[data-layer]{position:absolute;display:block}.vector{inset:0;width:100%;height:100%}
.backdrop{position:absolute;inset:0;width:100%;height:100%;display:block}
.text{display:flex;align-items:center}.text span{display:block;width:100%;white-space:pre-wrap;overflow-wrap:anywhere}
.motif{container-type:inline-size}
@media print{article{margin:0;width:100%;break-after:page}}
</style><main>""" + "\n".join(cards) + "</main></html>\n")


def style_guide(system):
    labels = {"primary": "主风格", "support": "辅助", "excluded": "排除"}
    kinds = {"measured": "实测", "observed": "观察", "inferred": "归纳", "extended": "延展"}
    result = ["# STYLE.md", "", f"主风格 `{system['primary_family']}` · 原稿 {system['source']['pages']} 页",
              "", "## 风格范围", ""]
    for name, family in system["families"].items():
        pages = "、".join(map(str, family["pages"]))
        result.append(f"- **{name}** · {labels[family['scope']]} · 第 {pages} 页。{family['reason']}")
        if backdrop := family.get("backdrop"):
            reference = system["evidence"][backdrop["evidence"]]
            result.append(f"  - 固定背景来自第 {reference['page']} 页 · `{backdrop['evidence']}`。{reference['finding']}")
    result.extend(["", "## 设计规则", ""])
    for name, rule in system["rules"].items():
        result.append(f"- **{name}** · {kinds[rule['kind']]} · {rule['policy']}。{rule['statement']}")
        for key in rule["evidence"]:
            evidence = system["evidence"][key]
            objects = "，对象 " + "、".join(map(str, evidence["objects"])) if evidence.get("objects") else ""
            result.append(f"  - 第 {evidence['page']} 页{objects} · `{key}`。{evidence['finding']}")
    result.extend(["", "## 可用版式", ""])
    for name, pattern in system["patterns"].items():
        rules = "、".join(pattern["rules"])
        result.append(f"- **{name}** · {pattern['role']}。{pattern['reason']} 规则 {rules}。")
    result.extend(["", "具体色值、字阶、形状、槽位和共享图形以配套的设计包为准。"])
    return "\n".join(result) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("system", type=Path)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--out", type=Path, required=True, help="New output directory")
    parser.add_argument("--source", type=Path, help="Verify the original file and evidence addresses")
    parser.add_argument("--assets", type=Path, help="Root for replacement raster assets")
    args = parser.parse_args()
    try:
        system, plan = load(args.system), load(args.plan)
        contracts = check_system(system)
        pages = check_plan(plan, system, contracts)
        if args.source:
            check_source(system, args.source)
        original_media = (source_media(args.source)
                          if args.source and system["source"]["kind"] == "pptx" else set())
        draw, asset, assets = make_renderer(system, args.assets, original_media)
        html = render(system, pages, draw, asset)
        used_families = {system["patterns"][page["pattern"]]["family"] for page in pages}
        backdrops = {name: item["backdrop"] for name, item in system["families"].items()
                     if name in used_families and "backdrop" in item}
        receipt = {
            "system_sha256": digest(args.system), "plan_sha256": digest(args.plan),
            "renderer_sha256": digest(Path(__file__)), "html_sha256": sha256(html.encode()).hexdigest(),
            "source_addresses_verified": args.source is not None,
            "pptx_exact_media_guard": bool(args.source and system["source"]["kind"] == "pptx"),
            "asset_sha256": assets, "sequence": plan.get("sequence"),
            "source_backdrops": backdrops,
            "source_fixed_assets": {key: item for key, item in system.get("fixed_assets", {}).items()
                                    if item["file"] in assets},
            "pages": [{k: page[k] for k in ("id", "role", "pattern", "focus", "density", "weight")}
                      for page in pages],
        }
        args.out.mkdir(parents=True, exist_ok=False)
        (args.out / "replay.html").write_text(html, encoding="utf-8")
        (args.out / "STYLE.md").write_text(style_guide(system), encoding="utf-8")
        (args.out / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
                                               encoding="utf-8")
    except (ValueError, ValidationError, OSError) as exc:
        parser.exit(2, f"Replay rejected: {exc}\n")


if __name__ == "__main__":
    main()
