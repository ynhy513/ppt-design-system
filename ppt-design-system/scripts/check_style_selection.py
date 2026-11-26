"""Check recorded reference research before producing a style-description deck.

Files/fingerprints are verified; human/model viewing and user intent remain attestations.
This does not infer the task's origin from arbitrary prose or prove visual quality.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from PIL import Image


def need(condition, message):
    if not condition:
        raise ValueError("Style selection: " + message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def artifact(record, root, *, image=False):
    need(isinstance(record, dict) and nonempty(record.get("file")), "missing evidence file")
    path = root / record["file"]
    need(path.is_file(), f"missing evidence file: {record['file']}")
    need(sha256(path.read_bytes()).hexdigest() == record.get("sha256"),
         f"evidence fingerprint mismatch: {record['file']}")
    if image:
        with Image.open(path) as source:
            source.verify()
    return path


def check_selection(path, *, request=None, source_sha256=None):
    path = Path(path)
    root = path.parent
    data = json.loads(path.read_text(encoding="utf-8"))
    need(isinstance(data, dict) and data.get("version") == 1, "unsupported decision record")
    need(data.get("origin") == "style-description", "record must describe a style-description request")
    brief = artifact(data.get("request"), root)
    if request is not None:
        need(brief.read_bytes() == Path(request).read_bytes(), "decision belongs to a different request")
    if source_sha256 is not None:
        need(data.get("design_source_sha256") == source_sha256, "decision belongs to a different design source")
    need(data.get("imagery") in {"direct", "independent", "mixed", "none"}, "missing imagery choice")
    need(type(data.get("prior_materials_allowed")) is bool, "declare whether prior material reuse is allowed")
    research = data.get("research", {})
    need(isinstance(research, dict), "invalid research record")
    refs = research.get("references", [])
    need(isinstance(refs, list), "references must be a list")
    seen = set()
    for ref in refs:
        need(isinstance(ref, dict), "invalid reference")
        identifier = ref.get("id")
        need(nonempty(identifier) and identifier not in seen, "missing or duplicate reference ID")
        seen.add(identifier)
        need(ref.get("kind") == "source-reference", "generated proposals cannot stand in for source references")
        need(ref.get("viewed") is True and nonempty(ref.get("observations")),
             f"reference has not been reviewed: {identifier}")
        need(nonempty(ref.get("source")) and nonempty(ref.get("region")), f"missing source/region: {identifier}")
        need(ref.get("prior") is False or (ref.get("prior") is True and data["prior_materials_allowed"]),
             f"prior reference is not authorized: {identifier}")
        artifact(ref, root, image=True)
    status = research.get("status")
    if status == "reviewed":
        need(refs, "reviewed research needs viewed source images, not a page URL or a style name")
    elif status == "user-waived":
        waiver = research.get("waiver", {})
        need(isinstance(waiver, dict) and waiver.get("authority") == "user"
             and waiver.get("scope") == "reference-research" and nonempty(waiver.get("quote")),
             "only an explicit user waiver of reference research can bypass research")
        need(research.get("output_label") == "original-proposal", "unresearched output must be labeled original-proposal")
    else:
        need(False, "research is incomplete; inaccessible sources or delegated selection do not complete it")
    selection = data.get("selection", {})
    need(isinstance(selection, dict) and selection.get("authority") in {"user", "delegated"}
         and nonempty(selection.get("quote")), "missing current user choice or explicit delegation")
    candidates = data.get("candidates", [])
    need(isinstance(candidates, list) and candidates, "missing rendered direction preview")
    candidate_ids = set()
    for candidate in candidates:
        need(isinstance(candidate, dict), "invalid candidate")
        identifier = candidate.get("id")
        need(nonempty(identifier) and identifier not in candidate_ids, "missing or duplicate candidate ID")
        candidate_ids.add(identifier)
        previews = candidate.get("previews", [])
        need(isinstance(previews, list) and previews, f"missing rendered preview: {identifier}")
        for preview in previews:
            artifact(preview, root, image=True)
    need(selection.get("candidate") in candidate_ids, "selected candidate has no rendered preview")
    handoffs = data.get("handoffs", [])
    need(isinstance(handoffs, list), "handoffs must be a list")
    for handoff in handoffs:
        need(isinstance(handoff, dict) and nonempty(handoff.get("model")), "missing handoff model")
        prompt = artifact(handoff.get("prompt"), root).read_text(encoding="utf-8")
        need(nonempty(prompt), "empty delegated prompt")
        ids = handoff.get("reference_ids", [])
        need(isinstance(ids, list) and set(ids) == seen, "handoff dropped reviewed reference context")
        mode = handoff.get("reference_mode")
        need(mode in {"images", "reviewed-observations"}, "declare how references reached the model")
        if mode == "reviewed-observations":
            need(all(ref["observations"] in prompt and ref["source"] in prompt for ref in refs),
                 "delegated prompt omits recorded source observations")
        else:
            attachments = handoff.get("attachments", [])
            need(isinstance(attachments, list) and all(isinstance(a, dict) for a in attachments)
                 and {a.get("sha256") for a in attachments} == {r["sha256"] for r in refs},
                 "image handoff is missing reviewed attachments")
            for attachment in attachments:
                artifact(attachment, root, image=True)
    return {"record_sha256": sha256(path.read_bytes()).hexdigest(), "research": status,
            "references": len(refs), "candidate": selection["candidate"], "handoffs": len(handoffs),
            "limits": "Files and recorded context checked; actual viewing, user intent, model receipt and visual quality are not machine-proven."}


def production_preflight(args, *, source_sha256=None):
    request = getattr(args, "style_request", None)
    record = getattr(args, "style_selection", None)
    need(request is None or record is not None, "--style-request requires --style-selection before production")
    if record is None:
        return None
    return check_selection(record, request=request, source_sha256=source_sha256)


def add_selection_arguments(parser):
    parser.add_argument("--style-request", type=Path, help="Original style-description request; requires a reviewed decision record")
    parser.add_argument("--style-selection", type=Path, help="Reference/selection decision record for style-description production")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--request", type=Path)
    parser.add_argument("--source-sha256")
    args = parser.parse_args()
    try:
        report = check_selection(args.record, request=args.request, source_sha256=args.source_sha256)
    except (ValueError, OSError, TypeError, KeyError) as error:
        parser.exit(2, f"{error}\n")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
