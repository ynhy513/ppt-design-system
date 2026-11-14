from hashlib import sha256

from PIL import Image
import pytest

from design_replay import check_plan, check_system, make_renderer, render
from review_variants import apply_review
from structural_components import standard_motif, variant_options


@pytest.fixture
def design_system():
    return {
        "version": 1,
        "source": {"kind": "image", "sha256": "0" * 64, "pages": 2},
        "primary_family": "main",
        "families": {
            "main": {"scope": "primary", "pages": [1], "reason": "Main identity"},
            "guest": {"scope": "excluded", "pages": [2], "reason": "Guest brand"},
        },
        "evidence": {
            "main-page": {"page": 1, "region": [0, 0, 100, 100], "finding": "Main layout"},
            "guest-page": {"page": 2, "region": [0, 0, 100, 100], "finding": "Guest layout"},
        },
        "rules": {
            "main-rule": {"kind": "inferred", "policy": "locked", "statement": "Keep the main layout",
                          "evidence": ["main-page"]},
            "guest-rule": {"kind": "observed", "policy": "variant", "statement": "Use for guest pages",
                           "evidence": ["guest-page"]},
        },
        "tokens": {
            "colors": {"paper": "#FFFFFF", "ink": "#20182C"},
            "type": {"body": {"font": "Arial, sans-serif", "size": 2, "weight": 400, "leading": 1.2}},
            "radii": {}, "strokes": {},
        },
        "token_rules": dict.fromkeys(["colors.paper", "colors.ink", "type.body"], "main-rule"),
        "motifs": {},
        "patterns": {
            "editorial": {
                "family": "main", "role": "comparison", "reason": "Compare peers", "rules": ["main-rule"],
                "background": "paper", "layers": [
                    {"kind": "text", "id": "title", "slot": "title", "box": [10, 10, 80, 10],
                     "ink": "ink", "type": "body", "align": "center"},
                ],
            },
        },
    }


def test_excluded_family_cannot_enter_via_a_color_token(design_system):
    design_system["token_rules"]["colors.ink"] = "guest-rule"
    with pytest.raises(ValueError, match="Excluded source evidence"):
        check_system(design_system)


def test_structural_variant_review_preserves_chapter_and_blocks_failed_selection(design_system):
    design_system["tokens"]["radii"]["dot"] = 8
    design_system["tokens"]["strokes"]["edge"] = 4
    styles = {
        "colors": dict.fromkeys(("first-marker", "second-marker", "third-marker", "edge", "text"), "ink"),
        "type": {"node": "body"}, "radii": {"corner": "dot"}, "strokes": {"connector": "edge"},
    }
    for relation, curves in (("linear-flow", [0, 2]), ("three-step-cycle", [1, 3])):
        for variant, expected in zip(variant_options(relation), curves, strict=True):
            layers = standard_motif(relation, design_system, styles, variant=variant)
            assert [layer["slot"] for layer in layers if layer["kind"] == "text"] == ["first", "second", "third"]
            assert sum(layer["kind"] == "curve" for layer in layers) == expected
    with pytest.raises(ValueError, match="Unsupported drawing variant"):
        standard_motif("linear-flow", design_system, styles, variant="ring-cycle")

    chapter = {"id": "intro", "relation": "linear-flow", "intent": "Explain the sequence",
               "fields": {"first": "Check", "second": "Record", "third": "Release"}, "items": []}
    manuscript = {"version": 1, "chapters": [chapter]}
    review = {"intro": {
        "selected": "milestone-path", "evidence": ["main-page"], "reason": "The reference uses a continuous path.",
        "candidates": {variant: {"render": variant + ".png", "observation": "Labels remain legible",
                                 "checks": {"relation": True, "readability": True, "editable": True}}
                       for variant in variant_options("linear-flow")},
    }}
    assert apply_review(manuscript, design_system, review)["chapters"] == [{**chapter, "variant": "milestone-path"}]
    assert "variant" not in manuscript["chapters"][0]
    review["intro"]["candidates"]["milestone-path"]["checks"]["editable"] = False
    with pytest.raises(ValueError, match="Selected variant has a failed check"):
        apply_review(manuscript, design_system, review)


