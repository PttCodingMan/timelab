# bloom：潮汐花鐘

2026-07-30

第九座時鐘。新增 `bloom/` 一個資料夾，**不動** `galaga`、`flip`、`bricks`、`zen`、`fog`、
`snake`、`receipt`、`life`、`tools/`、根 `index.html`、`deploy.yml`。
唯一動到的既有檔案是 `README.md:13` 的資料夾清單加一行。

**澎湖白沙灘，一整片天人菊。開著的花排成 HH:MM，潮水舔上來換掉要變的那幾朵，
整點時一道大浪蓋全場，退下去時四位數重新長出來。**

---

## 一、全畫面只有兩個動力源

這是整座鐘最重要的一條，違反了縮圖就會壞：

> **畫面上每一個會動的東西，動力只能來自「陣風」或「潮汐」。兩者都靜止時，整幀必須完全靜止。**

`tools/shoot.py:39-51` 的 `FREEZE` 只是把 `Date` 的**原點平移**，時間照樣流動
（它自己的註解就這麼寫）。所以不能靠「凍結時間」讓畫面停住 —— 得自己留一個真正靜止的窗口，
`shot.settle` 才拍得出每次 bytes 相同的圖。`fog` 用的是「寫完字停 1.5 秒」，
這座鐘用的是**陣風之間的無風段**。

受這條約束的東西，全部要綁到 gust envelope 或潮汐進度上：

| 東西 | 靜止時的樣子 |
|---|---|
| 花莖與花盤的擺動 | 完全不動（不是「幅度很小」，是 `w === 0`） |
| 海面白浪紋 | 無風＝鏡面，紋路不移動 |
| 泡沫粒子 | 潮汐動畫結束前必須全部消光 |
| 被吹走的花瓣 | lifetime ≤ 2.5s，在潮汐窗口內落地消失 |
| 濕沙變乾 | 潮退後 2.5s 內乾完，之後不再變化 |

沙的顆粒 noise、野花的種類與位置、花瓣的長短彎度，一律走 **mulberry32（固定 seed）**，
**全檔不准出現 `Math.random()`**（同 `fog`）。

## 二、場景與投影

不做真 3D。一個投影函式就夠了，花田用 `(u, v)` 網格座標，`v=0` 最遠、`v=ROWS-1` 最近：

```js
const d  = v / (ROWS - 1);
const k  = Math.pow(d, 1.35);          // 1.35：近排拉開、遠排擠密
const sy = HZ + BAND * k;
const sc = 0.35 + 0.65 * k;            // 遠處的花只有近處的 35%
const sx = W/2 + (u - (COLS-1)/2) * COLW * sc;
```

`HZ = 0.22 * H`（海平線），`BAND = H - HZ`。每朵花的 `(u, v)` 再加 seeded jitter
`±0.28` 格 —— **格線感必須消失，否則它是 LED 看板不是花田**。

由遠到近畫（painter's algorithm），近處的花自然蓋住遠處的，不用 z-buffer。

| 圖層 | 內容 |
|---|---|
| 天 | 頂 `#7fb8dd` → 海平線 `#cfe6f0`（大氣散射泛白） |
| 海 | 遠 `#3f8fb0` → 近 `#1d6e93`，白浪紋（水平細線，**風停就不動**） |
| 乾沙 | `#f2e6cf` → `#e8d7b8`，貼一張預生成的顆粒 noise texture 重複鋪 |
| 濕沙 | `#c9ac86` ＋ 一層天空色低 alpha 高光（反射） |
| 花田 | 由遠到近，莖 → 葉 → 花頭 |
| 過曝 | 全畫面壓一層 `rgba(255,248,235,.10)`，頂部加一圈很淡的光暈 |

## 三、花田佈局

`COLS = 30`、`ROWS = 11`。數字佔中間 `u = 3..26`、`v = 2..8`：

```
[5 欄數字][1 空][5 欄數字][2 欄冒號][5 欄數字][1 空][5 欄數字]
```

**其餘格子也種花，但永遠不開** —— 只有芽和灰綠葉。數字是從一整片花海裡「開出來」的，
不是浮在空沙上的亮點。例外：最前排 `v=10` 和最後排 `v=0` 散佈約 15% 的**野生開花**
（seeded、終生不變、不在數字帶上），沒有這一撮，整片田會像個開關板。

