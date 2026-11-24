# Source and reuse high-resolution photos

**English** | [简体中文](photo-sourcing.md)

First confirm the photo slot is needed using [image roles](image-roles.en.md). When a photo is baked into a screenshot, lacks pixels after cropping or must change with the story, retain the reference composition evidence. Record subject, purpose, aspect, subject placement, title-safe area and target dimensions. Check user originals, PPTX embedded media and permitted pack photos before searching; reuse existing assets that fulfill the role.

## Bilingual search

Write Chinese and English query sets per subject. Narrow by subject, location and shot size, then inspect work pages and actual layouts for subject placement, light and text-safe space. Fog-forest examples include Chinese queries `山谷 晨雾 松林 航拍 横图` and `黄山 云海 松林`, plus `misty forest valley evergreen aerial landscape` and `Huangshan pine forest sea of clouds`. Specific places, people and products require traceable real photos or official works. For other decorative roles, generated images are an option when stock candidates fall short; record provenance.

| Source | Look for | Verify |
| --- | --- | --- |
| [Unsplash](https://unsplash.com/) / [Pexels](https://www.pexels.com/) | General high-resolution photography; try both query languages | Check the individual free work and license. Distinguish free Unsplash from Unsplash+. Pexels restricts standalone distribution; CC0 requires the work's actual designation. [Unsplash license](https://unsplash.com/license) · [Pexels terms](https://www.pexels.com/terms-of-service/) |
| [影视飓风 / YSJF](https://www.ysjf.com/materialLibrary) | Documentary landscapes and aerials; search the official library in Chinese | Check asset type, work page and item-specific permission. If web search only finds the entrance, try site search and record whether individual terms were readable. |
| [Visual China / VCG](https://www.vcg.com/) / [Veer](https://www.veer.com/) | Chinese cities, industries and people | Inspect the work, license type, order or license document. Free comps are candidate previews. Extractable originals/electronic templates need the corresponding rights. [VCG authorization information](https://www1.visualchina.com/help/auth-message) |
| [Openverse](https://openverse.org/) / [Wikimedia Commons](https://commons.wikimedia.org/) | Real places and clearly licensed originals suitable for pack reuse | Openverse is a search entry. Check the original work's author, actual license and attribution. Commons permissions apply per image. [Reuse guide](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia) |

Use `site:` for work-hosting domains and site search for additional recall. Obtain selected high-resolution files from the work source. Record queries, creator, work URL, license/permission basis, verification date, original size and pixels retained after cropping. Previews, “free” search labels and stock-site homepages are discovery clues, not permission evidence.

## Review in the actual layout and deliver

1. Replay each usable candidate with the target aspect, crop and actual copy, keeping settings fixed for comparisons. Record remaining pixels, clipped subjects, title contrast and card focus. If downsampling, distinguish original, placed file and cropped dimensions.
2. Assess **current deliverable use** and **standalone redistribution in a pack** separately: allowed, disallowed or unresolved, with sources. Consider actual delivery format. PPTX/offline HTML can expose images; if extraction is restricted, use a permitted finished format or another image. Finished-use-only assets leave slots/composition/crop/source links in the pack. Unverified assets remain candidates.
3. Approved redistributable photos go in `assets/` and optional manifest `stock_photos`. Each entry includes `file` relative to assets, `sha256`, `creator`, `source_url`, `license`, `license_url`, `role`, `reuse` (aspect, alignment, subject/text-safe area), and `distribution_basis` (specific standalone-distribution terms and required attribution). A render derivative must retain applicable license/credit, dimensions and treatment. Machine checks validate registration/fingerprints, not licensing judgment.
4. Set manuscript image fields to `pack:photo.jpg`. Make reads the validated pack, and the same file can fill same/different-aspect slots. Layouts define `fit` and `position`. Project-only images with permissions covering the delivery format use `--assets`. Rerun directly from the delivered ZIP into a new directory and check the result/manifest.