def test_standard_structures_keep_slots_and_directed_connections_when_styled(design_system):
    design_system["tokens"]["radii"]["card"] = 6
    design_system["tokens"]["strokes"]["solid"] = 2
    styles = {
        "colors": {"strong": "ink", "inverse": "paper", "panel": "paper",
                   "text": "ink", "edge": "ink"},
        "type": {"node": "body"},
        "radii": {"corner": "card"},
        "strokes": {"outline": "solid", "connector": "solid"},
    }
    chain = ["first-to-second", "second-to-third"]
    cases = [
        ("linear-flow", ["first", "second", "third"], chain, 2),
        ("hierarchy-tree", ["parent", "left", "middle", "right"], [], 5),
        ("three-step-cycle", ["first", "second", "third"], chain + ["third-to-first"], 3),
    ]
    for name, slots, arrows, connector_count in cases:
        layers = standard_motif(name, design_system, styles)
        assert [layer["slot"] for layer in layers if layer["kind"] == "text"] == slots
        assert [layer["id"] for layer in layers if layer.get("arrow")] == arrows
        assert sum(layer["kind"] == "line" for layer in layers) == connector_count
        assert [layer["fill"] for layer in layers if layer["kind"] == "box"] == (
            ["ink"] + ["paper"] * (len(slots) - 1)
        )
    with pytest.raises(ValueError, match="Style roles do not match"):
        standard_motif("linear-flow", design_system, {**styles, "strokes": {}})
    with pytest.raises(ValueError, match="Unknown radius token"):
        standard_motif("linear-flow", design_system, {**styles, "radii": {"corner": "missing"}})


def test_sequence_blocks_wrong_focus_or_strength(design_system):
    step = {"patterns": ["editorial"], "focus": "title", "weight": "high", "density": "low"}
    design_system["sequences"] = {"review": [step, step]}
    contracts = check_system(design_system)
    page = {"id": "first", "role": "comparison", "pattern": "editorial", "focus": "title",
            "weight": "high", "density": "low", "slots": {"title": "Sample"}}
    plan = {"version": 1, "sequence": "review", "pages": [page, {**page, "id": "second", "weight": "medium"}]}
    with pytest.raises(ValueError, match="Sequence drift on second"):
        check_plan(plan, design_system, contracts)
    del plan["sequence"]
    with pytest.raises(ValueError, match="requires an approved sequence"):
        check_plan(plan, design_system, contracts)


def test_replay_keeps_content_as_text(design_system):
    draw, asset, _ = make_renderer(design_system, None, set())
    page = {"id": "first", "role": "comparison", "pattern": "editorial", "focus": "title",
            "weight": "high", "density": "low", "slots": {"title": '<img src="external">'}}
    pages = check_plan({"version": 1, "pages": [page]}, design_system, check_system(design_system))
    html = render(design_system, pages, draw, asset)
    assert '&lt;img src=&quot;external&quot;&gt;' in html
    assert '<img src="external">' not in html


def test_replay_can_fit_a_source_paper_to_the_full_box(design_system, tmp_path):
    Image.new("RGBA", (8, 16), "white").save(tmp_path / "paper.png")
    design_system["patterns"]["editorial"]["layers"].append({
        "kind": "image", "id": "paper-stock", "slot": "paper-stock",
        "box": [12, 24, 72, 38], "fit": "fill", "position": [50, 50],
    })
    page = {"id": "first", "role": "comparison", "pattern": "editorial", "focus": "title",
            "weight": "high", "density": "low", "slots": {"title": "Sample", "paper-stock": "paper.png"}}
    plan = {"version": 1, "pages": [page]}
    pages = check_plan(plan, design_system, check_system(design_system))
    draw, asset, hashes = make_renderer(design_system, tmp_path, set())
    html = render(design_system, pages, draw, asset)
    assert "width:72%;height:38%;object-fit:fill" in html
    assert hashes["paper.png"] == sha256((tmp_path / "paper.png").read_bytes()).hexdigest()


def test_required_fixed_asset_rejects_a_missing_or_replaced_layer(design_system):
    design_system["source"]["kind"] = "pptx"
    design_system["evidence"]["main-page"]["objects"] = [10]
    design_system["fixed_assets"] = {
        "paper-stock": {"file": "paper.png", "sha256": "1" * 64, "evidence": "main-page"},
        "paperclip": {"file": "clip.png", "sha256": "2" * 64, "evidence": "main-page"},
    }
    pattern = design_system["patterns"]["editorial"]
    layer = {"kind": "image", "id": "note", "asset": "paper-stock", "box": [12, 30, 72, 38],
             "fit": "fill", "position": [50, 50]}
    pattern["layers"].append(layer)
    pattern["required_fixed_assets"] = {"note": {"asset": "paper-stock", "purpose": "Carries the first section"}}
    check_system(design_system)

    pattern["layers"].pop()
    with pytest.raises(ValueError, match=r"editorial/note \(paper-stock\).*Carries the first section"):
        check_system(design_system)
    pattern["layers"].append({**layer, "asset": "paperclip"})
    with pytest.raises(ValueError, match="Required fixed asset missing or replaced"):
        check_system(design_system)
    pattern["layers"][-1] = {"kind": "box", "id": "note", "box": layer["box"], "fill": "paper"}
    with pytest.raises(ValueError, match="Required fixed asset missing or replaced"):
        check_system(design_system)
    del pattern["required_fixed_assets"]
    assert check_system(design_system)["editorial"][1] == {"title": "text"}


