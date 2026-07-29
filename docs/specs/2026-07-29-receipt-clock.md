# receipt：熱感紙收據時鐘

2026-07-29

第五座時鐘。新增 `receipt/` 一個資料夾，**不動** `galaga`、`bricks`、`flip`、`zen`、`tools/`、
根 `index.html`、`deploy.yml`（build 用 `*/clock.json` 掃描、deploy 用 `ls -d */clock.json` 生 matrix，
都不需要註冊）。

**熱感印表機每分鐘吐一張「賣時間」的帳單。** 紙一節節垂下來，過了掉落線就撕開，飄著掉出畫面外。

---

## 一、為什麼是 canvas

`flip` 刻意用 DOM，因為翻頁的擬真度來自真的 3D 透視。這座相反——熱感點陣字的顆粒、
送紙的揭露、撕下來那張一邊轉一邊飄——全是逐幀重畫的東西，canvas 直接寫 `requestAnimationFrame` 最短。

`tools/simulate.js` 的假 DOM 撐得住，但有五條硬線（違反就 crash 或 FAIL）：

| 假 DOM 的限制 | 對應寫法 |
|---|---|
| `els = { c: canvas }`（`simulate.js:47`）——**只有 id `c` 拿得到 `getContext`**，別的 id 回傳沒有 canvas 介面的 stub | `<canvas id="c">`，寫死這個 id |
| 注入的 peek 讀 `runs.length`（`simulate.js:88`）——IIFE 裡**沒有** `runs` 這個變數就 ReferenceError | 進行中的送紙動畫存進 `let runs = []`，跟 `flip`、`zen` 同名同型 |
| `script.lastIndexOf('})();')`（`simulate.js:91`）、`match(/<script>...<\/script>/)`（`:83`） | 全部邏輯放在**唯一一個**無屬性的 `<script>` 裡，結尾原樣是 `})();` |
| `measureText` 固定回 `{width:10}`、`getImageData` 回空 | 版面計算不准依賴文字量測；大字用自刻點陣 |
| `window.addEventListener` 是 noop、`devicePixelRatio` 為 1 | resize 不靠事件；版面每幀依 `canvas.clientWidth/Height` 重算 |

顏色寫成 JS 常數，不從 `getComputedStyle` 讀（假 DOM 一律回 `#888888`）。

## 二、印字＝送紙，同一件事

真的熱感印表機印字頭固定、紙往下走，圖案從上往下一行行冒出來。所以不做兩套動畫：

```
      ┌── 出紙口＋印字頭紅光 ──┐   固定不動
      └────────┬──────────────┘
               │  ← 紙往下送，內容用 clip 揭露
     ┌─────────┴─────────┐
     │  CLOCK LAB        │
     │  ▓▓▓▓ ▓▓▓▓        │  ← 大字 HH:MM
     │  TOTAL       $61  │
     - - - - - 撕線 - - -
     │  （上一分鐘那張）  │
     └───────────────────┘      ← 末端淡入背景，不留水平硬邊
        ╱─────────────╲
        │  09:05      │         ← 撕下來那張，一邊轉一邊飄出畫面
        ╲─────────────╱
```

換分鐘時把紙帶往下送一張收據的高度，**2600 ms ease-out**。整分之間紙完全不動——
真的收據機也不會空轉，「不停吐出」是就時間尺度說的，不是每一幀都在動。

追趕：分頁切回來可能一次落後很多分鐘。落後 ≥2 分鐘就直接把紙帶跳到定位、
只對最後一張跑動畫，不要排隊補印——排隊會讓時鐘永遠追不上牆上時間。

## 三、`dataset.shown` 契約

大字那條帶的**最後一排點真的畫出來**的那一幀寫入：

```js
document.documentElement.dataset.shown = 'HHMM';   // 四位，24 小時制補零
```

大字落在收據約 35% 高度處，2600 ms 的動畫裡約 1000 ms 到位，
遠低於 `simulate.js` 的 `SETTLE_MAX = 6000`。不需要動 `simulate.js`。

## 四、收據內容

一張把時間當商品賣的帳單。$1／分鐘，整點多一行 HOUR，午夜多一行 DAY。

```
      CLOCK LAB
   台北店  REG #04
   2026-07-29 (三)
- - - - - - - - - - -
      ▓▓▓▓  ▓▓▓▓
      ▓▓▓▓  ▓▓▓▓          ← 大字 09:07
- - - - - - - - - - -
 MINUTE       x1     $1
 HOUR         x1    $60   ← 只在 mm == 00 出現
 DAY          x1  $1440   ← 只在 00:00 出現
- - - - - - - - - - -
 SUBTOTAL           $61
 TAX                  -
 TOTAL              $61
- - - - - - - - - - -
   NO.20260729-0907
  █▌██▌▌█▌██▌█▌█▌██
      THANK YOU
```

大字用**手刻 5×7 點陣**（`0`–`9` 與 `:`，約 12 行資料），每個點畫成一顆小方塊，
放大後就是熱感機的顆粒感，順便完全繞開假 DOM 的 `measureText`。
小字用 `fillText` 等寬字型（模擬器裡是 noop，不影響驗證）。

