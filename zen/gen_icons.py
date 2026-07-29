from PIL import Image, ImageDraw

SAND = (230, 224, 210)
GROOVE = (179, 168, 146)
EDGE = (242, 238, 227)
STONE = (94, 90, 82)
STONE_HI = (130, 125, 114)


def render(size, inset):
    """inset = fraction of the canvas left as padding around the rings."""
    img = Image.new("RGB", (size, size), SAND)
    d = ImageDraw.Draw(img)

    cx, cy = size / 2, size * 0.54
    r0 = size * (0.5 - inset)
    lw = max(1, round(size * 0.022))

    # 同心耙痕：亮邊在下、深溝在上，看起來才是凹的
    for i in range(4):
        rx = r0 * (1 - i * 0.21)
        ry = rx * 0.74
        d.ellipse([cx - rx, cy - ry + lw, cx + rx, cy + ry + lw],
                  outline=EDGE, width=max(1, lw // 2))
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=GROOVE, width=lw)

    # 中央的石頭
    sx = r0 * 0.30
    sy = sx * 0.76
    d.ellipse([cx - sx, cy - sy, cx + sx, cy + sy], fill=STONE)
    d.ellipse([cx - sx * 0.62, cy - sy * 0.78, cx + sx * 0.2, cy - sy * 0.1],
              fill=STONE_HI)
    return img


# 一般 icon：留一點邊
render(192, 0.13).save("icon-192.png")
render(512, 0.13).save("icon-512.png")
render(180, 0.13).save("apple-touch-icon.png")
# maskable：安全區只有中央 80%，所以圖案要縮更多
render(512, 0.24).save("icon-maskable-512.png")
print("ok")
