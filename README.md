# CLOCKS

一座一座做的時鐘。每座時鐘是一個獨立資料夾，彼此不共用任何程式碼。

```
clocks/
├─ index.html              展示頁（不註冊 service worker，理由見下）
├─ clocks.json             由 build.py 產生，不進版控
├─ tools/
│  ├─ check.py             檢查每座時鐘有沒有守住約定
│  ├─ simulate.js          假 DOM + 虛擬時鐘，驗證分鐘真的會推進
│  ├─ build.py             glob */clock.json → 組出 dist/
│  └─ shoot.py             Playwright 截圖，時間會被凍結
├─ .github/workflows/deploy.yml
├─ galaga/                 ← 一座時鐘
│  ├─ index.html           全部邏輯都在這裡
│  ├─ clock.json           metadata
│  ├─ manifest.webmanifest
│  ├─ sw.js
│  └─ icon-*.png
└─ bricks/                 另一座，跟 galaga 之間零共用程式碼
```

## 新增一座時鐘

1. `mkdir 新名字`，放 `index.html`
2. 寫 `clock.json`，**`id` 必須跟資料夾同名**
3. `python tools/check.py && node tools/simulate.js && python tools/build.py`

沒有中央註冊表要改。build.py 自己 glob 出來。

```json
{
  "id": "galaga",
  "name": "小蜜蜂時鐘",
  "tagline": "一句話說它在幹嘛",
  "created": "2026-07-27",
  "tags": ["arcade", "canvas", "pwa"],
  "accent": "#f2c14e",
  "shot": { "width": 1200, "height": 750, "freeze": "2026-07-27T10:09:02+08:00", "settle": 3200 }
}
```

`accent` 會變成展示頁上那張卡片的重點色 —— 顏色由時鐘自己決定，不是展示頁決定的。

## 四個約定

**一、`?embed=1` 要能認得。**
展示頁滑過卡片時會用 iframe 載入 `./<id>/?embed=1`。看到這個參數時：

- 隱藏所有 UI，只留錶面
- **不要註冊 service worker**。不然使用者只是滑過去看看，就被裝了一堆 sw

```js
const EMBED = new URLSearchParams(location.search).has('embed');
if (!EMBED && 'serviceWorker' in navigator) {
  navigator.serviceWorker.register('./sw.js');
}
```

**二、cache 名稱要全站唯一。**
Cache Storage 是**整個 origin 共用**的。兩座時鐘都把 cache 叫 `clock-v1`，
就會互相覆蓋，症狀是某座時鐘離線後開出另一座的畫面。用 `<id>-v<n>`。

**三、要回報「畫面上真正顯示的時間」。**
數字**真的出現在畫面上**的那一刻（不是決定要換的那一刻），寫進：

```js
document.documentElement.dataset.shown = drawn.join('');
```

`tools/simulate.js` 只讀這一個值，不碰任何內部變數 —— 所以之後的時鐘
不管用 canvas、SVG 還是純 CSS，都能用同一支測試驗證。

**四、manifest 全部用相對路徑。**
`start_url` 和 `scope` 寫 `"./"`。寫成 `"/"` 會指到網域根目錄，
在 GitHub project page（網址有子路徑）上 manifest 直接失效，裝不起來。
另外每份 manifest 給一個明確的 `id`，同 origin 多個 PWA 才不會身分混淆。

## 為什麼展示頁不註冊 service worker

根目錄的 sw scope 是 `/`，會攔截**底下所有時鐘**的請求。
一旦快取策略跟某座時鐘的 sw 打架，debug 會非常痛苦。
展示頁本來就只是一個列表，離線可用沒什麼價值，不值得這個風險。

## 本機

```bash
pip install -r requirements.txt
playwright install chromium

python tools/check.py       # 約定沒守住會在這裡擋下來
node tools/simulate.js     # 幾秒內模擬幾十分鐘，加 --quick 更快
python tools/build.py
python tools/shoot.py      # 選用，要縮圖才跑
python tools/build.py      # 讓 clocks.json 補上 thumb 欄位
python -m http.server -d dist 8080
```

## 截圖為什麼要凍結時間

