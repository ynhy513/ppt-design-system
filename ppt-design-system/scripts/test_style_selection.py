"""Behavioral evidence checks; synthetic images stand in for viewed files only in tests."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from PIL import Image
import pytest

from check_style_selection import check_selection, production_preflight


def make_record(root, source_sha="a" * 64):
    root.mkdir(parents=True, exist_ok=True)
    (root / "request.txt").write_text("A film-inspired deck. Choose the direction; use no prior assets.")
    Image.new("RGB", (16, 9), "navy").save(root / "reference.png")
    Image.new("RGB", (16, 9), "gold").save(root / "preview.png")
    def file(name):
        return {"file": name, "sha256": sha256((root / name).read_bytes()).hexdigest()}
    data = {"version": 1, "origin": "style-description", "request": file("request.txt"),
            "design_source_sha256": source_sha, "prior_materials_allowed": False, "imagery": "independent",
            "research": {"status": "reviewed", "references": [{"id": "source", "kind": "source-reference",
                "source": "https://example.org/reference", "region": "full frame", **file("reference.png"),
                "viewed": True, "observations": "Quiet left field and a bright right focus.", "prior": False}]},
            "candidates": [{"id": "direction", "previews": [file("preview.png")]}],
            "selection": {"authority": "delegated", "quote": "Choose the direction", "candidate": "direction"},
            "handoffs": []}
    path = root / "style-selection.json"
    path.write_text(json.dumps(data))
    return path, data


def save(path, data):
    path.write_text(json.dumps(data))


def test_fresh_research_and_delegated_choice_pass_without_prior_assets(tmp_path):
    path, _ = make_record(tmp_path)
    report = check_selection(path, request=tmp_path / "request.txt", source_sha256="a" * 64)
    assert report["research"] == "reviewed" and report["references"] == 1
    assert report["candidate"] == "direction"


@pytest.mark.parametrize("mutate,match", [
    (lambda d: d["research"].update(references=[]), "viewed source images"),
    (lambda d: d["research"]["references"][0].update(viewed=False), "not been reviewed"),
    (lambda d: d["research"]["references"][0].update(kind="generated-proposal"), "cannot stand in"),
    (lambda d: d["research"]["references"][0].update(prior=True), "not authorized"),
    (lambda d: d["research"]["references"][0].update(sha256="0" * 64), "fingerprint mismatch"),
    (lambda d: d["candidates"][0].update(previews=[]), "missing rendered preview"),
    (lambda d: d["research"].update(status="unavailable"), "research is incomplete"),
])
def test_unresearched_or_untraceable_shortcuts_fail(tmp_path, mutate, match):
    path, data = make_record(tmp_path)
    mutate(data)
    save(path, data)
    with pytest.raises(ValueError, match=match):
        check_selection(path)


def test_delegating_selection_is_not_a_research_waiver(tmp_path):
    path, data = make_record(tmp_path)
    data["research"] = {"status": "user-waived", "references": [], "output_label": "original-proposal",
                        "waiver": {"authority": "user", "scope": "direction-selection", "quote": "You choose"}}
    save(path, data)
    with pytest.raises(ValueError, match="explicit user waiver"):
        check_selection(path)
    data["research"]["waiver"] = {"authority": "user", "scope": "reference-research",
                                    "quote": "Skip reference research and make an original proposal."}
    save(path, data)
    assert check_selection(path)["research"] == "user-waived"


def test_mismatched_request_and_pack_source_fail(tmp_path):
    path, _ = make_record(tmp_path)
    another = tmp_path / "other-request.txt"
    another.write_text("A different task.")
    with pytest.raises(ValueError, match="different request"):
        check_selection(path, request=another)
    with pytest.raises(ValueError, match="different design source"):
        check_selection(path, source_sha256="b" * 64)


def test_observation_handoff_checks_actual_prompt_contents(tmp_path):
    path, data = make_record(tmp_path)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Generate backgrounds directly. No source context included.")
    handoff = {"model": "external-model", "reference_ids": ["source"], "reference_mode": "reviewed-observations",
               "prompt": {"file": prompt.name, "sha256": sha256(prompt.read_bytes()).hexdigest()}}
    data["handoffs"] = [handoff]
    save(path, data)
    with pytest.raises(ValueError, match="omits recorded source observations"):
        check_selection(path)
    ref = data["research"]["references"][0]
    prompt.write_text(ref["source"] + "\n" + ref["observations"])
    handoff["prompt"]["sha256"] = sha256(prompt.read_bytes()).hexdigest()
    save(path, data)
    assert check_selection(path)["handoffs"] == 1
    handoff["reference_ids"] = []
    save(path, data)
    with pytest.raises(ValueError, match="dropped reviewed reference"):
        check_selection(path)


def test_image_handoff_requires_verified_attachments(tmp_path):
    path, data = make_record(tmp_path)
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Inspect attached fresh references. Preserve user restrictions and uncertainty.")
    data["handoffs"] = [{"model": "external-model", "reference_ids": ["source"], "reference_mode": "images",
                         "prompt": {"file": prompt.name, "sha256": sha256(prompt.read_bytes()).hexdigest()}}]
    save(path, data)
    with pytest.raises(ValueError, match="missing reviewed attachments"):
        check_selection(path)
    ref = data["research"]["references"][0]
    data["handoffs"][0]["attachments"] = [{k: ref[k] for k in ("file", "sha256")}]
    save(path, data)
    assert check_selection(path)["handoffs"] == 1


@pytest.mark.parametrize("script", ["make_deck.py", "serve_deck.py"])
def test_production_entry_rejects_missing_decision_before_render_or_server(tmp_path, script):
    request = tmp_path / "request.txt"
    request.write_text("Recognizable film style; you choose; use generated backgrounds.")
    command = [sys.executable, str(Path(__file__).with_name(script)), str(tmp_path / "missing-pack"),
               str(tmp_path / "missing-manuscript.json"), "--style-request", str(request)]
    if script == "make_deck.py":
        command += ["--out", str(tmp_path / "output")]
    result = subprocess.run(command, capture_output=True, text=True, timeout=15)
    assert result.returncode == 2
    assert "requires --style-selection before production" in result.stderr
    assert not (tmp_path / "output").exists()


def test_legacy_reference_route_remains_compatible():
    assert production_preflight(SimpleNamespace()) is None
