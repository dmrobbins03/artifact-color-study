// Swatch study check.  node check.js page.html [--shot out.png [swatchIndex]]
// Prints a short pass/fail summary: page errors, click speed, chip fit at three widths, every interaction, copy behavior.
// --shot saves one small image of a single swatch (with an overlay showing) for a visual check; read it only when the look changed.
const { chromium } = require('playwright');
const path = require('path');
const [file, ...rest] = process.argv.slice(2);
const shotAt = rest.indexOf('--shot');
const shot = shotAt >= 0 ? rest[shotAt + 1] : null;
const shotIdx = shotAt >= 0 ? +(rest[shotAt + 2] || 1) : 1;
const url = 'file://' + path.resolve(file);
const out = [];
let fails = 0;
const ok = (cond, msg) => {
  if (!cond) fails++;
  out.push((cond ? 'ok   ' : 'FAIL ') + msg);
};
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({
    viewport: { width: 1280, height: 900 },
    deviceScaleFactor: 1,
  });
  const errs = [];
  p.on('pageerror', (e) => errs.push(e.message));
  // fonts are left to load (or fail) as they would for a viewer: the original slowdown only showed with fonts in play
  await p.goto(url);
  await p.waitForTimeout(300);
  // section rows live in the page-order accordions: open them all so every row can be measured and clicked
  await p.evaluate(() => document.querySelectorAll('details.band').forEach((d) => (d.open = true)));
  const n = await p.locator('.sw').count();
  ok(
    errs.length === 0,
    `page loads, ${n} swatches${errs.length ? ' — errors: ' + errs.join('; ') : ''}`,
  );
  // click speed: overlay, border and text chips on a mid-page swatch, layout forced each time
  const t = await p.evaluate(async () => {
    const sws = document.querySelectorAll('.sw'),
      sw = sws[Math.floor(sws.length / 2)];
    sw.scrollIntoView({ block: 'center' });
    await new Promise((r) => setTimeout(r, 100));
    document.body.offsetHeight;
    const ts = [];
    sw.querySelector('.ochips button')?.click();
    document.body.offsetHeight; // warm-up click, not timed
    for (const sel of [
      '.ochips button',
      '.bchips button',
      '.tchips button',
      '.cgrid button',
    ])
      for (const i of [2, 3]) {
        const el = sw.querySelectorAll(sel)[i];
        if (!el) continue;
        const t0 = performance.now();
        el.click();
        document.body.offsetHeight;
        ts.push(performance.now() - t0);
      }
    return ts;
  });
  const med = [...t].sort((a, b) => a - b)[t.length >> 1];
  ok(
    med < 25,
    `click → layout median ${Math.round(med)} ms, range ${Math.round(Math.min(...t))}–${Math.round(Math.max(...t))} (limit 25; the container-query layout measures 30+ here)`,
  );
  // interactions on one swatch with all three option sets
  const idx = await p.evaluate(() =>
    [...document.querySelectorAll('.sw')].findIndex(
      (s) =>
        s.querySelector('.ochips') &&
        s.querySelector('.tchips') &&
        s.querySelector('.opt[data-k="b"]'),
    ),
  );
  const sw = p.locator('.sw').nth(idx);
  await sw.scrollIntoViewIfNeeded();
  const st = () =>
    sw.evaluate((s) => {
      const c = s.querySelector('.c'),
        q = (x) => s.querySelector(x);
      return {
        tx2: getComputedStyle(q('.tx2')).visibility,
        strip: getComputedStyle(q('.ochips')).borderTopColor,
        edge: getComputedStyle(c).borderTopColor,
        reset: !q('.reset').hidden,
        // Selected colors by role (bg, bd, tx), not position: the details panel groups and reorders its rows
        sel: ['bg', 'bd', 'tx'].map(
          (k) => (s.querySelector(`.srow[data-s="${k}"] .bl span`) || {}).textContent,
        ),
        bg: c.style.background,
      };
    });
  const s0 = await st();
  ok(
    s0.tx2 === 'hidden' && !s0.reset,
    'initial: right text hidden, reset hidden',
  );
  ok(s0.strip === s0.edge, 'overlay strip outline matches the box border');
  await sw.locator('.ochips button').nth(1).click();
  const s1 = await st();
  ok(
    s1.reset && s1.bg !== s0.bg && !s1.bg.includes('gradient') && s1.sel[0] !== s0.sel[0],
    'background option: fills the whole preview (no split), reset, Selected colors',
  );
  await sw.evaluate((s) =>
    [...s.querySelectorAll('.opt[data-k="b"]')].at(-1).click(),
  );
  const s2 = await st();
  ok(
    s2.edge !== s0.edge && s2.strip === s2.edge && s2.sel[1] !== s0.sel[1],
    'border: edge, strip outline and Selected colors update',
  );
  await sw.locator('.tchips button').nth(2).click();
  const s3 = await st();
  ok(s3.sel[2] !== s0.sel[2], 'text: chip updates Selected colors');
  const xk = await sw.evaluate((s) =>
    [
      ...new Set(
        [...s.querySelectorAll('.chips button')].map((b) => b.dataset.k),
      ),
    ].filter((k) => !'bot'.includes(k) && s.querySelectorAll(`.chips button[data-k="${k}"]`).length > 1),   /* a list with one option has nothing to switch to */
  );
  for (const k of xk) {
    const before = await sw.evaluate(
      (s, k) => s.querySelector(`.srow[data-s="${k}"] .bl span`).textContent,
      k,
    );
    await sw.locator(`.chips button[data-k="${k}"]`).nth(1).click();
    const after = await sw.evaluate(
      (s, k) => ({
        row: s.querySelector(`.srow[data-s="${k}"] .bl span`).textContent,
        pressed: s
          .querySelectorAll(`.chips button[data-k="${k}"]`)[1]
          .getAttribute('aria-pressed'),
      }),
      k,
    );
    ok(
      after.row !== before || after.pressed === 'true',
      `option set ${k}: chip updates the preview and Selected colors`,
    );
  }
  await sw.locator('.ochips button').nth(1).click();
  const s4 = await st();
  ok(
    s4.bg === s0.bg,
    'same background option again restores the original',
  );
  await sw.locator('.reset').click();
  const s5 = await st();
  ok(
    !s5.reset &&
      JSON.stringify(s5.sel) === JSON.stringify(s0.sel) &&
      s5.edge === s0.edge,
    'reset restores recommended colors',
  );
  await sw.locator('.meta b .copy').click();
  await p.waitForTimeout(100);
  const selTxt = await p.evaluate(() => getSelection().toString());
  ok(selTxt === '', 'copy leaves no text selection');
  await p.evaluate(() => {
    const n = document.querySelector('.sw .meta b').firstChild,
      r = document.createRange();
    r.selectNodeContents(n);
    getSelection().removeAllRanges();
    getSelection().addRange(r);
  });
  await sw.locator('.ochips button').nth(3).click();
  const s6 = await st();
  ok(
    s6.bg !== s0.bg,
    'clicks still work with a leftover text selection',
  );
  const opened = await sw.locator('details.acc[open]').count();   // the Selected colors groups (details.sgrp) are open by default
  ok(opened === 0, 'accordions stay closed');
  // chip fit at three widths
  const fit = [];
  for (const w of [1280, 700, 380]) {
    await p.setViewportSize({ width: w, height: 900 });
    await p.waitForTimeout(150);
    fit.push(
      await p.evaluate((w) => {
        let bad = 0;
        for (const s of document.querySelectorAll('.sw .stage')) {
          const st = s.getBoundingClientRect(),
            c = s.querySelector('.c').getBoundingClientRect();
          if (
            [...s.querySelectorAll('.chips button')].some(
              (b) => b.getBoundingClientRect().right > st.right + 0.5,
            ) ||
            c.right > st.right + 0.5
          )
            bad++;
          for (const bar of s.querySelectorAll('.cbar, .cgrid')) {
            const r = bar.getBoundingClientRect();
            if (r.bottom > c.top + 0.5 && r.top < c.bottom - 0.5) bad++;
          }
        }
        return {
          w,
          bad,
          scroll: document.documentElement.scrollWidth > innerWidth,
        };
      }, w),
    );
  }
  ok(
    fit.every((f) => !f.bad && !f.scroll),
    'chips fit, no sideways scroll at ' +
      fit
        .map(
          (f) =>
            `${f.w}px${f.bad ? ` (${f.bad} overflow)` : ''}${f.scroll ? ' (h-scroll)' : ''}`,
        )
        .join(', '),
  );
  if (shot) {
    await p.setViewportSize({ width: 1280, height: 900 });
    const s = p.locator('.sw').nth(shotIdx);
    await s.scrollIntoViewIfNeeded();
    const o = s.locator('.ochips button');
    if (await o.count()) await o.last().click();
    await s.locator('.stage').screenshot({ path: shot });
    out.push(`shot ${shot} (swatch ${shotIdx}, overlay +1 step)`);
  }
  await b.close();
  console.log(
    out.join('\n') + `\n${fails ? fails + ' FAILED' : 'all checks passed'}`,
  );
  process.exit(fails ? 1 : 0);
})();
