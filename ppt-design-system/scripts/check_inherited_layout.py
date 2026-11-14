"""Compare reviewed title, text, and highlight layers against the original design pack."""

import argparse
from pathlib import Path

from design_replay import TOKEN_GROUPS, load, require, used_tokens


def background_color(system, pattern):
    return system["tokens"]["colors"][system["patterns"][pattern]["background"]]


def check_inherited_layout(source, production, review):
    require(source["source"] == production["source"], "Design packs must refer to the same source")
    original = {layer["id"]: layer for layer in source["patterns"][review["source_pattern"]]["layers"]}
    revised = {layer["id"]: layer for layer in production["patterns"][review["production_pattern"]]["layers"]}
    errors = []
    if review.get("background"):
        before = background_color(source, review["source_pattern"])
        after = background_color(production, review["production_pattern"])
        if before.lower() != after.lower():
            errors.append(f"background {before} → {after}")
        original_pattern = source["patterns"][review["source_pattern"]]
        revised_pattern = production["patterns"][review["production_pattern"]]
        original_art = source["families"][original_pattern["family"]].get("backdrop", {})
        revised_art = production["families"][revised_pattern["family"]].get("backdrop", {})
        if original_art.get("sha256") != revised_art.get("sha256"):
            errors.append("background artwork changed")
    require(review["layers"] or review.get("background"), "List the source layers or background to protect")
    targets = [review["layers"][name].get("target", name) for name in original if name in review["layers"]]
    if [name for name in revised if name in targets] != [name for name in targets if name in revised]:
        errors.append("Relative layer order changed among the reviewed layers")
    for identifier, binding in review["layers"].items():
        before = original[identifier]
        target = binding.get("target", identifier)
        after = revised.get(target)
        if "box" in binding or "size" in binding:
            require(binding.get("reason", "").strip(), f"{identifier}: a reviewed change requires a reason")
        if after is None:
            errors.append(f"{identifier} → {target}: layer is missing")
            continue
        for key in ("kind", "box", "align", "rotation"):
            expected = binding.get("box", before.get(key)) if key == "box" else before.get(key)
            if expected != after.get(key):
                errors.append(f"{identifier} → {target}: {key} {expected} → {after.get(key)}")
        if before["kind"] == after["kind"] == "text":
            expected = source["tokens"]["type"][before["type"]]
            if "size" in binding:
                require(0 < binding["size"] <= expected["size"], f"{identifier}: reviewed size must fit the source scale")
                expected = {**expected, "size": binding["size"]}
            actual = production["tokens"]["type"][after["type"]]
            for key in ("font", "size", "weight", "leading"):
                if expected[key] != actual[key]:
                    errors.append(f"{identifier} → {target}: {key} {expected[key]} → {actual[key]}")
            if expected.get("italic", False) != actual.get("italic", False):
                errors.append(f"{identifier} → {target}: italic changed")
            if source["tokens"]["colors"][before["ink"]] != production["tokens"]["colors"][after["ink"]]:
                errors.append(f"{identifier} → {target}: text color changed")
        if before["kind"] == after["kind"] and before["kind"] in {"box", "image", "line", "curve"}:
            for field in ("fill", "stroke", "radius", "weight"):
                group = TOKEN_GROUPS[field]
                old_value = source["tokens"][group].get(before.get(field))
                new_value = production["tokens"][group].get(after.get(field))
                if old_value != new_value:
                    errors.append(f"{identifier} → {target}: {field} {old_value} → {new_value}")
        if before["kind"] == after["kind"] and before["kind"] in {"line", "curve"}:
            for key in ("points", "arrow"):
                if before.get(key) != after.get(key):
                    errors.append(f"{identifier} → {target}: {key} {before.get(key)} → {after.get(key)}")
        if before["kind"] == after["kind"] == "image":
            for key in ("fit", "position"):
                if before[key] != after[key]:
                    errors.append(f"{identifier} → {target}: {key} {before[key]} → {after[key]}")
            old_asset = source.get("fixed_assets", {}).get(before.get("asset"), {})
            new_asset = production.get("fixed_assets", {}).get(after.get("asset"), {})
            if old_asset.get("sha256") != new_asset.get("sha256"):
                errors.append(f"{identifier} → {target}: fixed artwork changed")
        if before["kind"] == after["kind"] == "motif":
            if (source["motifs"][before["motif"]] != production["motifs"][after["motif"]]
                    or before.get("paint", {}) != after.get("paint", {})):
                errors.append(f"{identifier} → {target}: motif layers or color mapping changed")
            else:
                for token in sorted(set(used_tokens([before], source))):
                    group, name = token.split(".", 1)
                    if source["tokens"][group][name] != production["tokens"][group][name]:
                        errors.append(f"{identifier} → {target}: motif token {token} changed")
    return errors


def verify_inherited_layout(path, production, pages, *, boxes=None):
    """Review every used pattern, including those authored for the production pack."""
    record = load(path)
    source = load(path.parent / record["source_system"])
    require(source["source"] == production["source"], "Design packs must refer to the same source")
    reviews = record["reviews"]
    extensions = record.get("extensions", {})
    require(not (reviews.keys() & extensions.keys()), "A pattern must have one review record")
    required = {page["pattern"] for page in pages}
    missing = required - reviews.keys() - extensions.keys()
    require(not missing, f"Missing inheritance review for: {', '.join(sorted(missing))}")
    results = {}
    for name in sorted(required):
        if name in extensions:
            reason = extensions[name].strip()
            require(reason, f"{name}: give the reason for the new composition")
            results[name] = {"extension": reason}
            continue
        review = dict(reviews[name], production_pattern=name)
        issues = check_inherited_layout(source, production, review)
        require(not issues, f"{name}: " + "\n".join(issues))
        results[name] = {"source_pattern": review["source_pattern"], "layers": review["layers"]}
        if review.get("background"):
            results[name]["background"] = background_color(source, review["source_pattern"])
    for page in pages:
        pattern = page["pattern"]
        edited_boxes = (boxes or {}).get(page["id"], {})
        for name, binding in results[pattern].get("layers", {}).items():
            target = binding.get("target", name)
            if "lines" not in binding and target not in edited_boxes:
                continue
            layer = next(layer for layer in production["patterns"][pattern]["layers"] if layer["id"] == target)
            if target in edited_boxes:
                require(edited_boxes[target] == layer["box"],
                        f"{page['id']}/{name}: edited box {edited_boxes[target]} changes reviewed geometry {layer['box']}")
            if "lines" not in binding:
                continue
            expected = binding["lines"]
            require(type(expected) is int and expected >= 1 and layer["kind"] == "text",
                    f"{name}: lines must be a positive count on a text layer")
            value = page["slots"][layer["slot"]] if "slot" in layer else layer["value"]
            rows = value.split("\n")
            require(len(rows) == expected and all(row.strip() for row in rows),
                    f"{page['id']}/{name}: expected {expected} explicit non-empty text lines")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "production", "review"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    try:
        issues = check_inherited_layout(load(args.source), load(args.production), load(args.review))
        require(not issues, "\n".join(issues))
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(2, f"Inherited layout check failed:\n{error}\n")
    print("Reviewed inherited layer geometry and typography match.")


if __name__ == "__main__":
    main()
