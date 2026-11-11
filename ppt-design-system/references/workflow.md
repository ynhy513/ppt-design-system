# 运行准备与 PPTX 证据采集

在仓库根目录运行以下命令，或用实际的 Skill 安装路径代替 `ppt-design-system`。使用 Python 3.11 和独立虚拟环境。

```bash
python -m pip install python-pptx Pillow jsonschema pdfplumber
python ppt-design-system/scripts/style_catalog.py reference.pptx --out element-catalog.json
```

扫描记录源稿文件指纹、对象位置、图层、样式和媒体指纹。源稿使用普通 PPTX，支持 1–120 页且文件不超过 200 MB。请结合代表页渲染和[提取指南](style-guide.md)决定保留哪些规则与素材。随后用[生产复用流程](element-compilation.md)编译新稿，并按[复现规范](reproducibility.md)渲染与检查。

浏览器检查可选，使用 Node.js、Playwright 与 Chromium。在仓库根目录安装 Playwright 并运行 `npx playwright install chromium` 后，即可用 `node ppt-design-system/scripts/audit_replay.cjs /path/to/replay.html` 检查。也可以通过 `REPLAY_PLAYWRIGHT_PACKAGE` 和 `REPLAY_CHROMIUM` 指向已有的安装。

## 从 PPTX 提取装饰素材

始终保留原始 PPTX，先用 `style_catalog.py` 扫描对象，再用 PDF 或图片预览判断哪些装饰可复用。把预览上的图标、剪贴、纸纹和笔刷对应到目录中的对象 ID。组合对象用 `parent` 找到内嵌图片的子对象。只导出本次选中的对象。工具只收到 PDF 预览时，标记原件缺失，并请用户提供 PPTX 以导出源素材。

```bash
python ppt-design-system/scripts/style_catalog.py reference.pptx --out element-catalog-reviewed.json \
  --assets-out design-pack/assets --asset-object p4-o23 --asset-object p4-o42
```

`assets-manifest.json` 记录源文件指纹、页码、对象、包内地址、裁切和素材指纹。导出保留内嵌文件原始字节，包括透明 PNG、SVG 及其可用的位图备份。用清单把获选素材的文件和使用条件登记到设计包。HTML 复用使用渲染器支持的 PNG、JPEG 或 WebP。原生绘图、整组效果和只有外链的对象可能没有独立媒体。遇到 `no-embedded-image` 时，记录对应对象并按可见结果隔离渲染或重建。
