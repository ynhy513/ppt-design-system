# From reference elements to new manuscript pages

**English** | [简体中文](element-compilation.md)

## 1. Extract the element catalog

Review representative pages by visual family, then number source pages/objects. Record IDs, position, parent groups and hierarchy. Deduplicate readable properties into tokens: colors, fonts/type scales, spacing, shapes/radii, fills/gradients, strokes, effects, image fingerprints/crops. Separate native/decorative backgrounds. Retain icon shapes/asset references; design review supplies meaning. Rasterized details remain observations/unknowns.

PPTX supports direct scanning and preserves object/media addresses for selected-asset export. Interpret grouped coordinates with parent transforms. For PDF, images and websites collect observable tokens/sources through [format-specific evidence](style-guide.en.md).

Inspect small distinctive accents: chapter highlights, step icons, corner labels and cutout subjects. Keep reusable originals and necessary derivatives in `assets/`; register source page/object/package location, fingerprints, roles, meaning and replacement conditions. Generic highlights may stay fixed, step icons follow actions, while people/products/platform marks follow content context. If master/layout objects matter, retain their scoped addresses and bind them to visible pages through evidence `catalog_refs`.

### Select reusable assets

Compare candidate assets with representative source pages/objects. State their role now and after changing copy; choose retention based on pack scope. Frequency is only a clue: a one-off horizontal highlight can be essential to a transition.

For screenshot regions that look like pictures, first use [image roles](image-roles.en.md) to distinguish actual photography, reconstructable language and data. Image decisions and layout extensions can proceed together for new relationships.

- **Keep the original:** retain contours, gloss or brand features that matter to the page role, with invocation conditions. Layer-dependent decoration may also include a text-free render derivative, such as a glass card surface.
- **Keep a replacement slot:** people, product photos and data figures may change with the topic. Define role, subject position, crop and stacking. A product-series-specific pack may retain its particular photos within scope.
- **Keep as evidence:** unclear use, independence or provenance stays as an observation/source page until there is a concrete reusable purpose.

The catalog records evidence/roles; grammar `use` and layout slots record invocation/replacement. Replacement-copy review checks fixed assets still contribute and new images preserve composition.

When reusing/extending a pack, inspect the actual placement of inherited roles. Papers, clips and cutouts affecting grouping/depth/focus should trace to originals, rendered layers and screenshots; a manifest only proves availability. Source-stretched paper/label decoration may use `fit: fill`; people/products retain subject proportions through crop rules.

