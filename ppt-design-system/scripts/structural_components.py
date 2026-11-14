"""Materialize a standard diagram as a shared motif using reviewed design tokens."""

from pathlib import Path

from design_replay import TOKEN_GROUPS, check_layers, load, require


LIBRARY = Path(__file__).resolve().parents[1] / "references/structural-components"
COMPONENTS = ("linear-flow", "hierarchy-tree", "three-step-cycle",
              "paired-state-comparison", "qualitative-matrix", "nested-ownership", "handoff-swimlane")


def variant_options(component):
    return load(LIBRARY / "variants.json").get(component, {})


def standard_motif(component, system, styles, *, variant=None):
    require(component in COMPONENTS, f"Unknown standard component: {component}")
    require(variant is None or variant in variant_options(component),
            f"Unsupported drawing variant for {component}: {variant}")
    layers = load(LIBRARY / f"{variant or component}.json")
    roles = {(TOKEN_GROUPS[field], value) for layer in layers for field, value in layer.items()
             if field in TOKEN_GROUPS}
    require(isinstance(styles, dict) and all(isinstance(values, dict) for values in styles.values())
            and {(group, role) for group, values in styles.items() for role in values} == roles,
            f"Style roles do not match {component}: {sorted(roles)}")
    require(all(isinstance(token, str) for values in styles.values() for token in values.values()),
            f"Style values must be token names on {component}")
    for layer in layers:
        for field, group in TOKEN_GROUPS.items():
            if field in layer:
                layer[field] = styles[group][layer[field]]
    check_layers(layers, system)
    return layers


def handoff_swimlane(system, styles, handoffs, *, ink, stroke, label_type):
    """Add one directed transfer per stage to the four-role, three-stage grid."""
    layers = standard_motif("handoff-swimlane", system, styles)
    actions = {layer["id"].replace("-bg", ""): layer["box"] for layer in layers
               if layer["id"].startswith("action-bg-")}
    used_columns = set()
    for source, target, slot in handoffs:
        require(source in actions and target in actions and source != target,
                "A handoff must identify two distinct action slots")
        sx, sy, sw, sh = actions[source]
        tx, ty, tw, th = actions[target]
        require(sx == tx and sx not in used_columns,
                "This swimlane supports one same-stage handoff per column")
        used_columns.add(sx)
        a, b = [sx + sw, sy + sh / 2], [tx + tw, ty + th / 2]
        bend = a[0] + 2.1
        points = [a, [bend, a[1]], [bend, b[1]], b]
        for part, (start, end) in enumerate(zip(points, points[1:])):
            layers.append({"kind": "line", "id": f"{slot}-edge-{part}", "points": [start, end],
                           "stroke": ink, "weight": stroke, "arrow": part == 2})
        layers.append({"kind": "text", "id": slot, "slot": slot, "type": label_type,
                       "box": [bend + .55, (a[1] + b[1]) / 2 - 3, 6.25, 6],
                       "ink": ink, "align": "left"})
    check_layers(layers, system)
    return layers
