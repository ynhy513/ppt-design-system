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

路径式流程可以用圆点、独立标签和连续曲线表达顺序，明确起终点。需要强调反馈的循环可保留清晰的前向路径，用一条独立弧线回到对应节点。参考图有环向构图时，可考虑环式画法并核对读图方向。记录选型所据的轮廓、标签位置和线条节奏。自由曲线在 HTML 和 PPTX 中共用四点的 `curve` 图层，分别为起点、两个控制点、终点。它在 PowerPoint 中是自由形状，拖动节点后需要调整曲线端点。

## 画法选型和成片评审

1. 在源包的证据中记录节点轮廓、布置轴、路径和箭头、标签留白与各自作用域。保留原包匹配结果及每章要讲清的关系。先核对原文是否真有前后依赖或回流，再判断形态。
2. 参照[选型条件](structural-components/variants.json)做两个候选。三步流程可比较 `step-rail` 与 `milestone-path`；循环可比较 `return-arc` 与 `ring-cycle`。候选保留同样的文案和参考参数，按实际图框调整节点、标签间距及箭头。圆环尽量用接近正方形的实际区域，细箭头需要在最终尺寸读得清。按每个候选调用 `standard_motif(relation, system, styles, variant=variant_id)`，分别登记 motif 和带 `variant` 的配方。四种画法的样式职责为三个 `colors.*-marker`、`colors.edge`、`colors.text`、`type.node`、`radii.corner` 和 `strokes.connector`。
3. 对同一语义稿临时绑定两个候选，分别经 Make 渲染。看实际页面后再选。先核对关系、阅读及约定的编辑能力，再给出一条可核对的取舍，比如「箭头从还种回到借种，环式图能把三环的共同作用放在同一焦点上」。标签歧义、箭头阻塞、文字压线和编辑能力缺口都应在候选观察中出现。若两版都失败，调整并重跑。自由 Bézier 曲线可保持路径形状；要求节点移动后线跟随时，须实测该候选的吸附，否则编辑检查记为失败。
4. 将以下评审记录留在制作目录。证据 ID 对应设计包，图片地址指向本次实际渲染。命令校验记录及通过条件，成片质量由模型或审阅者判断。用输出稿跑 Make，编译报告保留选中配方和来源。未选候选和原包保留供复审。

```json
{
  "chapter-id": {
    "evidence": ["reference-geometry"],
    "candidates": {
      "step-rail": {
        "render": "rail.png",
        "checks": {"relation": true, "readability": true, "editable": true},
        "observation": "阶段等距，短标签下置，读图最快。"
      },
      "milestone-path": {
        "render": "path.png",
        "checks": {"relation": true, "readability": true, "editable": true},
        "observation": "连续曲线与参考呼应，标签间留白充足。"
      }
    },
    "selected": "milestone-path",
    "reason": "参考以曲线串联阶段，当前有足够空间承接曲线。"
  }
}
```

```sh
python ppt-design-system/scripts/review_variants.py manuscript.json production/design-system.json \
  variant-review.json > selected-manuscript.json
```
