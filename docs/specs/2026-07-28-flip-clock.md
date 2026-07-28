# flip：黑白翻頁時鐘

2026-07-28

第三座時鐘。新增 `flip/` 一個資料夾，**不動** `galaga`、`bricks`、`tools/`、根 `index.html`、`deploy.yml`
（build 用 `*/clock.json` 掃描、deploy 用 `ls -d */clock.json` 生 matrix，都不需要註冊）。

**時 : 分兩張大牌，黑牌白字。** 機場看板調性，24 小時制、補零。

---

## 一、為什麼是 DOM/CSS 而不是 canvas

前兩座都是 canvas，這座刻意不是。翻頁的擬真度來自**真的 3D 透視**：
`perspective` + `rotateX` 會自然產生葉片翻下來時的透視收縮、加上 `box-shadow` 的接觸陰影。
canvas 要手刻投影矩陣才有同樣效果，程式碼多三倍、字還會糊。

`tools/simulate.js` 的假 DOM 撐得住這個選擇，但有三條硬線（違反就 crash 或 FAIL）：

| 假 DOM 的限制（`tools/simulate.js:30-56`） | 對應寫法 |
|---|---|
| `document` **只有** `getElementById` / `createElement` / `body` / `documentElement` | 一律 `document.getElementById()`，**不准**用 `document.querySelector(All)` |
| 元素的 `querySelector()` 回傳一個 stub，`querySelectorAll()` 回傳 `[]` | 取子元素用 `el.querySelector('span')`（兩邊都安全），不准用 `firstElementChild` |
| CSS 動畫、`animationend`、`Element.animate`、`getBoundingClientRect` 全部不存在 | 翻頁**必須**由 `requestAnimationFrame` 驅動、JS 直接寫 `style.transform` |

`window.addEventListener` 也是 noop，所以 resize 監聽在模擬裡不會觸發 →
版面靠 CSS 做 RWD，JS 不參與版面計算。

## 二、`dataset.shown` 契約

`simulate.js:150-152` 斷言 `dataset.shown === p2(getUTCHours()) + p2(getUTCMinutes())`。

- **24 小時制、補零**，`02:09` 顯示 `02` `09`、`dataset.shown === '0209'`。12 小時制會直接 FAIL。
- 更新時機：**翻頁動畫結束的那一幀**才寫入。起始畫面不播動畫，直接吸附並立刻寫入。
- 檢查點在跨分後 +7 秒（`advance(60000)` → `advance(7000)`），420ms 的動畫綽綽有餘。

## 三、DOM 結構（id 是契約，JS 只認 id）

每張牌四片，外加一條接縫。時牌 prefix `h`、分牌 prefix `m`：

```html
<div class="card" id="ch">
  <div class="pane top" id="hu" ><span>00</span></div>  <!-- 上半靜態：顯示「新」值 -->
  <div class="pane bot" id="hl" ><span>00</span></div>  <!-- 下半靜態：顯示「舊」值 -->
  <div class="leaf top" id="hfu"><span>00</span></div>  <!-- 落下的葉片：舊值上半 -->
  <div class="leaf bot" id="hfl"><span>00</span></div>  <!-- 接上的葉片：新值下半 -->
  <div class="seam"></div>
</div>
```

分牌同構，id 為 `mu` / `ml` / `mfu` / `mfl`。

**半個字怎麼切**：四片都 `position:absolute; height:50%; overflow:hidden`，
裡面的 `<span>` 是 `display:block; line-height: var(--ch)`（＝整張牌高）。
`.top` 的 span 從自己頂端排 → 露出字的上半；`.bot` 的 span 加
`transform: translateY(calc(var(--ch) * -0.5))` 把字拉上來 → 露出下半。
兩片對齊靠同一個 `--ch`，不准用 magic number。

## 四、翻頁動作

狀態放在 `runs` 陣列裡 —— **這個變數名是硬性的**，`simulate.js:88` 的探針直接讀 `runs.length`。
一筆 run＝一張正在翻的牌：`{card, from, to, t0}`。翻完就 splice 掉，靜止時 `runs.length === 0`。

`DUR = 420ms`。真實翻頁鐘的葉片落下比想像中快，600ms 以上會變成慢動作播放。

| 階段 | 進度 `p` | 動作 |
|---|---|---|
| 落下 | `0 → 0.43` | `#hfu` `rotateX(-90 * e)` where `e = q*q`（重力加速），`#hfl` 藏著 |
| 接住 | `0.43 → 1` | `#hfu` 隱藏，`#hfl` 從 `rotateX(90deg)` 轉到 `0`，用 `1-(1-q)^2.4` 再疊一個衰減彈跳 |

彈跳：落到底時往回彈 `4.5°`，一次就收（`Math.sin(Math.PI*q) * 4.5 * (1-q)^2` 之類）。
不要彈兩次，實體葉片撞到軸只會「咚」一聲，不會抖。

**打光**（擬真的關鍵，比角度還重要）：每片葉子用一層 `::after` 全覆蓋的純黑遮罩，
opacity 綁 CSS 變數 `--sh`，JS 用 `style.setProperty('--sh', v)` 寫（假 DOM 是 noop，安全）。

- `#hfu` 落下時 `--sh: 0 → 0.55`（葉面轉離光源）
- `#hfl` 接住時 `--sh: 0.55 → 0`
- `#hl`（下半靜態）在落下階段 `--sh: 0 → 0.3`，模擬葉片壓在上面的接觸陰影，第二階段歸零

沒有這三條，翻頁看起來像投影片切換，不像有厚度的東西在動。

