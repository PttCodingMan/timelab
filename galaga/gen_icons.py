from PIL import Image, ImageDraw

BEE = ["..1..1..", ".111111.", "31222213", "31111113",
       "33111133", ".311113.", "..3113..", ".3....3."]
C = {'1': (242,193,78), '2': (18,20,28), '3': (224,72,63)}
VOID = (5,6,10)

def render(size, inset):
    """inset = fraction of the canvas left as padding around the sprite."""
    img = Image.new("RGB", (size, size), VOID)
    d = ImageDraw.Draw(img)
    span = size * (1 - 2*inset)
    px = span / 8
    off = size * inset
    for r, row in enumerate(BEE):
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
# maskable：安全區只有中央 80%，所以蜜蜂要縮更多
render(512, 0.26).save("icon-maskable-512.png")
print("ok")
