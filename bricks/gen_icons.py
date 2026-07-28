from PIL import Image, ImageDraw

BRICK = ["XXXXXXXX", "XHHHHHHX", "XHAAAADX", "XHAAAADX",
         "XXXXXXXX", "XHAAAADX", "XDDDDDDX", "XXXXXXXX"]
C = {'X': (0,0,0), 'H': (248,248,248), 'A': (188,188,188), 'D': (124,124,124)}
SKY = (124,124,124)

def render(size, inset):
    img = Image.new("RGB", (size, size), SKY)
    d = ImageDraw.Draw(img)
    span = size * (1 - 2*inset); px = span / 8; off = size * inset
    for r, row in enumerate(BRICK):
        for c, ch in enumerate(row):
            x0, y0 = off + c*px, off + r*px
            d.rectangle([x0, y0, x0+px, y0+px], fill=C[ch])
    return img

render(192, 0.16).save("icon-192.png")
render(512, 0.16).save("icon-512.png")
render(180, 0.16).save("apple-touch-icon.png")
render(512, 0.26).save("icon-maskable-512.png")
print("icons ok")
