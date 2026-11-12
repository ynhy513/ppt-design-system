"""Compile a confirmed semantic manuscript into an editable offline deck and native PPTX."""

import argparse
from base64 import b64decode, b64encode
from binascii import Error as Base64Error
from copy import deepcopy
from hashlib import sha256
from html import escape
from io import BytesIO
import json
from math import isfinite
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from zipfile import BadZipFile, ZipFile

from jsonschema import ValidationError
from PIL import Image

from compile_story import compile_story
from design_replay import check_plan, check_source, check_system, load, make_renderer, render, require, source_media
from native_deck import write_pptx
from package_design import ZIP_ROOT, check_directory, check_zip


HERE = Path(__file__).resolve().parent
EDITOR = HERE.parent / "assets"
IMAGE_MIME = {"image/png": "PNG", "image/jpeg": "JPEG", "image/webp": "WEBP"}
MAX_IMAGE_BYTES = 6 * 1024**2


def snapshot(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def editor_model(system, plan, grammar, trace, manuscript):
    recipes = {row["chapter"]: grammar["recipes"][row["recipe"]] for row in trace["compiled"]}
    chapters = {chapter["id"]: chapter for chapter in manuscript["chapters"]}
    result = {"version": 1, "base": sha256(snapshot([system, plan, recipes]).encode()).hexdigest(), "pages": {}}
    for page in plan["pages"]:
        identifier = page["id"]
        pattern = system["patterns"][page["pattern"]]
        layers = []
        boxes = {}
        for layer in pattern["layers"]:
            key = layer["id"]
            if layer["kind"] in {"box", "motif"} or "slot" in layer:
                boxes[key] = layer["box"]
            if "slot" in layer:
                entry = {"layer": key, "slot": layer["slot"], "kind": layer["kind"]}
                if "underline_slot" in layer:
                    entry["underline"] = layer["underline_slot"]
                layers.append(entry)
            if layer["kind"] == "motif":
                bindings = layer.get("bindings", {})
                layers.extend({"layer": part["id"], "group": key, "slot": bindings[part["slot"]], "kind": "text"}
                              for part in system["motifs"][layer["motif"]] if "slot" in part)
        for entry in layers:
            entry["limit"] = recipes[identifier]["limits"][entry["slot"]]
        chapter = chapters[identifier]
        fields = chapter["fields"]
        label = fields.get("title") or fields.get("headline") or chapter["intent"]
        title_slot = recipes[identifier]["fields"].get("title") or recipes[identifier]["fields"].get("headline")
        result["pages"][identifier] = {"title": label, "intent": chapter["intent"],
                                       "titleSlot": title_slot, "layers": layers, "boxes": boxes, "slots": page["slots"]}
    return result


def empty_edits(model):
    return {"version": 1, "base": model["base"], "pages": {}}


def image_edit(value, originals):
    require(isinstance(value, str) and len(value) <= MAX_IMAGE_BYTES * 4 // 3 + 128, "Replacement image exceeds 6 MiB")
    mime, sep, encoded = value.partition(";base64,")
    require(sep and mime.startswith("data:") and mime[5:] in IMAGE_MIME, "Expected PNG, JPEG or WebP image")
    data = b64decode(encoded, validate=True)
    require(len(data) <= MAX_IMAGE_BYTES, "Replacement image exceeds 6 MiB")
    digest = sha256(data).hexdigest()
    require(digest not in originals, "Replacement image matches source artwork")
    with Image.open(BytesIO(data)) as image:
        require(image.format == IMAGE_MIME[mime[5:]] and image.width * image.height <= 16_000_000
                and not getattr(image, "is_animated", False), "Unsupported replacement image")
        image.verify()
    return f"edited-{digest}", f"{mime};base64,{b64encode(data).decode()}"


def apply_edits(plan, model, edits, originals):
    require(isinstance(edits, dict) and edits.keys() == {"version", "base", "pages"}
            and type(edits["version"]) is int and edits["version"] == 1 and edits["base"] == model["base"]
            and isinstance(edits["pages"], dict) and edits["pages"].keys() <= model["pages"].keys(),
            "Edits belong to a different deck or have an invalid format")
    adjusted, boxes, images = deepcopy(plan), {}, {}
    for page in adjusted["pages"]:
        key = page["id"]
        if key not in edits["pages"]:
            continue
        patch = edits["pages"][key]
        require(isinstance(patch, dict) and patch.keys() <= {"slots", "boxes", "images"}
                and all(isinstance(value, dict) for value in patch.values()), f"Invalid edits on {key}")
        spec = model["pages"][key]
        fields = {entry["slot"]: entry for entry in spec["layers"]}
        for slot, value in patch.get("slots", {}).items():
            entry = fields.get(slot)
            require(entry and entry["kind"] == "text" and isinstance(value, str) and value.strip()
                    and len(value) <= entry["limit"] and not re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", value),
                    f"Invalid text or character limit exceeded on {key}/{slot}")
            page["slots"][slot] = value
            if underline := entry.get("underline"):
                phrase = page["slots"][underline]
                if phrase and value.count(phrase) != 1:
                    page["slots"][underline] = ""
        for slot, value in patch.get("images", {}).items():
            require(slot in fields and fields[slot]["kind"] == "image", f"Unknown image slot on {key}/{slot}")
            name, url = image_edit(value, originals)
            images[name] = url
            page["slots"][slot] = name
        for layer, box in patch.get("boxes", {}).items():
            require(layer in spec["boxes"] and isinstance(box, list) and len(box) == 4
                    and all(type(value) in {int, float} and isfinite(value) and 0 <= value <= 100 for value in box)
                    and min(box[2:]) >= .5 and box[0] + box[2] <= 100.001 and box[1] + box[3] <= 100.001,
                    f"Invalid layer position on {key}/{layer}")
            boxes.setdefault(key, {})[layer] = box
    return adjusted, boxes, images


def editable_html(static_html, model, edits, export_token=None):
    def payload(identifier, value):
        data = snapshot(value).replace("<", "\\u003c")
        return f'<script type="application/json" id="{identifier}">{data}</script>'

    chrome = (EDITOR / "deck-editor.html").read_text(encoding="utf-8")
    style = (EDITOR / "deck-editor.css").read_text(encoding="utf-8")
    script = (EDITOR / "deck-editor.js").read_text(encoding="utf-8")
    export = payload("deck-export", export_token) if export_token else ""
    return (static_html.replace("<title>Design system replay</title>", "<title>演示与编辑</title>", 1)
            .replace("</style><main>", f"</style><style>{style}</style>{chrome}<main>", 1)
            .replace("</main></html>", "</main>" + payload("deck-model", model) + payload("deck-edits", edits)
                     + export + f"<script>{script}</script></html>", 1))


def storyboard_text(model, plan, trace):
    compiled = {row["chapter"]: row for row in trace["compiled"]}
    lines = ["# 制作分镜", ""]
    for i, page in enumerate(plan["pages"], 1):
        key = page["id"]
        spec, choice = model["pages"][key], compiled[key]
        title = page["slots"].get(spec["titleSlot"], spec["title"])
        lines.extend([f"## {i}. {title}", "", spec["intent"], "",
                      f"- 版式 `{choice['pattern']}` · 焦点 `{page['focus']}` · 密度 `{page['density']}`",
                      f"- 已绑定来源元素 {'、'.join(choice['elements'])}", ""])
    return "\n".join(lines)


def make(args, stage, *, export_token=None):
    if args.pack.is_dir():
        pack = args.pack
        errors = check_directory(pack, None)
    else:
        errors = check_zip(args.pack)
        require(not errors, "Design pack rejected: " + " / ".join(errors))
        with ZipFile(args.pack) as zipped:
            zipped.extractall(stage.parent)
        pack = stage.parent / ZIP_ROOT
    require(not errors, "Design pack rejected: " + " / ".join(errors))
    system, catalog, grammar = [load(pack / name) for name in
                               ("design-system.json", "element-catalog.json", "style-grammar.json")]
    manuscript = load(args.manuscript)
    plan, trace = compile_story(system, catalog, grammar, manuscript)
    save_json(stage / "compile-report.json", trace)
    if plan is None:
        return False

    model = editor_model(system, plan, grammar, trace, manuscript)
    edits = load(args.edits) if args.edits else empty_edits(model)
    originals = set()
    if args.source:
        check_source(system, args.source)
        if system["source"]["kind"] == "pptx":
            originals = source_media(args.source)
    adjusted, boxes, replacements = apply_edits(plan, model, edits, originals)
    pages = check_plan(adjusted, system, check_system(system))

    _, fixed_asset, fixed_hashes = make_renderer(system, pack / "assets", set())
    _, content_asset, content_hashes = make_renderer(system, args.assets, originals)
    def asset(name, expected_sha256=None, *, backdrop=False):
        if expected_sha256 is not None:
            return fixed_asset(name, expected_sha256, backdrop=backdrop)
        if name in replacements:
            return replacements[name]
        return content_asset(name)

    draw, _, _ = make_renderer(system, None, set(), asset_resolver=asset)
    base = render(system, plan["pages"], draw, asset)
    replay = render(system, pages, draw, asset, boxes)
    (stage / "deck.html").write_text(editable_html(base, model, edits, export_token), encoding="utf-8")
    (stage / "replay.html").write_text(replay, encoding="utf-8")
    (stage / "storyboard.md").write_text(storyboard_text(model, adjusted, trace), encoding="utf-8")
    save_json(stage / "storyboard.json", plan)
    save_json(stage / "edits.json", edits)
    if not args.html_only:
        write_pptx(system, pages, boxes, asset, stage / "deck.pptx")
    save_json(stage / "make-report.json", {"pages": len(pages), "base": model["base"],
              "native_pptx": not args.html_only, "fixed_assets": fixed_hashes, "content_assets": content_hashes,
              "edited_pages": list(edits["pages"])})
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack", type=Path, help="Reviewed design pack directory or ZIP")
    parser.add_argument("manuscript", type=Path, help="Confirmed semantic manuscript")
    parser.add_argument("--assets", type=Path, help="Root for replaceable content assets")
    parser.add_argument("--source", type=Path, help="Verify original source and artwork")
    parser.add_argument("--edits", type=Path, help="Edits saved from the HTML editor")
    parser.add_argument("--html-only", action="store_true", help="Skip the native export")
    parser.add_argument("--out", type=Path, required=True, help="New output directory")
    args = parser.parse_args()
    try:
        require(not args.out.exists() and not args.out.is_symlink(), f"Output already exists: {args.out}")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(dir=args.out.parent) as temp:
            stage = Path(temp) / "made"
            stage.mkdir()
            success = make(args, stage)
            stage.rename(args.out)
    except (ValueError, TypeError, KeyError, OSError, BadZipFile, Base64Error,
            Image.DecompressionBombError, ValidationError) as error:
        parser.exit(2, f"Make rejected: {error}\n")
    if not success:
        parser.exit(2, f"Review the unmatched chapters in {args.out / 'compile-report.json'}\n")
    print(f"Deck written to {args.out}")


if __name__ == "__main__":
    main()
