# 参考前置检查与模型交接

[English](style-preflight.en.md) | **简体中文**

用于最初只有风格描述、品牌或 IP 名称的制作请求。先读[选型规则](style-selection.md)。用户已给具体参考、或明确批准沿用时，保留原路径。这份检查记录放在生产项目中，不改变可复用设计包格式。

## 选方向之前

保存原始请求，搜索适用的视觉参考并实际查看图片或渲染区域，记录所见。搜索结果、纯文字页面、记忆中的审美、模型生成的氛围图都不能代替原始参考证据。把参考研究和最终使用原作、独立或生成素材的决定分开。

委托选型只改变谁来选，不豁免研究。只有用户明确允许跳过参考研究，才适用此例外；已有授权不重复询问。参考访问失败时，尝试适用的替代来源，再说明未解决缺口，不能自行宣布例外。获明确研究豁免后，将作品标为原创提案。

## 调用其他模型时

调用方对入口负责。不能假设 API 模型读过完整指令、有工具、或能看 URL。传入适用约束、原始简报、已审看图片或来源观察、素材方式、旧素材限制及待确认项。委托有搜索能力的模型时明确交代研究任务；模型没有搜索或视觉能力时，由调用方完成缺失步骤。除非用户实际禁止新搜图，不能把任务改写成禁止检索的生成指令。

保留实际 Prompt、声明的模型与工具能力、提供的图片或观察及原始返回。在 `handoffs` 中登记每次与视觉选型或制作相关的外部模型交接；未发生时用 `[]`。模型自述的 Prompt 或声称已看图，不能作为实际输入证据。整套编译前，对照原请求检查方向与文案。

## 记录格式

在生产项目创建 `style-selection.json`。文件路径相对此记录解析，也可用绝对路径；对实际字节计算 SHA-256。必需字段：

| 字段 | 内容 |
| --- | --- |
| `version`、`origin` | `1`、`"style-description"` |
| `request` | 原始请求文本的 `{file, sha256}` |
| `design_source_sha256` | 选定生产包的 `source.sha256`，由 Make 核对 |
| `prior_materials_allowed` | 来自用户范围的布尔值，与选型委托独立 |
| `imagery` | `direct`、`independent`、`mixed` 或 `none`；生成图属于独立制作方式，不构成研究豁免 |
| `research.status` | `reviewed`，或携带下述明确例外的 `user-waived` |
| `research.references` | 列表，每项为 `{id, kind:"source-reference", source, region, file, sha256, viewed:true, observations, prior:false}`。`source` 是 URL 或用户来源标识；`file` 是实际查看的 PNG/JPEG/WebP 区域。获准的旧参考可用 `prior:true`。生成提案不能充当原始参考。 |
| `candidates` | 列表，每项为实际渲染图片的 `{id, previews:[{file, sha256}]}`。通常比较 2–3 个同稿方向的封面与代表内容页；明确委托选型时可选择一个已审看的提案。 |
| `selection` | `{authority:"user" 或 "delegated", quote, candidate}`。引用适用的用户实际选择或委托原话，不填 Agent 自己的推荐。 |
| `handoffs` | 每项为 `{model, prompt:{file, sha256}, reference_ids:[...], reference_mode}`。已知工具能力与适用约束保留在登记的 Prompt 中。 |

使用 `reference_mode:"reviewed-observations"` 时，实际 Prompt 必须包含每份参考登记的观察及来源定位。使用 `reference_mode:"images"` 时，增加覆盖已审看参考图的 `attachments:[{file, sha256}]`。这些记录说明提供的输入；供应商实际收到什么，仍须由原始请求与响应证明。

使用 `research.status:"user-waived"` 时，增加 `research.waiver:{authority:"user", scope:"reference-research", quote:<实际明确豁免原话>}` 和 `research.output_label:"original-proposal"`。不能从“你来选”“用生成背景”“不要旧素材”制造研究豁免。

## 检查与制作

```bash
python ppt-design-system/scripts/check_style_selection.py project/style-selection.json \
  --request project/style-request.txt
python ppt-design-system/scripts/make_deck.py production-pack confirmed-manuscript.json \
  --style-request project/style-request.txt --style-selection project/style-selection.json \
  --assets project/assets --out project/deck
```

`serve_deck.py` 同样传入这两个参数，预览与导出共用前置检查。此来源的请求即使已创建新包，也必须传入两个参数。把生成图包装成设计包，不会把最初的风格描述请求变成用户提供具体参考的请求。Make 在编译与渲染前拒绝不完整或不匹配的记录，并输出 `style-selection-report.json`；记录留在生产项目，不放进可复用包。

检查器验证文件、图像解码、指纹、请求及来源绑定、已渲染的选择、声明交接的参考覆盖、声明豁免的范围。它不能证明实际审看、引文是否真实表达用户意图、交接登记是否齐全、供应商是否收到输入或视觉质量。未声明风格来源的旧命令保持兼容，脚本不能从任意文字推断隐藏的风格请求；不能宣称不带参数的调用也被强制拦截。Agent 仍对正确路由、真实证据、视觉审查和原有素材分发条件负责。
