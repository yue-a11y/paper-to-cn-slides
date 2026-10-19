# Paper to CN Slides

将英文科研论文自动转换为中文讲解 HTML 幻灯片，**并附赠配套的 Word 逐字讲解文档**，适合组会汇报。

## 功能
- 自动解析论文正文及随附的补充材料中的所有 Figure
- 兼容常见的补充材料命名（SI, Supplementary, Appendix 等）
- 按 Figure 编号自动排序
- 生成中文解说、保留英文专业术语的单文件 HTML 幻灯片
- **自动生成逐页口语化的 `speaker-notes.md`，并转换为 `.docx` 讲稿**

## 如何使用
1. 将这个文件夹放到你的 AI 工具（如 Claude Code / Cursor / Pi）的 skills 目录下。
2. 把论文 PDF 及补充材料（如 SI、Appendix 等）一同放到 src/ 文件夹。
3. 对 AI 说：“帮我做成讲解幻灯片”。

## 输出结构
运行后会在工作目录生成：
- `paper-brief.md`：结构化提炼与图片对照表
- `assets/`：压缩后的网页图（webp 格式）
- `paper-slides.html`：最终的幻灯片
- **`speaker-notes.md`：逐页讲稿源文件**
- **`paper-speaker-notes.docx`：最终的 Word 讲稿**

> **分发说明**：把 `paper-slides.html`、`assets/` 文件夹和 `paper-speaker-notes.docx` 一起打包发送。直接单发 HTML 会丢图。