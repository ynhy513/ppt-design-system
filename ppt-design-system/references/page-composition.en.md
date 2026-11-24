# Whole-page composition rules

**English** | [简体中文](page-composition.md)

## Extract

Inspect whole-page renders at the same scale, selecting representatives by family/task. Mark first focus, main information cluster, secondary regions and whitespace before tracing objects. Confirm recurring arrangements on similar pages and test scope against dense pages, transitions and opposing compositions. A single page initially supports an observation for that page type.

| Observation | Record |
| --- | --- |
| Balance/whitespace | Main cluster location, primary/secondary area ratios and counterweight; compare content importance, image/text area and actual visual strength. |
| Alignment/offset | Edges, axes and intervals supporting comparison; distinguish intentional staggering/rotation from numbers, headers, body/navigation needing stable alignment. Record grid discipline when no offsets exist. |
| Stacking/overflow | Foreground layers, permitted container crossings, and titles/notes/axes/key imagery that must remain visible. |
| Image direction | Evidence, reaction, action cue, material or mood; subject, framing, gaze/action direction, crop, text-safe space and recurring treatments. |
| Cross-page variation | Stable anchors versus task-driven changes in image proportion, balance, density and transitions. |
| Line roles | Phrase/baseline emphasis versus composition dividers; text target and divider column spans/endpoints. |

Translate adjectives into observed actions. “Social” may come from expressive close-ups, dynamic poses or transparent cutouts for participation/interaction/action pages. Specific treatments need reference evidence. Separate perspective diagonals, native rotation and production rotation angles.

For details changing hierarchy/grouping, record **source region, target, binding and change conditions**. Underlines bind phrases and wrap with them; backing fields may bind a line/phrase; cross-column dividers bind axes/spans. Compare family samples with/without a detail to distinguish general rules, variants and one-offs.

## Compile and select

Record a rule per composition: source page/region, relationship, first focus, region placement, offset-capable layers, protected reading areas, image role and replacement conditions. Distinguish fixed relationships from density/aspect-dependent ones. Generalize only with several supporting samples. A one-page angle/width is evidence for that page; new ranges are extensions.

Write rules in `STYLE.md`, cite them/page tasks in recipe `layout`, and implement size, position, order, rotation and image slots in `pattern`. For text-only storyboards, state equivalent positioning/asset instructions.

Even without a whole-page recipe match, evidenced local compositions can be reused. For line-by-line title backings, begin with the source pack's position, dimensions and padding, then check backing/title correspondence. Try same-family type/line-break variants before modifying the backing. Register necessary backing changes as extensions and compare reference, baseline replay and production side by side.

Record title/subtitle/body/label family or fallback, size relative to page width, weight, leading and alignment. Size ratios and text/backing geometry are reuse evidence. Screenshot estimates remain observations; prefer native PPTX/readable PDF values. Try original sizing first, wrapping before shrinking. Any reduced layer needs a reason/measured size while retaining family, weight and leading.

When title breaks are compositional, record each line's role/order/break. Bilingual covers use supplied/approved titles with inherited alignment/type. Same-size lines can share a slot with explicit breaks; different scales need separate layers. Missing translations remain gaps; approved monolingual variants need a recorded basis.

### Check inherited titles and emphasis layers

Keep the frozen original pack for comparison. Register selected layouts in existing Reuse review, including inherited title/subtitle/body/labels and backing/fields. New whole-page compositions still register comparable inherited local layers. Without comparable source geometry, record evidence/reasons in `extensions`. Use `target` for renamed layers, four percentage coordinates in `box` for container changes, and `size` for reduced type, with reasons. Checks compare actual size, weight, leading, family, alignment, box geometry, backing color and relative stacking.

If backing is a picture such as paper, register that image layer. Checks also compare fixed-asset fingerprints, fit and crop position; visually review glyph placement within it.

