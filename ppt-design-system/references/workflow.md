# 运行准备与 PPTX 证据采集

在仓库根目录运行以下命令，或用实际的 Skill 安装路径代替 `ppt-design-system`。使用 Python 3.11 和独立虚拟环境。

```bash
python -m pip install python-pptx Pillow jsonschema pdfplumber
python ppt-design-system/scripts/style_catalog.py reference.pptx --out element-catalog.json
```

扫描记录源稿文件指纹、对象位置、图层、样式和媒体指纹。源稿使用普通 PPTX，支持 1–120 页且文件不超过 200 MB。请结合代表页渲染和[提取指南](style-guide.md)决定保留哪些规则与素材。随后用[生产复用流程](element-compilation.md)编译新稿，并按[复现规范](reproducibility.md)渲染与检查。

浏览器检查可选，使用 Node.js、Playwright 与 Chromium。在仓库根目录安装 Playwright 并运行 `npx playwright install chromium` 后，即可用 `node ppt-design-system/scripts/audit_replay.cjs /path/to/replay.html` 检查。也可以通过 `REPLAY_PLAYWRIGHT_PACKAGE` 和 `REPLAY_CHROMIUM` 指向已有的安装。
