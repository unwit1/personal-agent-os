// Browser end-to-end for the Shopping tab. Real executive window + real adapter + real Shopping CLI (demo stores).
// Usage: node shopping_ui.e2e.js <shopping.py> <outDir>      (needs INGESTER_ENGINE_ROOT for the window process)
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const [shoppingPy, outDir] = process.argv.slice(2);
let PORT = 0;
const live = new Set();
process.on('exit', () => { for (const p of live) { try { p.kill('SIGKILL'); } catch (e) { /* gone */ } } });
const home = fs.mkdtempSync(path.join(os.tmpdir(), 'shop-e2e-'));
console.log('HOME', home);
const log = [];
const ok = (name, cond, extra) => { log.push({ name, pass: !!cond, extra: extra || '' }); console.log((cond ? 'PASS ' : 'FAIL ') + name + (extra ? ' - ' + extra : '')); };

function startServer(env) {
  return new Promise((resolve, reject) => {
    const p = spawn('python3', [path.join(__dirname, 'serve_for_e2e.py'), '0'], { env: { ...process.env, ...env } });
    let buf = '';
    live.add(p);
    p.stdout.on('data', d => { buf += d; const m = buf.match(/READY (\d+)/); if (m) { PORT = Number(m[1]); resolve(p); } });
    p.stderr.on('data', d => { buf += d; });
    p.on('exit', c => { if (!buf.includes('READY')) reject(new Error('server exited ' + c + ': ' + buf)); });
  });
}
const stop = p => new Promise(r => { live.delete(p); p.on('exit', r); p.kill('SIGTERM'); setTimeout(r, 3000); });

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const env = { AGENT_SHOPPING_HOME: home, AGENT_SHOPPING_CMD: `python3 ${shoppingPy} --demo-stores` };
  let server = await startServer(env);
  const browser = await chromium.launch();
  let page = await (await browser.newContext({ viewport: { width: 1400, height: 900 } })).newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  const shot = n => page.screenshot({ path: path.join(outDir, n + '.png') });
  const url = () => `http://127.0.0.1:${PORT}/#shopping`;

  // 1-2. open Command Center, open Shopping, empty state
  await page.goto(url());
  await page.getByRole('button', { name: 'Overview' }).waitFor();
  await page.waitForSelector('.sp-banner');
  ok('Shopping tab opens from #shopping', await page.locator('#shopping-tab.on').count() === 1);
  ok('Overview shows DEMO DATA label', (await page.locator('.sp-banner').innerText()).includes('DEMO DATA'));
  ok('Overview says live purchasing off', (await page.locator('.sp-banner').innerText()).includes('you check out manually'));
  await shot('01-overview-empty');

  // 3-5. research, inspect results and sources
  await page.getByRole('button', { name: 'Research & Add' }).click();
  await page.fill('#sp-text', 'Sonix WH-100 headphones, black, under $140');
  await page.getByRole('button', { name: 'Research', exact: true }).click();
  await page.waitForSelector('.sp-option', { timeout: 60000 });
  const optionText = await page.locator('#sp-research-out').innerText();
  ok('Research results appear with options', await page.locator('.sp-option').count() >= 2);
  ok('Fixture options are labelled DEMO DATA', optionText.includes('DEMO DATA'));
  ok('Options show delivered cost and source', /delivered \$/.test(optionText) && optionText.includes('via demo-'));
  ok('Option explains why', optionText.includes('Lowest delivered price') || optionText.includes('Meets'));
  await shot('02-research-results');

  // 6. save a product
  await page.locator('.sp-option button', { hasText: 'Save to wishlist' }).first().click();
  await page.waitForSelector('.sp-okmsg');
  ok('Save to wishlist confirmed', (await page.locator('.sp-notice').innerText()).includes('Saved'));

  // add exact item with target + variant via form
  await page.fill('#sp-f-description', 'Sonix WH-100 headphones');
  await page.fill('#sp-f-target', '150'); await page.fill('#sp-f-max', '200'); await page.fill('#sp-f-variant', 'color=black');
  await page.getByRole('button', { name: 'Add to wishlist' }).click();
  await page.waitForSelector('.sp-table');
  ok('Wishlist lists both items', await page.locator('.sp-table tbody tr').count() >= 2);

  // 7-8. watch + deal assessment
  const exactRow = () => page.locator('.sp-table tbody tr', { has: page.locator('strong', { hasText: /^Sonix WH-100 headphones$/ }) });
  const row = exactRow();
  await row.getByRole('button', { name: 'Search now' }).click();
  await page.waitForSelector('.sp-okmsg');
  await page.waitForSelector('.sp-table');
  // New wants are watched by default; the button must reflect that, and toggling must round-trip.
  ok('Watch state is shown (watched by default)', await exactRow().getByRole('button', { name: 'Pause watch' }).count() === 1);
  await exactRow().getByRole('button', { name: 'Pause watch' }).click();
  await exactRow().getByRole('button', { name: 'Watch', exact: true }).waitFor();
  ok('Pausing a watch is reflected', true);
  await exactRow().getByRole('button', { name: 'Watch', exact: true }).click();
  await exactRow().getByRole('button', { name: 'Pause watch' }).waitFor();
  ok('Resuming a watch is reflected', true);
  await page.getByRole('button', { name: 'Run watcher now' }).click();
  await page.waitForSelector('.sp-okmsg');
  await page.getByRole('button', { name: 'Deals' }).click();
  await page.waitForSelector('.sp-list li');
  const deals = await page.locator('.sp-list').innerText();
  ok('Deals show an assessed opportunity with evidence + source', /Quality/.test(deals) && /Sources:/.test(deals));
  await shot('03-deals');

  // price history
  await page.getByRole('button', { name: 'Wishlist' }).click();
  await page.waitForSelector('.sp-table');
  await exactRow().getByRole('button', { name: 'Price history' }).click();
  await page.waitForSelector('#sp-history h3');
  console.log('HISTORY:', (await page.locator('#sp-history').innerText()).slice(0, 400));
  ok('Price history shows observations', /\d+ observation\(s\)/.test(await page.locator('#sp-history').innerText()));

  // 9. manual checkout handoff
  await exactRow().locator('input[type=checkbox]').check();
  await page.getByRole('button', { name: 'Build cart from selected' }).click();
  await page.getByRole('button', { name: /Build cart \(1/ }).click();
  await page.waitForSelector('text=Manual checkout', { timeout: 60000 }).catch(async e => { console.log('NOTICE:', await page.locator('.sp-body, .sp-notice').allInnerTexts()); throw e; });
  const cart = await page.locator('.sp-body').innerText();
  ok('Handoff says nothing is bought', cart.includes('Nothing has been purchased'));
  ok('Handoff has retailer link opening in new tab safely', await page.locator('.sp-body a[rel="noopener noreferrer"][target=_blank]').count() >= 1);
  ok('Handoff marks demo link', cart.includes('DEMO'));
  await shot('04-checkout-handoff');

  // order record
  await page.getByRole('button', { name: 'Orders' }).click();
  const labels = page.locator('.sp-form label');
  await labels.nth(0).locator('input').fill('demo-alphamart');
  await labels.nth(1).locator('input').fill('Sonix WH-100');
  await labels.nth(2).locator('input').fill('129.00');
  await page.getByRole('button', { name: 'Record order' }).click();
  await page.waitForSelector('.sp-list li');
  ok('Order recorded and listed', (await page.locator('.sp-list').innerText()).includes('demo-alphamart'));

  // 10-11. restart everything, reopen
  await browser.close(); await stop(server);
  server = await startServer(env);
  const browser2 = await chromium.launch();
  page = await (await browser2.newContext({ viewport: { width: 1400, height: 900 } })).newPage();
  await page.goto(url());
  await page.getByRole('button', { name: 'Wishlist' }).click();
  await page.waitForSelector('.sp-table', { timeout: 30000 }).catch(async () => console.log('BODY:', await page.locator('#shopping-tab').innerText()));
  ok('Wishlist survives restart', await page.locator('.sp-table tbody tr').count() >= 2);
  await page.getByRole('button', { name: 'Orders' }).click();
  await page.waitForSelector('.sp-list li');
  ok('Order survives restart', (await page.locator('.sp-list').innerText()).includes('demo-alphamart'));
  await page.getByRole('button', { name: 'Deals' }).click();
  await page.waitForSelector('.sp-list li');
  ok('Opportunities survive restart', await page.locator('.sp-list li').count() >= 1);
  await page.getByRole('button', { name: 'Diagnostics' }).click();
  await page.waitForSelector('.sp-table');
  ok('Diagnostics lists sources flagged DEMO', (await page.locator('.sp-body').innerText()).includes('DEMO'));
  await shot('05-diagnostics-after-restart');

  // keyboard: nav buttons reachable by Tab, and responsive 360px width
  await page.setViewportSize({ width: 360, height: 800 });
  await page.getByRole('button', { name: 'Wishlist' }).click();
  await page.waitForSelector('.sp-table');
  const overflow = await page.evaluate(() => document.getElementById('shopping-tab').scrollWidth - document.getElementById('shopping-tab').clientWidth);
  ok('No horizontal overflow at 360px', overflow <= 4, 'overflow=' + overflow);
  await shot('06-mobile-wishlist');
  await page.setViewportSize({ width: 1400, height: 900 });
  await page.keyboard.press('Tab');
  ok('Keyboard focus lands on an interactive element', await page.evaluate(() => !!document.activeElement && document.activeElement !== document.body));
  await browser2.close(); await stop(server);

  // G. source failure / not installed: broken command
  server = await startServer({ AGENT_SHOPPING_HOME: home, AGENT_SHOPPING_CMD: '/nonexistent/agent-shopping' });
  const browser3 = await chromium.launch();
  page = await (await browser3.newContext()).newPage();
  await page.goto(url());
  await page.waitForSelector('.sp-banner');
  const bad = await page.locator('.sp-banner').innerText();
  ok('Missing Shopping install shows a clear error + fix', bad.includes('not connected') && /install|Start-Shopping/i.test(bad), bad.replace(/\n/g, ' ').slice(0, 160));
  await shot('07-not-installed');
  await browser3.close(); await stop(server);

  ok('No uncaught page errors', errors.length === 0, errors.join(' | '));
  fs.writeFileSync(path.join(outDir, 'e2e-results.json'), JSON.stringify(log, null, 2));
  const failed = log.filter(x => !x.pass);
  console.log(`\n${log.length - failed.length}/${log.length} checks passed`);
  process.exit(failed.length ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
