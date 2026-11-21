"""Check reviewed flat-color areas in actual slide screenshots, not token presence."""

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import re

from PIL import Image, ImageChops


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fraction(value):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1


def check_color_fields(contract, root):
    pages = contract["pages"]
    require(isinstance(pages, list) and pages, "List the rendered pages to review")
    checks = []
    identifiers = set()
    for page in pages:
        identifier = page["id"]
        require(isinstance(identifier, str) and identifier.strip() and identifier not in identifiers,
                "Page IDs must be nonempty and unique")
        identifiers.add(identifier)
        fields = page["fields"]
        require(isinstance(fields, list) and fields, f"{identifier}: list the color fields")
        screenshot = root / page["screenshot"]
        with Image.open(screenshot) as source:
            image = source.convert("RGB")
        for field in fields:
            label = f"{identifier}/{field['role']}"
            require(isinstance(field["role"], str) and field["role"].strip(), "Name the color role")
            for key in ("evidence", "basis"):
                require(isinstance(field[key], str) and field[key].strip(), f"{label}: missing {key}")
            color = field["color"]
            require(isinstance(color, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", color),
                    f"{label}: use a six-digit hex color")
            lower, upper = field["min_fraction"], field["max_fraction"]
            require(fraction(lower) and fraction(upper) and lower <= upper,
                    f"{label}: coverage bounds must satisfy 0 <= min <= max <= 1")
            tolerance = field.get("tolerance", 3)
            require(type(tolerance) is int and 0 <= tolerance <= 255,
                    f"{label}: tolerance must be an integer from 0 to 255")
            region = field.get("region", [0, 0, 1, 1])
            require(isinstance(region, list) and len(region) == 4 and all(fraction(v) for v in region),
                    f"{label}: region uses normalized [left, top, right, bottom]")
            left, top, right, bottom = region
            require(left < right and top < bottom, f"{label}: region must have positive area")
            bounds = tuple(round(v * size) for v, size in zip(region, image.size * 2))
            require(bounds[0] < bounds[2] and bounds[1] < bounds[3], f"{label}: region is below one pixel")
            crop = image.crop(bounds)
            target = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
            masks = [channel.point([255 if abs(value - expected) <= tolerance else 0
                                    for value in range(256)])
                     for channel, expected in zip(crop.split(), target)]
            mask = ImageChops.multiply(ImageChops.multiply(masks[0], masks[1]), masks[2])
            actual = mask.histogram()[255] / (crop.width * crop.height)
            checks.append({"page": identifier, **field, "region": region, "tolerance": tolerance,
                           "fraction": actual, "passed": lower <= actual <= upper,
                           "screenshot": page["screenshot"],
                           "screenshot_sha256": sha256(screenshot.read_bytes()).hexdigest()})
    return {"passed": all(check["passed"] for check in checks), "checks": checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review", type=Path, help="JSON review; screenshot paths are relative to this file")
    parser.add_argument("--out", type=Path, help="Write the machine-readable result here")
    args = parser.parse_args()
    try:
        result = check_color_fields(json.loads(args.review.read_text()), args.review.parent)
        output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.out:
            args.out.write_text(output)
        else:
            print(output, end="")
        if not result["passed"]:
            parser.exit(2, "Rendered color fields differ from the reviewed coverage bounds\n")
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(2, f"Color review rejected: {error}\n")


if __name__ == "__main__":
    main()