def test_replay_binds_one_motif_in_two_layouts(design_system):
    overview = design_system["patterns"]["editorial"]
    design_system["motifs"]["summary"] = overview["layers"]
    instance = {"kind": "motif", "id": "summary", "motif": "summary",
                "box": [5, 20, 90, 60], "bindings": {"title": "headline"}}
    overview["layers"] = [instance]
    design_system["patterns"]["sidebar"] = {
        **overview,
        "layers": [{**instance, "box": [35, 15, 60, 70], "bindings": {"title": "aside"}}],
    }
    first = {"id": "first", "role": "comparison", "pattern": "editorial", "focus": "summary",
             "weight": "high", "density": "low", "slots": {"headline": "Overview <sample>"}}
    second = {**first, "id": "second", "pattern": "sidebar", "slots": {"aside": "Sidebar sample"}}
    plan = {"version": 1, "pages": [first, second]}
    contracts = check_system(design_system)
    assert contracts["editorial"] == ({"summary"}, {"headline": "text"})
    assert contracts["sidebar"] == ({"summary"}, {"aside": "text"})
    draw, asset, _ = make_renderer(design_system, None, set())
    html = render(design_system, check_plan(plan, design_system, contracts), draw, asset)
    assert html.count('data-motif="summary"') == 2
    assert "left:5%;top:20%;width:90%;height:60%" in html
    assert "left:35%;top:15%;width:60%;height:70%" in html
    assert "<span>Overview &lt;sample&gt;</span>" in html
    assert "<span>Sidebar sample</span>" in html
    second["slots"] = {"headline": "Wrong layout slot"}
    with pytest.raises(ValueError, match="Slot mismatch on second"):
        check_plan(plan, design_system, contracts)


def test_replay_rejects_missing_unknown_or_colliding_motif_bindings(design_system):
    layers = design_system["patterns"]["editorial"]["layers"]
    design_system["motifs"]["summary"] = [{**layers[0], "slot": "inner-title"}]
    motif = {"kind": "motif", "id": "summary", "motif": "summary", "box": [5, 20, 90, 60]}
    layers.append(motif)
    with pytest.raises(ValueError, match="Motif slot bindings do not match"):
        check_system(design_system)
    motif["bindings"] = {"unknown": "caption"}
    with pytest.raises(ValueError, match="Motif slot bindings do not match"):
        check_system(design_system)
    motif["bindings"] = {"inner-title": "title"}
    with pytest.raises(ValueError, match="Repeated page slot"):
        check_system(design_system)


def test_replay_underlines_only_the_exact_phrase(design_system):
    design_system["patterns"]["editorial"]["layers"][0]["underline_slot"] = "emphasis"
    contracts = check_system(design_system)
    page = {"id": "first", "role": "comparison", "pattern": "editorial", "focus": "title",
            "weight": "high", "density": "low", "slots": {"title": "Read <key> terms", "emphasis": "<key>"}}
    plan = {"version": 1, "pages": [page]}
    pages = check_plan(plan, design_system, contracts)
    draw, asset, _ = make_renderer(design_system, None, set())
    html = render(design_system, pages, draw, asset)
    assert '<span>Read <u ' in html
    assert '>&lt;key&gt;</u> terms</span>' in html
    page["slots"]["emphasis"] = ""
    pages = check_plan(plan, design_system, contracts)
    assert '<u ' not in render(design_system, pages, draw, asset)
    page["slots"]["title"] = ""
    with pytest.raises(ValueError, match="Invalid slot title"):
        check_plan(plan, design_system, contracts)
    for title, emphasis in [("Read terms", "<key>"), ("terms and terms", "terms"), ("aaa", "aa")]:
        page["slots"] = {"title": title, "emphasis": emphasis}
        with pytest.raises(ValueError, match="Underline must match one exact phrase"):
            check_plan(plan, design_system, contracts)


def test_source_background_is_fixed_beneath_content(design_system, tmp_path):
    image = tmp_path / "background.png"
    Image.new("RGB", (16, 9), "white").save(image)
    fingerprint = sha256(image.read_bytes()).hexdigest()
    backdrop = {"file": image.name, "sha256": fingerprint, "evidence": "main-page"}
    design_system["families"]["main"]["backdrop"] = backdrop
    page = {"id": "first", "role": "comparison", "pattern": "editorial", "focus": "title",
            "weight": "high", "density": "low", "slots": {"title": "Sample"}}
    pages = check_plan({"version": 1, "pages": [page]}, design_system, check_system(design_system))
    draw, asset, hashes = make_renderer(design_system, tmp_path, {fingerprint})
    html = render(design_system, pages, draw, asset)
    assert html.index('<img class="backdrop"') < html.index('data-layer="title"')
    assert hashes == {image.name: fingerprint}
    with pytest.raises(ValueError, match="Original source media"):
        asset(image.name)
    backdrop["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="Approved background SHA-256"):
        render(design_system, pages, draw, asset)
    backdrop["evidence"] = "guest-page"
    with pytest.raises(ValueError, match="Background must cite its own approved family"):
        check_system(design_system)
