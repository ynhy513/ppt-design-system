# 运行准备与参考证据采集

在仓库根目录运行以下命令，或用实际的 Skill 安装路径代替 `ppt-design-system`。使用 Python 3.11 和独立虚拟环境。

```bash
python -m pip install python-pptx Pillow jsonschema pdfplumber
python ppt-design-system/scripts/style_catalog.py reference.pptx --out element-catalog.json
```

扫描记录源稿文件指纹、对象位置、图层、样式和媒体指纹。源稿使用普通 PPTX，支持 1–120 页且文件不超过 200 MB。请结合代表页渲染和[提取指南](style-guide.md)决定保留哪些规则与素材。随后用[生产复用流程](element-compilation.md)编译新稿，并按[复现规范](reproducibility.md)渲染与检查。

浏览器检查可选，使用 Node.js、Playwright 与 Chromium。在仓库根目录安装 Playwright 并运行 `npx playwright install chromium` 后，即可用 `node ppt-design-system/scripts/audit_replay.cjs /path/to/replay.html` 检查。也可以通过 `REPLAY_PLAYWRIGHT_PACKAGE` 和 `REPLAY_CHROMIUM` 指向已有的安装。

## 自动生成素材清单和覆盖表

```bash
python ppt-design-system/scripts/extract_review.py scan reference.pptx --out extract-scan
python ppt-design-system/scripts/extract_review.py assess extract-scan --pack baseline.zip --out baseline-review
python ppt-design-system/scripts/extract_review.py assess extract-scan --pack completed.zip \
  --baseline baseline.zip --review decisions.json --out completed-review
```

两步都输出 `asset-inventory.md`、`component-coverage.md` 和 `component-coverage.json`。用新的输出目录保留每轮结果。扫描阶段同时生成 `element-catalog.json` 和 `assets/assets-manifest.json`，供挑选入包的原件和区域。PPTX 扫描可见幻灯片对象树中的内嵌图，保留对象实例、包内地址和裁切。PDF 按绘制实例导出图流，原件按指纹去重，另记区域、滤镜和解码或掩码依赖。截图只登记整张图的像素证据，后续可登记裁切及重建件。母版独有的对象、链接资源、PDF 矢量绘图和截图内分层需要结合原稿另行审阅。

默认探测双向闭环和三阶段行动验收。用 `--probe` 指定其他中性语义稿，首轮及补足轮使用同一份。若设计包规定全稿顺序，语义稿也须指定该顺序。扫描表的初始状态是待人工核对。评估通过正式编译器验证现有配方，并记录槽位容量与独立图形绑定。目录和 ZIP 均可输入。待改造或延展的人工判断用章节 ID、目录证据 ID 和一句说明登记。

```json
{"checkpoints":{"decision":"adapt","evidence":["p8-o52"],"note":"沿用阶段带，补行动与验收字段。"}}
```

`decision` 可选 `adapt`、`extend` 或 `pending`。人工判断不能将编译缺口改为填槽通过。把选中资产的 `role` 和 `follows` 补在设计包清单的实例记录中。角色用承载、装饰、可换内容或证据，跟随范围用页面、组件或内容槽。补足后将最新覆盖表并入 `STYLE.md`，测试稿和生成报告作为包外证据。

## 从 PPTX 提取装饰素材

始终保留原始 PPTX，先扫描对象，再用 PDF 或图片预览判断哪些装饰可复用。把预览上的图标、剪贴、纸纹和笔刷对应到目录中的对象 ID。组合对象用 `parent` 找到内嵌图片的子对象。以下命令可单独重导本次选中的对象。工具只收到 PDF 预览时，按 PDF 图流定位，PPTX 原始对象需回源。

```bash
python ppt-design-system/scripts/style_catalog.py reference.pptx --out element-catalog-reviewed.json \
  --assets-out design-pack/assets --asset-object p4-o23 --asset-object p4-o42
```

