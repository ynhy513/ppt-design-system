/* Print the complete static replay, one edge-to-edge 16:9 slide per PDF page. */
const { resolve } = require('node:path');
const { pathToFileURL } = require('node:url');

async function main() {
  const [input, output] = process.argv.slice(2);
  if (!input || !output) throw new Error('Usage: node export_pdf.cjs replay.html output.pdf');
  const { chromium } = require(process.env.REPLAY_PLAYWRIGHT_PACKAGE || 'playwright');
  const browser = await chromium.launch({ executablePath: process.env.REPLAY_CHROMIUM });
  try {
    const page = await browser.newPage({ offline: true, viewport: { width: 1280, height: 720 } });
    const url = pathToFileURL(resolve(input)).href;
    await page.route('**/*', route => {
      const target = route.request().url();
      return target === url || target.startsWith('data:') ? route.continue() : route.abort();
    });
    await page.goto(url);
    await page.addStyleTag({ content: `
      @page { size: 960pt 540pt; margin: 0; }
      html,body { margin: 0; background: white; print-color-adjust: exact; -webkit-print-color-adjust: exact; }
      main > article { width: 960pt; height: 540pt; margin: 0; break-inside: avoid; break-after: page; }
      main > article:last-child { break-after: auto; }
    ` });
    await page.emulateMedia({ media: 'print' });
    await page.evaluate(async () => {
      if (!document.querySelector('main > article')) throw new Error('Replay contains no slides');
      await Promise.all([document.fonts.ready, ...[...document.images].map(image => image.decode())]);
    });
    await page.pdf({ path: resolve(output), printBackground: true, preferCSSPageSize: true });
  } finally {
    await browser.close();
  }
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