For fixed PPTX foreground originals the layout promises to retain, register layers/assets/purposes in `required_fixed_assets`. Choose required originals per page/variant, such as separate paper surfaces for two columns; select mood cutouts by page task. Retain source comparisons and inspect overlap, stacking and first focus after replay. [Configuration and acceptance](reproducibility.en.md#fixed-original-asset-acceptance)

## 2. Compile usage rules

Select reusable elements from the catalog. Register `kind`, `family`, `objects`, `tokens`, `relations`, `use`, `status`; use `change` to explain extensions. Icons need direction/meaning; photos need subject/crop/depth; backgrounds belong to family base layers. Cards need relationship, capacity, title/body hierarchy and boundaries.

Before recipes, complete [whole-page observation](page-composition.en.md). Attach rules to page tasks, distinguishing original arrangements/image usage from new-content extensions.

`recipes` bind a chapter relationship and optional `variant` to a pack `pattern`. Trace layers to reviewed elements. Allocate slots/capacity through `fields`, `items`, `limits`. `layout` describes first focus, primary/secondary placement, alignment/offsets and image role/omission; implement it in `pattern`. Character limits are preliminary; browser rendering determines fit. The system owns positions, colors, type and motifs.

## 3. Read, match and extend

Inputs are original copy and a pack; outputs are separate `storyboard.json` and `compile-report.json`. `STYLE.md` explains design, `element-catalog.json` records evidence, `style-grammar.json` selects recipes and `design-system.json` renders them. Production assets live under the current asset root while preserving source paths/fingerprints.

Normalize chapters into `id`, `intent`, `relation`, `fields`, `items`, with `variant` when needed. The top level contains `version`, `chapters`, and `sequence` when reviewed rhythm exists. Relations express judgments such as feedback, peers, row correspondence, progression or monitoring. Preserve slide copy/order; recipes own layout/layer IDs.

The compiler checks relation, variant, fields, count, capacity and sequence. It writes a storyboard only when every chapter has one match. Gaps distinguish missing-relation recipes, failed constraints and multiple candidates, retaining affected copy and reusable elements.

### Identify relationships from natural language

The executing model reads the original before providing semantic relationships to the compiler. Keep paragraph locations, source wording, relationship/direction, rationale and uncertainty per candidate. Use prerequisites, handoffs and dependencies for order, including reverse-narrated prose. Parent/child relationships need ownership/reporting evidence; cycles need the last step affecting the next start. Shared location/time/purpose alone often supports peers.

When evidence is insufficient, mark the missing relationship and present known facts in parallel/text. When the relation is clear but branches/count exceed components, report a structural gap. Retain source and inference records. During acceptance, compare those records, strict gaps, style mapping and actual renders, tracing each directed edge back to the manuscript.

## 4. Design extensions

1. **Locate the expression gap.** Keep the first match report and state the relationship readers need. Distinguish capacity, ambiguous candidates and missing structure. For capacity, first regroup, split or choose a dense variant. Resolve candidate ambiguity using page tasks/source composition. Extend only when candidates still cannot carry the relationship/content.
2. **Recompose before adding the minimum.** In production, use existing type, colors, assets, axes and components first. Add necessary layers/slots/layout only if the relation remains incomplete. Choose flows/trees/cycles from [structural components](structural-components.en.md). Record inherited evidence, retained relationships, additions/roles, conditions and capacity. Media-slot changes/page splits need editability/reading-order notes.

   For multi-level ownership/cross-role handoffs, consult [ownership and handoffs](reference-led-diagrams.en.md#multi-level-ownership-and-cross-role-handoffs) by the reader's question. Confirm relation/slots before style mapping. Recomposition using evidenced type/backdrops also needs the [inherited-layer check](page-composition.en.md#check-inherited-titles-and-emphasis-layers).

3. **Verify with a second manuscript.** Compile/render the current and another same-relationship manuscript. Replace parties, phrases or assets; check fit, grouping and meaning. For flow/feedback, also check direction, endpoints and label ownership. Review family recognition/hierarchy at the same scale, recording technical checks separately.
4. **Decide where it belongs.** One-off/unverified candidates stay in production. Candidates with replacement-copy/visual acceptance and clear scope can enter a new pack: add patterns to `design-system.json`, rules to `style-grammar.json`, and mark elements `extended`. Reuse catalog evidence, add new sources when needed and explain scope in `STYLE.md`. Retain the original and replay affected samples; preserve reusable old recipes.

### Example: two feedback wheels in a report style

| Stage | Treatment |
| --- | --- |
| Gap | Two sides need reciprocal feedback; existing horizontal bands can state two findings but do not express the loop. |
| Recomposition | Retain magenta/gold, hard edges, regular black text and white spacing; arrange equal fields side by side with a central connection region. |
| Minimum additions | Two native SVG outlines, two directed curves and flow-text slots. First output runs upper left→right, second lower right→left. Shared result sits centrally; constraints stay beneath each side. |
| Replacement and decision | Substitute demand/delivery teams, recompile/render and verify parties/flows. Following original/neutral-copy browser checks and outline/arrow-endpoint review, register `two-wheel-feedback-loop` as a `feedback-loop` recipe. Keep old bands for parallel findings. |

## Run

```bash
skill=ppt-design-system/scripts
py=python
pack=/path/to/extracted-design-pack
"$py" "$skill/compile_story.py" "$pack/design-system.json" "$pack/element-catalog.json" \
  "$pack/style-grammar.json" /path/to/manuscript.json --out /path/to/compiled
"$py" "$skill/design_replay.py" "$pack/design-system.json" /path/to/compiled/storyboard.json \
  --assets /path/to/production-assets --out /path/to/rendered
```

Compiled `STYLE.md` summarizes elements, adaptation rules and rendering parameters. `compile-report.json` records recipe, declared density, slot character usage/limits, objects, source tokens, executable tokens and gaps per chapter. Use these to trace splitting, merging and choices across copy variants; [actual rendering](reproducibility.en.md) determines fit. Semantic and aesthetic recipe judgments require review.
