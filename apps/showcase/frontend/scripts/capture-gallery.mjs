// Full page screenshots of the design system gallery with real device emulation (Chrome DevTools
// Protocol, no extra dependencies). Needs a local Chrome or Edge and a running showcase.
//
//   node apps/showcase/frontend/scripts/capture-gallery.mjs http://127.0.0.1:8080 apps/showcase/docs/gallery
//
// Writes one PNG per entry in SHOTS.
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const base = process.argv[2] ?? "http://127.0.0.1:8080";
const outDir = process.argv[3] ?? "gallery-shots";
const SHOTS = [
  { file: "gallery-390-finhub-light.png", route: "finhub/light", width: 390, mobile: true },
  { file: "gallery-390-finhub-dark.png", route: "finhub/dark", width: 390, mobile: true },
  { file: "gallery-390-klassesall-light.png", route: "klassesall/light", width: 390, mobile: true },
  { file: "gallery-desktop-finhub-light.png", route: "finhub/light", width: 1440, mobile: false },
  { file: "gallery-desktop-finhub-dark.png", route: "finhub/dark", width: 1440, mobile: false },
  { file: "gallery-desktop-predictiveeconomics-light.png", route: "predictiveeconomics/light", width: 1440, mobile: false },
];

const browsers = [
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "/usr/bin/google-chrome",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
];
const exe = browsers.find((p) => existsSync(p));
if (!exe) throw new Error("No Chrome or Edge found");

const port = 9300 + Math.floor(Math.random() * 500);
const profile = mkdtempSync(join(tmpdir(), "nx-capture-"));
const browser = spawn(exe, [`--remote-debugging-port=${port}`, "--headless=new", "--disable-gpu", "--no-first-run", "--hide-scrollbars", `--user-data-dir=${profile}`, "about:blank"], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function json(path, method = "GET") {
  for (let i = 0; i < 50; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${port}${path}`, { method });
      if (res.ok) return res.json();
    } catch {
      /* browser still starting */
    }
    await sleep(200);
  }
  throw new Error(`DevTools endpoint ${path} did not answer`);
}

function connect(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let id = 0;
  const pending = new Map();
  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id)(msg);
      pending.delete(msg.id);
    }
  };
  const send = (method, params = {}) =>
    new Promise((resolve, reject) => {
      const mid = ++id;
      pending.set(mid, (msg) => (msg.error ? reject(new Error(msg.error.message)) : resolve(msg.result)));
      ws.send(JSON.stringify({ id: mid, method, params }));
    });
  return new Promise((resolve) => (ws.onopen = () => resolve({ send, close: () => ws.close() })));
}

try {
  mkdirSync(outDir, { recursive: true });
  const target = await json("/json/new?about:blank", "PUT");
  const page = await connect(target.webSocketDebuggerUrl);
  await page.send("Page.enable");
  for (const shot of SHOTS) {
    await page.send("Emulation.setDeviceMetricsOverride", {
      width: shot.width,
      height: shot.mobile ? 844 : 900,
      deviceScaleFactor: 1,
      mobile: shot.mobile,
    });
    await page.send("Page.navigate", { url: `${base}/#gallery/${shot.route}` });
    await sleep(2500);
    const { result } = await page.send("Runtime.evaluate", {
      expression: "JSON.stringify([document.documentElement.scrollWidth, document.documentElement.scrollHeight])",
      returnByValue: true,
    });
    const [scrollWidth, height] = JSON.parse(result.value);
    if (scrollWidth > shot.width) console.warn(`${shot.file}: page is ${scrollWidth}px wide at ${shot.width}px (horizontal overflow)`);
    const { data } = await page.send("Page.captureScreenshot", {
      format: "png",
      captureBeyondViewport: true,
      clip: { x: 0, y: 0, width: shot.width, height, scale: 1 },
    });
    writeFileSync(join(outDir, shot.file), Buffer.from(data, "base64"));
    console.log(`${shot.file}: ${shot.width}x${height}, scroll width ${scrollWidth}`);
  }
  page.close();
} finally {
  browser.kill();
}
