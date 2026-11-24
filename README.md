# PPT-design-system

**English** | [简体中文](README.zh-CN.md)

Turn visual references into reusable design packs, then make editable presentations from confirmed copy. Start with a PPTX, PDF, screenshot, Markdown design specification, or simply a style direction.

This is a cross-tool preview for coding agents with local file and shell access. The agent reviews references and design choices; the included scripts scan, compile, render and export supported objects.

**[Usage guide](docs/usage.en.md)** · **[Death Stranding-inspired story](docs/examples/death-stranding.en.md)** · [Skill instructions](ppt-design-system/SKILL.md)

## How it works

**Have a reference?** Extract a pack, match your manuscript in Reuse, then produce and edit the deck in Make. Keep the source pack separate from production extensions. Missing layouts appear in the match report.

**Have only a style description or brand/IP name?** First choose direct IP imagery or independent similar-style assets where images are needed. Then compare 2–3 rendered visual directions using the same sample copy. Select a direction, or scope a secondary direction to specific pages, before making the full deck. Existing references and approved choices bypass this entry. [Selection rules](ppt-design-system/references/style-selection.en.md)

![Workflow: Extract builds a design pack; Reuse matches new copy; Make delivers editable slides.](docs/images/workflow.en.svg)

[Full-size diagram](docs/images/workflow.en.svg)

## Quick start

1. Clone or download the repository into your agent's workspace.
2. Set up Python 3.11 and the [runtime dependencies](ppt-design-system/references/workflow.en.md).
3. Ask the agent to read [SKILL.md](ppt-design-system/SKILL.md). If your tool supports installed skills, copy the entire `ppt-design-system/` folder into its skills directory and invoke `$ppt-design-system`.

With a reference:

> Use $ppt-design-system to extract a pack from this reference and make a 6–8-slide deck from my confirmed manuscript. Preserve facts and numbers. Report which pages match and which need extensions. Give me editable HTML and a local editing page where I can download PPTX and PDF.

With only a style direction:

> Use $ppt-design-system to make this manuscript in a Death Stranding-inspired direction. I have no template. First let me choose direct IP imagery or independent similar-style assets. Then render 2–3 different directions using the same cover and content-page copy. Let me choose before producing the full deck.

The [worked story](docs/examples/death-stranding.en.md) explains reference research, image decisions, layout gaps and delivery limits.

## Choose an entry

| What you have | Entry | What you receive |
| --- | --- | --- |
| A style description or brand/IP name | Select imagery and direction | Rendered candidates, source evidence and a recorded choice |
| A reference PPTX, PDF or screenshot | Extract | Asset inventory, component coverage and a reviewed design-pack ZIP |
| A `design.md` or other Markdown design specification | Extract | An agent-reviewed pack separating declarations, interpretation, extensions and unknowns |
| A pack and a new manuscript | Reuse | Storyboard, matched layouts, density/slot usage and explicit gaps |
| A reviewed pack and confirmed manuscript | Make | Editable offline HTML, supported native PPTX objects and a 16:9 PDF |

Markdown is interpreted by the agent, not passed through a generic Markdown parser. Third-party brand analyses retain their non-official status. [Markdown input](ppt-design-system/references/markdown-design.en.md)

Image roles determine whether to reuse, search, extend or redraw. For photo needs, the agent can search with Chinese and English keywords, check original dimensions and cropping, and retain source/license conditions. Only distributable assets travel with a reusable pack. [Image roles](ppt-design-system/references/image-roles.en.md) · [Photo sourcing](ppt-design-system/references/photo-sourcing.en.md)

## Run locally

After the agent maps confirmed copy into the [semantic manuscript format](ppt-design-system/references/coverage-probe.json):

```bash
python ppt-design-system/scripts/serve_deck.py design-pack.zip manuscript.json \
  --assets ./content-assets --name "Project review"
```

