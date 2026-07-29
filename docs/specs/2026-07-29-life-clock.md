# 生命遊戲時鐘（life）

2026-07-29

新增 `life/` 一個資料夾，**不動任何既有檔**。build/CI 靠 glob 自動收錄（`tools/build.py:29`、`.github/workflows/deploy.yml:32`），沒有中央註冊表要改。

一句話：一整片跑著 Conway's Game of Life 的黑白單色顯示器，時間以「數學上永不變的靜物」形式釘在細胞海裡；每分鐘換位時，舊數字被引信噪點炸成混沌，新數字從混沌中倒著長出來。

---

## 一、為什麼這樣設計

生命遊戲是混沌的，**不可能讓隨機演化自然跑出 `12:34`**，而 `tools/simulate.js:156-163` 要求動畫 6000ms 內收斂。所以數字不能靠演化「碰運氣」得到，必須是建構出來的：

1. **數字 = still life**：5×7 點陣的每個亮點放大成 2×2 block，block 之間永遠隔 2 格空隙。孤立的 2×2 block 在 B3/S23 下是靜物，數學上永不變 → 數字永遠正確可讀，零收斂風險。
2. **成形動畫 = 錄影倒放**：把「目標數字 + 噪點」往前演化 N 代錄下來，播放時倒著放。畫面上是混沌自己聚合成數字，規則仍是真的 GoL（只是時間反著走），且 100% 保證最後一幀就是目標。

## 二、`dataset.shown` 契約（`tools/simulate.js:139` 硬檢查）

- `document.documentElement.dataset.shown` 恆為 24 小時制補零 4 位字串，例：`"0934"`。
- 每個數字位的換位動畫（run）結束、block 字定格的那一刻，才更新該位。
- 首次載入不播動畫，直接定格並寫入。

## 三、結構（單一 `<script>`，頂層必須有 `runs` 陣列）

| 部件 | 說明 |
|---|---|
| `grid` / `next` | `Uint8Array(cols*rows)` 雙 buffer，B3/S23，**環形邊界** |
| `step(src, dst, w, h, wrap)` | 一代演化。`wrap=false` 時邊界外視為死細胞（子網格用） |
| `GLYPH` | 5×7 點陣數字表，從 `galaga/index.html:130-141` 複製一份（本專案刻意各自持有，見 `bricks/index.html:118`） |
| `layout()` | 沿用 `galaga/index.html:159-179` 的算法，但每個點陣亮點佔 **4×4 cells**（2×2 block + 2 格空隙）。橫式數字區 96×28 cells、直式 44×60；`cell` 邊長因此為既有時鐘的 1/4 |
| `pinned[]` / `halo[]` | 已定格數字位的 block 格 index／block 外 **2 格** index。每代 step 後 `pinned→1`、`halo→0` |
| `runs[]` | 進行中的換位動畫，每個變動的數字位一個。空陣列 = 已收斂 |

**防撞**：背景滑翔機會吃掉數字，所以每代 step 完強制套用 pinned/halo。數字像帶著斥力場，背景貼得到旁邊但進不來。正在跑 run 的數字位暫時解除 pinned/halo。

護城河寬 2 格而不是 1 格：1 格只夠擋住入侵，擋不住「背景細胞緊貼著筆畫」，數字在細胞海裡會糊掉。

## 四、動作時序

平時 **1000ms／代**——一秒一代，畫面心跳就是秒針。換位期間**全盤一起**加速到 **120ms／代**，換完回落。全盤同步變速，規則只有一套。

每個 run 在該數字位的**封閉邊界子網格**上算（範圍 = 該位點陣區向外 padding 4 格，`wrap=false`），算完貼回主網格，不外溢到隔壁位。

