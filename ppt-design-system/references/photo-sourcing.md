# 高清照片搜图与复用

先按[图片职责](image-roles.md)确认当前页需要这个照片槽。照片被烘焙进截图、裁切后像素不够，或新稿里的照片需要随内容替换时，保留参考页的构图证据。给图片槽记录题材、用途、比例、主体落点、标题留字区和目标输出尺寸。优先检查用户原图、PPTX 内嵌原件和有使用许可的包内照片。已有素材能完成职责时直接复用。

## 双语搜索

每种题材各写一组中文和英文查询。先用题材、拍摄地点和景别缩小搜索，再在作品页和实际版式里筛主体位置、光线和留字区。比如雾林可搜「山谷 晨雾 松林 航拍 横图」「黄山 云海 松林」，英文搜 `misty forest valley evergreen aerial landscape` 或 `Huangshan pine forest sea of clouds`。需要表现真实地点、人物或产品时，用可追溯的实拍或官方作品。其他装饰性画面可在图库候选不足时考虑生图，并记录来源。

| 来源 | 优先找什么 | 核对方式 |
| --- | --- | --- |
| [Unsplash](https://unsplash.com/) / [Pexels](https://www.pexels.com/zh-cn/) | 通用高清摄影，分别尝试中英文检索 | 回免费作品页核对许可。Unsplash 免费许可与 Unsplash+ 分开看。Pexels 对独立分发有限制，CC0 图片以作品标注为准。[Unsplash](https://unsplash.com/license) · [Pexels 条款](https://www.pexels.com/zh-cn/terms-of-service/) |
| [影视飓风](https://www.ysjf.com/materialLibrary) | 纪实风景、航拍，用中文在官方素材库搜 | 核对素材类型、作品页和该项授权。网页搜索只能找到入口时，尝试站内检索，记录逐项授权是否可读。 |
| [视觉中国](https://www.vcg.com/) / [Veer](https://www.veer.com/) | 中国城市、产业和人物等本土场景 | 先查看具体作品、授权类型、订单或授权书。免费小样只作候选预览。分发可提取原图或电子模板要看对应许可。[视觉中国授权](https://www1.visualchina.com/help/auth-message) |
| [Openverse](https://openverse.org/) / [Wikimedia Commons](https://commons.wikimedia.org/) | 真实地点及许可明确、适合随包复用的原图 | Openverse 是搜索入口。回作品来源核对作者、实际许可和署名条件。Commons 的许可逐图生效。[复用指南](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia) |

网页搜索用 `site:` 限定到作品页所在站点，站内搜索补充召回。对已选候选从作品来源获取高清文件。记录每个候选的搜索词、作者、作品 URL、许可或授权依据、核验日期、原图尺寸和实际裁切后像素。预览图、搜索结果的「免费」标签和图库首页都只提供筛选线索。

## 在实际构图里验收并交付

1. 对每张可用的候选，用目标版式的真实图片比例、裁切位置和文案重放。对照时使用同一设置。记录裁切后实际保留的像素、主体有无被切掉、封面标题的局部对比和图片卡的阅读焦点。渲染副本如有下采样，分别记录原图、入稿文件和裁切后尺寸。
2. 分别判断 **当前成稿** 和 **独立图片随包分发**，各填「允许」「不允许」或「待核实」并给出处。成稿还需考虑实际交付形式。可编辑 PPTX 和离线 HTML 能导出或提取图片，授权限制提取时可用符合许可的成稿形式，或换图。仅允许成稿使用时，设计包留图片槽、构图、裁切和来源链接；许可待核实的素材留作候选。
3. 确认可随包分发的照片放入 `assets/`，在 `assets-manifest.json` 的可选 `stock_photos` 数组中登记。每项包含 `file`（相对 assets 的文件路径）、`sha256`、`creator`、`source_url`、`license`、`license_url`、`role`、`reuse`（比例、对齐、主体与留字区）、`distribution_basis`（允许独立分发的具体条款及需保留的署名）。使用同一照片原件的渲染副本时，许可和署名需适用于该副本，说明尺寸和处理方式。机器校验登记与文件指纹，许可判断以作品证据为准。
4. 在文稿的图片字段填 `pack:照片文件名`，Make 从已校验的包读取，同一文件可进入相同或不同比例的图片槽。版式自身定义 `fit` 和 `position`。仅当前成稿可用且许可覆盖交付形式的图片从 `--assets` 读取。用新目录直接从交付 ZIP 重跑，核对成稿和素材清单。
