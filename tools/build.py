#!/usr/bin/env python3
"""把所有時鐘收集起來組成 dist/。

一座時鐘 = 一個資料夾，裡面有 index.html 和 clock.json。
沒有中央註冊表要維護 —— 新增時鐘只要多一個資料夾，這支程式自己會找到。
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
# 縮圖產在 dist 外面，這樣重跑 build 清掉 dist 也不會把它們一起洗掉
THUMBS = ROOT / "thumbs"

# 這些資料夾不是時鐘
SKIP = {"tools", "dist", "thumbs", ".git", ".github", "node_modules", "assets"}

REQUIRED = ("id", "name")


def discover() -> list[dict]:
    clocks: list[dict] = []
    for meta_path in sorted(ROOT.glob("*/clock.json")):
        folder = meta_path.parent
        if folder.name in SKIP or folder.name.startswith("."):
            continue

        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            sys.exit(f"clock.json 壞掉：{meta_path} — {exc}")

        missing = [k for k in REQUIRED if not meta.get(k)]
        if missing:
            sys.exit(f"{meta_path} 缺少欄位：{', '.join(missing)}")

        if meta["id"] != folder.name:
            sys.exit(
                f"{meta_path} 的 id 是 {meta['id']!r}，但資料夾叫 {folder.name!r}。"
                "兩者必須一致，網址才會對。"
            )

        if not (folder / "index.html").exists():
            sys.exit(f"{folder} 沒有 index.html")

        meta["_folder"] = folder
        clocks.append(meta)

    # 新的排前面
    clocks.sort(key=lambda c: (c.get("created") or "0000-00-00", c["id"]), reverse=True)
    return clocks


def build() -> None:
    clocks = discover()
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    shutil.copy2(ROOT / "index.html", DIST / "index.html")
    (DIST / ".nojekyll").touch()
    if THUMBS.exists():
        shutil.copytree(THUMBS, DIST / "thumbs")

    index: list[dict] = []
    for c in clocks:
        folder: Path = c.pop("_folder")
        shutil.copytree(folder, DIST / c["id"])

        thumb = f"thumbs/{c['id']}.webp"
        entry = {k: v for k, v in c.items() if k != "shot"}
        entry["thumb"] = thumb if (DIST / thumb).exists() else None
        index.append(entry)

        print(f"  + {c['id']:<16} {c['name']}")

    (DIST / "clocks.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"\n{len(index)} 座時鐘 → {DIST}")
    print("預覽：python -m http.server -d dist 8080")


if __name__ == "__main__":
    print(f"build {date.today()}\n")
    build()
