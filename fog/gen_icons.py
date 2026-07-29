from PIL import Image, ImageDraw, ImageFilter

INK = (10, 14, 20)      # 夜窗的暗
FOG = (214, 227, 235)   # 糊掉的玻璃
GLOW = (255, 180, 107)  # 擦開之後透出來的街燈


def render(size, inset):
    """inset = fraction of the canvas left as padding around the pane."""
    p = size * inset
    pane = Image.new("L", (size, size), 0)
    ImageDraw.Draw(pane).rounded_rectangle(
        [p, p, size - p, size - p], radius=size * 0.15, fill=255
    )

    # 夜色那一層：光斑先畫好再糊，擦痕會從上面切出一段來
    night = Image.new("RGB", (size, size), INK)
    ImageDraw.Draw(night).ellipse(
        [size * 0.26, size * 0.50, size * 0.56, size * 0.80], fill=GLOW
    )
    night = night.filter(ImageFilter.GaussianBlur(size * 0.07))

    # 一道斜的擦痕。兩端故意畫到玻璃外面，被 pane 切掉就沒有難看的方頭
    wipe = Image.new("L", (size, size), 0)
    ImageDraw.Draw(wipe).line(
        [(size * 0.06, size * 0.97), (size * 0.94, size * 0.10)],
        fill=255, width=round(size * 0.20),
    )
    wipe = Image.composite(wipe, Image.new("L", (size, size), 0), pane)
    wipe = wipe.filter(ImageFilter.GaussianBlur(size * 0.012))

    img = Image.new("RGB", (size, size), INK)
    img.paste(Image.new("RGB", (size, size), FOG), mask=pane)
    img.paste(night, mask=wipe)
    return img


# 一般 icon：留一點邊
render(192, 0.16).save("icon-192.png")
render(512, 0.16).save("icon-512.png")
render(180, 0.16).save("apple-touch-icon.png")
# maskable：安全區只有中央 80%，所以圖案要縮更多
render(512, 0.26).save("icon-maskable-512.png")
print("ok")