Open the printed local link. Edit text, replace images, move/resize components, and download the current state through Export. PDF requires Node.js, Playwright and Chromium. Omit `--assets` if no replacement images are needed. [Setup and editor](ppt-design-system/references/workflow.en.md#direct-export-from-the-editor)

For a batch build or portable editable HTML:

```bash
python ppt-design-system/scripts/make_deck.py design-pack.zip manuscript.json \
  --assets ./content-assets --out ./first-draft
```

Open `first-draft/deck.html`. The single-file HTML remains editable offline; direct in-page PPTX/PDF downloads require the local editor.

**Export scope:** native text, images, basic shapes, straight arrows, single-segment cubic Bézier curves and groups. Native tables and data-linked charts are not integrated into the standard exporter. A visually editable chart made of shapes is not a data-linked PowerPoint chart. [Production and limits](ppt-design-system/references/workflow.en.md#produce-and-edit-a-complete-deck)

## Use stories and reviewed examples

- **Death Stranding-inspired English handover deck.** Eight pages combine a landscape opening, practical handover principles, a route process, and three fictional quantitative exhibits. Official images informed the reference; the final atmospheric image was separately generated. The story explains the new selection entry and distinguishes standard export from a separate native-chart adapter. [Read the story](docs/examples/death-stranding.en.md)
- **Different design languages from public Markdown analyses.** Two fictional manuscripts produced 30 pages across Figma, Mailchimp and Spotify-inspired packs: multicolor sections, yellow/cream/brown editorial pages, and a near-black action interface. These inputs are third-party analyses, not official company specifications. [Figma analysis](https://github.com/VoltAgent/awesome-design-md/blob/main/design-md/figma/DESIGN.md) · [Mailchimp analysis](https://github.com/administrakt0r/design-systems/blob/main/designs/mailchimp.design.md) · [Spotify analysis](https://github.com/VoltAgent/awesome-design-md/blob/main/design-md/spotify/DESIGN.md)
- **Bilingual adaptation with explicit gaps.** An IBM-inspired pack first rejected missing process/comparison layouts, then added them in a production copy. Fifteen Chinese/English pages received layout, editing, color-field and native-text checks. Font substitutions, an inconsistent color-step label and native weight approximation remained documented limits. [Third-party source](https://github.com/VoltAgent/awesome-design-md/blob/main/design-md/ibm/DESIGN.md) · [Official color reference](https://www.ibm.com/design/language/color/)
- **One manuscript, two public templates.** Four rounds produced 18 corrected pages from Colorado State System Fonts and Purdue Polytechnic Gold Widescreen. A six-item checklist took two three-column pages in one pack and one page in the other. Frozen source replays stayed unchanged; a Purdue title edit survived Mac PowerPoint save/reopen. [Colorado State](https://brand.colostate.edu/templates/) · [Purdue](https://polytechnic.purdue.edu/office-marketing-communications/toolbox-guides/templates)
- **Freeze the source before adapting copy.** A Texas A&M Duotone PPTX was replayed with original text, then used for a five-page fictional sensor-loan brief with separate long-title/two-column adaptations. Original replay HTML and screenshot hashes held. [Public template](https://marcomm.tamu.edu/template/presentation-templates/)
- **Image decisions in a mixed report.** A 14-page public US National Park Service PDF received per-page image decisions. Adding the new target location changed one photo from reuse to search; unclear objects stayed unresolved. [Decision workflow](ppt-design-system/references/workflow.en.md#automatic-asset-inventory-and-component-coverage)
- **Editable relationship diagrams.** Fictional manuscripts exercised flows, cycles, hierarchies, swimlanes and Gantt structures. Mac PowerPoint checks covered editing process labels, resizing a Gantt bar and recoloring a return curve, then saving/reopening. [Structural components](ppt-design-system/references/structural-components.en.md)
- **A fog-forest report with role-based image choices.** Search for the 16:9 photo cover, reuse a crop of a CC0 Huangshan original for a 4:3 card, redraw a trend from simulated data, and extend abstract artwork with nine editable shapes. Two placements of the same packed photo rendered in HTML/PPTX. [Image roles](ppt-design-system/references/image-roles.en.md) · [Photo and license](https://commons.wikimedia.org/wiki/File:Dense_fog_over_Huangshan_%28Unsplash%29.jpg)
- **A ten-page, three-chapter pilot.** A screenshot-derived pack supported green chapter pages, a green/blue/white three-column page and white analysis pages. Text edits, image replacement and component movement reached the exported PPTX/PDF. [Follow the walkthrough](docs/usage.en.md#walkthrough-a-ten-page-return-pilot)

These are bounded historical examples, not claims that every reference or model behaves identically. Templates, private inputs, generated decks and test output are not bundled with this documentation.

## Latest update

- All 15 reference guides now have English editions and reciprocal language links. English documentation stays English through internal navigation; automated checks reject missing translations, broken anchors and accidental Chinese fallbacks.
- Added the conditional imagery-and-direction selection entry; Extract → Reuse → Make remains unchanged.
- Added separate English/Chinese README and usage pages with language links.
- Added the Death Stranding-inspired story, including copy/data status and standard-export limits.

The new instructions received format/link validation and ten static scenario walkthroughs. This does not establish independent-model selection stability. Earlier runtime regression results belong to their tested samples.

### Existing review tools

Markdown source fingerprints, explicit style extensions, source/production separation, inherited typography/backdrops and source-backed title line breaks remain part of the workflow. The screenshot color-field checker validates reviewed flat-color bounds; gradients, photos and aesthetics require visual review. The prior release passed 32 Python tests and a Chromium print regression, with color checks across 45 rendered Chinese/English pages and three rejected counterexamples. Windows/WPS and unavailable brand fonts remain outside that evidence. [Color checks](ppt-design-system/references/color-language.en.md) · [Inheritance review](ppt-design-system/references/page-composition.en.md#check-inherited-titles-and-emphasis-layers)

## Credits

- **[@ynhy513](https://github.com/ynhy513)** initiated the project, defined the design-system and component-reuse direction, supplied use cases and reviewed designs.
- **OpenAI Codex** assisted with implementation, testing and documentation.

## License

[Apache 2.0](LICENSE). The Skill originated in Deck AI Studio. External reference images and fonts retain their own rights.
