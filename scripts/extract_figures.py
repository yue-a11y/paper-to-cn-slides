"""
扫描 src/ 目录下所有 PDF，提取每个 PDF 的 Figure 到 figs/ 目录。

策略：
1. 页面含嵌入位图 → 直接提取原图
2. 矢量图 → 按图注位置裁剪渲染（200 dpi），支持图注在上方或下方
3. 双栏论文 → 按图注 x 坐标判断栏位
4. 提取后用 PIL 自动去白边，并防止误裁剪
5. 自动提取图注文本，并生成 figs/manifest.json 索引

用法：
    python scripts/extract_figures.py
    python scripts/extract_figures.py a.pdf b.pdf
"""

import glob
import os
import sys
import json

import fitz
from PIL import Image, ImageChops

SRC_DIR = "src"
OUT_DIR = "figs"
DPI = 200
MARGIN = 40
MIN_SIDE = 400  # 小于此边长的嵌入图当作页眉 logo 跳过

# 全局 manifest 列表，用于记录所有提取的图片信息
manifest_data = []


def trim(path):
    """自动去白边，并增加防误杀保护"""
    try:
        img = Image.open(path).convert("RGB")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bbox = ImageChops.difference(img, bg).getbbox()
        if bbox:
            cropped = img.crop(bbox)
            # 防止裁剪掉大部分内容（例如深色主题或反色图片）
            if cropped.width * cropped.height > img.width * img.height * 0.1:
                cropped.save(path)
                return True
            else:
                print(f"  [warn] 裁剪后面积过小，跳过裁剪以保护原图: {path}")
        return False
    except Exception as e:
        print(f"  [error] 裁剪失败 {path}: {e}")
        return False


def extract_caption(page, hits):
    """根据搜索到的关键字，提取附近的图注文本"""
    if not hits:
        return ""
    first_hit = hits[0]
    # 尝试从文本块中获取完整图注
    blocks = page.get_text("blocks")
    for b in blocks:
        # b: (x0, y0, x1, y1, text, block_no, block_type)
        if first_hit.y0 >= b[1] - 20 and first_hit.y0 <= b[3] + 20:
            caption = b[4].strip().replace("\n", " ")
            return caption
    # 回退方案：截取附近文本
    clip_rect = fitz.Rect(first_hit.x0, first_hit.y0, min(first_hit.x0 + 600, page.rect.width), first_hit.y0 + 40)
    caption = page.get_text("text", clip=clip_rect).strip().replace("\n", " ")
    return caption


def extract(pdf_path, out_dir=OUT_DIR):
    global manifest_data
    stem = os.path.splitext(os.path.basename(pdf_path))[0]
    doc = fitz.open(pdf_path)

    for pno in range(len(doc)):
        page = doc[pno]
        imgs = page.get_images(full=True)
        
        # 扩展图注搜索关键词，兼容不同期刊和补充材料的命名
        keywords = ["Figure", "Fig.", "Supplementary Figure", "Appendix Figure"]
        hits = []
        for kw in keywords:
            hits.extend(page.search_for(kw))
        hits = sorted(hits, key=lambda r: (r.y0, r.x0))
        
        caption_text = extract_caption(page, hits)
        extracted_bitmaps = []

        if imgs:
            for idx, img in enumerate(imgs):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                # PNG 不支持 CMYK，带 alpha 的灰度也统一转 RGB
                if pix.n - pix.alpha >= 4:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                if min(pix.width, pix.height) < MIN_SIDE:
                    print(f"[skip] p{pno + 1} img{idx + 1} "
                          f"too small ({pix.width}x{pix.height})")
                    continue
                out = f"{out_dir}/{stem}_p{pno + 1}_img{idx + 1}.png"
                pix.save(out)
                trim(out)
                print(f"[bitmap] {out}")
                extracted_bitmaps.append(out)
                manifest_data.append({
                    "source_pdf": pdf_path,
                    "page": pno + 1,
                    "filename": out,
                    "type": "bitmap",
                    "caption": caption_text
                })

        # 如果没有提取到可用的位图，且页面上有 Figure 字样，则尝试提取矢量图
        if not extracted_bitmaps and hits:
            first_hit = hits[0]
            is_top = first_hit.y0 < page.rect.height / 2
            is_left = first_hit.x0 < page.rect.width / 2
            
            # 根据图注位置判断栏位
            if is_left:
                x0 = MARGIN
                x1 = page.rect.width / 2 - 20
            else:
                x0 = page.rect.width / 2 + 20
                x1 = page.rect.width - MARGIN
                
            if is_top:
                # 图注在页面顶部，图片在下方
                clip_y0 = first_hit.y1 + 10
                clip_y1 = page.rect.height - MARGIN
            else:
                # 图注在页面底部，图片在上方
                clip_y0 = MARGIN
                clip_y1 = first_hit.y0 - 10
                
            clip = fitz.Rect(x0, clip_y0, x1, clip_y1)
            
            # 边界保护，防止裁剪区域越界
            if clip.is_empty or clip.width <= 0 or clip.height <= 0:
                clip = fitz.Rect(MARGIN, MARGIN, page.rect.width - MARGIN, page.rect.height - MARGIN)
                
            pix = page.get_pixmap(clip=clip, dpi=DPI)
            out = f"{out_dir}/{stem}_p{pno + 1}_fig.png"
            pix.save(out)
            trim(out)
            print(f"[vector] {out}")
            manifest_data.append({
                "source_pdf": pdf_path,
                "page": pno + 1,
                "filename": out,
                "type": "vector",
                "caption": caption_text
            })


def main():
    global manifest_data
    try:
        os.makedirs(OUT_DIR, exist_ok=True)
    except OSError as e:
        print(f"[error] 无法创建 {OUT_DIR}/：{e}")
        sys.exit(1)

    if len(sys.argv) > 1:
        pdfs = sys.argv[1:]
    else:
        if not os.path.isdir(SRC_DIR):
            print(f"[error] {SRC_DIR}/ 不存在，也没有指定 PDF")
            sys.exit(1)
        pdfs = sorted(glob.glob(os.path.join(SRC_DIR, "*.pdf")))

    if not pdfs:
        print(f"[error] 没有找到 PDF（扫描目录：{SRC_DIR}/）")
        sys.exit(1)

    print(f"found {len(pdfs)} PDF(s):")
    for p in pdfs:
        print(f"  - {p}")

    for p in pdfs:
        extract(p)
        
    # 输出 manifest 索引文件
    manifest_path = os.path.join(OUT_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)
    print(f"\n[manifest] 索引已保存到 {manifest_path}")

    print("done.")


if __name__ == "__main__":
    main()