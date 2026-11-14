"""Inventory source artwork and check component coverage against a neutral manuscript."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import BadZipFile, ZipFile

from jsonschema import ValidationError
from PIL import Image

from compile_story import check_manuscript, compile_story
from design_replay import digest, load, reject_constant, reject_duplicates, require
from package_design import MANIFEST, ZIP_ROOT, check_directory, check_zip
from style_catalog import catalog as pptx_catalog


DEFAULT_PROBE = Path(__file__).resolve().parents[1] / "references" / "coverage-probe.json"
PACK_FILES = ("design-system.json", "element-catalog.json", "style-grammar.json", MANIFEST)
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
IMAGE_FORMATS = {"PNG", "JPEG", "WEBP"}
DECISIONS = {
    "ready-to-fill": "可直接填槽",
    "completed": "补足后可填槽",
    "adapt": "可改造现有结构",
    "extend": "需按风格延展",
    "pending": "待人工核对",
}


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def table(headers, rows):
    def line(cells):
        return "| " + " | ".join(str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                                  .replace("|", "&#124;").replace("\n", " ") for value in cells) + " |"
    return "\n".join([line(headers), line(["---"] * len(headers)), *(line(row) for row in rows)])


def pdf_inventory(source, assets, catalog):
    import pdfplumber
    from pdfminer.pdfexceptions import PDFException
    from pdfminer.pdftypes import PDFStream, resolve1
    from pdfminer.psparser import literal_name

    objects = []

    def extract_stream(stream, context):
        raw = stream.get_rawdata()
        if not raw:
            return None
        filters = [literal_name(name) for name, _ in stream.get_filters()]
        suffix, mime = (".jpg", "image/jpeg") if filters == ["DCTDecode"] and raw.startswith(b"\xff\xd8") else (
            ".bin", "application/octet-stream"
        )
        fingerprint = sha256(raw).hexdigest()
        filename = fingerprint + suffix
        destination = assets / filename
        if not destination.exists():
            destination.write_bytes(raw)
        return {"part": f"xref:{stream.objid}" if stream.objid is not None else "inline",
                "file": filename, "sha256": fingerprint, "mime": mime, "crop": {},
                "filters": filters, "needs_context": context or suffix == ".bin"}

    try:
        with pdfplumber.open(source) as pdf:
            require(not pdf.doc.encryption, "PDF inventory requires an unencrypted PDF")
            catalog["pages"] = len(pdf.pages)
            require(catalog["pages"] > 0, "PDF contains no pages")
            for page in pdf.pages:
                for index, image in enumerate(page.images, 1):
                    stream = image["stream"]
                    masks = [resolve1(stream.attrs[key]) for key in ("SMask", "Mask") if key in stream.attrs]
                    contextual = bool(image["imagemask"] or masks or stream.attrs.get("Decode")
                                      or stream.attrs.get("SMaskInData"))
                    original = extract_stream(stream, contextual)
                    media = [original] if original else []
                    for mask in masks:
                        if isinstance(mask, PDFStream) and (record := extract_stream(mask, True)):
                            if record not in media:
                                media.append(record)
                    identifier = f"p{page.page_number}-image-{index}"
                    bounds = [round(value / dimension, 6) for value, dimension in zip(
                        (image["x0"] - page.bbox[0], image["top"] - page.bbox[1], image["width"], image["height"]),
                        (page.width, page.height, page.width, page.height),
                    )]
                    token_ids = []
                    for record in media:
                        value = {key: record[key] for key in ("sha256", "mime", "crop")}
                        token_id = "asset-" + sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:16]
                        catalog["tokens"][token_id] = {"kind": "asset", "value": value}
                        if token_id not in token_ids:
                            token_ids.append(token_id)
                    obj = {"page": page.page_number, "object": index, "kind": "PDF_IMAGE",
                           "bounds": bounds, "pixel_size": list(image["srcsize"]), "xref": stream.objid}
                    catalog["objects"][identifier] = {**obj, "tokens": token_ids}
                    objects.append({"id": identifier, **obj, "media": media,
                                    "status": "exported" if media else "no-embedded-image"})
                page.close()
    except PDFException as error:
        raise ValueError(f"Cannot read PDF image evidence: {error}") from error
    return objects


def scan_source(source, out):
    assets = out / "assets"
    suffix = source.suffix.lower()
    if suffix == ".pptx":
        catalog = pptx_catalog(source, assets_out=assets)
        kind, manifest = "pptx", load(assets / "assets-manifest.json")
    else:
        assets.mkdir()
        catalog = {"version": 1, "source_sha256": digest(source), "pages": 1, "objects": {}, "tokens": {}}
        if suffix == ".pdf":
            kind, objects = "pdf", pdf_inventory(source, assets, catalog)
        else:
            require(suffix in IMAGE_SUFFIXES, "Expected PPTX, PDF, PNG, JPEG or WebP")
            kind, objects = "image", []
            with Image.open(source) as image:
                require(image.format in IMAGE_FORMATS and getattr(image, "n_frames", 1) == 1,
                        "Expected a single screenshot")
                image.verify()
                catalog["tokens"]["raster-frame"] = {"kind": "raster-frame",
                                                      "value": {"pixel_size": list(image.size),
                                                                "format": image.format}}
            catalog["objects"]["p1-frame"] = {"page": 1, "object": 1, "kind": "RASTER_FRAME",
                                              "bounds": [0, 0, 1, 1], "tokens": ["raster-frame"]}
        manifest = {"version": 1, "source_sha256": catalog["source_sha256"], "objects": objects}
        require(digest(source) == catalog["source_sha256"], "Source changed during extraction")
        save_json(assets / "assets-manifest.json", manifest)
    catalog["source_kind"] = kind
    save_json(out / "element-catalog.json", catalog)
    return catalog, manifest


def inventory_markdown(catalog, manifest):
    kind = catalog["source_kind"]
    rows, unique = [], set()
    for obj in manifest["objects"]:
        for item in obj["media"] or [{}]:
            source = item.get("part", "—")
            crop = ", ".join(f"{edge}={value}" for edge, value in item.get("crop", {}).items()) or "—"
            file = item.get("file", "—")
            if item:
                unique.add(item["sha256"])
            status = "需解码或合成" if item.get("needs_context") else (
                "原件已剥离" if item else "未发现独立媒体"
            )
            if item and not item.get("needs_context") and item["mime"] not in {
                "image/png", "image/jpeg", "image/jpg", "image/webp",
            }:
                status += " · HTML 需转格式"
            bounds = ", ".join(f"{value:.3f}" for value in obj.get("bounds", ())) or "—"
            rows.append((obj["id"], source, bounds, crop, file, status,
                         obj.get("role", "待判定"), obj.get("follows", "待判定")))
    output = ["# 素材清单", "", f"来源 **{kind}** · {catalog['pages']} 页 · "
              f"{len(manifest['objects'])} 个登记实例 · {len(unique)} 份去重原件", "",
              f"来源 SHA-256 `{catalog['source_sha256']}`", "",
              "原件可导出是文件证据。页面角色、取舍和实际渲染效果需结合预览核对。", ""]
    if kind == "pdf":
        output += ["PDF 的区域来自图像绘制实例。实际裁切、遮挡和透明度以页面预览为准。", ""]
    if kind == "pptx":
        output += ["组内对象保留原始坐标及父组地址。摆放时结合父组变换与预览核对。", ""]
    if kind == "image":
        size = catalog.get("tokens", {}).get("raster-frame", {}).get("value", {}).get("pixel_size")
        output += [f"整张截图提供视觉证据{' · ' + ' × '.join(map(str, size)) if size else ''}。"
                   "裁切与重建件可在审阅后登记，截图内的独立原件和图层待确认。", ""]
    if rows:
        output.append(table(("实例", "包内地址", "画幅内区域", "源裁切", "文件", "文件状态", "视觉角色", "跟随"), rows))
    derivatives = manifest.get("derivatives", [])
    if derivatives:
        output += ["", "## 衍生件", "", table(("文件", "来源", "处理", "角色"), (
            (d["file"], "、".join(d.get("sources", []) + d.get("evidence", [])),
             d["treatment"], d.get("role", "待判定")) for d in derivatives))]
    if photos := manifest.get("stock_photos", []):
        output += ["", "## 随包复用的外部照片", "", table(
            ("文件", "作者", "作品页", "许可", "角色", "摆放和裁切", "分发依据"),
            ((photo["file"], photo["creator"], photo["source_url"], photo["license_url"],
              photo["role"], photo["reuse"], photo["distribution_basis"]) for photo in photos))]
    return "\n".join(output) + "\n"


def read_pack(path, catalog, probe):
    errors = check_directory(path, None) if path.is_dir() else check_zip(path)
    require(not errors, "Design pack rejected: " + "; ".join(errors))
    if path.is_dir():
        system, pack_catalog, grammar, manifest = (load(path / name) for name in PACK_FILES)
    else:
        with ZipFile(path) as archive:
            system, pack_catalog, grammar, manifest = (
                json.loads(archive.read(ZIP_ROOT + name), object_pairs_hook=reject_duplicates,
                           parse_constant=reject_constant) for name in PACK_FILES
            )
    require(system["source"] == {"kind": catalog["source_kind"], "sha256": catalog["source_sha256"],
                                  "pages": catalog["pages"]}, "Design pack does not describe the scanned source")
    require(not system.get("sequences") or "sequence" in probe, "Probe must name the design pack's approved sequence")
    _, matches = compile_story(system, pack_catalog, grammar, probe)
    for row in matches["compiled"]:
        recipe = grammar["recipes"][row["recipe"]]
        layers = system["patterns"][row["pattern"]]["layers"]
        focus = next(layer for layer in layers if layer["id"] == recipe["focus"])
        row["placement"] = "slot-bound-motif" if focus.get("bindings") else "page-recipe"
        row["slot_limits"] = recipe["limits"]
    return matches, manifest, pack_catalog


def coverage(catalog, probe, probe_sha, current=None, baseline=None, review=None):
    review = {} if review is None else review
    chapters = probe["chapters"]
    require(isinstance(review, dict) and review.keys() <= {c["id"] for c in chapters},
            "Review entries must name probe chapter IDs")
    matches = {row["chapter"]: row for row in (current or {}).get("compiled", [])}
    gaps = {row["chapter"]: row for row in (current or {}).get("extensions_needed", [])}
    before = {row["chapter"]: row for group in (baseline or {}).values() for row in group}
    previously_matched = {row["chapter"] for row in (baseline or {}).get("compiled", [])}
    rows = []
    for chapter in chapters:
        identifier = chapter["id"]
        judgment = review.get(identifier)
        if identifier in review:
            require(isinstance(judgment, dict) and judgment.keys() == {"decision", "evidence", "note"}
                    and judgment["decision"] in {"adapt", "extend", "pending"}
                    and isinstance(judgment["evidence"], list) and judgment["evidence"]
                    and all(ref in catalog["objects"] for ref in judgment["evidence"])
                    and isinstance(judgment["note"], str) and judgment["note"].strip(),
                    f"Review needs a decision, known evidence IDs and a note: {identifier}")
        match, gap = matches.get(identifier), gaps.get(identifier)
        if match:
            state = "completed" if baseline is not None and identifier not in previously_matched else "ready-to-fill"
        elif judgment is not None:
            state = judgment["decision"]
        else:
            state = "pending"
        rows.append({"id": identifier, "relation": chapter["relation"],
                     "fields": list(chapter["fields"]), "item_fields": [list(item) for item in chapter["items"]],
                     "status": state, "match": match, "gap": gap,
                     "baseline": before.get(identifier), "review": judgment})
    return {"version": 1, "source_sha256": catalog["source_sha256"], "probe_sha256": probe_sha,
            "phase": "assessed" if current is not None else "scanned", "rows": rows}


def coverage_markdown(report):
    rows = []
    for row in report["rows"]:
        match, gap, judgment = row["match"], row["gap"], row["review"]
        if match:
            placement = "独立绑定图形" if match["placement"] == "slot-bound-motif" else "整页配方"
            note = f"{match['recipe']}（{placement}）"
        else:
            note = gap["reason"] if gap else "等待设计包与语义配方"
        if gap:
            details = [f"{name}：{reason}" for name, reason in gap["rejected"].items()]
            if gap["candidates"]:
                details.append("待取舍配方 " + "、".join(gap["candidates"]))
            if gap["reusable_elements"]:
                details.append("相关元素 " + "、".join(gap["reusable_elements"]))
            note = "；".join([note, *details])
        evidence = sorted({ref for item in (match or {}).get("elements", {}).values() for ref in item["source"]})
        if judgment:
            evidence += [ref for ref in judgment["evidence"] if ref not in evidence]
            note += "。人工评审：" + judgment["note"]
        baseline = row["baseline"]
        before = (baseline.get("recipe") or baseline.get("reason")) if baseline else "—"
        fields = "、".join(row["fields"]) or "—"
        item_fields = "、".join(dict.fromkeys(key for item in row["item_fields"] for key in item))
        contract = f"{fields} / {len(row['item_fields'])} 项" + (f" × {item_fields}" if item_fields else "")
        rows.append((row["id"], row["relation"], contract, DECISIONS[row["status"]],
                     before, note, "、".join(evidence) or "—"))
    return "\n".join(["# 组件覆盖表", "", f"试验稿 SHA-256 `{report['probe_sha256']}`", "",
                      "填槽状态由正式编译器按试验稿检查。视觉复用和字符上限仍需回放核对。"
                      "改造与延展结论来自带来源证据的人工评审。", "",
                      table(("章节", "内容关系", "字段与项数", "状态", "原包结果", "本轮依据", "来源证据"), rows), ""])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    scan = subcommands.add_parser("scan", help="Extract source media and write initial coverage")
    scan.add_argument("source", type=Path)
    assess = subcommands.add_parser("assess", help="Reassess coverage with a reviewed design pack")
    assess.add_argument("scan", type=Path, help="Output directory of the scan command")
    assess.add_argument("--pack", type=Path, required=True, help="Reviewed design pack directory or ZIP")
    assess.add_argument("--baseline", type=Path, help="Optional baseline pack for before/after comparison")
    assess.add_argument("--review", type=Path, help="Optional source-backed manual gap decisions")
    for command in (scan, assess):
        command.add_argument("--out", type=Path, required=True, help="New report directory")
        command.add_argument("--probe", type=Path, default=DEFAULT_PROBE, help="Neutral semantic manuscript")
    args = parser.parse_args()
    try:
        probe = load(args.probe)
        check_manuscript(probe)
        require(not args.out.exists() and not args.out.is_symlink(), f"Output already exists: {args.out}")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(dir=args.out.parent) as temporary:
            out = Path(temporary) / "result"
            out.mkdir()
            if args.command == "scan":
                catalog, manifest = scan_source(args.source, out)
                report = coverage(catalog, probe, digest(args.probe))
            else:
                scan_catalog = load(args.scan / "element-catalog.json")
                matches, manifest, catalog = read_pack(args.pack, scan_catalog, probe)
                catalog["source_kind"] = scan_catalog["source_kind"]
                catalog["objects"] = {**scan_catalog["objects"], **catalog["objects"]}
                before = read_pack(args.baseline, scan_catalog, probe)[0] if args.baseline else None
                review = load(args.review) if args.review else None
                report = coverage(catalog, probe, digest(args.probe), matches, before, review)
            (out / "asset-inventory.md").write_text(inventory_markdown(catalog, manifest), encoding="utf-8")
            save_json(out / "component-coverage.json", report)
            (out / "component-coverage.md").write_text(coverage_markdown(report), encoding="utf-8")
            out.rename(args.out)
    except (ValueError, OSError, KeyError, TypeError, BadZipFile, ValidationError, Image.DecompressionBombError) as error:
        parser.exit(2, f"Extract review rejected: {error}\n")
    print(f"Extract review written to {args.out}")


if __name__ == "__main__":
    main()
