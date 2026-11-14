"""Draft image actions from local source evidence and optional manuscript context."""

from collections import defaultdict
import re

from design_replay import box_ok, require


ACTIONS = {"reuse": "复用候选", "search": "搜图", "extend": "组件延展", "redraw": "重绘", "review": "待核对"}
MARKER = re.compile(r"image\s+(at top|below)|(?:上图|下图)[：:]?", re.I)
ART = re.compile(r"\bartwork\b|\b(?:painted|painting|illustrated by|illustration|watercolor)\b|插画|绘画|拼贴", re.I)
DIAGRAM = re.compile(r"\b(?:diagram|diagrams|workflow|flowchart|chart|charts)\b|图表|流程图|示意图", re.I)
MAP = re.compile(r"\bmaps?\b|地图", re.I)
PHOTO = re.compile(r"\b(?:photos?|photographs?|filmed|flmed|camera)\b|\bvisitors?\b.{0,60}\b(?:use|explore|read|view)\b|实拍|照片|摄影", re.I)
PROCESS = re.compile(r"\b(?:processes|workflow|workflows|flowchart)\b|工作流程|流程图", re.I)


def separate_lines(page):
    # PDF extraction can merge text across a spread on the same baseline.
    rows = []
    for line in page.extract_text_lines():
        group = []
        for char in sorted((c for c in line["chars"] if not c["text"].isspace()), key=lambda c: c["x0"]):
            if group and char["x0"] - group[-1]["x1"] > page.width * .045:
                rows.append(group)
                group = []
            group.append(char)
        if group:
            rows.append(group)
    lines = []
    for group in rows:
        text = group[0]["text"]
        for left, right in zip(group, group[1:]):
            space = " " if right["x0"] - left["x1"] > min(left["size"], right["size"]) * .12 else ""
            text += space + right["text"]
        lines.append({"text": text, "x0": group[0]["x0"], "x1": group[-1]["x1"],
                      "top": min(c["top"] for c in group), "bottom": max(c["bottom"] for c in group)})
    return lines


def pdf_signals(page, images):
    """Pair explicit top/below captions only when object order corroborates the pairing."""
    lines = separate_lines(page)
    captions = []
    for line in lines:
        if not MARKER.fullmatch(line["text"].strip()):
            continue
        left = (line["x0"] - page.bbox[0]) / page.width
        height = line["bottom"] - line["top"]
        candidates = sorted((other for other in lines
                             if other["top"] > line["top"] + height * .5
                             and min(abs(other["x0"] - line["x0"]), abs(other["x1"] - line["x1"]))
                             < page.width * .025),
                            key=lambda other: other["top"])
        words, end = [], line["bottom"]
        for part in candidates:
            if part["top"] - end > height * 1.35 or MARKER.fullmatch(part["text"].strip()):
                break
            words.append(part["text"])
            end = part["bottom"]
        if words:
            captions.append((left, line["top"], " ".join(words)[:360]))
    groups = defaultdict(list)
    for left, top, caption in sorted(captions):
        anchor = next((x for x in groups if abs(left - x) < .05), left)
        groups[anchor].append((top, caption))

    columns = defaultdict(list)
    for image in images:
        left, top, _, _ = image["bounds"]
        if groups:
            anchor = min(groups, key=lambda x: abs(x - left))
            if abs(anchor - left) <= .15:
                columns[anchor].append((top, image["id"]))
    matches = {}
    for anchor, column in columns.items():
        if len(column) == len(groups[anchor]) and len({top for top, _ in column}) == len(column):
            for (_, image_id), (_, caption) in zip(sorted(column), sorted(groups[anchor])):
                matches[image_id] = caption
    vectors = len(page.lines) + len(page.rects) + len(page.curves)
    has_process = vectors >= 12 and any(PROCESS.search(line["text"]) for line in lines)
    return {"captions": matches, "vector_objects": vectors, "process_cue": has_process}


def read_context(context, catalog):
    require(isinstance(context, dict) and context.keys() == {"regions"} and isinstance(context["regions"], list),
            "Image context needs an array of regions")
    pages = defaultdict(list)
    for row in context["regions"]:
        require(isinstance(row, dict) and {"page", "region", "subject"} <= row.keys() <=
                {"page", "region", "subject", "purpose", "identity_required"} and type(row["page"]) is int
                and 1 <= row["page"] <= catalog["pages"] and box_ok(row["region"])
                and type(row.get("identity_required", False)) is bool
                and all(isinstance(row[key], str) and row[key].strip() for key in row if key in {"subject", "purpose"}),
                "Image context needs a valid page, percent rectangle and target subject")
        pages[row["page"]].append(row)
    return pages


