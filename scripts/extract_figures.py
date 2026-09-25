"""
扫描 src/ 目录下所有 PDF，提取每个 PDF 的 Figure 到 figs/ 目录。

策略：
1. 页面含嵌入位图 → 直接提取原图
2. 矢量图 → 按图注位置裁剪渲染（200 dpi）
3. 双栏论文 → 按图注 x 坐标判断栏位
4. 提取后用 PIL 自动去白边

用法：
    python scripts/extract_figures.py
    python scripts/extract_figures.py a.pdf b.pdf
"""

import glob
import os
import sys

import fitz
from PIL import Image, ImageChops

SRC_DIR = "src"
OUT_DIR = "figs"
DPI = 200
MARGIN = 40
MIN_SIDE = 400  # 小于此边长的嵌入图当作页眉 logo 跳过


def trim(path):
    img = Image.open(path).convert("RGB")
    bg = Image.new("RGB", img.size, (255, 255, 255))
    bbox = ImageChops.difference(img, bg).getbbox()
    if bbox:
        img.crop(bbox).save(path)


def extract(pdf_path, out_dir=OUT_DIR):
    stem = os.path.splitext(os.path.basename(pdf_path))[0]
    doc = fitz.open(pdf_path)

    for pno in range(len(doc)):
        page = doc[pno]
        imgs = page.get_images(full=True)

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
        else:
            hits = page.search_for("Figure")
            if not hits:
                continue
            cap_y = hits[0].y0
            x0, x1 = MARGIN, page.rect.width - MARGIN
            if hits[0].x0 < page.rect.width / 2:
                x1 = page.rect.width / 2 - 20
            else:
                x0 = page.rect.width / 2 + 20
            clip = fitz.Rect(x0, MARGIN, x1, cap_y - 5)
            pix = page.get_pixmap(clip=clip, dpi=DPI)
            out = f"{out_dir}/{stem}_p{pno + 1}_fig.png"
            pix.save(out)
            trim(out)
            print(f"[vector] {out}")


def main():
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

    print("done.")


if __name__ == "__main__":
    main()
