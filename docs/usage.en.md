# PPT-design-system usage guide

**English** | [简体中文](usage.md)

[Back to README](../README.md) · [Runtime setup](../ppt-design-system/references/workflow.en.md) · [Death Stranding-inspired story](examples/death-stranding.en.md)

## Choose an entry

| What you have | Start here | Result |
| --- | --- | --- |
| Only a style description or brand/IP name | [Select imagery and direction](#only-a-style-description-select-imagery-and-direction) | An imagery choice, rendered candidates and a selected direction |
| A reference PPTX, PDF or screenshot | [Extract](#extract-a-design-pack) | Asset inventory, component coverage and a reviewed pack ZIP |
| A `design.md` or other Markdown specification | [Read a specification](#start-with-a-markdown-specification) | An agent-reviewed pack with declarations, interpretations and unknowns |
| A pack and a new manuscript | [Reuse](#reuse-match-layouts-and-fill-slots) | Page storyboard, matches and gaps |
| A pack and confirmed copy | [Make](#make-edit-and-export) | Local editor, supported native PPTX, 16:9 PDF or portable editable HTML |

Keep the reference and manuscript in the workspace. Install the whole Skill folder and invoke `$ppt-design-system`, or ask the agent to read [SKILL.md](../ppt-design-system/SKILL.md). [Quick start](../README.md#quick-start)

## Only a style description: select imagery and direction

> Use $ppt-design-system to make this manuscript in a brand/IP-inspired direction. I have no template. First let me choose direct IP images or independent similar-style assets. Then render 2–3 distinct directions using identical copy. Wait for my selection before making the full deck. I may choose one overall direction and another only for data pages.

Choose the image approach before comparing visual directions. Each candidate normally includes a cover and a representative content page, with actual reference sources shown separately from generated previews. Differences should include typography, composition, density or image treatment, not just colors. Existing references and approved choices carry forward without repeated questions. This is an agent-guided entry, not a new automatic search or selection command. [Full rules](../ppt-design-system/references/style-selection.en.md)

For a Death Stranding-inspired request, inspect real official environmental references, then choose direct images or independent assets with similar visual qualities. Candidate previews use the same copy. A combination such as “A overall, B only for data pages” is recorded before extracting, extending and making the full deck. [Worked story](examples/death-stranding.en.md)

## Extract a design pack

Provide the reference and intended uses. Name any chapter color, layout feature or decorative asset that matters particularly.

> Use $ppt-design-system to extract this reference. My future internal reviews need a two-way comparison and staged actions with acceptance criteria. List separately reusable assets, component coverage and missing layouts, then deliver a reviewed design-pack ZIP.

Review the asset inventory and representative pages. Decide which artwork stays fixed and which imagery changes with the story. PPTX scanning reads native objects and embedded media; PDF scanning records obtainable image streams. Screenshots support visible observation and reconstruction, while independent layers and exact font identity may need other evidence. [Extraction commands](../ppt-design-system/references/workflow.en.md#automatic-asset-inventory-and-component-coverage)

### Start with a Markdown specification

> Use $ppt-design-system to read this design.md and map color roles, type proportions, components and reuse conditions. Separate source declarations from interpretation and new design extensions. Report missing geometry or assets. Freeze the baseline before filling gaps in a production copy, then deliver editable HTML and PPTX.

The agent interprets Markdown; do not pass it to `extract_review.py scan`. Supply visual references when available. Without them, check specification consistency and readability rather than claiming visual reproduction. Third-party brand analyses remain non-official. [Markdown input](../ppt-design-system/references/markdown-design.en.md)

For another language, check actual word length and wrapping. A character limit is not a cross-language fit guarantee. Put capacity and title-container adaptations in the production copy, preserve the type hierarchy and color fields, and verify the render.

## Reuse: match layouts and fill slots

Provide the pack ZIP and new copy, either page by page or as prose. Mark facts, numbers, caveats and sequence that must stay unchanged. The agent maps it into a separate semantic manuscript.

> Use this pack to make a page storyboard. For each page, state the content relationship, chosen layout and rationale. If capacity or structure does not fit, explain whether to change layout, split a page or extend a component.

Check whether the titles form a coherent story and whether comparisons, sequences and causal claims use appropriate relationships. Fill a gap in a production copy before making the deck. [Matching and extensions](../ppt-design-system/references/element-compilation.en.md#3-read-match-and-extend)

## Make: edit and export

Provide a reviewed pack, confirmed manuscript and required content images. Choose the local editor or an offline artifact.

> Open the local editor using this pack and confirmed copy. I will change text and images, then download PPTX and PDF from that page.

1. Open the supplied local link and select a title, image or component on the canvas or in the sidebar.
2. Change text or images. Drag to move components and drag the lower-right handle to resize. Use Undo for the last change.
3. In Export, download Editable PPTX or PDF. Both reflect the current state when clicked. Open PPTX to check required editability and PDF to check order and cropping.
4. Use Save HTML for an offline editable copy. Direct in-page PPTX/PDF downloads require the local editor; PDF also needs Node.js, Playwright and Chromium.

The current editor has Chinese labels: **编辑** = Edit, **导出** = Export, **可编辑 PPTX** = Editable PPTX, **另存 HTML** = Save HTML, **撤销** = Undo. This documentation language switch does not change the editor's interface language.

Standard PPTX export supports text, images, basic shapes, straight arrows, single-segment cubic Bézier curves and groups. Native tables and data-linked charts are not integrated. HTML chart text/shape editing does not automatically rescale marks. [Local commands and limits](../ppt-design-system/references/workflow.en.md#direct-export-from-the-editor)

## Walkthrough: a ten-page return pilot

| Step | Action | Check |
| --- | --- | --- |
| 1. Prepare | Provide a reference and confirmed copy in three chapters: entry, receipt/archive, action/acceptance. | Identify confirmed facts and illustrative images. |
| 2. Extract | Map chapter pages, three-column pages and white analysis pages to their roles. | Review inventory, coverage and pack. |
| 3. Review the storyboard | Open chapters with section pages, compare receipt states in three columns and show acceptance with stage components. | Review colors, relationships and missing structures. |
| 4. Edit | Change page 2's title, replace page 4's image and move page 9's component. | Updates appear and the latest change can be undone. |
| 5. Deliver | Download PPTX and PDF from the same Export menu. | Both retain the three changes; PDF has one slide per page and PPTX text remains editable. |

This bounded workflow was checked with a Wikimedia-style pack and neutral copy. Green chapter pages, a green/blue/white three-column page and white analysis pages coexisted; edits reached the ten-page PPTX and PDF. Use your own reference and manuscript to repeat the workflow.