`prefers-reduced-motion` → `DUR = 0`，直接吸附。（`matchMedia` 在假 DOM 回 `matches:false`，走正常路徑。）

## 五、外觀

- **底色** `#08090a`，中央一圈很淡的徑向光暈，模擬頭頂投射燈。
- **牌面** 消光黑，`linear-gradient(#1b1c1f, #0d0e10)`；圓角 `calc(var(--cw) * 0.045)`。
- **接縫** 牌高正中一條 3px `#000`，下緣壓一條 `rgba(255,255,255,.07)` 的高光 —— 塑膠邊緣反光。
- **轉軸** 接縫高度、牌的左右兩側各一個小凹槽（深色半圓），這是翻頁鐘一眼認得出來的特徵。
- **字** 白 `#f2f3f5`，`font-variant-numeric: tabular-nums`，字重 500，`letter-spacing: -0.02em`。
  字體走 repo 慣例（Google Fonts CDN + `sw.js` 的 stale-while-revalidate）：`Inter`，
  fallback `'Helvetica Neue', Helvetica, Arial, sans-serif`。Inter 最接近真實翻頁鐘的 Helvetica 系數字。
- **沒有冒號。** 真的翻頁鐘（Copal / Twemco）跟機場看板都沒有，兩張牌中間就是機殼的縫。

**版面**（純 CSS，JS 不碰）

| 量 | 值 |
|---|---|
| 牌寬 `--cw` | 橫式 `min(38vw, 62vh)`；直式（`@media (max-aspect-ratio: 4/5)`）`min(82vw, 33vh)` |
| 牌高 `--ch` | `calc(var(--cw) / 1.25)`（第一版 1.45 太扁，牌像被壓過） |
| 字級 | `calc(var(--cw) * 0.64)`（跟著牌高一起加，不然字在高牌裡會顯得空） |
| 間距 | `calc(var(--cw) * 0.10)`，直式時改成上下堆疊 |
| 透視 | 容器 `perspective: calc(var(--cw) * 2.2)` |

## 六、其餘檔案

照 `galaga/` 抄，只換內容：

- **`flip/clock.json`** — `id:"flip"`（**必須等於資料夾名**，`tools/build.py:43`、`tools/check.py:25`），
  `name:"翻頁時鐘"`，tagline 一句話講機構，`created:"2026-07-28"`，
  `tags:["flip","dom","pwa"]`，`accent:"#e9eaec"`（黑牌白字，強調色取近白），
  `shot:{width:1200, height:750, freeze:"2026-07-27T10:09:03+08:00", settle:900}`。
- **`flip/sw.js`** — `VERSION = 'flip-v1'`（`check.py:43-48` 要求 `<資料夾名>-v<n>`），
  SHELL 與 fetch 策略照 `galaga/sw.js` 抄（含 Google Fonts 的 stale-while-revalidate）。
- **`flip/manifest.webmanifest`** — `start_url` / `scope` 必須 `./` 開頭，
  每個 `icons[].src` 檔案要真的存在（`check.py:53-61`）。
- **`flip/gen_icons.py`** — Pillow 點陣，四個輸出檔（192 / 512 inset 0.16、maskable 512 inset 0.26、
  apple-touch 180 inset 0.16）。圖案：黑底白邊的牌，正中一條深色接縫。
- **`flip/index.html`** — 單檔自足，**只有一個無屬性的 `<script>`**（`simulate.js:83` 的正則是
  `/<script>([\s\S]*)<\/script>/`，貪婪比對，多一個 script tag 會把中間的 HTML 一起吃進去），
  程式包在 `(() => { 'use strict'; ... })();` 裡，`})();` 必須是檔案裡**最後一次**出現
  （`simulate.js:91` 用 `lastIndexOf` 定位注入點）。
  serviceWorker 註冊要跟 `galaga/index.html:527` 一樣寫在**同一行**：
  `if(!EMBED && 'serviceWorker' in navigator && location.protocol.startsWith('http')){ ... }`
  （`check.py:37` 的正則 `!EMBED\s*&&[^;]*serviceWorker` 不跨分號）。
  embed 慣例：`body.embed` 時隱藏全螢幕按鈕。

## 不做的事

- **翻頁音效不做。** 自動播放被瀏覽器擋，而且掛在桌上一整天每分鐘「咖」一聲會被砸。
- **秒牌不做。** 使用者選了時:分。真實 Solari 也沒有秒。
- **日期牌不做。**
- **縮圖不拍翻頁中。** `shoot.py` 要求連跑兩次 bytes 相同，動畫中途的畫面靠 rAF 時序，不可重現。
  所以 `freeze` 定在 `10:09:03`、`settle` 只給 900ms —— 下一次翻頁在 `10:10:00`，穩穩停在靜止態。
- **不碰** `galaga`、`bricks`、`tools/`、根 `index.html`、`.github/`。

## 驗收條件

1. `python tools/check.py` 全過。
2. `node tools/simulate.js flip/index.html` 四個情境全 PASS，且每段結尾「殘留 run 0」。
   跨午夜（`23:58` 起）與跨整點（`09:58` 起，時分同時翻）都要過。
3. `python tools/build.py` 後 `dist/clocks.json` 裡有三座，`flip` 排最前面（`created` 最新）。
4. `python tools/shoot.py` 連跑兩次，`thumbs/flip.webp` 的 bytes 完全相同。
5. 瀏覽器實看 `flip/index.html`：手動把系統時間或程式裡的 `now` 推過整分，
   肉眼確認 —— 葉片有透視收縮、落下比回彈快、翻頁當下下半牌有一道陰影掃過。
6. `flip/manifest.webmanifest` 列的四個 icon 檔都真的產出來了。
