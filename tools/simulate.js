// 用假的 DOM + 虛擬時鐘把時鐘跑起來，驗證分鐘真的會推進。
// 不裝 jsdom，因為這些時鐘用到的 DOM 介面很少，自己刻比較快也比較可控。
// 期望值用 UTC 算，時鐘畫面用 local，所以整支強制 UTC —— 不然非 UTC 的機器全 FAIL。
// 必須在任何 Date 之前設定。
process.env.TZ = 'UTC';
const fs = require('fs');
const vm = require('vm');

const RAF_LAG = 20;                               // 見下面 performance.now 的註解

function makeEnv(html, opts = {}) {
  const W = opts.width ?? 1200, H = opts.height ?? 750;
  let vnow = 0;                                   // 虛擬毫秒
  let vwall = opts.start ?? Date.UTC(2026, 6, 27, 2, 9, 0); // 真實世界時間軸
  const timers = [];
  let tid = 1;

  const noop = () => {};
  // 用純物件而不是 Proxy：draw() 每幀有幾百次 fillRect，
  // 走 Proxy 攔截會讓模擬慢兩個數量級
  const ctx = {};
  for (const k of ['fillRect','clearRect','strokeRect','beginPath','closePath','moveTo','lineTo',
                   'arc','arcTo','quadraticCurveTo','bezierCurveTo','rect','fill','stroke','save',
                   'restore','translate','rotate','scale','setTransform','resetTransform','clip',
                   'drawImage','fillText','strokeText','putImageData','ellipse','setLineDash'])
    ctx[k] = noop;
  ctx.createLinearGradient = ctx.createRadialGradient = () => ({ addColorStop: noop });
  ctx.createPattern = () => null;
  ctx.measureText = () => ({ width: 10 });
  ctx.getImageData = () => ({ data: [] });

  const mkEl = (id) => ({
    id, textContent: '', innerHTML: '', hidden: false, tagName: 'DIV',
    style: { setProperty: noop, width: '' },
    classList: { add: noop, remove: noop, contains: () => false },
    setAttribute: noop, getAttribute: () => null,
    appendChild: noop, removeChild: noop, remove: noop, prepend: noop,
    replaceChildren(...n) { this.textContent = n.map(String).join(''); },
    querySelector: () => mkEl('x'), querySelectorAll: () => [],
    addEventListener: noop, removeEventListener: noop,
    requestFullscreen: () => Promise.resolve(),
    click() { if (typeof this.onclick === 'function') this.onclick(); }
  });

  const canvas = Object.assign(mkEl('c'), {
    clientWidth: W, clientHeight: H, width: W, height: H,
    getContext: () => ctx
  });

  const els = { c: canvas };
  const document = {
    getElementById: (id) => (els[id] ||= mkEl(id)),
    createElement: (tag) => Object.assign(mkEl(tag), { tagName: tag.toUpperCase() }),
    body: mkEl('body'),
    documentElement: Object.assign(mkEl('html'), { dataset: {} }),
    addEventListener: noop,
    fullscreenElement: null,
    exitFullscreen: noop
  };

  class FakeDate extends Date {
    constructor(...a) { a.length ? super(...a) : super(vwall); }
    static now() { return vwall; }
  }

  const win = {
    innerWidth: W, innerHeight: H, devicePixelRatio: 1,
    document, addEventListener: noop, removeEventListener: noop,
    matchMedia: () => ({ matches: false, addEventListener: noop }),
    getComputedStyle: () => ({ getPropertyValue: () => '#888888' }),
    location: { protocol: 'http:', search: '' },
    // language + localStorage：各頁的語言判定要用。給 en-US 且 getItem 回 null，
    // 等於「英文瀏覽器第一次造訪」，讓模擬真的跑過 i18n 那條分支而不是繞過它
    navigator: { serviceWorker: undefined, language: 'en-US' },
    localStorage: { getItem: () => null, setItem: noop, removeItem: noop },
    requestAnimationFrame: (cb) => { timers.push({ at: vnow + 16.67, cb: () => cb(vnow), raf: true, id: tid }); return tid++; },
    setTimeout: (cb, ms = 0) => { timers.push({ at: vnow + ms, cb, id: tid }); return tid++; },
    clearTimeout: (id) => { const i = timers.findIndex(t => t.id === id); if (i >= 0) timers.splice(i, 1); },
    setInterval: (cb, ms) => { const rec = { at: vnow + ms, cb, every: ms, id: tid }; timers.push(rec); return tid++; },
    clearInterval: (id) => { const i = timers.findIndex(t => t.id === id); if (i >= 0) timers.splice(i, 1); },
    // performance.now() 刻意比 rAF 的時間戳快 RAF_LAG。真的瀏覽器上 rAF 給的是
    // 「這一幀開始的時刻」，它可能早於頁面啟動時讀到的 performance.now()，所以
    // 第一次的 dt 會是負的。主迴圈撐不住負 dt 的話整條主執行緒會卡死，畫面一幀都
    // 交不出來 —— 之前 life 就是這樣過了模擬、卻在 CI 拍縮圖時逾時。
    performance: { now: () => vnow + RAF_LAG },
    Date: FakeDate, URLSearchParams, Math, JSON, Intl, console,
    AudioContext: undefined
  };
  win.window = win;
  win.globalThis = win;
  win.self = win;

  const script = html.match(/<script>([\s\S]*)<\/script>/)[1];
  // 偷一個觀測點出來：只在測試時注入，不動到原始檔
  const peek = `
    window.__peek = () => ({
      drawn: document.documentElement.dataset.shown || '?',
      runs: runs.length
    });
  `;
  const cut = script.lastIndexOf('})();');
  if (cut < 0) throw new Error('找不到 IIFE 結尾');
  const patched = script.slice(0, cut) + peek + '\n' + script.slice(cut);

  vm.createContext(win);
  vm.runInContext(patched, win, { filename: 'clock.js' });

  return {
    peek: () => win.__peek(),
    wall: () => vwall,
    // 往前推 ms 毫秒，虛擬時間與真實世界時間一起走
    advance(ms, step = 16.67) {
      const end = vnow + ms;
      while (vnow < end) {
        const next = Math.min(vnow + step, end);
        vwall += next - vnow;
        vnow = next;
        for (let i = 0; i < timers.length; i++) {
          const t = timers[i];
          if (t.at <= vnow) {
            timers.splice(i--, 1);
            if (t.every) timers.push({ ...t, at: vnow + t.every });
            try { t.cb(); } catch (e) { console.error('timer 爆了:', e.message); }
          }
        }
      }
    }
  };
}

