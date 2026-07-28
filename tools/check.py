#!/usr/bin/env python3
"""檢查每座時鐘有沒有守住約定。

這些約定違反的時候不會噴錯，只會在使用者端出現很難查的怪症狀：
cache 撞名會讓某座時鐘離線後開出另一座的畫面；manifest 用絕對路徑會在
GitHub project page 上安靜失效；embed 時註冊 sw 會讓人只是滑過展示頁
就被裝一堆 service worker。所以用機器擋，不要靠記憶。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check_clock(folder: Path) -> list[str]:
    bad: list[str] = []
    meta = json.loads((folder / "clock.json").read_text(encoding="utf-8"))
    html = (folder / "index.html").read_text(encoding="utf-8")

    if meta.get("id") != folder.name:
        bad.append(f"clock.json 的 id 是 {meta.get('id')!r}，資料夾卻叫 {folder.name!r}")

    if "dataset.shown" not in html:
        bad.append(
            "index.html 沒有寫 document.documentElement.dataset.shown，"
            "tools/simulate.js 沒辦法驗證時間有沒有真的在走"
        )

    if "embed" not in html:
        bad.append("index.html 沒有處理 ?embed=1，展示頁的預覽會連 UI 一起顯示")

    if "serviceWorker" in html and not re.search(r"!EMBED\s*&&[^;]*serviceWorker", html):
        bad.append("embed 模式下沒有跳過 service worker 註冊")

    sw = folder / "sw.js"
    if sw.exists():
        text = sw.read_text(encoding="utf-8")
        names = re.findall(r"""['"]([\w.-]+-v\d+)['"]""", text)
        if not names:
            bad.append("sw.js 找不到 <id>-v<n> 格式的 cache 名稱")
        for n in names:
            if not n.startswith(folder.name):
                bad.append(f"sw.js 的 cache 名稱 {n!r} 沒有 {folder.name!r} 前綴，會跟別座撞")

    man = folder / "manifest.webmanifest"
    if man.exists():
        m = json.loads(man.read_text(encoding="utf-8"))
        if "id" not in m:
            bad.append("manifest 缺少明確的 id")
        for key in ("start_url", "scope"):
            val = m.get(key, "")
            if not val.startswith("./"):
                bad.append(f"manifest 的 {key} 是 {val!r}，必須用 './' 開頭的相對路徑")
        for icon in m.get("icons", []):
            if not (folder / icon["src"]).exists():
                bad.append(f"manifest 指到不存在的圖示 {icon['src']}")

    return bad


def main() -> None:
    folders = [p.parent for p in sorted(ROOT.glob("*/clock.json"))]
    if not folders:
        sys.exit("找不到任何時鐘")

    failed = 0
    for folder in folders:
        problems = check_clock(folder)
        if problems:
            failed += 1
            print(f"\n[{folder.name}]")
            for p in problems:
                print(f"  ✗ {p}")
        else:
            print(f"  ✓ {folder.name}")

    if failed:
        sys.exit(f"\n{failed} 座時鐘沒過")
    print(f"\n{len(folders)} 座全部通過")


if __name__ == "__main__":
    main()
