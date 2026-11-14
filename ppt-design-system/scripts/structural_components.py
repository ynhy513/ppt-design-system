"""Materialize a standard diagram as a shared motif using reviewed design tokens."""

from pathlib import Path

from design_replay import TOKEN_GROUPS, check_layers, load, require


LIBRARY = Path(__file__).resolve().parents[1] / "references/structural-components"
COMPONENTS = ("linear-flow", "hierarchy-tree", "three-step-cycle")


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