// ── 測試 ────────────────────────────────────────────────────────
// 用法：node tools/simulate.js [某座時鐘的 index.html]
//       不給參數就跑全部
const path = require('path');
const ROOT = path.join(__dirname, '..');
// --quick 只跑短情境，本機改一行想快速確認時用
const QUICK = process.argv.includes('--quick');
const args = process.argv.slice(2).filter(a => !a.startsWith('--'));
const targets = args[0]
  ? [args[0]]
  : fs.readdirSync(ROOT)
      .filter(d => fs.existsSync(path.join(ROOT, d, 'clock.json')))
      .map(d => path.join(d, 'index.html'));

function p2(n) { return String(n).padStart(2, '0'); }
// 等畫面收斂的上限。最長的一次換字是 zen 的抹平 1.4 s + 耙出 2.6 s = 4.0 s，
// 這裡取 4000 的 1.5 倍當餘裕 —— 要驗的是「時鐘會收斂到牆上時間」，
// 不是「動畫要在某個固定秒數內收完」。動畫真的卡住的話還是等不到。
const SETTLE_MAX = 4000 * 1.5;
let fails = 0;
let html = '';

function run(title, opts, minutes, extra) {
  const env = makeEnv(html, opts);
  console.log(`\n${title}`);
  env.advance(4000);
  console.log(`  起點      畫面 ${env.peek().drawn}`);
  for (let i = 0; i < minutes; i++) {
    env.advance(60000);
    if (extra) extra(env, i);
    env.advance(7000);
    // 一輪往前推 67 秒，判定點對分鐘邊界的相位每輪飄 7 秒，總有一次會剛好落在
    // 動畫還沒收完的時候 —— 那是取樣相位的巧合，不是時鐘壞了。所以改成輪詢到
    // 收斂為止。期望值一律從模擬器自己的牆上時間取，而且每一圈都重取：
    // 輪詢期間可能跨過分鐘邊界，在迴圈外算一次會拿到過期的期望值。
    let wantStr, p, waited = 0;
    for (;;) {
      const t = new Date(env.wall());
      wantStr = p2(t.getUTCHours()) + p2(t.getUTCMinutes());
      p = env.peek();
      if (p.drawn === wantStr || waited >= SETTLE_MAX) break;
      env.advance(500); waited += 500;
    }
    const ok = p.drawn === wantStr;
    if (!ok) fails++;
    if (!ok || i < 3 || i === minutes - 1)
      console.log(`  ${ok ? 'PASS' : 'FAIL'}  第 ${i + 1} 分  期望 ${wantStr}  畫面 ${p.drawn}  殘留 run ${p.runs}  等了 ${waited} ms`);
  }
  console.log(`  ${minutes} 分鐘跑完，殘留 run ${env.peek().runs}`);
}

for (const target of targets) {
  html = fs.readFileSync(path.join(ROOT, target), 'utf8');
  console.log(`\n=== ${target} ===`);

  run('一般推進（橫式 1200x750）',
      { start: Date.UTC(2026, 6, 27, 2, 9, 0) }, 5);

  run('跨整點：09:58 起，三個數字同時變',
      { start: Date.UTC(2026, 6, 27, 9, 58, 0) }, 4);

  run('直式版面 420x900（跨午夜）',
      { start: Date.UTC(2026, 6, 27, 23, 58, 0), width: 420, height: 900 }, 4);

  if (!QUICK) run('連續二十分鐘', { start: Date.UTC(2026, 6, 27, 12, 0, 0) }, 20);
}

console.log(fails ? `\n${fails} 次沒過\n` : '\n全部通過\n');
process.exit(fails ? 1 : 0);
