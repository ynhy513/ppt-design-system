# Inherit color roles and fields

**English** | [简体中文](color-language.md)

Use when identity depends on large color fields, light/dark rhythm or specific color roles. Keep Extract → Reuse → Make; do not force colorful chapters onto every reference.

## Extract and select

Record “source region → color role → actual token/layer → conditions” in existing `STYLE.md` and evidence. Beyond HEX, identify canvas background, chapter field, content surface, text, action, state or color within an image. Record page types, position, area and cross-page transitions. Image colors do not automatically become chapter backgrounds; action, logo and state colors are not interchangeable decoration.

Use representative/contrast pages to distinguish stable rules from incidental color. Separate declarations, measurements, interpretations and production extensions. Select light, dark and chapter variants within source-supported scope. A restrained reference's restraint is an inherited rule; do not add unsupported fields simply to distinguish references.

For third-party `design.md` analyses, record author, repository/URL, revision/retrieval date, fingerprint and non-official status. Official-page cross-checks do not make third-party text official. State observed scope, unloaded regions and conflicts separately. Without page evidence, document-led adaptation is possible, but website fidelity is not established. Keep current-page/document disagreements without silently replacing frozen packs.

## Map and produce

- Bind fields to existing background tokens, boxes, components or approved art. A palette without composition evidence supports limited representative designs, labeled as adaptations; chosen area ratios are not source facts.
- Choose reviewed variants by page task, preserving their field placement and light/dark rhythm. For long copy, regroup, split or adjust production slots before shrinking a field into an accent line or making every light page dark. Record changes in production; leave the frozen pack intact.
- Review thumbnails and reading-size pages for actual field appearance/placement, text contrast and state meaning. Type proportions, density and image roles retain their separate acceptance checks.
- For drift-prone flat fields, register reviewed regions/bounds and run the check below. Pixels detect observable area changes, not semantic/aesthetic/sequence quality. Check native PPTX backgrounds/fills/text separately in the target environment.

## Check color fields in actual screenshots

`check_color_fields.py` reads an independent production-review JSON without changing the pack schema. Use actual single-slide screenshots without editor controls; paths are relative to the review file. `region` is normalized `[left, top, right, bottom]`, defaulting to the whole slide. Coverage denominator is the selected region. `tolerance` is per-channel RGB error, default 3. Bounds need source/reviewed-adaptation support; there is no universal brand-area threshold.

These numbers illustrate one review, not a brand rule:

```json
{
  "pages": [{
    "id": "cover",
    "screenshot": "renders/cover.png",
    "fields": [{
      "role": "chapter-field",
      "color": "#FFE01B",
      "region": [0, 0, 1, 1],
      "min_fraction": 0.75,
      "max_fraction": 1,
      "evidence": "source.md: chapter color; official hero screenshot",
      "basis": "Reviewed full-page field adaptation, allowing overlaid title and body text"
    }]
  }]
}
```

```bash
python ppt-design-system/scripts/check_color_fields.py color-review.json --out color-report.json
```

The report records actual coverage, expected range, region, source note, screenshot SHA-256 and pass status. Empty lists, invalid bounds, missing basis and unreadable screenshots are rejected; out-of-range coverage exits nonzero. Use `region` to stop unrelated same-color elements elsewhere compensating for a missing local field. Do not use one HEX fraction to accept gradients, translucent layers, photographs or textures; retain screenshots and compare regions visually. Do not hide unreviewed drift by increasing tolerance or widening bounds.
