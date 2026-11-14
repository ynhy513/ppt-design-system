"""Validate a comparative structural review and bind the selected recipe variants."""

import argparse
import json
from pathlib import Path

from compile_story import check_manuscript
from design_replay import load, require
from structural_components import variant_options


CHECKS = {"relation", "readability", "editable"}


def apply_review(manuscript, system, review):
    check_manuscript(manuscript)
    chapters = {chapter["id"]: chapter for chapter in manuscript["chapters"]}
    require(isinstance(review, dict) and review and review.keys() <= chapters.keys(),
            "Review must reference known manuscript chapters")
    for identifier, decision in review.items():
        available = variant_options(chapters[identifier]["relation"])
        candidates = decision["candidates"]
        refs = decision["evidence"]
        selected = decision["selected"]
        require(len(candidates) >= 2 and candidates.keys() <= available.keys(),
                f"Compare at least two applicable variants on {identifier}")
        require(isinstance(refs, list) and refs and all(ref in system["evidence"] for ref in refs),
                f"Missing reference evidence on {identifier}")
        require(selected in candidates and decision["reason"].strip(),
                f"Missing selection or selection reason on {identifier}")
        renders = set()
        for candidate in candidates.values():
            checks = candidate["checks"]
            require(checks.keys() == CHECKS and all(type(value) is bool for value in checks.values()),
                    f"Review needs Boolean checks for {sorted(CHECKS)} on {identifier}")
            require(candidate["render"].strip() and candidate["observation"].strip(),
                    f"Missing rendered example or observation on {identifier}")
            renders.add(candidate["render"])
        require(len(renders) == len(candidates), f"Each variant needs its own render on {identifier}")
        require(all(candidates[selected]["checks"].values()), f"Selected variant has a failed check on {identifier}")
    return {**manuscript, "chapters": [
        {**chapter, "variant": review[chapter["id"]]["selected"]} if chapter["id"] in review else chapter
        for chapter in manuscript["chapters"]
    ]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manuscript", "system", "review"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    try:
        review = load(args.review)
        prepared = apply_review(load(args.manuscript), load(args.system), review)
        for decision in review.values():
            for candidate in decision["candidates"].values():
                render = args.review.parent / candidate["render"]
                require(render.is_file(), f"Rendered page not found: {render}")
        print(json.dumps(prepared, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as error:
        parser.exit(2, f"Variant review rejected: {error}\n")


if __name__ == "__main__":
    main()
