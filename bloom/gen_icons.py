import math

from PIL import Image, ImageDraw, ImageFilter

SAND = (242, 230, 207)   # 白沙
SAND_LO = (232, 215, 184)
DISC = (74, 30, 18)      # 心盤深栗
MID = (224, 74, 31)      # 中段橘紅
TIP = (246, 195, 59)     # 瓣端黃

PETALS = 13


def petal(d, cx, cy, ang, length, width, fill):
    """一片舌狀花瓣，末端三齒。用多邊形逼近就夠了，圖示只有 192px。"""
    ca, sa = math.cos(ang), math.sin(ang)

    def pt(x, y):
        return (cx + x * ca - y * sa, cy + x * sa + y * ca)

    pts = [
        pt(length * 0.10, 0),
        pt(length * 0.45, width * 0.95),
        pt(length * 0.80, width * 0.86),
        pt(length * 1.00, width * 0.44),
        pt(length * 0.89, width * 0.15),
        pt(length * 1.06, 0),
        pt(length * 0.89, -width * 0.15),
        pt(length * 1.00, -width * 0.44),
        pt(length * 0.80, -width * 0.86),
        pt(length * 0.45, -width * 0.95),
    ]
    d.polygon(pts, fill=fill)


def render(size, inset):
    """inset = 圖案四周留白佔畫布的比例。"""
    img = Image.new("RGB", (size, size), SAND)
    # 沙的層次：右下角壓暗一點，不然整塊白得像空白圖
    shade = Image.new("RGB", (size, size), SAND_LO)
    grad = Image.new("L", (size, size), 0)
    gd = ImageDraw.Draw(grad)
    for i in range(size):
        gd.line([(0, i), (size, i)], fill=int(150 * i / size))
    img.paste(shade, mask=grad)

    r = size * (0.5 - inset)
    cx = cy = size / 2

    # 花瓣分兩層：先鋪一圈橘紅的底，再蓋一圈短一點的黃瓣端
    d = ImageDraw.Draw(img)
    for i in range(PETALS):
        a = i / PETALS * math.tau
        petal(d, cx, cy, a, r * 0.98, r * 0.135, MID)

    tips = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    td = ImageDraw.Draw(tips)
    for i in range(PETALS):
        a = i / PETALS * math.tau
        td.polygon(
            [
                (cx + math.cos(a) * r * 0.62 - math.sin(a) * r * 0.115,
                 cy + math.sin(a) * r * 0.62 + math.cos(a) * r * 0.115),
                (cx + math.cos(a) * r * 1.04, cy + math.sin(a) * r * 1.04),
                (cx + math.cos(a) * r * 0.62 + math.sin(a) * r * 0.115,
                 cy + math.sin(a) * r * 0.62 - math.cos(a) * r * 0.115),
            ],
            fill=TIP + (255,),
        )
    img.paste(tips, mask=tips)

    # 心盤：深栗色 ＋ 一圈細小的黃色管狀花
    d = ImageDraw.Draw(img)
    dr = r * 0.30
    d.ellipse([cx - dr, cy - dr, cx + dr, cy + dr], fill=DISC)
    for i in range(13):
        a = i / 13 * math.tau + 0.2
        px, py = cx + math.cos(a) * dr * 0.66, cy + math.sin(a) * dr * 0.66
        rr = max(1, dr * 0.10)
        d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=TIP)

    return img.filter(ImageFilter.SMOOTH)


# 一般 icon：留一點邊
render(192, 0.16).save("icon-192.png")
render(512, 0.16).save("icon-512.png")
render(180, 0.16).save("apple-touch-icon.png")
# maskable：安全區只有中央 80%，所以圖案要縮更多
render(512, 0.26).save("icon-maskable-512.png")
print("ok")
