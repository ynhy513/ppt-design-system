# From reference material to STYLE.md

**English** | [简体中文](style-guide.md)

With only a style description or brand/IP name, start with [imagery and visual-direction selection](style-selection.en.md): resolve direct IP versus similar-style assets where needed, then render same-copy candidates. With a concrete reference or approved direction, continue below.

## Collect evidence

Record the source scope and target medium. Frames, watermarks and contents pages may belong to a compiler, while photos, labels and packaging belong to another system. Identify each source and the layer being extracted.

| Input | Collection method | Address and limits |
| --- | --- | --- |
| PPTX | Read native objects, groups, title alignment and backgrounds with project scripts; inspect representative renders for hierarchy, crops and stacking. | Page, object ID and normalized coordinates. Retain native/render conflicts. A PDF preview does not replace object/media scanning of the original PPTX. |
| PDF | Inspect thumbnails/page types, render representative pages, and use readable text/vector objects to check size, position and color. Treat scanned pages as images. | Physical PDF page and region. Sampled colors describe that render. |
| Image | Mark canvas/regions; measure color, whitespace, axes, stacking and image roles. | Filename and pixel/normalized region. Type hierarchy can be estimated; exact family and vector structure usually remain uncertain. |
| Web page | Inspect the supplied URL's actual rendering. Where available, combine page structure/computed styles with visible components; compare representative viewports. | URL, viewport, state, region/selector. One screenshot supports only that viewport/state. |

Choose representative page types/states and record coverage. Decide whether counterexamples are local exceptions, variants or evidence against a rule. Limited material supports limited observations, not a claimed complete original specification. For multiple visual systems, record primary/supporting/excluded families using the [reproduction contract](reproducibility.en.md).

For diagrams, additionally inspect geometry, paths, grouping, emphasis and label density. Record page roles and scope through [reference-led diagram design](reference-led-diagrams.en.md). Different references support different visual behaviors.

## Decide what needs completion

- **Measured:** properties, coordinates, colors or values explicitly available in the source. Record method and source.
- **Observed:** visible relationships, such as a title preceding an image group or a warm-gray content field. Specify scope.
- **Inferred:** reusable rules derived from several samples. State applicable page types and exceptions.
- **Extended:** a design decision for a new task. Name the missing page/component/state, derive a treatment from confirmed roles, and record inherited/variable parts and verification. New values may be starting points or ranges.
- **Unresolved:** unknowns affecting identity/output, such as exact fonts, spot colors or approved logo variants. Keep a usable fallback and when confirmation is needed.

Extensions fill task-specific gaps: layouts, density, image/text proportion, narrow-screen reflow, long copy or components. Preserve source-supported hierarchy, color roles, geometry and image treatment. Prefer a few transferable rules over a new system per example.

## Structure of STYLE.md

With the [element-to-page workflow](element-compilation.en.md), derive `STYLE.md` from the catalog, adaptation rules and executable pack. Explain element roles/conditions before composition and compilation checks.

1. **Scope and quick use:** goals, main layouts, invariants and allowed variation.
2. **Visual parameters:** color roles, type hierarchy, alignment, whitespace, borders and imagery. Distinguish exact values from proposed ranges. Record image roles, subject placement, text-safe space, crop, light/color and replacement conditions.
3. **Page composition/components:** focal point, primary/secondary regions, reading order, alignment/offsets, image role, occlusion boundaries and capacity adaptations. Use [page composition rules](page-composition.en.md) to connect evidence with variation.
4. **Extensions:** target scenario, evidence, inherited rules, adjustable parameters and acceptance method.
5. **Checks/sources:** dry-run new content through selection, slot binding and hierarchy review. For multiple pages, use [visual storyboarding](visual-storyboard.en.md) with page roles/placeholders, shared rules and per-page extensions. List exact evidence, unknowns and completed check types.

Cross-reference facts/rules by ID when useful. Keep practical instructions easy to find and evidence centralized. Label locally supported rules as observations/extensions. New-copy acceptance checks hierarchy, relation to the source language and content fit.
