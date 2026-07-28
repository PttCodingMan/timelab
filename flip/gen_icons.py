from PIL import Image, ImageDraw

VOID = (8, 9, 10)
CARD = (23, 24, 27)
SEAM = (0, 0, 0)
INK = (242, 243, 245)


def render(size, inset):
    """inset = fraction of the canvas left as padding around the card."""
    img = Image.new("RGB", (size, size), VOID)
    d = ImageDraw.Draw(img)

    cw = size * (1 - 2 * inset)
    ch = cw / 1.45
    x0 = size * inset
    y0 = (size - ch) / 2
    r = cw * 0.09

    d.rounded_rectangle([x0, y0, x0 + cw, y0 + ch], radius=r, fill=CARD)
    d.rectangle([x0, y0 + ch / 2 - cw * 0.012, x0 + cw, y0 + ch / 2 + cw * 0.012], fill=SEAM)

    bar_w, bar_h = cw * 0.46, cw * 0.09
    bx0 = x0 + (cw - bar_w) / 2
    d.rounded_rectangle(
        [bx0, y0 + ch * 0.24, bx0 + bar_w, y0 + ch * 0.24 + bar_h],
        radius=bar_h / 2, fill=INK,
    )
    return img


# 一般 icon：留一點邊
render(192, 0.16).save("icon-192.png")
render(512, 0.16).save("icon-512.png")
render(180, 0.16).save("apple-touch-icon.png")
# maskable：安全區只有中央 80%，所以牌要縮更多
render(512, 0.26).save("icon-maskable-512.png")
print("ok")