## 五、隨機但可重現

序號、條碼、撕下那張的擺動幅度與旋轉，全部用 **seed = 該分鐘的 epoch 分鐘數**的小 PRNG
（mulberry32 之類，5 行）。`tools/shoot.py` 凍結時間截圖時每次長一樣——
這正是[截圖要凍結時間](../notes.md#截圖為什麼要凍結時間)那條約定要的東西。

開場**不做入場動畫**，直接畫好成品（跟 `zen` 尾巴同一招）。不然縮圖是空的，
開頁也要等一分鐘才有東西看。

## 六、地上不留東西

**這一節是繞了三圈才回到最簡的，別再往回加。**

撕下來那張自由落體、飄出畫面下緣就從陣列移除，物件數自然有界。
初速接近撕開那一刻的送紙速度（不從靜止 pop），一邊掉一邊輕微擺動與旋轉。
`GRAV` 刻意比真重力慢（單位是「每秒加速幾個畫面高」，所以螢幕多大都掉一樣快）——
紙很輕，而且要看得清楚它飄走。

原本設計是「舊的一捲捲落到地上堆著」，做了三版都被退：

| 落地畫法 | 看起來像 | 結局 |
|---|---|---|
| 實心橢圓＋同心弧＋一根紙尾 | 蒜頭、洋蔥、木頭切面 | 退（畫成紙卷的端面，是實心物體不是紙） |
| 螺旋路徑用紙寬 stroke | 蚊香 | 退（規則同心螺旋，整堆還被壓平） |
| 蛇腹摺的一疊 | 摺好的紙，過關了 | 使用者仍決定整套砍掉 |

砍掉紙堆一次刪了 230 行（`pile`／`drawRoll`／`newRoll`／`rolls`／`buried`／土丘／
30 疊上限／落地陰影）。**教訓是：這座時鐘的戲在「吐出來、撕掉、飄走」，
地上那堆從頭到尾只是背景，卻吃掉三輪工。**

紙帶末端不准留水平硬邊（切過兩次、退過兩次）。現在的收尾是往背景色線性淡入。

## 七、版面與配色

實測定案：`HEAD = H*0.09`（出紙口）、`DROP = H*0.75`（撕線）、
`RW = min(W*0.74, H*0.62)`、`RH = RW*1.10`。

`DROP` 是三個目標拉扯出來的值，改它之前先讀懂為什麼：

- 往上（如 `0.60H`）→ 下緣一大片空黑，而且橫式連條碼都看不到
- 往下（如 `0.88H`）→ 構圖飽滿，但撕下那張幾乎一出現就出畫面，落下等於看不見
- `0.75H` 是取捨點：下方留 25% 當掉落走廊，`GRAV=1.2` 讓那張在畫面內飄約 1.1 秒

| 尺寸 | 用途 | 要看得到 | 收據寬佔畫面寬 |
|---|---|---|---|
| 1200×750 | 展示頁縮圖與桌機 | 大字完整、序號與條碼、掉落走廊 | 38.7% |
| 420×900 | 手機直式 | 同上，另有撕線與下一張的頭 | 73.9% |

已知瑕疵：橫式收據高 511px、撕線在 562px，末端只有 16px 落在淡出區，
但淡出帶有 45px，所以 `THANK YOU` 那行會被淡掉。要救得動 `HEAD` 或縮淡出帶，
兩者都會把撕線推出畫面外，判斷不值得。直式不受影響。

深暖底 `#1b1815`／紙 `#f2ece0`／熱感字 `#23211f`／印字頭紅光 `#d9583c`。
`clock.json` 的 `accent` 用 `#e9e0cd`。

## 八、`?embed=1`

看到參數就隱藏 UI（全螢幕鈕之類）只留錶面，而且[不註冊 service worker](../notes.md#為什麼展示頁不註冊-service-worker)：

```js
const EMBED = new URLSearchParams(location.search).has('embed');
if (!EMBED && 'serviceWorker' in navigator) navigator.serviceWorker.register('./sw.js');
```

`tools/check.py:37` 的 regex 要求 `!EMBED &&` 和 `serviceWorker` 在同一條敘述裡，照上面寫。

## 九、檔案

```
receipt/
├─ index.html                全部邏輯
├─ clock.json                id "receipt"、accent #e9e0cd、shot.freeze 用 +08:00
├─ sw.js                     cache 名稱 receipt-v1
├─ manifest.webmanifest      id / start_url / scope 全用 "./"
├─ gen_icons.py              產下面四顆
└─ icon-192.png  icon-512.png  icon-maskable-512.png  apple-touch-icon.png
```

`sw.js`、`manifest.webmanifest`、`gen_icons.py` 照 `zen/` 的樣板改字串即可，不要重新發明。

## 十、驗收

```bash
python tools/check.py                        # 五座全過
node tools/simulate.js receipt/index.html    # 全部通過
python tools/build.py                        # dist/ 生得出來
```
