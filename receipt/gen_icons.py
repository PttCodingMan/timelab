from PIL import Image, ImageDraw

BG = (27, 24, 21)
PAPER = (242, 236, 224)
INK = (35, 33, 31)
RED = (217, 88, 60)


def render(size, inset):
    """inset = fraction of the canvas left as padding around the receipt."""
    img = Image.new("RGB", (size, size), BG)
    d = ImageDraw.Draw(img)

    h = size * (1 - inset * 2)
    w = h * 0.66
    x0 = (size - w) / 2
    y0 = (size - h) / 2
    body = h * 0.90

    d.rectangle([x0, y0, x0 + w, y0 + body], fill=PAPER)
    # 撕開的下緣：鋸齒才看得出這是一張撕下來的收據
    n = 6
    step = w / n
    for i in range(n):
        d.polygon([(x0 + step * i, y0 + body),
                   (x0 + step * (i + 0.5), y0 + body + h * 0.075),
                   (x0 + step * (i + 1), y0 + body)], fill=PAPER)

    # 印字頭那條紅光
    d.rectangle([x0, y0, x0 + w, y0 + h * 0.055], fill=RED)

    pad = w * 0.15
    lw = max(1, round(h * 0.028))
    for t in (0.16, 0.24):
        d.rectangle([x0 + pad, y0 + h * t, x0 + w - pad, y0 + h * t + lw], fill=INK)
    # 大字那條帶
    d.rectangle([x0 + pad, y0 + h * 0.37, x0 + w - pad, y0 + h * 0.55], fill=INK)
    # 條碼
    bx = x0 + pad
    for bw in (0.07, 0.03, 0.06, 0.02, 0.08, 0.03, 0.05):
        d.rectangle([bx, y0 + h * 0.67, bx + w * bw, y0 + h * 0.80], fill=INK)
        bx += w * (bw + 0.04)
    return img


# 一般 icon：留一點邊
render(192, 0.10).save("icon-192.png")
render(512, 0.10).save("icon-512.png")
render(180, 0.10).save("apple-touch-icon.png")
# maskable：安全區只有中央 80%，所以圖案要縮更多
render(512, 0.22).save("icon-maskable-512.png")
print("ok")
