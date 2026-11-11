"""Validate a source design pack and optionally write a source-only ZIP."""

import argparse
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
from stat import S_ISLNK
from zipfile import BadZipFile, ZIP_DEFLATED, ZipFile

from jsonschema import ValidationError

from compile_story import check_grammar
from design_replay import check_system

ROOT_FILES = {"STYLE.md", "design-system.json", "element-catalog.json", "style-grammar.json"}
MANIFEST = "assets/assets-manifest.json"
ZIP_ROOT = "design-pack/"


def safe_path(name):
    path = PurePosixPath(name)
    return (bool(path.parts) and not path.is_absolute() and ".." not in path.parts
            and "\\" not in name and path.as_posix() == name)


def evidence_objects(record):
    return set(record.get("catalog_refs", ())) | {
        f"p{record['page']}-o{number}" for number in record.get("objects", ())
    }


def validate_pack(names, read):
    required = ROOT_FILES | {MANIFEST}
    errors = [f"Missing required file: {name}" for name in sorted(required - names)]
    errors += [f"Unexpected top-level file: {name}" for name in sorted(names - required)
               if not name.startswith("assets/")]
    if required - names:
        return errors
    if not read("STYLE.md").strip():
        errors.append("STYLE.md is empty")

    system, catalog, grammar, manifest = (json.loads(read(name)) for name in
        ("design-system.json", "element-catalog.json", "style-grammar.json", MANIFEST))
    check_grammar(system, catalog, grammar, check_system(system))
    if manifest["version"] != 1 or manifest["source_sha256"] != catalog["source_sha256"]:
        errors.append("Asset manifest version or source fingerprint does not match")

    declared = {}
    originals = {}
    derivatives = {}

    def register(item):
        file, fingerprint = item["file"], item["sha256"]
        if not safe_path(file) or f"assets/{file}" == MANIFEST:
            errors.append(f"Invalid asset path: {file}")
            return
        if file in declared and declared[file] != fingerprint:
            errors.append(f"Conflicting asset hashes: {file}")
        declared[file] = fingerprint

    def catalog_media(object_id):
        return [catalog["tokens"][token]["value"]
                for token in catalog["objects"][object_id]["tokens"]
                if catalog["tokens"][token]["kind"] == "asset"]

    for item in manifest["objects"]:
        object_id = item["id"]
        source = catalog["objects"].get(object_id)
        if not source or item["page"] != source["page"] or item["object"] != source["object"]:
            errors.append(f"Unresolved manifest source object: {object_id}")
            continue
        if object_id in originals:
            errors.append(f"Duplicate manifest source object: {object_id}")
        originals[object_id] = item["media"]
        expected_media = catalog_media(object_id)
        observed_media = [{k: m[k] for k in ("sha256", "mime", "crop")} for m in item["media"]]
        if (item["status"] != ("exported" if expected_media else "no-embedded-image")
                or any(token not in observed_media for token in expected_media)):
            errors.append(f"Incorrect export status or missing native media: {object_id}")
        for media, observed in zip(item["media"], observed_media):
            if observed not in expected_media:
                errors.append(f"Native media does not match its catalog object: {object_id}/{media['file']}")
            register(media)

    for derivative in manifest.get("derivatives", []):
        file = derivative["file"]
        register(derivative)
        if file in derivatives or any(file == m["file"] for records in originals.values() for m in records):
            errors.append(f"Duplicate or overlapping derivative: {file}")
        source_ids = set(derivative.get("sources", []))
        for ref in derivative.get("evidence", []):
            if ref not in system["evidence"]:
                errors.append(f"Unknown derivative evidence: {file}/{ref}")
            else:
                source_ids.update(evidence_objects(system["evidence"][ref]))
        if not derivative["treatment"].strip() or not (source_ids or derivative.get("evidence")):
            errors.append(f"Derivative needs source evidence and a treatment description: {file}")
        for object_id in sorted(source_ids):
            if object_id not in catalog["objects"]:
                errors.append(f"Unknown derivative source object: {file}/{object_id}")
            elif catalog_media(object_id) and not originals.get(object_id):
                errors.append(f"Derivative requires a registered original: {file}/{object_id}")
        derivatives[file] = source_ids

    for file, fingerprint in sorted(declared.items()):
        name = f"assets/{file}"
        if name not in names:
            errors.append(f"Missing manifest asset: {name}")
        elif sha256(read(name)).hexdigest() != fingerprint:
            errors.append(f"SHA-256 mismatch: {name}")
    errors += [f"Asset is not listed in the manifest: {name}" for name in sorted(names - required)
               if name.startswith("assets/") and name[7:] not in declared]

    def check_reference(asset):
        if declared.get(asset["file"]) != asset["sha256"]:
            errors.append(f"Design asset has no matching manifest entry: {asset['file']}")

    for family in system["families"].values():
        if "backdrop" in family:
            check_reference(family["backdrop"])
    for asset in system.get("fixed_assets", {}).values():
        check_reference(asset)
        evidence = system["evidence"][asset["evidence"]]
        object_id = f"p{evidence['page']}-o{evidence['objects'][0]}"
        source_hash = asset.get("source_sha256", asset["sha256"])
        if source_hash not in {m["sha256"] for m in originals.get(object_id, [])}:
            errors.append(f"Fixed asset source hash is not registered: {asset['file']}/{object_id}")
        if "source_sha256" in asset and object_id not in derivatives.get(asset["file"], set()):
            errors.append(f"Fixed derivative has no source link: {asset['file']}/{object_id}")
    return errors


def check_zip(path):
    with ZipFile(path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if (len(names) != len(set(names))
                or any(not safe_path(entry.filename.rstrip("/")) or S_ISLNK(entry.external_attr >> 16)
                       for entry in entries)):
            return ["ZIP has duplicate entries, symbolic links, or invalid paths"]
        files = {entry.filename for entry in entries if not entry.is_dir()}
        errors = [f"File outside design-pack/: {name}" for name in sorted(files)
                  if not name.startswith(ZIP_ROOT)]
        pack_names = {name[len(ZIP_ROOT):] for name in files if name.startswith(ZIP_ROOT)}
        return errors + validate_pack(pack_names, lambda name: archive.read(ZIP_ROOT + name))


def check_directory(path, output):
    entries = list(path.rglob("*"))
    if any(entry.is_symlink() for entry in entries):
        return ["Design pack has symbolic links"]
    files = {entry.relative_to(path).as_posix(): entry for entry in entries if entry.is_file()}
    errors = validate_pack(files.keys(), lambda name: files[name].read_bytes())
    if not errors and output is not None:
        if output.resolve().is_relative_to(path.resolve()):
            return ["Output ZIP must be outside the design pack"]
        with ZipFile(output, "x", compression=ZIP_DEFLATED) as archive:
            for name, entry in sorted(files.items()):
                archive.writestr(ZIP_ROOT + name, entry.read_bytes())
        return check_zip(output)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack", type=Path, help="Design pack directory or existing ZIP")
    parser.add_argument("--out", type=Path, help="Write a new source-only ZIP from a directory")
    args = parser.parse_args()
    try:
        if args.pack.is_dir():
            errors = check_directory(args.pack, args.out)
        elif args.out is None:
            errors = check_zip(args.pack)
        else:
            parser.error("--out requires a design pack directory")
    except (OSError, BadZipFile, ValueError, KeyError, TypeError, ValidationError) as error:
        errors = [str(error)]
    if errors:
        parser.exit(2, "Design pack rejected:\n- " + "\n- ".join(errors) + "\n")
    print(f"Design pack verified: {args.out or args.pack}")


if __name__ == "__main__":
    main()