| 階段 | 代數 | 累計 |
|---|---|---|
| 解除 pinned/halo；在該位的空隙帶灑 15% 隨機活細胞當引信 | 0 | 0 |
| 舊字正放：`evolve(舊字+噪點, 12)` 依序播 → block 被鄰居干擾而崩解成混沌 | 12 | 1.44s |
| 硬切到新字序列（兩端都是混沌，視覺上不明顯） | 0 | 1.44s |
| 新字倒放：`evolve(新字+噪點, 12)` 的 frames 倒著播，最後一幀 = 新字+噪點 | 12 | 2.88s |
| 清空隙（噪點被斥力場吸走）、恢復 pinned/halo、寫 `dataset.shown`、結束 run | 1 | ≈2.9s |

2.9s 遠低於 6000ms 上限。00:00 四位同時換也一樣，四個 run 平行跑。

`prefers-reduced-motion` → 背景停止演化、換位直接跳到目標 block 字（假 DOM 回 `false`，simulate 走正常路徑）。

## 五、外觀

| 項目 | 值 |
|---|---|
| 底色 | `#0a0a0a` |
| 數字 block / accent | `#ffffff`，另加 `shadowBlur` 光暈（`shadowColor` 同色） |
| 背景活細胞 | `#4a4a4a`（暗灰） |
| 拖尾 | 每幀用 `fillStyle='rgba(10,10,10,0.25)'` 疊，**不用 `clearRect`** → 天然單色顯示器鬼影 |
| 掃描線 | 一層靜態 CSS `repeating-linear-gradient` div（中性黑），JS 完全不碰 |
| HUD | 直接畫在 canvas 上，零額外 DOM。`#8a8a8a`，比細胞亮、比數字暗。頂 `> CONWAY LIFE v1.0`，底 `GEN 41203  POP 187  RULE B3/S23` |
| 背景 | 開場灑隨機 soup（約 12% 密度），之後放著跑 |

`GEN` 為實際演化代數計數器（載入時歸零），`POP` 為當前活細胞數。

## 六、專案硬約束（不遵守會直接被工具擋下）

1. 只能有**一個無屬性 `<script>`**，`})();` 必須是檔案最後一次出現（`tools/simulate.js:83,91`）。
2. 頂層必須有名為 `runs` 的陣列變數，探針直接讀 `runs.length`（`tools/simulate.js:88`）。
3. 假 DOM 只有 `getElementById`/`createElement`/`body`/`documentElement`；**無 `querySelectorAll`、無 CSS 動畫、無 `Element.animate`、無 `getBoundingClientRect`**，`window.addEventListener` 是 noop（`tools/simulate.js:30-56`）。
4. SW 註冊寫成同一行 `if(!EMBED && 'serviceWorker' in navigator && ...)`（`tools/check.py:37` 的正則不跨分號；抄 `galaga/index.html:529`）。
5. `life/sw.js` 的 `VERSION` 必須以資料夾名開頭：`'life-v1'`（`tools/check.py:43-48`）。
6. `life/manifest.webmanifest` 的 `start_url`/`scope` 必須以 `"./"` 開頭，且要有明確 `id`（`tools/check.py:53-58`）。

## 不做的事

- 多規則切換（B36/S23 之類）、滑鼠互動播種、glider gun 等固定裝置。先讓隨機 soup 跑，畫面太空再說。
- 秒數不另外顯示，由 `GEN` 的跳動體現。
- 不共用既有時鐘的任何程式碼（本專案的明文約定，`README.md:6`）。

## 驗收條件

1. `python3 tools/check.py` → 全綠，且 `life` 有被檢查到。
2. `node tools/simulate.js life` → 通過（`dataset.shown` 四位補零、收斂 < 6000ms）。
3. `python3 tools/build.py` → `dist/life/` 產出，`dist/clocks.json` 含 `id: "life"`。
4. `python3 tools/shoot.py` → `thumbs/life.webp` 產出，縮圖上肉眼可讀出 `clock.json` 的 `shot.freeze` 時刻。
5. `life/` 含：`index.html`、`clock.json`、`sw.js`、`manifest.webmanifest`、`gen_icons.py`、`icon-192.png`、`icon-512.png`、`icon-maskable-512.png`、`apple-touch-icon.png`。
6. 既有四座時鐘的 check/simulate 結果不從綠變紅。
