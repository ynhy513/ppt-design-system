# Runtime setup and reference evidence

**English** | [简体中文](workflow.md)

Run these commands from the repository root, or replace `ppt-design-system` with the installed Skill path. Use Python 3.11 in a separate virtual environment.

```bash
python -m pip install python-pptx Pillow jsonschema pdfplumber
python ppt-design-system/scripts/style_catalog.py reference.pptx --out element-catalog.json
```

Scanning records the source fingerprint, object positions, layers, styles and media fingerprints. Ordinary PPTX inputs support 1–120 slides and a maximum of 200 MB. Review representative renders with the [extraction guide](style-guide.en.md), then compile new copy through the [reuse workflow](element-compilation.en.md) and check it against the [reproduction contract](reproducibility.en.md).

For blank PPTX placeholders, inspect `placeholder-type` tokens. They distinguish first-level type-size, family, weight, italic and alignment candidates from the matching layout and master text styles. Visible text properties remain in `type`. These candidates are not a complete PowerPoint style calculation; check actual rendering, available fonts and leading when placing text.

Optional browser checks require Node.js, Playwright and Chromium. Install Playwright in the repository root and run `npx playwright install chromium`, then `node ppt-design-system/scripts/audit_replay.cjs /path/to/replay.html`. Existing installations can be selected with `REPLAY_PLAYWRIGHT_PACKAGE` and `REPLAY_CHROMIUM`.

For references defined by flat-color fields, run `python ppt-design-system/scripts/check_color_fields.py color-review.json --out color-report.json` on actual slide screenshots and reviewed bounds. See [color roles and review format](color-language.en.md). This optional check changes neither the pack nor Make commands. Without reviewed regions, do not claim automatic color-area acceptance.

## Automatic asset inventory and component coverage

```bash
python ppt-design-system/scripts/extract_review.py scan reference.pptx --out extract-scan
python ppt-design-system/scripts/extract_review.py scan reference.pdf --image-context image-context.json --out extract-with-context
python ppt-design-system/scripts/extract_review.py assess extract-scan --pack baseline.zip --out baseline-review
python ppt-design-system/scripts/extract_review.py assess extract-scan --pack completed.zip \
  --baseline baseline.zip --review decisions.json --out completed-review
```

Both stages write `asset-inventory.md`, `component-coverage.md` and `component-coverage.json`. Use a new output directory for each run. Scanning also writes `element-catalog.json` and `assets/assets-manifest.json` for selecting original assets and regions. PPTX scanning retains embedded pictures in the visible slide object tree, occurrences, package addresses and crops. PDF extraction follows drawing occurrences, deduplicates originals by fingerprint and records regions, filters, decoding and mask dependencies. A screenshot initially supplies whole-image pixel evidence; crops and reconstructions can be recorded later. Master-only objects, linked resources, PDF vector drawings and layers within screenshots need separate source review.

Scanning also writes `image-decisions.md` and `image-decisions.json`; `assess` copies decisions from the same source. Every page is covered, with object-level captions, recommendations, reasons and uncertainties. PDF drafts use pairable “IMAGE AT TOP / IMAGE BELOW” or Chinese top/bottom captions and process clues. PPTX native charts and tables can suggest redrawing. Unpaired captions, screenshots and semantically unclear photos or illustrations remain for visual review.

`--image-context` describes **subjects the new manuscript needs**, without preselecting actions. Associate a target with an original PDF region using a 1-based physical page and top-left percentage box `[x, y, width, height]`. Add `purpose` if useful. Set `identity_required: true` when a specific artwork must be shown. Overlapping targets without a unique association still require review.

```json
{"regions":[{"page":7,"region":[0,0,50,45],"subject":"Gulf Islands National Seashore","purpose":"Show regional orientation"}]}
```

Reuse recommendations assume the subject, original, crop and permission all fit. A target/caption mismatch can flag possible aliases; it produces a [search recommendation](photo-sourcing.en.md), not a download or replacement. Artistic extensions, redrawn graphics and process nodes still need final-page review.

The default probe covers a two-way feedback loop and three-stage action checkpoints. Use `--probe` for another neutral semantic manuscript, keeping it identical for baseline and completion runs. If the pack requires a deck sequence, the probe must name it. Initial scan coverage awaits human review. Assessment uses the actual compiler to check recipes, slot capacity and independent motif bindings. Directories and ZIPs are accepted. Record adaptation/extension judgments with chapter IDs, catalog evidence IDs and a short explanation.

```json
{"checkpoints":{"decision":"adapt","evidence":["p8-o52"],"note":"Reuse the stage band and add action and acceptance fields."}}
```

`decision` accepts `adapt`, `extend` or `pending`. A manual judgment cannot turn a compilation gap into a slot-binding pass. Add selected assets' `role` and `follows` to manifest occurrences: distinguish layout surfaces, decoration, replaceable content and evidence, and whether they follow a page, component or slot. Include the latest coverage table in `STYLE.md` after completion; keep probes and generated reports outside the pack.

## Extract decorative assets from PPTX

Keep the original PPTX. Scan objects first, then use PDF/image previews to decide which decorations are reusable. Map visible icons, cutouts, paper textures and brush marks to catalog object IDs. For groups, use `parent` to locate embedded-picture children. The command below re-exports selected objects. If only a PDF preview is available, locate PDF image streams; native PPTX objects require the PPTX source.

```bash
python ppt-design-system/scripts/style_catalog.py reference.pptx --out element-catalog-reviewed.json \
  --assets-out design-pack/assets --asset-object p4-o23 --asset-object p4-o42
```

