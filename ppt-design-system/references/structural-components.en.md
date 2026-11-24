# Standard structural components

**English** | [简体中文](structural-components.md)

When a pack provides the visual language but lacks a layout for the manuscript's relationship, start from a standard graphic. Structure comes from the manuscript; colors, type hierarchy, radii and line weights come from the reviewed reference. The whole-page layout places the title, explanation and graphic.

| Standard graphic | Use when | Text slots | Reading order |
| --- | --- | --- | --- |
| `linear-flow` | A three-step linear process | `first`, `second`, `third` | First → second → third |
| `hierarchy-tree` | One parent and three direct peers | `parent`, `left`, `middle`, `right` | Top down, with a shared child connector |
| `three-step-cycle` | Three ordered steps with an explicit return to the start | `first`, `second`, `third` | Start → lower right → lower left → start |
| `paired-state-comparison` | Two states on three shared dimensions | `left-heading`, `right-heading`; `dimension-1`, `left-1`, `right-1`, and equivalent rows 2/3 | Align common dimensions; manuscript determines any stage direction |
| `qualitative-matrix` | Two explicit low/high classification axes and justified quadrant membership | `x-axis`, `y-axis`, `x-low`, `x-high`, `y-low`, `y-high`; four sets such as `top-left-heading`, `top-left-body` | Axes, then quadrants/items; within-quadrant position does not encode quantities |
| `nested-ownership` | One shared scope with three exclusive groups, two members each | `root`, `group-1`–`group-3`, `role-1-1`–`role-3-2` | Outer scope, then group and members |
| `handoff-swimlane` | Four roles, three phases, at most one named same-phase handoff per phase | `lane-1`–`lane-4`, `phase-1`–`phase-3`, `action-0`–`action-11`; a separate text slot per handoff | Phases horizontally; actions aligned by role; arrows identify sender, recipient and item |

First match the original pack strictly. After confirming a gap, import the required [standard graphic](structural-components/) into a production copy. Use `standard_motif(component, system, styles)` in `scripts/structural_components.py` to map reference colors/type, then register returned layers in `system["motifs"]`. These style-role names map to existing token IDs:

```python
styles = {
    "colors": {"strong": "enamel", "inverse": "white", "panel": "green-tint",
               "text": "ink", "edge": "enamel"},
    "type": {"node": "insight"},
    "radii": {"corner": "card"},
    "strokes": {"outline": "hair", "connector": "diagram-line"},
}
system["motifs"]["linear-flow"] = standard_motif("linear-flow", system, styles)
```

Bind text through a layout's `motif` layer and `bindings`; recipes connect manuscript fields to page slots. Mark the component `extended`, citing reference pages that support inherited visual parameters. Nodes, labels and connectors use existing HTML/PPTX rendering. PPTX uses native shapes/text/straight connectors; group movement moves them together, while individual-node edits require endpoint checks. The standard cycle uses three directed segments to preserve direction and return semantics.

Define `diagram-line` in the production copy. Check arrows at the actual size of small sidebar figures; if needed, derive a heavier diagram stroke from the reference's thin-line style, keeping the original pack and recording the extension.

Each graphic currently has the fixed item count above. Report capacity/structure gaps for multi-level trees, branching flows, long labels or more nodes before adapting. Check direction, ownership, return flow, copy, style and native PPTX objects in different placements and with replacement copy.

### Bind nested containers and swimlanes

- Nested containers use `standard_motif("nested-ownership", system, styles)`. Bind members by group. Style roles are `colors.panel/surface/accent/ink/line`, `type.label/body`, `radii.corner`, `strokes.rule`. Hierarchy, boundaries and spacing express membership. For shared roles/multiple memberships, consider labeled connections or a grouped table.
- Swimlanes use `handoff_swimlane(system, styles, handoffs, ink=..., stroke=..., label_type=...)`. Base roles are `colors.panel/surface/ink/line`, `type.label/body`, `radii.corner`, `strokes.rule`. Action slots are row-major, with three phases left to right per row. Pass `(sender action slot, recipient action slot, handoff label slot)` tuples: `("action-9", "action-3", "available-window")` means phase one, row four to row two. Arrows derive from those positions. Use a unique text slot per handoff and regenerate connectors when phases/direction change.
- Register returned layers in the production copy's `motifs`. Keep existing `motif.bindings`; record semantic fields, corresponding slots and measured placement `limits` in the recipe. Prefer full-width swimlanes; check label width, arrow exits and long actions with the current font. For cross-phase or multiple same-phase handoffs, consider a role table naming sender/recipient or a separate phase detail. Edges remain independent shapes; check endpoints after moving nodes.

A route flow can use markers, separate labels and a continuous curve with explicit start/end. Feedback cycles can preserve a clear forward route and use a separate returning arc. A ring is an option when the reference supports circular composition; verify direction. Record contours, label positions and line rhythm behind the choice. HTML/PPTX share a four-point `curve` layer: start, two controls, end. In PowerPoint it is a freeform; adjust curve endpoints after moving a node.

## Drawing selection and rendered review

1. Record source evidence for node outlines, placement axes, routes/arrows, label spacing and scope. Keep the strict match and the relationship each chapter needs. Confirm actual dependency or return flow before selecting a form.
2. Build two applicable candidates using the [selection conditions](structural-components/variants.json). Compare `step-rail`/`milestone-path` for a three-step flow or `return-arc`/`ring-cycle` for a cycle. Keep copy and reference parameters identical, adapting markers, label spacing and arrows to the real frame. Rings need a nearly square region; thin arrows must read at final size. Call `standard_motif(relation, system, styles, variant=variant_id)` per candidate, registering motifs and recipes with `variant`. Their roles use three `colors.*-marker` entries, `colors.edge`, `colors.text`, `type.node`, `radii.corner` and `strokes.connector`.
3. Temporarily bind the same semantic manuscript to both candidates and render through Make before selecting. Check relationship, readability and agreed editability, then give a verifiable reason: for example, the return arrow goes from seed return to borrowing, and a ring gives all three stages a common focus. Record ambiguous labels, blocked arrows, text crossing lines and editing limits. If both fail, revise and rerender. A freeform Bézier preserves route shape; automatic connector following after moving a node must be actually tested, or that editing check fails.
4. Keep the following record in production. Evidence IDs refer to the pack; images refer to actual renders. The command validates the record/pass conditions, while the model/reviewer judges the finished design. Make with the selected manuscript retains recipe/source in the compile report. Keep the original pack and unselected candidates.

```json
{
  "chapter-id": {
    "evidence": ["reference-geometry"],
    "candidates": {
      "step-rail": {
        "render": "rail.png",
        "checks": {"relation": true, "readability": true, "editable": true},
        "observation": "Evenly spaced stages and short labels below give the fastest reading."
      },
      "milestone-path": {
        "render": "path.png",
        "checks": {"relation": true, "readability": true, "editable": true},
        "observation": "The continuous curve echoes the reference with sufficient label spacing."
      }
    },
    "selected": "milestone-path",
    "reason": "The reference connects stages with curves and this placement has enough space."
  }
}
```

```sh
python ppt-design-system/scripts/review_variants.py manuscript.json production/design-system.json \
  variant-review.json > selected-manuscript.json
```
