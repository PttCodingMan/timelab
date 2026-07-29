#!/usr/bin/env python3
"""幫每一座時鐘拍縮圖。

重點在「凍結時間」：如果讓瀏覽器讀真實時間，每次 CI 跑出來的截圖都不一樣，
git diff 會被沒有意義的二進位變動洗版。這裡在頁面所有腳本執行之前先把
Date 換掉，讓它從 clock.json 指定的時刻開始走 —— 時間照樣流動（動畫才會動），
但起點固定，同一份程式碼永遠產生同一張圖。

用法：
    python tools/build.py && python tools/shoot.py && python tools/build.py
    （第二次 build 是為了讓 clocks.json 補上 thumb 欄位）
"""

from __future__ import annotations

import contextlib
import functools
import http.server
import json
import socketserver
import threading
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
THUMBS = ROOT / "thumbs"   # 故意放在 dist 外面

DEFAULT_SHOT = {
    "width": 1200,
    "height": 750,
    "freeze": "2026-01-01T09:06:02",
    "settle": 3000,
}

# 在頁面自己的腳本之前注入。時間會繼續走，只是原點被平移。
FREEZE = """
(() => {
  const Real = Date;
  const shift = new Real('__FREEZE__').getTime() - Real.now();
  class Frozen extends Real {
    constructor(...a) { a.length ? super(...a) : super(Real.now() + shift); }
    static now() { return Real.now() + shift; }
  }
  Frozen.parse = Real.parse;
  Frozen.UTC = Real.UTC;
  window.Date = Frozen;
})();
"""


@contextlib.contextmanager
def serve(directory: Path, port: int = 8931):
    """截圖一定要走 http://，用 file:// 會撞 fetch 的 CORS。"""
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(directory)
    )
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        try:
            yield f"http://127.0.0.1:{port}"
        finally:
            httpd.shutdown()


def load_clocks() -> list[dict]:
    out = []
    for meta_path in sorted(ROOT.glob("*/clock.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        shot = {**DEFAULT_SHOT, **meta.get("shot", {})}
        out.append({"id": meta["id"], "name": meta["name"], "shot": shot})
    return out


def main() -> None:
    clocks = load_clocks()
    THUMBS.mkdir(parents=True, exist_ok=True)

    with serve(DIST) as base, sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--force-color-profile=srgb"])
        for c in clocks:
            shot = c["shot"]
            page = browser.new_page(
                viewport={"width": shot["width"], "height": shot["height"]},
                device_scale_factor=2,
                color_scheme="dark",
                # 時鐘畫的是 getHours()，也就是瀏覽器當地時間。freeze 帶著 +08:00，
                # 不釘時區的話 CI（UTC）會拍成 01:06，本機（台北）才是 09:06
                timezone_id="Asia/Taipei",
            )
            page.add_init_script(FREEZE.replace("__FREEZE__", shot["freeze"]))
            page.goto(f"{base}/{c['id']}/?embed=1", wait_until="networkidle")
            page.wait_for_timeout(shot["settle"])  # 等進場動畫歸位

            png = THUMBS / f"{c['id']}.png"
            page.screenshot(path=str(png))
            page.close()

            # 2x 截圖縮回 1x 存 webp，檔案小很多
            with Image.open(png) as im:
                im.convert("RGB").resize(
                    (shot["width"], shot["height"]), Image.LANCZOS
                ).save(THUMBS / f"{c['id']}.webp", "WEBP", quality=82, method=6)
            png.unlink()

            kb = (THUMBS / f"{c['id']}.webp").stat().st_size / 1024
            print(f"  * {c['id']:<16} {kb:6.1f} KB  @ {shot['freeze'][11:16]}")

        browser.close()

    print(f"\n{len(clocks)} 張縮圖 → {THUMBS}")


if __name__ == "__main__":
    main()