讓瀏覽器讀真實時間的話，每次 CI 產出的縮圖都不一樣，
git 會被沒有意義的二進位差異洗版。`shoot.py` 在頁面腳本執行前把 `Date`
換成一個平移過的版本 —— 時間照樣流動（動畫才會動），但**起點固定**，
所以同一份程式碼永遠產生同一張圖。`freeze` 挑一個數字好看的時刻。

## 部署

推上 main 就會跑 `.github/workflows/deploy.yml`：
約定檢查 → 模擬（**一座時鐘一個 job，平行跑**）→ build → 截圖 → build → 發到 Pages。

模擬是整條 pipeline 唯一的瓶頸，單座約五分鐘而且是純 CPU，快取幫不上忙。
拆成 matrix 之後牆上時間等於最慢的那一座，加再多時鐘都不會變慢。
matrix 由 `ls */clock.json` 產生，新增時鐘一樣不用改 workflow。
GitHub Pages 自動有 HTTPS，PWA 的安裝條件直接滿足。

改版後記得把該座時鐘 `sw.js` 裡的 cache 版本號加一，否則舊的 sw 會一直回舊檔案。

## GitHub Pages 相容性

全部是靜態檔案，沒有伺服器端邏輯，時間來自瀏覽器的 `new Date()`。

需要先做的設定：

1. **Settings → Pages → Source 選 `GitHub Actions`**，不是 `Deploy from a branch`。
   選錯的話 `deploy-pages` 會直接失敗。workflow 裡的 `configure-pages@v5`
   加了 `enablement: true`，多數情況會幫你自動開起來。
2. workflow 觸發的分支寫死 `main`，預設分支叫 `master` 的話要改。

已知的限制：

- **Pages 不能自訂 HTTP header。** 也就是說 `Service-Worker-Allowed` 設不了，
  sw 的 scope 永遠只能是自己所在的資料夾或更窄。這套架構剛好不需要放寬，
  但如果哪天想做「一個 sw 管全部時鐘」就辦不到 —— 那也不該做，理由見上面。
- **有 CDN 快取。** 剛 push 完有時候要等幾分鐘才看得到新版，
  用無痕視窗確認比較快，不要以為是 build 壞了。
- **檔名大小寫敏感。** `build.py` 已經強制 `id` 跟資料夾同名，這關過了就不會出事。
- 官方容量上限 1 GB、單次部署逾時 10 分鐘。縮圖是 webp，一張幾十 KB，放幾百座都不會碰到。

`manifest.webmanifest` 的 Content-Type 沒問題就不用管。真的裝不起來的話，
去 DevTools → Application → Manifest 看有沒有解析成功，
不行就改名成 `manifest.json`（規格允許，只要是 JSON 系的 MIME 都可以）。

## 關於原創性

時鐘可以致敬既有的遊戲**機制**（玩法不受著作權保護），但不要重製角色設計、
sprite、配色或名稱。`bricks` 的做法是留下「從下方頂碎磚塊」這個動作，
角色換成原創的工地師傅，配色與造型都自己畫。
`galaga` 同理：編隊俯衝的路徑是共通玩法，蜜蜂 sprite 是自己畫的。

## 為什麼要分 want 和 drawn

第一版的寫法是「發現時間變了 → 更新 `displayStr` → 播動畫」。
問題在於 `displayStr` 是**無條件**先更新的：只要動畫因為任何理由沒跑完，
`displayStr` 已經宣稱自己是新時間了，下一幀比對相等，**連重試的機會都沒有**。
`bricks` 就踩到了 —— 師傅的離場目標算錯，走到畫面內就停住，
run 永遠不被回收，那個數字從此再也不會變。

現在拆成兩個：

- `want[d]` — 想顯示的
- `drawn[d]` — 真的已經放到畫面上的，只有 `buildDigit` 成功才寫入

每一幀都比對 `want` 和當下時間，卡住的數字下一幀會自己追上。
另外每個 run 有 15 秒看門狗，超時強制收掉並補上數字。

這類 bug 的代價是「時鐘永遠停住」，而且**只有等到第二次分鐘變化才看得出來** ——
開著看三十秒完全正常。所以它必須由機器擋，`tools/simulate.js` 就是為此存在。
