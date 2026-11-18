// Headless screenshots of viewer/index.html for verification.
// usage: node scripts/screens.mjs <out-dir> <pmtiles-url-relative-to-viewer> <name>@<zoom>/<lat>/<lon> ...
// Env: VIEWER (default viewer/, e.g. viewer/country.html), VW/VH viewport px (default 1200x800).
// Needs scripts/serve.py running on :8000. CDN URLs are routed to the npm-packed copies in data/vendor
// (the container cannot reach unpkg); versions must match viewer/index.html.
import { createRequire } from 'node:module';
import { readFileSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const { chromium } = createRequire(import.meta.url)('playwright');
const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const [outDir, tiles, ...views] = process.argv.slice(2);
mkdirSync(outDir, { recursive: true });
const vendor = join(root, 'data/vendor');
const pkgDir = nameVersion => join(vendor, nameVersion, 'package/dist'); // npm pack + tar -x layout

const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: +(process.env.VW || 1200), height: +(process.env.VH || 800) }, deviceScaleFactor: 1 });
await page.route('https://unpkg.com/**', route => {
  const u = new URL(route.request().url());
  const m = u.pathname.match(/^\/(maplibre-gl|pmtiles)@([^/]+)\/dist\/(.+)$/);
  const body = readFileSync(join(pkgDir(`${m[1]}-${m[2]}`), m[3]));
  route.fulfill({ body, contentType: m[3].endsWith('.css') ? 'text/css' : 'application/javascript' });
});
page.on('pageerror', e => console.error('pageerror', e.message));
for (const v of views) {
  const [name, pos] = v.split('@');
  await page.goto(`http://127.0.0.1:8000/${process.env.VIEWER || 'viewer/'}?pmtiles=${encodeURIComponent(tiles)}#${pos}`);
  await page.waitForFunction(() => document.getElementById('hud').textContent.startsWith('z'), null, { timeout: 30000 });
  // Wait until tiles are loaded and rendered; never hang (idle may already have fired).
  await page.evaluate(() => new Promise(r => {
    const m = window.__map, t0 = Date.now();
    const tick = () => (m.loaded() && m.areTilesLoaded()) || Date.now() - t0 > 60000 ? r() : setTimeout(tick, 250);
    tick();
  }));
  await page.waitForTimeout(1500);
  const file = join(outDir, `${name}.png`);
  await page.screenshot({ path: file });
  console.log(file, await page.evaluate(() => document.getElementById('hud').textContent));
}
await browser.close();