`assets-manifest.json` records source fingerprints, pages, objects, package addresses, crops and asset fingerprints. Export preserves original embedded bytes, including transparent PNG, SVG and available raster fallbacks. Register selected files and reuse conditions in the pack. HTML supports PNG, JPEG and WebP. Native drawings, whole-group effects and linked-only objects may lack independent media. For `no-embedded-image`, record the object and isolate-render or reconstruct its visible result.

## Validate a deliverable design pack

The source pack contains `STYLE.md`, `design-system.json`, `element-catalog.json`, `style-grammar.json` and `assets/`. Record a matching `source_sha256` in `assets/assets-manifest.json`. Pure-layer/vector packs still include the manifest, with `objects` allowed to be empty. Keep manuscripts, storyboards, compilation reports and finished HTML in separate production directories.

- Put originals under `assets/` and retain their exported SHA-256. Renaming a file requires updating its manifest path. A manifest without the file requires re-export from source.
- Put converted, cropped or composited render derivatives under `assets/` too. Register `file`, derivative `sha256`, source object ID array `sources` and `treatment` in `derivatives`. Page-only sources can use `evidence` IDs from the system. When a PPTX derivative cites an independently exportable picture, include that original in the manifest and package.
- When `fixed_assets` uses a derivative, its `file`/`sha256` identify that render, and `source_sha256` identifies the evidence object's original image. The renderer checks both. Direct use of an original needs only the existing fields.
- New content assets such as product photos belong with production, referenced through manuscript media slots.
- For low-resolution screenshots, follow [bilingual photo search and permission review](photo-sourcing.en.md). Approved redistributable external photos go in manifest `stock_photos` and use `pack:filename` in Make image fields. Project-only images use `--assets` under their actual delivery conditions; the pack retains slots and source links.

```bash
python ppt-design-system/scripts/package_design.py ./design-pack --out ./design-pack.zip
python ppt-design-system/scripts/package_design.py ./design-pack.zip
```

The command checks structure, syntax, fingerprints of originals/derivatives and source links. A valid ZIP has `design-pack/` as its only root. Missing files, untraceable sources or mixed-in production files produce specific errors. Supply `--source` separately to replay when checking against the original PPTX.

## Produce and edit a complete deck

For delivery from the editing page, use the [local editor](#direct-export-from-the-editor). These commands suit batch production and portable-file delivery.

```bash
python ppt-design-system/scripts/make_deck.py design-pack.zip confirmed-manuscript.json \
  --assets ./content-assets --out ./first-draft
python ppt-design-system/scripts/make_deck.py design-pack.zip confirmed-manuscript.json \
  --assets ./content-assets --edits ./edits.json --out ./edited-draft
```

Input can be a validated directory or ZIP. The manuscript uses Reuse's semantic structure. Fixed assets come from the pack; replaceable assets come from `--assets`, or registered packed photos via `pack:filename`. `--source` rechecks the source and fixed assets. Initial matching gaps go into `compile-report.json`; complete them explicitly before rerunning.

If the request began with only a style name/description, pass `--style-request original-request.txt --style-selection style-selection.json` to Make and `serve_deck.py`. This [reference preflight](style-preflight.en.md) checks research/selection evidence before production and writes `style-selection-report.json`. Delegated choice and generated backgrounds do not waive research. Concrete supplied references and explicitly approved reuse keep the existing commands.

For reference-based reuse, pass `--inheritance-review inherited-layout.json` to production and local-editor commands. See the [review checklist](page-composition.en.md#check-inherited-titles-and-emphasis-layers).

- `deck.html` is the offline presentation/editor. It starts with one slide per screen, navigation and full screen. Enable editing, then select a canvas layer or list entry. Drag/resize with the lower-right handle; enter exact geometry, slot text and replacement images in the sidebar. Component text edits independently; position/size changes apply to the group. Replacements support PNG, JPEG and WebP up to 6 MiB.
- Edits can remain in the current browser. Save HTML includes them in an editable copy. Export edits produces `edits.json`, which can be reimported into the same deck or used by the command above to rebuild PPTX/static replay. Rebuild from the original pack and confirmed manuscript; these remain the editing baseline.
- `storyboard.md` supports sequence/task/layout review; `replay.html` supports static layout checks. HTML overflow warnings check text slots; inspect occlusion, focus and reading order separately.
- PPTX supports native text, shapes, straight arrows, single-segment cubic Bézier freeforms, pictures and groups. Curves allow size/stroke adjustment in PowerPoint; moving one node leaves the line in place. Native tables/data charts are not integrated here. Check fonts and fidelity in the target Office environment. Opening, editing, saving and reopening are separate checks.

### Direct export from the editor

```bash
python ppt-design-system/scripts/serve_deck.py design-pack.zip confirmed-manuscript.json \
  --assets ./content-assets --name "Presentation"
```

Open the printed link. Export downloads the current editable PPTX or 16:9 PDF; Save HTML creates an offline editable copy. Geometry uses canvas percentages. Undo restores the last drag, resize, text/image edit, reset or import. Current UI labels are Chinese: `编辑` = Edit, `导出` = Export, `撤销` = Undo, `另存 HTML` = Save HTML.

Exports use the edit state when clicked. PPTX uses native production; Chromium PDF puts one slide on each page. Install Node.js, Playwright and Chromium as above, or set `REPLAY_PLAYWRIGHT_PACKAGE`, `REPLAY_CHROMIUM` and `--node`. The editor runs while the server is active, by default at `http://127.0.0.1:8769/`. Saved single-file HTML edits offline; direct PPTX/PDF export uses the local server.

With `--inheritance-review`, PDF export checks protected line breaks/backgrounds and text-slot overflow in print state. Deviations identify the page and layer while retaining current edits for correction. Passing slot checks still requires visual review of overlap and reading order.
