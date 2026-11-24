"""Check repository Markdown links, anchors and English reference navigation."""

import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit


def prose(text):
    lines = []
    fence = None
    for line in text.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            if fence is None:
                fence = marker[1][0]
            elif marker[1][0] == fence:
                fence = None
            continue
        if fence is None:
            lines.append(line)
    return "\n".join(lines)


def heading_ids(text):
    seen = {}
    result = set()
    for heading in re.findall(r"^#{1,6}\s+(.+)$", text, re.MULTILINE):
        slug = heading.lower().strip().replace("`", "")
        slug = "".join(c for c in slug if c in "-_ " or not
                       unicodedata.category(c).startswith(("P", "S"))).replace(" ", "-")
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        result.add(slug + (f"-{count}" if count else ""))
    return result


def english(path, root):
    return path.name.endswith(".en.md") or path in {
        root / "README.md", root / "ppt-design-system/SKILL.md"
    }


def check(root):
    root = Path(root).resolve()
    if not (root / "README.md").is_file():
        return [f"Missing repository README.md: {root}"], 0, 0
    references = root / "ppt-design-system/references"
    paths = {root / "README.md", root / "README.zh-CN.md",
             root / "ppt-design-system/SKILL.md"}
    paths.update((root / "docs").rglob("*.md"))
    paths.update(references.glob("*.md"))
    documents = {p: prose(p.read_text(encoding="utf-8")) for p in paths if p.is_file()}
    errors = []
    links = 0
    parsed = {p: re.findall(r"!?\[([^\]]*)\]\(([^)]+)\)", text)
              for p, text in documents.items()}
    for path, entries in parsed.items():
        for label, href in entries:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                continue
            links += 1
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            source = path.relative_to(root)
            if not target.is_relative_to(root):
                errors.append(f"{source}: link leaves repository: {href}")
            elif not target.exists():
                errors.append(f"{source}: missing file: {href}")
            elif target.suffix == ".md":
                if english(path, root) and label != "简体中文" and not english(target, root):
                    errors.append(f"{source}: English link targets Chinese documentation: {href}")
                if url.fragment and unquote(url.fragment) not in heading_ids(
                        documents.get(target, prose(target.read_text(encoding="utf-8")))):
                    errors.append(f"{source}: missing heading: {href}")
    for cn in references.glob("*.md"):
        if cn.name.endswith(".en.md"):
            continue
        en = cn.with_name(cn.stem + ".en.md")
        if en not in documents:
            errors.append(f"{cn.relative_to(root)}: missing English counterpart")
            continue
        if ("English", en.name) not in parsed[cn] or ("简体中文", cn.name) not in parsed[en]:
            errors.append(f"{cn.relative_to(root)}: missing reciprocal language links")
    return errors, len(documents), links


if __name__ == "__main__":
    failures, pages, links = check(sys.argv[1] if len(sys.argv) > 1 else ".")
    for failure in failures:
        print(failure)
    if failures:
        sys.exit(1)
    print(f"Passed: {pages} Markdown pages, {links} local links/anchors; English navigation stays English.")
