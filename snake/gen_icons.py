from PIL import Image, ImageDraw

LCD, OFF, ON = (199, 212, 122), (184, 198, 108), (47, 58, 16)
N = 7                                     # 7x7 才有正中間那一格，圖案好置中
BODY = [(1,4),(2,4),(3,4),(4,4),(5,4),(5,3),(5,2),(4,2),(3,2)]   # 尾 → 頭
HEAD_DIR = (-1, 0)
FOOD = (1, 2)


def render(size, inset):
    """inset = 四周留白佔畫布的比例。maskable 的安全區只有中央 80%，要縮更多。"""
    img = Image.new("RGB", (size, size), LCD)
    d = ImageDraw.Draw(img)
    span = size * (1 - 2 * inset)
    px = span / N
    off = size * inset
    gap = max(1.0, px * 0.07)

    def cell(c, r, col, k=1.0):
        s = (px - gap) * k
        m = (px - gap - s) / 2
        x = off + c * px + gap / 2 + m
        y = off + r * px + gap / 2 + m
        d.rectangle([x, y, x + s, y + s], fill=col)

    for r in range(N):
        for c in range(N):
            cell(c, r, OFF)
    for c, r in BODY:
        cell(c, r, ON)

    # 頭上挖一顆底色的眼睛，朝行進方向偏
    hc, hr = BODY[-1]
    s = px - gap
    e = s / 3
    x = off + hc * px + gap / 2 + (s - e) / 2 + HEAD_DIR[0] * (s - e) * 0.34
    y = off + hr * px + gap / 2 + (s - e) / 2 + HEAD_DIR[1] * (s - e) * 0.34
    d.rectangle([x, y, x + e, y + e], fill=LCD)

    cell(FOOD[0], FOOD[1], ON, 0.5)
    return img


render(192, 0.07).save("icon-192.png")
render(512, 0.07).save("icon-512.png")
render(180, 0.07).save("apple-touch-icon.png")
render(512, 0.19).save("icon-maskable-512.png")
print("icons ok")
