from PIL import Image, ImageDraw

# 生命遊戲的 Glider 圖案
GLIDER = ["..1...", "...1..", "111...", "......",
          "......", "......", "......", "......"]
C = {'1': (255, 255, 255)}  # #ffffff
VOID = (10, 10, 10)         # #0a0a0a

def render(size, inset):
    """inset = fraction of the canvas left as padding around the sprite."""
    img = Image.new("RGB", (size, size), VOID)
    d = ImageDraw.Draw(img)
    span = size * (1 - 2*inset)
    px = span / 8
    off = size * inset
    for r, row in enumerate(GLIDER):
        for c, ch in enumerate(row):
            if ch == '.':
                continue
            x0, y0 = off + c*px, off + r*px
            d.rectangle([x0, y0, x0+px, y0+px], fill=C[ch])
    return img

# 一般 icon：留一點邊
render(192, 0.16).save("icon-192.png")
render(512, 0.16).save("icon-512.png")
render(180, 0.16).save("apple-touch-icon.png")
# maskable：安全區只有中央 80%，所以圖案要縮更多
render(512, 0.26).save("icon-maskable-512.png")
print("ok")
