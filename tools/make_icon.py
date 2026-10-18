"""Sinh icon cho app (assets/app.ico + assets/app.png).

Chạy:  uv run python tools/make_icon.py
Icon được vẽ ở 1024px rồi thu nhỏ (PIL không khử răng cưa khi vẽ).
"""
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(os.path.dirname(HERE), "assets")

S = 1024                      # vẽ ở kích thước lớn cho mượt
TOP = (139, 123, 247)         # tím sáng
BOTTOM = (88, 62, 216)        # tím đậm
INK = (95, 74, 226)           # màu "ảnh" bên trong thẻ trắng

ICO_SIZES = [256, 128, 64, 48, 40, 32, 24, 20, 16]


def _rounded_mask(size, margin, radius, box=None):
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    if box is None:
        box = (margin, margin, size - margin, size - margin)
    d.rounded_rectangle(box, radius=radius, fill=255)
    return m


def _gradient(size, top, bottom):
    g = Image.new("RGB", (1, size))
    pix = g.load()
    for y in range(size):
        t = y / max(1, size - 1)
        pix[0, y] = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
    return g.resize((size, size))


def build(size=S):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # nền: ô vuông bo góc, chuyển màu tím
    bg_mask = _rounded_mask(size, int(size * 0.0625), int(size * 0.195))
    img.paste(_gradient(size, TOP, BOTTOM).convert("RGBA"), (0, 0), bg_mask)

    # thẻ ảnh trắng bo góc
    card = (int(size * 0.227), int(size * 0.266), int(size * 0.773), int(size * 0.734))
    card_mask = _rounded_mask(size, 0, int(size * 0.070), box=card)
    img.paste(Image.new("RGBA", (size, size), (255, 255, 255, 255)), (0, 0), card_mask)

    # bên trong thẻ: mặt trời + núi (cắt gọn theo thẻ)
    inner = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(inner)
    r = int(size * 0.055)
    cx, cy = int(size * 0.383), int(size * 0.415)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=INK + (255,))
    d.polygon([(int(size * 0.266), int(size * 0.688)),
               (int(size * 0.459), int(size * 0.451)),
               (int(size * 0.594), int(size * 0.625)),
               (int(size * 0.664), int(size * 0.543)),
               (int(size * 0.734), int(size * 0.688))], fill=INK + (255,))
    clipped = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    clipped.paste(inner, (0, 0), card_mask)
    img.alpha_composite(clipped)

    return img


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    big = build(S)
    png = os.path.join(OUT_DIR, "app.png")
    big.resize((256, 256), Image.LANCZOS).save(png)
    ico = os.path.join(OUT_DIR, "app.ico")
    big.save(ico, format="ICO",
             sizes=[(n, n) for n in ICO_SIZES])
    print("created:", png)
    print("created:", ico, "(%d sizes)" % len(ICO_SIZES))


if __name__ == "__main__":
    sys.exit(main())
