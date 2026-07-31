#!/usr/bin/env python3
"""掃過全部 1440 分鐘，量「數字帶 on/off 兩群」的亮度間距。

這座鐘的配色隨顯示時間插值，花的亮度和沙的亮度會在一天裡各自升降。
兩群一旦重疊，那一分鐘的數字就從畫面上消失 —— 而且**抽樣驗不出來**：
六個關鍵時刻全部合格的版本，中間的插值段仍有 770 分鐘是壞的（訊號在
keyframe 之間變號、必然過零）；橫式全綠的版本，直式有 716 分鐘是壞的。
兩次都是這支腳本掃出來的，不是看圖看出來的。

**動過 TOD 色票、SIG_* 夾制常數、OPEN 花徑、或任何幾何之後，重跑這支。**
合格線：橫式與直式各自的最小間距 ≥ 30、gap<30 的分鐘數 = 0。

    .venv/bin/python3 bloom/scan_gap.py out.json            # 橫式
    .venv/bin/python3 bloom/scan_gap.py out.json --vp=420x900  # 直式

做法不是拍 1440 張圖（一張要 5 秒 settle，跑一整天），而是把 bloom/index.html
複製一份、把結尾的 requestAnimationFrame 開機碼換成一支 window.__probe(hhmm)：
它直接把時間寫死、把該開的花設成 bloom=1、該關的設 0、潮水歸零，再走同一條
setTOD → buildSand/buildShade/buildBg/tintAtlas → render() 的路徑，最後對
canvas 做一次 getImageData，用跟 gap_measure.py 完全一樣的規則（每一格花頭中心
半徑 0.55r 的圓盤平均亮度）算兩群的間距。

也就是說：量的是真的畫出來的像素，只是省掉截圖與動畫。

用法：
    .venv/bin/python3 scan_gap.py [輸出.json] [--src=快照.html] [--only=0808,0000]
                                  [--vp=420x900]

`--vp=` 是這一輪（直式驗收）加的：只換 playwright 的 viewport，其餘一個字沒動。
版面常數（COLS/ROWS/SLOTS/COLW/HEAD）全部是 layout() 在瀏覽器裡依 MW/MH 現算的，
`PORT = MH > MW` 也是，所以把 viewport 換成 420x900 就是在量真正的直式版面，
不需要在 Python 這邊複製任何一條版面公式。預設仍是橫式 1200x750。
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from playwright.sync_api import sync_playwright  # noqa: E402

from shoot import serve  # noqa: E402

HERE = Path(__file__).resolve().parent
PROBE_DIR = Path(tempfile.gettempdir()) / "bloom-probe"   # 產物不留在 repo 裡

BOOT = "layout();\nlast = performance.now();\nrequestAnimationFrame(frame);\n"

PATCH = r"""
layout();