For distinctive background colors/fixed master art, set `"background": true` and establish the baseline from a source flat region/native fill. Production checks the background/art hash. A new layout inheriting only background can leave `layers` empty while explaining new type/positions. Passing inheritance does not replace source comparison: an old readability adaptation is not the original color.

For white strips behind individual title lines, measure source glyph height, strip thickness, left axis and side padding. Recheck new glyph widths/line counts and record remeasured layouts. Fixed-width slots apply only when the source has a fixed field.

Register independent emphasis-line layers too; checks compare path, stroke color and width.

```json
{
  "source_system": "extracted/design-system.json",
  "reviews": {
    "adapted-cover": {
      "source_pattern": "blue-print-cover",
      "layers": {
        "title": {},
        "title-band": {},
        "subtitle-band": {},
        "subtitle": {"target": "caption", "size": 4.2, "reason": "Longer copy takes two lines on the original strip."}
      }
    }
  },
  "extensions": {
    "nested-ownership": "The reference has no hierarchy layout; reuse its color scale for ownership containers."
  }
}
```

```bash
python ppt-design-system/scripts/make_deck.py production.zip manuscript.json \
  --inheritance-review inherited-layout.json --out new-run
```

`source_system` is relative to the review file. Missing reviews or deviations stop production before rendering. Batch output includes `inheritance-report.json`; the local editor accepts `--inheritance-review` too. Keep the record even for storyboard-only handoff; run checks when rendering. Compare actual glyph size, wrapping, font substitutions and backing weight side by side. Record deliberate title/body and subtitle/body ratio changes on representative pages.

For protected explicit breaks, register nonempty line counts such as `"lines": 2` per text layer. Register each layer separately for two-layer bilingual titles. Make checks line breaks and final layer geometry after filling slots/loading edits. Update production pack/review and rebuild the baseline when protected geometry must change.

Run `audit_replay.cjs` on static HTML beside its inheritance report. It checks actual rendered title lines and identifies page/layer when copy wraps further. Choose a reviewed long-title variant or confirm shorter copy, then rerun. Check language order/translations visually.

Phrase emphasis binds through a text layer's `underline_slot`. Supply a phrase occurring exactly once in title/body, or an empty string to skip emphasis. Native browser underlines follow fonts/wrapping. Independent dividers use `line` layers with original axes/spans; review both separately.

1. Select candidate layouts by relationship, content length, comparison dimensions and order; then choose variants by source balance, alignment and imagery. Equal item counts can have different compositions.
2. If peer content uses unequal containers, preserve peer status through equal type, label treatment or clear order. Stagger/overlap/rotation require support from both the reference and page task.
3. Choose reuse/search/extension/data drawing through [image roles](image-roles.en.md). Check subject/placement. Originals enter fixed assets or replacement slots by use. When imagery can be omitted, rebalance whitespace/weight and register the extension.
4. For excess capacity, first try a dense same-style variant or adjust slots while preserving focus/reading axes. Record relationship changes and reasons.

## Acceptance

Compare source representatives and new pages at the same scale. Review thumbnail focus/balance/whitespace/rhythm, then rotated bounds, occlusion and image storytelling at reading size. Browser passes are technical evidence; composition/asset-direction reproduction requires visual review.

Trace every used feature to source evidence, its actual production treatment and applicable role. Check a distinctive and a dense page; when material permits, replace content/assets. If an applicable source-backed feature disappears in rendering, repair the recipe and recheck. For document/storyboard-only scope, record completed checks and untested parts.

For local details, compare regions at reading size, confirm the target and change position/wrapping to test bindings. For example, replace the emphasized phrase across lines and check that underlines follow each line. Check divider axes, endpoints and column spans independently.

## Contrasting examples

- **Collaged peer findings:** offset papers/slight rotations add motion while peer headings share type. Expressive face cutouts can support participation. Row-corresponding information retains horizontal axes; slant stays on backings/short labels.
- **Aligned peer cards:** retain equal cards/shared starts. Detail pages can reuse a locator at one position with shifting highlights. Offsets/person stickers require that family's own evidence.