**冒號**是兩朵比較小（`0.7×`）的花，`v=4` 和 `v=6`，常開不謝。

字形是 5×7 點陣，十個 glyph 直接寫死成 bit string（**不抄 `zen` 的貝茲筆順**，
點陣不需要筆順，這是這座鐘比 `fog`／`zen` 省的地方）：

```js
const G = ['0111010001100111010111001100010111 0'.replace(/ /g,''), ...];
// 實作時用可讀的 7 行陣列，check 只看畫面
```

**直式版面**（`h > w`，模擬會跑 420×900）：`COLS = 11`、`ROWS = 17`，
HH 排在 `v = 2..8`、MM 排在 `v = 9..15`，**冒號省略**。`dataset.shown` 照樣四位。

## 四、一朵天人菊

Gaillardia pulchella：外圈舌狀花瓣末端黃、中段橘紅、心盤深栗色。

- **13 片花瓣**（費氏數，看起來自然），每片末端 3 齒。
- 徑向漸層：心 `#7a2618` → `#e04a1f` → 瓣端 `#f6c33b`。
- 心盤深栗 `#4a1e12`，上面點一圈細小的黃色管狀花。
- 每朵用 seeded random 決定花瓣長短（±12%）與彎度 —— **沒有兩朵一樣**。
- 含苞：綠球 ＋ 幾片沒張開、帶紅邊的萼片。
- 莖：從沙面到花心的兩段 quadratic，灰綠 `#6e8a5e`；葉子 `#5c7a4a`，一片，朝背風側。

**開花 `bloom` 0→1 分三段：**

| 區間 | 動作 |
|---|---|
| `0.00–0.30` | 花苞脹大、萼片外翻 |
| `0.30–0.85` | 花瓣從捲曲展開（`easeOutBack`，過衝 1.08），第 `i` 片延遲 `i/13*0.15` → 旋著開 |
| `0.85–1.00` | 心盤的黃色管狀花一圈圈亮起 |

**謝花 `bloom` 1→0：** 花瓣下垂、褪色、變薄，其中 2～4 片脫落被水／風帶走
（各自的速度，lifetime ≤ 2.5s），最後只剩心盤縮回沙裡。

## 五、風：陣風制

無風是預設狀態，這既是第一節的硬需求，也讓陣風真的有戲。

```
週期 12s，對齊分鐘邊界（每分鐘剛好 5 陣）
第 k 陣：onset = k*12 + rnd(0, 1.0)s，dur = rnd(3.5, 4.5)s，amp = rnd(0.6, 1.0)
envelope e(τ) = sin(π τ / dur)^1.6        // 兩端都是 0，接得平滑
```

陣風要**看得出從左掃過去**，所以相位跟 `u` 綁：

```js
const lead  = (τ/dur) * (COLS + 8) - 8;              // 陣風前緣的欄位
const local = clamp(lead - u, 0, 6) / 6;             // 前緣還沒到的花不動
const w = amp * e(τ) * local * (0.55 + 0.45*Math.sin(τ*7 - u*0.4 - v*0.15));
```

`w` 的用法：莖尖偏移 `w * 0.30 * cell`、花頭旋轉 `w * 0.25` rad、
花盤 `scaleY = 1 - 0.18*|w|`（傾斜away 的透視壓縮）。海面的白浪紋位移也乘 `w`。

**陣風之間 `w` 恆等於 0**，不是很小的值。

| 參數 | 初值 | 為什麼 |
|---|---|---|
| 週期 | 12s | 短於 8s 像被搖，長於 16s 靜止段會悶 |
| `dur` | 3.5～4.5s | 留下 7～8s 的無風窗口給截圖 |
| 前緣寬 | 6 欄 | 窄了像一條線掃過，寬了看不出方向 |

這幾個數字**一定要在瀏覽器裡對眼睛調**，寫死的初值只是起點。

## 六、潮：小潮舒分、大潮換時

### 小潮（每分鐘 :00）

