# Reproduce a design language

**English** | [简体中文](reproducibility.md)

For handoff to another designer, model or renderer, derive `STYLE.md` and `design-system.json` from shared evidence. One explains judgments; the other locks replayable colors, type, radii, strokes, slots and motifs. Accept reproduction through the executable pack and actual renders.

## Select and approve the design language

1. Group same-scale references by canvas, type hierarchy, axes, image grammar and repetition. Choose one primary family and record supporting uses, exclusions and pages. Leave uncovered pages unclassified. Check each distinctive rule against a representative and contrast page. Resolve style conflicts through task scope and selected evidence.
2. Record source page/region per rule, with native PPTX IDs when available. Separate facts, inference and extensions. Measurements apply to observed samples; transplanted values, fallback fonts and new components are extensions. Unresolved identity rules stay unresolved in `STYLE.md` until evidence supports freezing.
3. Make visual judgments executable: shared top edges, image/text areas and whitespace direction; colors on canvas, titles, labels and within imagery. Image rules need role, subject/text-safe space, crop, color/light and replacement conditions. Distinguish retained original assets from transferred treatments.
4. Encode only reviewed rules. Bind color/type/radius/stroke rules to IDs; layouts name page tasks, families and rules. Multiple reviewed variants may remain selectable. New compositions start as extensions and enter candidates after evidence/review. Keep old versions and rerun affected samples when the pack changes.
5. Before freezing, replay representative pages with original copy and compare against actual sources on the same canvas. Record background, title ink height/left axis, line breaks, backing thickness and side padding. Mark approximated screenshot fonts/backgrounds. Replacement copy reveals variable rules. Record bilingual wrapping, type/backdrop sizing and contrast adaptations in production and select them via `variant`, leaving the baseline independent. If a legacy pack contains only production values, reconstruct that page type's source baseline first.

## Reproduction and review

- **Single page:** fill reviewed slots; compare subject placement, proportion and text-safe regions before cropping replacement photos. Check long titles/body and CJK/Latin mixtures.
- **Multiple pages:** select by narrative role. Reuse the same `motif` for callbacks; approved layouts control scale/highlights. Critical order lives in `sequences`, defining permitted patterns, focus, density and strength per step.
- **Asset replacement:** compare source/output using new images and redrawn shapes. Check visual-language continuity, topic over decoration, and composition after hiding brand/original imagery. If the treatment only works with source assets, revisit roles and relationships.
- **Original backgrounds:** when fidelity requires them, register approved 16:9 art, SHA-256 and source evidence in family `backdrop`. Export source background layers separately beneath new content. Use a separate reconstructed-background pack for replacement review.
- **Across models:** freeze pack, page roles, content, assets and runtime. Models independently submit pattern IDs/slots. Repeated identical mappings should reproduce; different approved layouts need separate focus/order/family review. Do not conflate deterministic rendering with independent visual-selection performance.
- **Two scales:** inspect thumbnail rhythm/focus first, then contrast, weight, crops, collisions and space at viewing size. Assess narrative importance, density and visual strength separately. Title/image must support the same relation. Fix incorrect families, assets, reading order, occlusion or overflow before rechecking.
- **Local detail:** trace source region → rule → actual layer/slot → render observation. Recheck bindings with changed copy/wrapping. Keep technical/visual results distinct; uncertain sources or renderer limits remain unresolved/unreplicated.
- **Type/backdrops:** [check inherited layers](page-composition.en.md#check-inherited-titles-and-emphasis-layers), size ratios and text/backing positions. Record deliberate changes and compare actual glyphs, lines, backing extent and occlusion.
- **Color fields/rhythm:** review [color roles](color-language.en.md) in actual output, not just token presence. Flat areas can use screenshot coverage; photos/gradients/state meaning still need visual/semantic review.

## Tools and limits

The [schema](design-system.schema.json) defines allowed fields. `patterns` are ordered 16:9 layers: text, boxes, lines, curves, images and motifs. Positions use canvas percentages; font sizes/radii use container width; strokes use a 1600 × 900 reference canvas. Layers reference named tokens; layouts position/scale/remap motifs.

Motifs declare text slots in `motifs`. A layout's `motif` layer uses `box` for placement and `bindings` to map each component slot to one page slot, for example `{"party-1": "aside-party-1"}`. Recipes fill page slots and rendering resolves bindings. Motif graphics scale with placement; bound text retains slide type sizing. Bound motifs support text, boxes, lines and single-segment cubic Bézier curves in HTML/native PPTX.

Use `rotation` for slanted boxes, short titles and images. Register selected source pictures in `fixed_assets` with file, SHA-256 and one source-picture object. Source-backed runs compare original image bytes. Replaceable images remain manuscript slots. Check rotated bounds, occlusion and visual balance.

`storyboard.json` contains `version: 1` and `pages`; each page has `id`, `role`, `pattern`, `focus`, `density`, `weight`, `slots`, with focus naming a layer ID. When sequences exist, supply `sequence`; every page must satisfy its allowed pattern/focus/strength.

Run from the repository root into a new output directory, retaining earlier evidence.

```bash
skill=ppt-design-system
python "$skill/scripts/design_replay.py" design-system.json storyboard.json \
  --source /path/to/reference.pptx --assets /path/to/replacement-assets --out /path/to/new-run
node "$skill/scripts/audit_replay.cjs" /path/to/new-run/replay.html
```

- `--source` checks fingerprints, page counts and supplied PPTX object numbers. For PPTX replacement, it also rejects media byte-identical to embedded originals. Recompressed copies, screenshots and PDF image provenance need source/visual review. Supply the source for first freezing; later approved-pack replay receipts state whether source checking ran.
- Pictures/fixed backgrounds stay within `--assets` and are embedded offline. `receipt.json` records pack/storyboard/renderer/HTML/asset hashes and actual original backgrounds. Browser checks use local Playwright/Chromium, selectable through `REPLAY_PLAYWRIGHT_PACKAGE` and `REPLAY_CHROMIUM`.
- Checks cover source addresses, allowed families/patterns, fields, bounds, bindings, sequence, Chromium text collisions/overflow and image loading. Reports include versions and screenshot hashes. Same-runtime screenshots can check replay consistency. Reaccept when fonts, OS, browser or medium change. Focus, evidence-supported inference and family recognition after replacements require design review.
- The command renders reviewed packs into HTML visual samples. Collect web/image/PDF evidence through the [extraction guide](style-guide.en.md).

## Fixed original asset acceptance

Declare `required_fixed_assets` when a layout must retain original PPTX foreground media. Keys are top-level image-layer IDs; `asset` names a `fixed_assets` entry and `purpose` describes its page role.

```json
{
  "left-paper": {
    "asset": "creased-paper",
    "purpose": "Carry the left party and its constraints"
  }
}
```

Packaging, compilation and replay check the binding to the required original. Receipts record required layers, purposes, evidence IDs and asset hashes per page. Keep `receipt.json` beside HTML for browser checking of rendered layers, visible areas and actual embedded bytes. `requiredFixedAssetChecks` records counts per width; checking old HTML alone yields zero. Separately compare source/output for occlusion, role and hierarchy.
