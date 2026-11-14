# 标准组件库 v0.1

目前覆盖八个组件家族。使用原有截图包的复用试验和对应的生成证据标记状态。颜色、字阶与图形样式随参考风格确定。新设计包按实际用途选用组件并记录覆盖缺口。

## 分层

| 层 | 这一层负责的决定 |
| --- | --- |
| Art Direction | 视觉方向、识别特征和变化范围。Artsy 用硬边色块组织信息，Wikimedia 用白底、蓝签、深蓝字和细线建立层级。 |
| L0 · Design Tokens | 色彩角色、字阶、描边、边距和对齐。现有两包有颜色与字阶，间距和网格主要由版式坐标体现。 |
| L1 · Primitives | 文字、框、线段、曲线、图片与局部强调。Artsy 的封面网格和 Wikimedia 的蓝白条已有固定图形定义，可单独引用。 |
| L2 · Components | 将基础元素组织成有用途的内容结构。下表登记语义、状态和现有实现。 |
| L3 · Layouts | 决定页面区域、位置、比例与容量。整页总览与侧栏是同一组件的两种放置方式。 |
| L4 · Slide Archetypes | 决定页面任务，例如开场、对照、证据、框架、路线图。按任务和内容关系选择组件及版式。 |
| L5 · Deck System | 决定顺序、密度、视觉强弱和跨页回扣。试验包沿用稿件页序，整套节奏由分镜规划。 |

## 组件清单

- **独立复用** · 有一份组件定义及独立内容槽，已在同一风格的两种构图中生成并通过换稿检查。
- **整页绑定** · 当前有实际生成用法，内容槽或结构仍由整页配方持有。
- **待延展** · 有用途与最小内容约定，尚待实现并验证。

| 家族 | 组件 | 最小内容约定 | 状态与现有落点 |
| --- | --- | --- | --- |
| Typography | 主标题 · Hero Title | 主标题；可按需要附副标题 | **整页绑定** · Wikimedia `blue-print-cover`，Artsy `modular-color-cover`。 |
| Typography | 章节标题 · Section Title | 章节名；可附短论点 | **整页绑定** · Wikimedia `green-manifesto`，Artsy `mosaic-three-stages`。 |
| Typography | 引言 · Quote | 原话、说话人或出处 | **待延展** · Wikimedia 来源对照页有引语示例，可补引语和出处的独立绑定。 |
| Typography | 页眉标 · Eyebrow | 章节名或页面上下文 | **整页绑定** · Wikimedia 白底信息页与 Artsy 编辑页的 `kicker` 槽。 |
| Content | 正文块 · Text Block | 一段说明；可有小标题 | **整页绑定** · Wikimedia `white-paired-evidence` 的说明槽。 |
| Content | 要点组 · Bullet Group | 同一主题下若干要点；有顺序时保留编号 | **整页绑定** · Artsy `split-numbered-outline` 支持固定三项。 |
| Content | 洞察块 · Insight Block | 一个结论及解释或依据 | **整页绑定** · Wikimedia `green-manifesto` 的论点与说明槽。 |
| Data | 指标卡 · KPI Card | 指标、数值、单位、时间或范围；变化量需带基准 | **待延展** · 需定义可核对的数值槽和缺失状态。 |
| Data | 图表 · Chart | 数据、单位、比较关系与来源 | **待延展** · Artsy 有来源图表证据，试验包将部分构图重建为定性证据块。 |
| Data | 数据表 · Data Table | 列名、记录、单位、缺失状态 | **待延展** · 需定义真实行列与可编辑数据约定。 |
| Data | 进度条 · Progress Bar | 当前值、目标或上限、单位 | **待延展** · 需验证上下限、超额和未知状态。 |
| Visual | 封面主视觉 · Hero Image | 主体、图像角色、裁切和可读区 | **整页绑定** · Wikimedia 封面使用已重建的蓝墨背景。 |
| Visual | 图片网格 · Image Grid | 多个可换图片槽、次序与主体裁切规则 | **待延展** · 已有色块网格可提供布局依据。 |
| Visual | 图标组 · Icon Group | 图标语义、对应标签、适用条件 | **待延展** · 需验证换图标后仍能表达同一职责。 |
| Relationship | 流程阶段 · Process Flow | 阶段、顺序、交接或依赖 | [标准结构](structural-components.md)提供三步直线流程。Artsy `mosaic-three-stages` 是已有整页版式。 |
| Relationship | 层级 · Hierarchy | 一个上级与各自归属明确的下级 | [标准结构](structural-components.md)提供一层上级、三项直属下级。 |
| Relationship | 循环 · Cycle | 循环中的有序节点和明确的回到起点关系 | [标准结构](structural-components.md)提供三步循环，区别于双向反馈闭环。 |
| Relationship | 双向反馈闭环 · Feedback Loop | 两方、两条相反的流、共同结果、各方约束 | **独立复用** · Wikimedia `two-way-feedback` 通过总览和侧栏换稿；Artsy 仍使用整页闭环配方。 |
| Relationship | 维度矩阵 · Matrix | 两个有意义的分类轴、象限、各项归类依据 | [标准结构](structural-components.md)提供定性双轴矩阵；Wikimedia 另有整页维度归类配方。 |
| Relationship | 三阶段行动与验收 · Action Checkpoints | 三个有序阶段，每阶段含一项行动和一个验收条件 | **独立复用** · Wikimedia `three-action-checkpoints` 通过总览和侧栏换稿；Artsy 仍使用三列整页配方。 |
| Comparison | 两项对照 · Paired Comparison | 两个同级对象、共同维度、各自证据 | **整页绑定** · Wikimedia `white-paired-evidence`，Artsy `paired-finding-bands`。 |
| Comparison | 同维度状态对照 · Paired State Comparison | 两种状态、各自的值或描述、共同维度 | [标准结构](structural-components.md)提供三维度双列对照。仅当原稿说明是前后阶段时表达推进。 |
| Navigation | 页码 · Page Number | 页码或用户批准的页序 | **整页绑定** · 白底总览和侧栏版式各自声明 `folio` 槽。 |
| Navigation | 目录与章节导航 · Agenda / Section Marker | 章节名、顺序或当前章节 | **整页绑定** · Artsy `split-numbered-outline` 提供固定三项的编号式目录结构。 |
| Emphasis | 短句强调 · Callout | 一句要突出的说明及其语境 | **整页绑定** · Wikimedia `blue-print-cover` 以蓝底短句承担辅助论点。 |
| Emphasis | 短语高亮 · Phrase Highlight | 原文中唯一的强调片段 | **整页绑定** · Wikimedia `flush-three-colors` 与 `white-ruled-framework` 的下划线槽。 |
| Emphasis | 指向性标注 · Annotation | 注释、对应对象或区域、连接关系 | **待延展** · 需验证裁切或换位后标注仍指向原对象。 |

双向反馈闭环与三阶段行动与验收的字段和项数见[组件覆盖约定](component-coverage.md#起始组件约定)。标准图形的字段和接入方法见[标准结构组件](structural-components.md)。提升复用状态前，核对第二种构图、换稿、容量边界和视觉层级。