**水舌不是整條橫線，是一片有寬度的舌狀水**，只在「這次要變動的欄位」範圍內爬上來。
分鐘個位變 → 只有畫面最右那位數腳下濕一片；`09:59 → 10:00` 那種三位同時變 → 舌很寬。
海浪打上沙灘本來就是舌狀、深度不均，這件事不用解釋就成立。

| 時間 | 動作 | `runs` |
|---|---|---|
| `0.0 – 1.4s` | 水舌從畫面下緣爬到最深那朵要變的花再多半列，前緣一排白泡沫點 | 1 |
| `1.4 – 1.8s` | 停在最高點 | 1 |
| `1.8 – 3.0s` | 退回；**水舌退離某朵花的那一幀，那朵花開始 bloom** | 1 |
| `3.0 – 3.5s` | 最後一朵開完、泡沫消光 → 寫 `dataset.shown` | 0 |

要**關**的花，在水舌覆蓋到它的那一幀開始 wither（0.5s）。
覆蓋過的沙 `wet = 1`，之後 2.5s 線性乾回 0。

### 大潮（每小時 :00:00）

| 時間 | 動作 | `runs` |
|---|---|---|
| `0.0 – 2.2s` | 水一路推到 `v=0`（花田最遠端），蓋全場，泡沫大量 | 1 |
| `2.2 – 2.8s` | 停 | 1 |
| `2.8 – 4.6s` | 由遠到近退去，露出來的花跟著開 —— stagger 是水退的副作用，不另外寫 | 1 |
| `4.6 – 5.4s` | 最後一朵開完、泡沫殘跡淡出 → 寫 `dataset.shown` | 0 |

### 進場

首次載入與 `resize` 之後：只跑「大潮退去」的後半段（不爬上來，直接從全覆蓋退），約 2.5s。
不特別處理，跟大潮共用同一段程式。

**`runs` 這個變數名是硬性的**，`tools/simulate.js:98` 直接讀 `runs.length`。
潮汐動畫（含進場）開始時 push、結束時清空；**風不算 run**（它從不結束）。

## 七、`dataset.shown` 契約

```js
document.documentElement.dataset.shown = p2(h) + p2(m);   // 24 小時制、補零
```

寫入時機：**最後一朵新花的 `bloom ≥ 0.6` 那一幀**（已經看得出是花，不是還在脹的苞）。
不是決定要換的那一刻 —— 這就是 `README.md:54-61` 那條約定的重點。

`simulate.js:166-174` 是輪詢到收斂為止，所以 3.5s／5.4s 的動畫長度不會 FAIL，
但每段結尾的**殘留 run 必須是 0**。

## 八、效能

330 朵花 × 13 片花瓣 = 4000+ path/frame，一定掉幀。**花頭預渲染成 sprite atlas**：

- 4 種 seed 變體 × 24 格 bloom 階段 = 96 張，tile 128px，atlas 3072×512。
- 畫的時候只有 `drawImage` ＋ transform；**風的傾斜靠 transform，不重畫 path**。
- 莖和葉各自 batch 成**一條** path（330 個 `moveTo`／`quadraticCurveTo`，一次 `stroke()`／`fill()`）。
- 沙的顆粒 noise 生成一張 256×256 texture，`createPattern` 重複鋪。
- `devicePixelRatio` 上限 2。

## 九、假 DOM 的地雷（會 crash，不是會變醜）

`tools/simulate.js:47,53`：**只有 id 為 `c` 的那個 canvas 有 `getContext`**，
`document.createElement('canvas')` 回傳的 stub **沒有** `getContext`。
這座鐘要開離屏 canvas 做 atlas 和 noise texture，直接 `oc.getContext('2d')` 會在模擬裡爆掉。

```js
const mk = (w,h) => { const e = document.createElement('canvas');
  const g = e.getContext && e.getContext('2d');
  if (g) { e.width = w; e.height = h; } return g && { e, g }; };
```

任一張開不出來 → `HEADLESS = true`，`render()` 開頭直接 `return`。
狀態機（`runs`、`bloom` 進度、`dataset.shown`）照跑，模擬只看這三樣。

其餘三條硬線同 `fog`：

