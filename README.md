# PPT-design-system

Extract a reusable design pack from a reference presentation, then use it to make a new deck. This is a cross-tool preview for coding agents with local file and shell access.

把参考演示提炼成可复用的设计包，再用同一套设计做新稿。可以从 PPTX、PDF 或截图开始，交付可编辑 HTML、原生 PPTX 和 16:9 PDF。第一次使用，建议准备一份参考和一份短文稿。

**[打开操作指南](docs/usage.md)** · 按模式找入口，或跟着示例从参考稿做到可编辑 PPTX 和 PDF。

## Quick start · 快速开始

1. Clone or download this repository and open it in your agent's workspace.
2. Set up Python 3.11 and install the [runtime dependencies](ppt-design-system/references/workflow.md).
3. Ask the agent to read [the Skill](ppt-design-system/SKILL.md). For a tool that supports installed skills, copy the whole `ppt-design-system/` folder into its skills directory and invoke `$ppt-design-system`.

> Read `ppt-design-system/SKILL.md`. Extract a design pack from my reference PPTX. Then use the pack and my manuscript to produce a five-slide HTML deck. Report any page that needs a layout extension.

也可以直接把参考和文稿交给 Codex，用下面这段话开始。

> 用 `$ppt-design-system` 从参考稿提取设计包，再把已确认文稿做成一份 6–8 页的演示。保留原文中的事实和数字，告诉我哪些页面可直接套版、哪些需要延展。交付一个可以改字、换图、拖动组件的编辑入口，我要从里面下载 PPTX 和 PDF。

## Usage · 使用方式

| 你想做什么 | 准备什么 | 会得到什么 |
| --- | --- | --- |
| **Extract · 提取风格** | 参考 PPTX、PDF 或截图，以及未来常做的演示类型 | 素材清单、组件覆盖表和经审阅的设计包 ZIP。设计包记录颜色、字阶、版式、内容槽、选中的素材及来源。 |
| **Reuse · 选版和填槽** | 已有设计包和新文稿 | 逐页分镜、版式匹配结果和具体缺口。可先确认分镜，再生成成稿。 |
| **Make · 制作与交付** | 已有设计包、确认后的文稿，以及需要替换进去的图片 | 可编辑 HTML 和支持原生对象的 PPTX。打开本机编辑入口后，可直接下载当前稿的 PPTX 或 PDF。 |

首次提取时，扫描会先登记可获取的素材和来源证据。Agent 结合页面预览确认素材角色、版式和组件覆盖，再整理成可复用的设计包。后续换稿可沿用同一个设计包。 [提取与打包说明](ppt-design-system/references/workflow.md#自动生成素材清单和覆盖表)

照片型参考的原图不够清晰时，Agent 可以按图片槽的题材、留字区和构图，用中英文关键词从国内外来源找图，核对裁切后的尺寸和许可。允许分发的照片可以随设计包调用。 [搜图与素材复用](ppt-design-system/references/photo-sourcing.md)

### Run locally · 本机制作

有了设计包和确认后的语义文稿，就可以启动编辑页。普通文稿可先交给 Agent，字段结构见[语义稿示例](ppt-design-system/references/coverage-probe.json)。

```bash
python ppt-design-system/scripts/serve_deck.py design-pack.zip manuscript.json \
  --assets ./content-assets --name 项目汇报
```

打开命令给出的本机链接。点击画布上的图层即可改字、换图或移动组件，右上角「导出」提供「可编辑 PPTX」「PDF」和「另存 HTML」。下载取点击时的编辑状态。PDF 需要本机 Node.js、Playwright 和 Chromium。没有替换图片时可省略 `--assets`。 [安装与启动说明](ppt-design-system/references/workflow.md#在编辑页直接导出)

如果只需批量制稿或交付一个可离线编辑的文件，运行以下命令，然后打开输出目录里的 `deck.html`。

```bash
python ppt-design-system/scripts/make_deck.py design-pack.zip manuscript.json \
  --assets ./content-assets --out ./first-draft
```

PPTX 当前支持可编辑文字、图片、基础形状、直线箭头和组件分组。原生表格和数据图表尚未接入。另存的单文件 HTML 可离线继续编辑，页面内直接下载 PPTX 和 PDF 需要启动本机编辑入口。 [输出范围与复核](ppt-design-system/references/workflow.md#制作并编辑整套演示)

## Use cases · 使用案例

- **把品牌参考变成可反复使用的设计包。** 用一份既有汇报提取标题、色彩、对照页和装饰素材。下一次周会换入新文稿，先查看哪些页面可直接套版，再补需要的新结构。
- **把截图参考做成分章节的演示。** 用截图重建可见版式，把章节开场、同级三栏和正文对照分别对应到文稿里的任务。一份中性的十页归还试点样稿验证了绿色章节页、绿蓝白三栏和白底分析页可以在同一套设计里共存。
- **按画面职责制作雾林报告。** 先判断这一页需要摄影氛围、章节衔接、数据证据，还是抽象构图，再决定素材怎么来。[图片职责判断](ppt-design-system/references/image-roles.md) · [中英文多站搜图与授权核对](ppt-design-system/references/photo-sourcing.md)
  - **16:9 雾林封面｜搜图。** 远近层次和林景暗部承担开场。中英文跨站搜实拍后，用原版式试排，选了能让左侧白字读得更清楚的照片。
  - **4:3 图片卡｜复用。** 照片负责延续雾林氛围。包内 CC0 黄山原图裁切后仍保留了雾谷和前后层次，直接用 `pack:照片文件名` 调用。也用同一张原图从 ZIP 跑通了两种版式的 HTML 和 PPTX。[黄山照片与许可](https://commons.wikimedia.org/wiki/File:Dense_fog_over_Huangshan_%28Unsplash%29.jpg)
  - **数据趋势页｜重绘。** 白色图区和右侧说明沿用参考结构，按六个月的模拟数据重新绘制折线。导出的 PPTX 可单独替换图表图片。
  - **艺术样张｜延展。** 用独立的 Artsy 风格样张测试抽象配图。把错落色块移到右半幅，左侧腾出标题区，PPTX 保留九个可编辑形状。
- **改完稿后交给同事。** 在浏览器里改标题、换图、调整组件，再下载当前稿的可编辑 PPTX 供同事接手，或导出 PDF 供审阅。

## Credits · 项目贡献

- **[@ynhy513](https://github.com/ynhy513)** 发起项目，提出设计体系与组件复用方向，确定使用场景并评审样稿。
- **OpenAI Codex** 协助实现、测试和编写文档。

## License

[Apache 2.0](LICENSE). The Skill originated in Deck AI Studio.
