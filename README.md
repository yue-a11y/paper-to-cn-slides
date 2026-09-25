# Paper to CN Slides

将英文科研论文自动转换为中文讲解 HTML 幻灯片，适合组会汇报。

## 功能
- 自动解析论文正文及随附的补充材料中的所有 Figure
- 兼容常见的补充材料命名（SI, Supplementary, Appendix 等）
- 按 Figure 编号自动排序
- 生成中文解说、保留英文专业术语的单文件 HTML 幻灯片

## 如何使用
1. 将这个文件夹放到你的 AI 工具（如 Claude Code / Cursor）的 skills 目录下。
2. 把论文 PDF 及补充材料（如 SI、Appendix 等）一同放到 src/ 文件夹。
3. 对 AI 说：“帮我做成讲解幻灯片”。

## 输出结构
运行后会在工作目录生成：
- `paper-brief.md`：结构化提炼
- `assets/`：压缩后的网页图
- `paper-slides.html`：最终的幻灯片