# Standard component library v0.1

**English** | [简体中文](component-library.md)

The library currently covers eight component families. States below come from screenshot-pack reuse trials and their generated evidence. Colors, type and graphics follow the active reference. New packs select components by actual use and record gaps.

## Layers

| Layer | Responsibility |
| --- | --- |
| Art Direction | Identity and variation. Artsy uses hard-edged fields; Wikimedia uses white, blue labels, navy text and fine rules. |
| L0 · Design Tokens | Color roles, type, strokes, margins and alignment. The two existing packs define color/type; coordinates mainly express spacing/grid. |
| L1 · Primitives | Text, boxes, lines, curves, images and local emphasis. Artsy's cover grid and Wikimedia's blue/white strips have individually referenceable definitions. |
| L2 · Components | Content structures assembled from primitives; semantics, state and implementation are listed below. |
| L3 · Layouts | Regions, placement, proportions and capacity. Full-page overview and sidebar are two placements of a component. |
| L4 · Slide Archetypes | Page tasks: opening, comparison, evidence, framework, roadmap. Tasks/relationships drive selection. |
| L5 · Deck System | Order, density, visual strength and callbacks. Trial packs preserve manuscript order; storyboards plan the overall rhythm. |

## Inventory

- **Independent reuse:** one definition and separate slots, generated in two same-style compositions and checked with replacement copy.
- **Whole-page bound:** used in generated output, but the page recipe still owns its slots/structure.
- **Needs extension:** purpose/minimum contract exists, implementation and verification remain.

| Family | Component | Minimum content contract | State and implementation |
| --- | --- | --- | --- |
| Typography | Hero Title | Main title, optional subtitle | **Whole-page bound:** Wikimedia `blue-print-cover`, Artsy `modular-color-cover`. |
| Typography | Section Title | Chapter name, optional short claim | **Whole-page bound:** Wikimedia `green-manifesto`, Artsy `mosaic-three-stages`. |
| Typography | Quote | Exact quotation and speaker/source | **Needs extension:** source comparison page has an example; add independent quote/source bindings. |
| Typography | Eyebrow | Chapter/context | **Whole-page bound:** `kicker` slots on white Wikimedia and Artsy editorial pages. |
| Content | Text Block | Explanation, optional heading | **Whole-page bound:** Wikimedia `white-paired-evidence` explanation slots. |
| Content | Bullet Group | Related points, numbering when ordered | **Whole-page bound:** Artsy `split-numbered-outline` has three fixed items. |
| Content | Insight Block | A conclusion and explanation/evidence | **Whole-page bound:** Wikimedia `green-manifesto` claim/explanation slots. |
| Data | KPI Card | Metric, value, unit, time/scope; change needs baseline | **Needs extension:** verifiable numeric slots and missing states. |
| Data | Chart | Data, units, relationship and source | **Needs extension:** Artsy has source evidence; the trial reconstructed some compositions as qualitative evidence blocks. |
| Data | Data Table | Columns, records, units, missing states | **Needs extension:** actual rows/columns and editable-data contract. |
| Data | Progress Bar | Current value, target/maximum, unit | **Needs extension:** bounds, excess and unknown states. |
| Visual | Hero Image | Subject, image role, crop and readable region | **Whole-page bound:** Wikimedia's cover uses a reconstructed blue-ink background. |
| Visual | Image Grid | Replaceable slots, sequence and crop rules | **Needs extension:** existing color grids suggest composition. |
| Visual | Icon Group | Meaning, labels and use conditions | **Needs extension:** verify replacements preserve the role. |
| Relationship | Process Flow | Stages, order, handoff/dependency | [Standard structure](structural-components.en.md) supplies a three-step flow; Artsy `mosaic-three-stages` is a whole-page layout. |
| Relationship | Hierarchy | Parent and clearly assigned children | [Standard structure](structural-components.en.md) supplies one parent/three direct children. |
| Relationship | Cycle | Ordered nodes and explicit return | [Standard structure](structural-components.en.md) supplies a three-step cycle, distinct from two-way feedback. |
| Relationship | Feedback Loop | Two parties, opposite flows, shared result, party limits | **Independent reuse:** Wikimedia `two-way-feedback` passed overview/sidebar replacement-copy checks; Artsy remains whole-page bound. |
| Relationship | Matrix | Two meaningful axes, quadrants, classification evidence | [Standard structure](structural-components.en.md) supplies a qualitative matrix; Wikimedia also has a whole-page classification recipe. |
| Relationship | Action Checkpoints | Three ordered stages, each with action/acceptance | **Independent reuse:** Wikimedia `three-action-checkpoints` passed overview/sidebar checks; Artsy remains a three-column page recipe. |
| Comparison | Paired Comparison | Peer objects, shared dimensions and evidence | **Whole-page bound:** Wikimedia `white-paired-evidence`, Artsy `paired-finding-bands`. |
| Comparison | Paired State Comparison | Two states, descriptions/values and shared dimensions | [Standard structure](structural-components.en.md) supplies three dimensions/two columns. Show progression only when the manuscript specifies stages. |
| Navigation | Page Number | Page or approved order | **Whole-page bound:** overview/sidebar layouts each declare `folio`. |
| Navigation | Agenda / Section Marker | Chapters, order/current chapter | **Whole-page bound:** Artsy `split-numbered-outline` has three numbered items. |
| Emphasis | Callout | A highlighted statement and context | **Whole-page bound:** Wikimedia `blue-print-cover` uses a blue-backed supporting claim. |
| Emphasis | Phrase Highlight | One unique source-text phrase | **Whole-page bound:** underline slots in Wikimedia `flush-three-colors` and `white-ruled-framework`. |
| Emphasis | Annotation | Note, target object/region, connection | **Needs extension:** verify crops/repositioning preserve its target. |

See [initial contracts](component-coverage.en.md#initial-component-contracts) for feedback/action-checkpoint fields and counts, and [structural components](structural-components.en.md) for standard graphic integration. Before promoting a reuse state, check a second composition, replacement copy, capacity boundaries and hierarchy.