// ── 量測探針（只有 scan_gap.py 用的副本才有這一段）────────────────
window.__probe = function(hhmm){
  drawn = hhmm;
  introPending = false;
  runs.length = 0; foam.length = 0; petals.length = 0;
  gustNow = null;
  applyTime(hhmm);
  for(const f of field){ f.bloom = f.want ? 1 : 0; f.mode = null; f.sub = 0; }
  for(let i = 0; i < wa.length; i++) wa[i] = 0;
  wetAny = false;
  PAL_MIN = -1;
  setTOD(todMin(hhmm));
  buildSand(); buildShade(); buildBg(); tintAtlas();
  render();

  const img = ctx.getImageData(0, 0, MW, MH).data;
  const on = [], off = [];
  for(const f of field){
    if(f.kind !== 'digit') continue;
    const rad = f.r * 0.55, cx = f.hx, cy = f.hy, r2 = rad * rad;
    let tot = 0, n = 0;
    for(let y = Math.round(cy - rad); y <= Math.round(cy + rad); y++){
      if(y < 0 || y >= MH) continue;
      for(let x = Math.round(cx - rad); x <= Math.round(cx + rad); x++){
        if(x < 0 || x >= MW) continue;
        const dx = x - cx, dy = y - cy;
        if(dx * dx + dy * dy > r2) continue;
        const i = (y * MW + x) * 4;
        tot += 0.299 * img[i] + 0.587 * img[i + 1] + 0.114 * img[i + 2];
        n++;
      }
    }
    (f.want ? on : off).push(tot / Math.max(n, 1));
  }
  window.__last = [];
  for(const f of field){
    if(f.kind !== 'digit') continue;
    const rad = f.r * 0.55, cx = f.hx, cy = f.hy, r2 = rad * rad;
    let tot = 0, n = 0;
    for(let y = Math.round(cy - rad); y <= Math.round(cy + rad); y++){
      if(y < 0 || y >= MH) continue;
      for(let x = Math.round(cx - rad); x <= Math.round(cx + rad); x++){
        if(x < 0 || x >= MW) continue;
        const dx = x - cx, dy = y - cy;
        if(dx * dx + dy * dy > r2) continue;
        const i = (y * MW + x) * 4;
        tot += 0.299 * img[i] + 0.587 * img[i + 1] + 0.114 * img[i + 2];
        n++;
      }
    }
    window.__last.push([tot / Math.max(n, 1), f.vv, f.uu, f.want ? 1 : 0]);
  }
  on.sort((a, b) => a - b); off.sort((a, b) => a - b);
  const a0 = on[0], a1 = on[on.length - 1], b0 = off[0], b1 = off[off.length - 1];
  const gap = a1 < b0 ? b0 - a1 : a0 - b1;      // gap_measure.py 同一條規則
  return { on: [a0, a1], off: [b0, b1], gap: gap, sign: a1 < b0 ? -1 : 1,
           n: [on.length, off.length], glowA: PAL.glowA, exp: PAL.exp };
};
// 版面幾何傾印：__probe 跑過之後才有意義（place() 在 render() 裡跑）
window.__cells = function(){
  return { MW, MH, COLS, ROWS, PORT, COLW, HEAD,
           cells: field.filter(f => f.kind === 'digit')
                       .map(f => [f.hx, f.hy, f.r, f.want ? 1 : 0, f.uu, f.vv]) };
};
window.__ready = 1;
"""


def build_probe(src_path: Path | None = None) -> None:
    src = (src_path or ROOT / "bloom" / "index.html").read_text(encoding="utf-8")
    if BOOT not in src:
        raise SystemExit("找不到開機碼，bloom/index.html 的結尾變了")
    out = PROBE_DIR / "bloom"
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(src.replace(BOOT, PATCH), encoding="utf-8")


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    only = None
    src = None
    vw, vh = 1200, 750
    for a in sys.argv[1:]:
        if a.startswith("--only="):
            only = a.split("=", 1)[1].split(",")
        if a.startswith("--src="):
            src = Path(a.split("=", 1)[1])
        if a.startswith("--vp="):
            vw, vh = (int(x) for x in a.split("=", 1)[1].split("x"))
    dest = Path(args[0]) if args else HERE / "scan.json"
    build_probe(src)
    rows = []
    t0 = time.time()
    with serve(PROBE_DIR, port=8937) as base, sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--force-color-profile=srgb"])
        page = browser.new_page(
            viewport={"width": vw, "height": vh},
            device_scale_factor=2,
            color_scheme="dark",
            timezone_id="Asia/Taipei",
        )
        page.goto(f"{base}/bloom/?embed=1", wait_until="load")
        page.wait_for_function("window.__ready === 1", timeout=20000)
        mins = ([int(t[:2]) * 60 + int(t[2:]) for t in only] if only
                else list(range(1440)))
        for md in mins:
            hhmm = f"{md // 60:02d}{md % 60:02d}"
            r = page.evaluate("h => window.__probe(h)", hhmm)
            r["md"] = md
            r["t"] = hhmm
            rows.append(r)
            if only or md % 120 == 0:
                print(f"  {hhmm}  gap {r['gap']:+7.2f}   ({time.time() - t0:5.1f}s)",
                      flush=True)
        browser.close()

    dest.write_text(json.dumps(rows), encoding="utf-8")
    gaps = sorted(r["gap"] for r in rows)
    worst = sorted(rows, key=lambda r: r["gap"])[:10]
    n = len(gaps)
    print(f"\n{len(rows)} 分鐘掃完 viewport {vw}x{vh}（{time.time() - t0:.0f}s）→ {dest}")
    print(f"  最小 {gaps[0]:+7.2f}   P5 {gaps[n // 20]:+7.2f}   "
          f"中位 {gaps[n // 2]:+7.2f}   P95 {gaps[n * 19 // 20]:+7.2f}   "
          f"最大 {gaps[-1]:+7.2f}")
    print("  最差 10 分鐘：")
    for r in worst:
        print(f"    {r['t']}  gap {r['gap']:+7.2f}   on {r['on'][0]:6.1f}–{r['on'][1]:6.1f}"
              f"   off {r['off'][0]:6.1f}–{r['off'][1]:6.1f}")
    # 兩群誰亮誰暗翻面的分鐘
    flips = [rows[i]["t"] for i in range(1, len(rows))
             if rows[i]["sign"] != rows[i - 1]["sign"]]
    print(f"  訊號翻面於：{flips}")


if __name__ == "__main__":
    main()