def targets_at(bounds, contexts):
    if not bounds:
        return []
    left, top, width, height = bounds
    center_x, center_y = (left + width / 2) * 100, (top + height / 2) * 100
    return [item for item in contexts if (rect := item["region"])[0] <= center_x < rect[0] + rect[2]
            and rect[1] <= center_y < rect[1] + rect[3]]


def recommendation(caption, target, native_kind):
    subject = target["subject"] if target else ""
    same = bool(subject) and " ".join(subject.casefold().split()) in " ".join(caption.casefold().split())
    if ART.search(caption):
        if target and target.get("identity_required", False):
            if same:
                return ("artwork", "reuse", "新稿需要特定作品，源图注与目标名称匹配。",
                        ["核对版本、作品权利及可用原件。"])
            return ("artwork", "search", "新稿需要特定作品，源图注尚未确认身份。",
                    ["找原始作品来源，核对作者、版本和许可。"])
        return ("artwork", "extend", "图注指向插画或创作作品。可先提炼构图与层次，再按新内容延展。",
                ["若新稿必须呈现这一件作品，需核对身份和许可，不能用延展图替代。"])
    if DIAGRAM.search(caption) or native_kind in {"CHART", "TABLE", "DIAGRAM"}:
        return ("diagram", "redraw", "图注或原生对象表明这里承载关系或数值，先用新稿的关系或数据重建。",
                ["核对要表达的关系、数值和新稿数据来源。"])
    if MAP.search(caption):
        if subject and not same:
            return ("map", "search", "图注未确认目标地点。先找同一地点的正式地图。",
                    ["核对地点别名、版本和范围。"])
        return ("map", "reuse", "图注表明是地图。" + ("与目标地点文字匹配。" if same else "同区位和同范围时可保留。"),
                ["核对地图版本、地名在目标尺寸的可读性，以及原件授权。"])
    if PHOTO.search(caption):
        if subject and not same:
            return ("photo", "search", "图注未确认目标主体。先找能核实地点或对象的照片。",
                    ["图注可能使用别名。换图前核对出处、主体和许可。"])
        return ("photo", "reuse", "图注提示实拍场景。" + ("与目标主体文字匹配。" if same else "新稿仍用同一主体时可考虑保留。"),
                ["核对画面身份、目标裁切和原件许可。"])
    return ("unknown", "review", "当前没有可靠图注或原生语义来判定图片职责。",
            ["需看页面预览，区分实拍、插画、图表和装饰。"])


def image_report(catalog, manifest, signals, context=None, context_sha=None):
    by_page = defaultdict(list)
    exported = {item["id"]: item for item in manifest["objects"]}
    contexts = read_context(context, catalog) if context is not None else {}
    for identifier, obj in catalog["objects"].items():
        kind = obj["kind"]
        if identifier in exported or kind in {"PICTURE", "LINKED_PICTURE", "RASTER_FRAME", "CHART", "TABLE", "DIAGRAM"}:
            by_page[obj["page"]].append((identifier, obj))
    pages = []
    for page in range(1, catalog["pages"] + 1):
        signal = signals.get(page, {})
        decisions = []
        for identifier, obj in by_page[page]:
            bounds = obj.get("bounds", [])
            targets = targets_at(bounds, contexts.get(page, []))
            target = targets[0] if len(targets) == 1 else None
            caption = signal.get("captions", {}).get(identifier, "")
            media = exported.get(identifier, {}).get("media", [])
            role, action, reason, uncertain = recommendation(caption, target, obj["kind"])
            if len(targets) > 1:
                action = "review"
                uncertain.append("多个新稿目标覆盖此对象，需确定对应的区域。")
            if media and any(item.get("needs_context") for item in media):
                uncertain.append("已导出源图流，仍需还原遮罩、裁切或叠放并检查成像。")
            if action == "reuse" and not media:
                action = "review"
                uncertain.append("未导出独立原件，需确认能否从原稿单独取得。")
            decisions.append({"object": identifier, "bounds": bounds, "role": role, "action": action,
                              "reason": reason, "uncertainty": uncertain, "caption": caption,
                              "media_count": len(media), "target": target})
        if signal.get("process_cue"):
            decisions.append({"object": None, "bounds": [], "role": "process", "action": "redraw",
                              "reason": "页面有流程文字线索和成组的矢量对象。按新稿的顺序重建结构。",
                              "uncertainty": ["这是页级线索，仍需定位节点与连接线。"],
                              "caption": "", "media_count": 0, "target": None})
        pages.append({"page": page, "vector_objects": signal.get("vector_objects"), "decisions": decisions})
    return {"version": 1, "source_sha256": catalog["source_sha256"], "source_kind": catalog["source_kind"],
            "context_sha256": context_sha, "pages": pages}