- 只有**一個無屬性的 `<script>`**（`simulate.js:83` 的正則貪婪比對）。
- 程式包在 `(() => { 'use strict'; ... })();`，`})();` 必須是全檔**最後一次**出現。
- serviceWorker 註冊寫在同一行：`if(!EMBED && 'serviceWorker' in navigator && ...)`
  （`check.py:41` 的正則不跨分號）。

## 十、i18n 與 UI

照 `README.md:66-85`。`#ctrl` 裡四顆裸 `button`：`bInstall` / `bWake` / `bFull` / `bLang`，
`?embed=1` 時整個 `#ctrl` 隱藏。

```js
const EN = { _title:'Tide Bloom Clock', bInstall:'Install',
             bWake:'Stay awake', bFull:'Fullscreen' };
```

畫面上只有數字，沒有其他中文，字典就這四個 key。

## 十一、其餘檔案

- **`bloom/clock.json`**

```json
{
  "id": "bloom",
  "name": "潮汐花鐘",
  "tagline": "潮水退去，天人菊開成現在幾點",
  "name_en": "Tide Bloom Clock",
  "tagline_en": "the tide pulls back and the blanketflowers open into the hour",
  "created": "2026-07-30",
  "tags": ["nature", "canvas", "pwa"],
  "accent": "#e04a1f",
  "shot": { "width": 1200, "height": 750,
            "freeze": "2026-07-30T12:34:28+08:00", "settle": 4000 }
}
```

  `freeze` 落在分鐘的第 28 秒、`settle` 4000ms → 拍在第 32 秒：
  進場動畫（2.5s）早就收完、離下一次潮汐還有 28 秒、
  而第 2 陣風跨 `24.5–29s`，第 32 秒穩穩落在無風段（`29–36s`）正中間。**畫面完全靜止。**

- **`bloom/sw.js`** — `VERSION = 'bloom-v1'`（`check.py:47` 要求 `<資料夾名>-v<n>`）。
- **`bloom/manifest.webmanifest`** — `start_url`／`scope` 必須 `./` 開頭，給明確的 `id`，icons 要真的存在。
- **`bloom/gen_icons.py`** — Pillow，四個輸出（192／512 inset 0.16、maskable 512 inset 0.26、
  apple-touch 180 inset 0.16）。圖案：白沙底，一朵橘紅心／金黃邊的天人菊。
- **`README.md:13`** 資料夾清單加 `bloom/`。

## 不做的事

- **秒不做。** 秒針會把潮水的節奏打碎，而且每秒一次動畫就沒有無風窗口可以截圖。
- **蝴蝶、海鳥、雲不做。** 每一個都是自己的動力源，會違反第一節那條，而且都得為了縮圖再想一次靜止怎麼辦。
- **真 3D、z-buffer、光照模型不做。** 一個投影函式 ＋ 由遠到近畫就夠了。
- **互動不做**（`fog` 有擦玻璃是因為那是它的機制，這座沒有對應的動作）。
- **日期、主題切換不做。**
- **不碰**其他八座、`tools/`、根 `index.html`、`.github/`。

## 驗收條件

1. `python tools/check.py` 全過。
2. `node tools/simulate.js bloom/index.html` 全情境 PASS，每段結尾「殘留 run 0」；
   跨午夜（`23:58` 起）、跨整點（`09:58` 起）、直式 420×900 都要過。
3. `python tools/build.py` 後 `dist/clocks.json` 裡有九座，`bloom` 排最前面（`created` 最新）。
4. `python tools/shoot.py` 連跑兩次，`thumbs/bloom.webp` 的 bytes **完全相同**。
5. 全檔 `grep -c 'Math.random'` === 0。
6. 瀏覽器實看：
   (a) 靜止時整幀真的不動 —— 盯 10 秒，花、海、泡沫都沒有任何位移；
   (b) 陣風來時看得出是**從左掃到右**的一道波，不是整片同時晃；
   (c) 分鐘跳動時，水舌只出現在要變的那幾位數腳下，其他位置的沙不會濕；
   (d) 整點時大浪蓋全場，退下去時花是**由遠到近**開的；
   (e) 直式 420×900 下 HH／MM 上下兩排，讀得出來；
   (f) 花田不像格線 —— 隨手截一張，看不出方陣。
7. `bloom/manifest.webmanifest` 列的四個 icon 檔都真的產出來了。
