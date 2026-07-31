"""數位雨時鐘的圖示：幾根綠色字柱往下掉，最下面那一格是白亮的頭。

不畫真的字元 —— 192px 的圖示上，一個 20px 的假名只會糊成一團綠。
改用方塊當字格，保留「一柱一柱、頭亮尾暗」這件事，縮到桌面小圖也還讀得出來。

用法：python rain/gen_icons.py（輸出跟這支檔案放在一起，跟 cwd 無關）
"""

import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent

BG = (2, 6, 4)          # 關掉的映像管，不是純黑
LEAF = (43, 240, 122)   # 磷光綠本色
HEAD = (226, 255, 238)  # 頭部：綠得幾乎發白

COLS = 8                # 幾根字柱
ROWS = 12               # 一柱切幾格。要比欄數多，字柱才看得出是「一長條」不是幾個點
SEED = 20260731


def render(size, inset):
    """inset = 圖案四周留白佔畫布的比例（maskable 要留多一點）。"""
    ink = Image.new("RGB", (size, size), (0, 0, 0))
    d = ImageDraw.Draw(ink)

    pad = size * inset
    span = size - pad * 2
    cw = span / COLS
    ch = span / ROWS

    rnd = random.Random(SEED)
    for c in range(COLS):
        head = rnd.uniform(0.3, 1.0) * ROWS       # 頭掉到第幾列
        length = rnd.randint(4, ROWS)
        for k in range(length + 1):
            r = int(head) - k
            if r < 0:
                break
            # 指數衰減，尾端剩不到一成。頭那一格另外給白
            a = 2.718 ** (-2.9 * k / length)
            col = HEAD if k == 0 else tuple(int(v * a) for v in LEAF)
            x = pad + c * cw
            y = pad + r * ch
            d.rectangle(
                [x + cw * 0.14, y + ch * 0.14, x + cw * 0.86, y + ch * 0.70],
                fill=col,
            )

    # 一點點 bloom：模糊一份加回去。加法混色不會把亮處推暗，正是磷光的行為
    glow = ink.filter(ImageFilter.GaussianBlur(size * 0.022))
    glow = ImageChops.multiply(glow, Image.new("RGB", ink.size, (150, 150, 150)))
    ink = ImageChops.add(ink, glow)

    img = Image.new("RGB", (size, size), BG)
    img = ImageChops.add(img, ink)

    # 掃描線。整條壓死會吃掉三分之一的畫面，所以壓完再跟原圖 blend 回來一半
    scanned = img.copy()
    scan = ImageDraw.Draw(scanned)
    step = max(3, round(size / 42))
    for y in range(0, size, step):
        scan.line([(0, y), (size, y)], fill=(0, 0, 0))

    return Image.blend(img, scanned, 0.5)


# 一般 icon：留一點邊
render(192, 0.10).save(OUT / "icon-192.png")
render(512, 0.10).save(OUT / "icon-512.png")
render(180, 0.10).save(OUT / "apple-touch-icon.png")
# maskable：安全區只有中央 80%，圖案要縮更多
render(512, 0.22).save(OUT / "icon-maskable-512.png")
print("ok")
