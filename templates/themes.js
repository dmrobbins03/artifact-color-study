const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  const errs = [];
  p.on('pageerror', (e) => errs.push(e.message));
  await p.goto('file://' + process.cwd() + '/' + process.argv[2]);
  await p.evaluate(() => document.querySelectorAll('details.band').forEach((d) => (d.open = true)));
  await p.waitForTimeout(200);
  const sw = p.locator('.sw.wide').nth(1);
  await sw.scrollIntoViewIfNeeded();
  const st = () =>
    sw.evaluate((s) => {
      const c = s.querySelector('.c');
      return {
        vars: ['--cbg', '--cbd', '--cacc', '--ctx', '--cta'].map((v) =>
          c.style.getPropertyValue(v),
        ),
        bgChips: [...s.querySelectorAll('.chips button[data-k="cb"]')].map(
          (b) => (b.style.background.length ? b.title.split(' ').pop() : ''),
        ),
        reset: !s.querySelector('.reset').hidden,
        theme: s.querySelector('.srow[data-s="th"] small').textContent,
      };
    });
  const s0 = await st();
  console.log('default', JSON.stringify(s0));
  const n = await sw.locator('.chips button[data-k="th"]').count();
  for (let i = 0; i < n; i++) {
    await sw.locator('.chips button[data-k="th"]').nth(i).click();
    const s = await st();
    console.log(
      i,
      s.theme,
      s.vars.join(' '),
      '| bg steps:',
      s.bgChips.join(' '),
      '| reset',
      s.reset,
    );
    await sw.locator('.c').screenshot({ path: `kit/th${i}.png` });
  }
  await sw.locator('.chips button[data-k="cb"]').last().click();
  await sw.locator('.reset').click();
  const s9 = await st();
  console.log(
    'after reset matches default:',
    JSON.stringify(s9) === JSON.stringify(s0),
    errs.length ? errs : '',
  );
  await b.close();
})();
