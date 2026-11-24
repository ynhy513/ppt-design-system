# Review component coverage by intended use

**English** | [简体中文](component-coverage.md)

Before scanning, state the pack's intended use in one sentence and identify recurring content relationships. Prioritize relationships affecting comprehension/decisions. Also extract distinctive compositions, assets and local details.

Use the [component library](component-library.en.md) for content contracts/reuse states. Select needed components by use; actual implementation follows the target reference evidence.

## Initial component contracts

These two contracts support internal mechanism explanations and progress reviews. Keep semantic fields/relationships consistent; source evidence and the target medium determine shapes, colors, typography, composition and capacity.

| Relationship | Page fields | Item fields/count | What readers must understand |
| --- | --- | --- | --- |
| Two-way feedback `feedback-loop` | `kicker`, `folio`, `title`, `setup`, `loop-label` | Two items, each with `party`, `mechanism`, `flow`, `constraint` | One flow points to the second party; the other returns to the first. Show a shared result and each party's limits. |
| Three-stage actions/acceptance `action-checkpoints` | `kicker`, `folio`, `title`, `decision` | Three items, each with `milestone`, `action-label`, `action`, `check-label`, `check` | Preserve manuscript stage order and group each action with its acceptance condition. |

Existing recipes continue owning their semantic contracts. Complete missing relationships in a working copy using these contracts or current content requirements.

Action checkpoints require explicit stage actions and acceptance conditions. If a page combines immediate actions, milestones and independent measures, preserve those groups and use their corresponding recipes. Require separate acceptance fields as manuscript inputs.

## From a coverage gap to a callable layout

1. Record asset evidence separately from its page role. Export native PPTX media by object ID; deduplicate originals by hash while retaining each occurrence's crop, position and grouping. For PDF, check page image objects/streams and identify masks, crops and render derivatives. Screenshots support visible reconstruction; independent originals, exact fonts and layers depend on obtainable evidence. Classify layout surfaces, decoration, replaceable content and evidence, and whether they follow a page, component or slot.
2. Strictly match one fixed neutral manuscript against the source pack, retaining pack/report. In `STYLE.md`, record target component, fields/capacity, baseline result, source addresses, completion decision, recipe and checked scope. Use the state table below. Catalog/manifests separately track independent exportability.
3. For frequent missing relationships, first recombine confirmed axes, type hierarchy, color roles and parts. Extend missing flows/trees/cycles via [standard structure/style mapping](structural-components.en.md). Mark new elements `extended`; distinguish inherited visual evidence from added structure. Keep probes/reports outside the pack.
4. For one component in two compositions, reuse its slots, layer relationships and style definition before arranging page regions/titles. HTML layouts can reference [shared motifs with text slots](reproducibility.en.md#tools-and-limits). Recipes and `variant` still select the whole-page layout.
5. Freeze the candidate and rerun the neutral probe plus a second same-relationship manuscript from a fresh ZIP extraction. Check arrows, stage order, copy/slots, Chinese wrapping and hierarchy. Use an over-capacity counterexample. Record recipe limits separately from visually verified lengths; claims cover tested placements/media only.

| State | Evidence |
| --- | --- |
| Directly callable | Source recipe matches relationship, fields and capacity, with verified slot binding and layout. |
| Adapt existing structure | The source/pack has the relationship; extra/rebound fields can meet the need. Identify independent and whole-page-bound parts. |
| Extend in the reference style | Reusable rules/parts exist, but the relationship needs new grouping, connections or hierarchy. |
| Unverified | Evidence, implementation or verification is incomplete; record impact/scope. |

For format/style comparisons, first run the same semantic manuscript against each original pack and retain matches/gaps. Run it again against source-backed working copies. Record shared content slots and each style's visual rules; check original text, order and relationships page by page.
