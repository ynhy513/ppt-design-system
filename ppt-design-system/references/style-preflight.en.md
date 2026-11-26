# Reference preflight and model handoff

**English** | [简体中文](style-preflight.md)

Use this production check for requests that started with only a style description or brand/IP name. Read [selection](style-selection.en.md) first. Supplied concrete references and explicitly approved reuse retain their existing path. The gate is a project decision record, outside the reusable pack schema.

## Before choosing a direction

Save the original request. Search for relevant visual references and actually view the images or rendered regions; record what was seen. Search results, a text-only page, a remembered aesthetic, or a model-generated mood image cannot substitute for original reference evidence. Keep reference study separate from the choice to place original, independent, or generated assets in the final deck.

Delegated selection changes who chooses; it does not waive research. A current user statement specifically allowing research to be skipped is the only research exception. Do not ask for permission already given. If reference access fails, try suitable alternatives, then explain the unresolved gap rather than silently declaring an exception. With an explicit research waiver, label the result an original proposal.

## When calling another model

The caller owns this gate. Do not assume an API model has read the skill, has tools, or can inspect URLs. Supply the applicable constraints, original brief, reviewed images or source observations, selected asset method, prior-material restrictions, and remaining uncertainties. Give a search-capable delegate the research task explicitly; if it lacks search/vision, the caller must perform the missing step. Do not replace the brief with instructions that forbid fresh search unless the user actually did so.

Keep the exact prompts, declared model/tool capabilities, supplied image files or observations, and raw outputs. Record every external model handoff relevant to visual direction or production in `handoffs`; use `[]` when none occurred. A model's self-reported prompt or assertion that it viewed a reference is not evidence of the actual input. Check direction/copy against the brief before compiling a full deck.

## Record format

Create `style-selection.json` in the production project. All file paths are relative to this record (absolute paths also work); hash actual bytes with SHA-256. Required fields:

| Field | Content |
| --- | --- |
| `version`, `origin` | `1`, `"style-description"` |
| `request` | `{file, sha256}` for the original request text |
| `design_source_sha256` | The selected production pack's `source.sha256`; checked by Make |
| `prior_materials_allowed` | Boolean from the user's scope, independent of selection delegation |
| `imagery` | `direct`, `independent`, `mixed`, or `none`; generated art is an independent method, not a research waiver |
| `research.status` | `reviewed`, or `user-waived` with the explicit exception below |
| `research.references` | List of `{id, kind:"source-reference", source, region, file, sha256, viewed:true, observations, prior:false}`. `source` is the URL or supplied source identity; `file` is the viewed PNG/JPEG/WebP region. Authorized prior references may use `prior:true`. Generated proposals cannot be source references. |
| `candidates` | List of `{id, previews:[{file, sha256}]}` for actual rendered images. Normally compare 2–3 same-copy directions, cover and representative content page; explicit delegated choice can select one reviewed proposal. |
| `selection` | `{authority:"user" or "delegated", quote, candidate}`. Quote the applicable actual user choice/delegation, not the agent's recommendation. |
| `handoffs` | Each entry: `{model, prompt:{file, sha256}, reference_ids:[...], reference_mode}`. Keep tools/capabilities and applicable constraints in the recorded prompt. |

For `reference_mode:"reviewed-observations"`, the exact prompt must include the recorded observations and source locator of every reference. For `reference_mode:"images"`, add `attachments:[{file, sha256}]` covering the reviewed reference images. These records describe supplied inputs; a separate raw request/response establishes what a provider actually received.

For `research.status:"user-waived"`, add `research.waiver:{authority:"user", scope:"reference-research", quote:<actual explicit waiver>}` and `research.output_label:"original-proposal"`. Do not manufacture a waiver from “you choose,” “use generated backgrounds,” or “do not use old assets.”

## Check and produce

```bash
python ppt-design-system/scripts/check_style_selection.py project/style-selection.json \
  --request project/style-request.txt
python ppt-design-system/scripts/make_deck.py production-pack confirmed-manuscript.json \
  --style-request project/style-request.txt --style-selection project/style-selection.json \
  --assets project/assets --out project/deck
```

Use the same two arguments with `serve_deck.py`; preview and export use the same preflight. For this origin, agents must supply both arguments even after creating a fresh pack. Creating a pack from generated artwork does not convert the original style-only request into a supplied-reference request. Make writes `style-selection-report.json` and rejects incomplete or mismatched records before compilation/rendering. The record remains in the project, not inside the reusable pack.

The checker verifies files, decodable images, fingerprints, request/source binding, a rendered selection, reference coverage in declared handoffs, and a properly scoped declared waiver. It cannot establish actual human/model viewing, whether a quotation reflects user intent, the completeness of declared handoffs, provider receipt, or visual quality. Legacy commands without declared style origin remain compatible: the script cannot infer a hidden style-only request from arbitrary prose. Do not claim that unflagged calls are mechanically blocked. Agents remain responsible for correct routing, honest evidence, visual review, and existing asset distribution conditions.