`assets-manifest.json` 记录源文件指纹、页码、对象、包内地址、裁切和素材指纹。导出保留内嵌文件原始字节，包括透明 PNG、SVG 及其可用的位图备份。用清单把获选素材的文件和使用条件登记到设计包。HTML 复用使用渲染器支持的 PNG、JPEG 或 WebP。原生绘图、整组效果和只有外链的对象可能没有独立媒体。遇到 `no-embedded-image` 时，记录对应对象并按可见结果隔离渲染或重建。

## 设计包交付校验

将源设计包整理为 `STYLE.md`、`design-system.json`、`element-catalog.json`、`style-grammar.json` 和 `assets/`。在 `assets/assets-manifest.json` 记录与设计系统一致的 `source_sha256`。纯图层或纯矢量规则的包也保留清单，可将 `objects` 写为空数组。文稿、分镜、编译报告、换稿和成品 HTML 放在独立的生产目录。

- 原件放进 `assets/`，保留导出清单中的原始 SHA-256。文件名可改，清单路径也要同步。仅有清单记录时，需要回源重新导出。
- 转格式、裁切或合成的渲染件同样放进 `assets/`。在清单的 `derivatives` 中登记 `file`、衍生件 `sha256`、源对象 ID 数组 `sources` 和 `treatment`。如果源材料只能按页定位，可用 `evidence` 数组指向设计系统的证据 ID。PPTX 衍生件引用到可独立导出的图片对象时，清单要登记其原件并一并随包。
- 固定素材使用衍生图时，`fixed_assets` 的 `file` 和 `sha256` 对应渲染件，并填 `source_sha256` 指向证据对象原图。渲染器分别核对原件与渲染件。固定素材直接使用原图时保留现有字段即可。
- 复用新稿的产品图等内容素材随生产目录交付，通过文稿媒体槽引用。

```bash
python ppt-design-system/scripts/package_design.py ./design-pack --out ./design-pack.zip
python ppt-design-system/scripts/package_design.py ./design-pack.zip
```

命令检查目录、语法、原件和衍生件的文件指纹及来源链接。通过后生成以 `design-pack/` 为唯一根目录的 ZIP。缺文件、来源无法对应或混入生产文件时返回具体错误。用原 PPTX 校验时另在重放命令传入 `--source`。

## 制作并编辑整套演示

```bash
python ppt-design-system/scripts/make_deck.py design-pack.zip confirmed-manuscript.json \
  --assets ./content-assets --out ./first-draft
python ppt-design-system/scripts/make_deck.py design-pack.zip confirmed-manuscript.json \
  --assets ./content-assets --edits ./edits.json --out ./edited-draft
```

可输入已校验的设计包目录或 ZIP。文稿沿用 Reuse 的语义结构。固定素材从包内读取，可换素材从 `--assets` 读取。传入 `--source` 可再次核对原稿和固定素材。首次匹配缺口写入 `compile-report.json`，确认补足后重新执行。

- `deck.html` 是可离线打开的演示和编辑入口。默认一页一屏，支持翻页及全屏。点击编辑，再点页面上的图层或从列表选择。拖动或用右下角控制点缩放，右侧可输入精确坐标、改槽位文字和替换图片。组件内文字可单独改，组件位置和大小按组处理。换图支持 6 MiB 以内的 PNG、JPEG 或 WebP。
- 修改可存于当前浏览器。另存 HTML 会携带修改并继续可编辑。导出修改会得到 `edits.json`，可导入同一份演示，或用上面的命令重新生成 PPTX 和静态预览。重建应使用原设计包与原确认稿。源设计包和确认稿作为编辑基线。
- `storyboard.md` 供审阅页序、任务和布局，`replay.html` 用于静态排版复核。HTML 的溢出提示检查文字槽，成稿还需看遮挡、焦点和阅读顺序。
- PPTX 支持原生文字、形状、直线箭头、图片及组件分组。复杂曲线可用 `--html-only` 交付，原生表格和数据图表尚未接入此导出路径。保真度和字体在目标 Office 验收，打开文件、局部编辑、保存并重开是单独的检查。
