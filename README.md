# TimeLab

一間研究「時間還能長成什麼樣子」的實驗室。同一件事——把現在幾點顯示出來——
每次換一套完全不同的做法：街機、翻頁、工地施工、枯山水。

每座時鐘是一個獨立資料夾，彼此不共用任何程式碼，只共用下面五個約定。

**歡迎用你的想法新增時鐘，我都會上架。** 開個 PR，`check.py` 和 `simulate.js` 過得了就收。

```
index.html                展示頁
tools/                    check / simulate / build / shoot
galaga/  flip/  bricks/  zen/  fog/   一座時鐘一個資料夾
├─ index.html             全部邏輯都在這裡
├─ clock.json             metadata
└─ sw.js  manifest.webmanifest  icon-*.png
```

## 新增一座時鐘

`mkdir 新名字` → 放 `index.html` → 寫 `clock.json`。沒有中央註冊表要改，`build.py` 自己 glob 出來。

```json
{
  "id": "galaga",
  "name": "小蜜蜂時鐘",
  "tagline": "一句話說它在幹嘛",
  "name_en": "Galaga Clock",
  "tagline_en": "the same one line, in English",
  "created": "2026-07-27",
  "tags": ["arcade", "canvas", "pwa"],
  "accent": "#f2c14e",
  "shot": { "width": 1200, "height": 750, "freeze": "2026-07-27T09:06:02+08:00", "settle": 3200 }
}
```

`id` 必須跟資料夾同名。`accent` 是展示頁那張卡片的重點色 —— 顏色由時鐘自己決定。
`shot.freeze` 是截圖用的凍結時刻，讓縮圖每次都長一樣（[為什麼](docs/notes.md#截圖為什麼要凍結時間)）。
`name_en` 和 `tagline_en` 是展示頁英文版用的，`check.py` 會擋沒填的 —— 別機翻，那兩句是門面。

## 五個約定

**一、`?embed=1` 要能認得。** 展示頁用 iframe 載入 `./<id>/?embed=1` 當預覽。
看到這個參數就隱藏 UI 只留錶面，而且[不要註冊 service worker](docs/notes.md#為什麼展示頁不註冊-service-worker)。

```js
const EMBED = new URLSearchParams(location.search).has('embed');
if (!EMBED && 'serviceWorker' in navigator) navigator.serviceWorker.register('./sw.js');
```

**二、cache 名稱用 `<id>-v<n>`。** Cache Storage 是整個 origin 共用的，
撞名的症狀是某座時鐘離線後開出另一座的畫面。

**三、要回報「畫面上真正顯示的時間」。** 數字**真的畫出來**的那一刻（不是決定要換的那一刻）寫進：

```js
document.documentElement.dataset.shown = drawn.join('');
```

`simulate.js` 只讀這一個值、不碰內部變數，所以 canvas、SVG 還是純 CSS 都能用同一支測試驗證。
（這個約定是[踩到「時鐘永遠停住」](docs/notes.md#為什麼要分-want-和-drawn)才長出來的。）

**四、manifest 全用相對路徑。** `start_url` 和 `scope` 寫 `"./"`，
寫成 `"/"` 在 GitHub project page 上會直接失效、裝不起來。每份 manifest 再給一個明確的 `id`。

**五、雙語。** 繁中／英文，靠 `localStorage['clocklab.lang']`（`'zh'`｜`'en'`）在同一個 origin 全站共用，
所以從展示頁點進來、或直接開書籤，語言都接得上。HTML 裡的中文**就是** `zh` 原文，
每頁只內嵌一份英文字典 —— 中文使用者不跑任何字串替換。字典的 key 直接用 element id：

```js
const EN = { _title:'Galaga Clock', bInstall:'Install', bWake:'Stay awake', bFull:'Fullscreen' };
const LANG_EN = (localStorage.getItem('clocklab.lang')
              || (navigator.language.startsWith('zh') ? 'zh' : 'en')) === 'en';
if (LANG_EN) {
  document.documentElement.lang = 'en';
  document.title = EN._title;
  for (const [k, s] of Object.entries(EN)) document.getElementById(k)?.replaceChildren(s);
}
```

語言鈕 id 用 `bLang` 並放進 `#ctrl`：那裡是裸 `button` 選擇器，樣式自動吃到，
也會跟著 `?embed=1` 一起隱藏。切換就是寫 `localStorage` 然後 `location.reload()` —— 不做雙向
DOM 還原，省掉「保存中文原文」和「重新渲染清單」兩件事。`<title>` 和 `<html lang>` 留中文原文，
英文由 JS 改寫。畫面本來就全英文的時鐘（bricks、life）字典只要 `_title` 一個 key。
manifest 一律英文：PWA manifest 規格不支援 i18n，靜態站也沒有 `Accept-Language` 可談。

另外：可以致敬既有遊戲的**機制**，但角色、sprite、配色、名稱要自己畫（[細節](docs/notes.md#關於原創性)）。

## 本機

```bash
pip install -r requirements.txt
playwright install chromium

python tools/check.py      # 約定沒守住會在這裡擋下來
node tools/simulate.js     # 幾秒內模擬幾十分鐘，加 --quick 更快
python tools/build.py
python tools/shoot.py      # 選用，要縮圖才跑；跑完再 build 一次補 thumb 欄位
python -m http.server -d dist 8080
```

## 部署

推上 main 就跑 `.github/workflows/deploy.yml`：
檢查 → [模擬（一座一個 job 平行跑）](docs/notes.md#模擬為什麼要拆成-matrix) → build → 截圖 → build → 發到 Pages。
matrix 由 `ls */clock.json` 產生，新增時鐘不用改 workflow。

改版記得把該座 `sw.js` 的 cache 版本號加一，否則舊的 sw 會一直回舊檔案。

**第一次要自己把 Pages 開起來**：Settings → Pages → Source 選 `GitHub Actions`，不是 `Deploy from a branch`。
workflow 裡的 `enablement: true` 不要指望它，job 的 `GITHUB_TOKEN` 通常沒這個權限，
第一次 push 會停在 `Resource not accessible by integration`。等價指令：

```bash
gh api -X POST repos/PttCodingMan/timelab/pages -f build_type=workflow
```

---

其他踩過的坑、Pages 的已知限制、設計取捨都在 **[docs/notes.md](docs/notes.md)**。
