# 标准结构组件

当设计包能提供视觉语言，却没有适合新稿关系的版式时，可以用标准图形作起点。结构来自新稿，颜色、字阶、圆角和线宽来自已审阅的参考。整页布局负责标题、说明和图形位置。

| 标准图形 | 使用条件 | 组件文字槽 | 读图顺序 |
| --- | --- | --- | --- |
| `linear-flow` | 三步线性过程 | `first`、`second`、`third` | 第一 → 第二 → 第三 |
| `hierarchy-tree` | 一个上级与三个同级直属项 | `parent`、`left`、`middle`、`right` | 自上而下，三项共用连接横线 |
| `three-step-cycle` | 三步可回到起点，回流在文稿中明确 | `first`、`second`、`third` | 起点 → 右下 → 左下 → 起点 |

先严格匹配原包。缺口确认后，在生产副本导入需要的[标准图形](structural-components/)，用 `scripts/structural_components.py` 的 `standard_motif(component, system, styles)` 映射参考的颜色和字阶，然后在 `system["motifs"]` 登记返回的图层。以下名称是组件内的样式职责，映射值使用原包中存在的 token ID：

```python
styles = {
    "colors": {"strong": "enamel", "inverse": "white", "panel": "green-tint",
               "text": "ink", "edge": "enamel"},
    "type": {"node": "insight"},
    "radii": {"corner": "card"},
    "strokes": {"outline": "hair", "connector": "diagram-line"},
}
system["motifs"]["linear-flow"] = standard_motif("linear-flow", system, styles)
```

在版式中通过 `motif` 图层和 `bindings` 绑定文字，配方把具体文稿字段接到页面槽。将补入的组件记为 `extended`，证据引用用于继承视觉参数的参考页。组件中的节点、标签和连接按现有 HTML 与 PPTX 渲染路径生成。PPTX 里是原生形状、文字和直线连接件，组移动时一起移动，调整单个节点后需检查端点位置。标准循环使用三条有向线段，保持方向和回流语义。

示例中的 `diagram-line` 需要定义在生产副本中。复用前检查侧栏小图中的箭头是否清楚，必要时从原参考的细线样式派生更粗的图形线宽，保留原包并记录延展依据。

每个图形当前提供表中的固定项数。遇到多层树、分支流程、长标签或更多节点时，先报告容量或结构缺口，再据新稿改造。用不同构图和换稿检查方向、父子归属、回流、文本、视觉风格及 PPTX 对象。
