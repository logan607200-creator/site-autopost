// 폭 390, 1280 에서 가로 스크롤이 생기는지 잰다. 인자: playwright index.mjs 경로, html 경로
const [, , pwPath, html] = process.argv;
const { chromium } = await import(pwPath);
const b = await chromium.launch();
const out = {};
for (const w of [390, 1280]) {
  const p = await b.newPage({ viewport: { width: w, height: 900 } });
  await p.goto('file://' + html);
  await p.waitForTimeout(400);
  out['w' + w] = await p.evaluate(() => ({ scrollWidth: document.documentElement.scrollWidth, innerWidth: window.innerWidth }));
  await p.close();
}
await b.close();
console.log(JSON.stringify(out));
