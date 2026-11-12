# PPT-design-system

Extract a reusable design pack from a reference presentation, then use it to make a new deck. This is a cross-tool preview for coding agents with local file and shell access.

把参考演示提炼成可复用的设计包，再用同一套设计做新稿。首轮跨工具测试建议用自己的 PPTX 和一份短文稿。

## Try it

1. Clone or download this repository and open it in your agent's workspace.
2. Set up Python 3.11 and install the [runtime dependencies](ppt-design-system/references/workflow.md).
3. Ask the agent to read [the Skill](ppt-design-system/SKILL.md). For a tool that supports installed skills, copy the whole `ppt-design-system/` folder into its skills directory and invoke `$ppt-design-system`.

> Read `ppt-design-system/SKILL.md`. Extract a design pack from my reference PPTX. Then use the pack and my manuscript to produce a five-slide HTML deck. Report any page that needs a layout extension.

The extraction delivers `STYLE.md`, `design-system.json`, `element-catalog.json`, `style-grammar.json`, and selected assets. Reuse delivers a storyboard, match report, and, when requested, a standalone HTML deck.

The local Extract commands inventory PPTX, PDF and screenshot evidence and generate component coverage reports. The host agent reviews representative pages, selects artwork and writes design rules. The compiler checks manuscripts against reviewed recipes. [Make](ppt-design-system/references/workflow.md#制作并编辑整套演示) produces a single-slide offline player with an edit mode and a native PPTX for supported layers.

## License

[Apache 2.0](LICENSE). The Skill originated in Deck AI Studio.
