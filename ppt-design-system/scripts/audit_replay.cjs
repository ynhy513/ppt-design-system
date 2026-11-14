/* Check actual Chromium output without loading the network or writing screenshots. */
const { createHash } = require('node:crypto');
const { resolve } = require('node:path');
const { pathToFileURL } = require('node:url');
const { checkRenderedInheritance, readOptionalReport } = require('./replay_inheritance.cjs');

function readFixedAssetRequirements(input) {
  const receipt = readOptionalReport(input, 'receipt.json');
  return (receipt.pages || []).flatMap(page => (page.required_fixed_assets || []).map(asset => ({
    ...asset, page: page.id,
  })));
}

async function checkFixedAssets(page, requirements) {
  const issues = [];
  for (const expected of requirements) {
    const images = page.locator(`main > article[id="${expected.page}"] > img[data-layer="${expected.layer}"]`);
    const source = await images.evaluateAll(matches => {
      if (matches.length !== 1) return null;
      const [image] = matches;
      const rect = image.getBoundingClientRect();
      const slide = image.parentElement.getBoundingClientRect();
      const style = getComputedStyle(image);
      const intersectsSlide = rect.left < slide.right && rect.right > slide.left &&
        rect.top < slide.bottom && rect.bottom > slide.top;
      return image.complete && image.naturalWidth && rect.width && rect.height && intersectsSlide &&
        style.visibility === 'visible' && Number(style.opacity) > 0 ? image.currentSrc : null;
    });
    const label = `${expected.page}/${expected.layer} (${expected.asset}) — ${expected.purpose}`;
    const bytes = source?.match(/^data:image\/(?:png|jpeg|webp);base64,(.+)$/)?.[1];
    if (!bytes) {
      issues.push(`${label}: required fixed asset is missing or invisible`);
    } else if (createHash('sha256').update(Buffer.from(bytes, 'base64')).digest('hex') !== expected.sha256) {
      issues.push(`${label}: required fixed asset bytes do not match`);
    }
  }
  return issues;
}

async function main() {
  const input = process.argv[2];
  if (!input || process.argv.length !== 3) {
    throw new Error('Usage: node audit_replay.cjs /path/to/replay.html');
  }
  const requiredAssets = readFixedAssetRequirements(input);
  const inheritance = readOptionalReport(input, 'inheritance-report.json');
  const { chromium } = require(process.env.REPLAY_PLAYWRIGHT_PACKAGE || 'playwright');
  const browser = await chromium.launch({
    executablePath: process.env.REPLAY_CHROMIUM,
  });
  try {
    const page = await browser.newPage({ offline: true, deviceScaleFactor: 1 });
    const checks = [];
    const errors = [];
    await page.route('**/*', route => /^file:|^data:/.test(route.request().url())
      ? route.continue() : route.abort());
    page.on('pageerror', error => errors.push(error.message));
    for (const width of [1200, 390]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(pathToFileURL(resolve(input)).href);
      await page.evaluate(() => document.fonts.ready);
      const pages = page.locator('main > article');
      if (await pages.count() === 0) throw new Error('No replay pages found');
      const issues = await pages.evaluateAll(slides => {
        const issues = [];
        const outside = (child, outer) => child.left < outer.left - 1 ||
          child.right > outer.right + 1 || child.top < outer.top - 1 || child.bottom > outer.bottom + 1;
        for (const slide of slides) {
          const glyphs = [];
          for (const text of slide.querySelectorAll('.text')) {
            const span = text.querySelector('span');
            const range = document.createRange();
            range.selectNodeContents(span);
            const lines = [...range.getClientRects()];
            const name = text.closest('.motif')
              ? `${text.closest('.motif').dataset.layer}/${text.dataset.layer}`
              : text.dataset.layer;
            if (lines.some(line => outside(line, text.getBoundingClientRect()))) {
              issues.push(`${slide.id}/${name}: text exceeds its slot`);
            }
            for (const { name: other, lines: otherLines } of glyphs) {
              const overlaps = lines.some(a => otherLines.some(b =>
                Math.min(a.right, b.right) - Math.max(a.left, b.left) > 1 &&
                Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 1));
              if (overlaps) issues.push(`${slide.id}: ${name} collides with ${other}`);
            }
            glyphs.push({ name, lines });
          }
          for (const image of slide.querySelectorAll('img')) {
            if (!image.complete || image.naturalWidth === 0) {
              issues.push(`${slide.id}/${image.dataset.layer}: image failed to load`);
            }
          }
          for (const layer of slide.querySelectorAll('[data-layer]')) {
            if (layer.style.transform && outside(layer.getBoundingClientRect(), slide.getBoundingClientRect())) {
              issues.push(`${slide.id}/${layer.dataset.layer}: transformed layer exceeds the canvas`);
            }
          }
          for (const vector of slide.querySelectorAll('svg.vector')) {
            const matrix = vector.getScreenCTM();
            const origin = new DOMPoint(0, 0).matrixTransform(matrix);
            const end = new DOMPoint(1600, 900).matrixTransform(matrix);
            const box = vector.getBoundingClientRect();
            if (Math.max(Math.abs(origin.x - box.left), Math.abs(origin.y - box.top),
                         Math.abs(end.x - box.right), Math.abs(end.y - box.bottom)) > 1) {
              issues.push(`${slide.id}/${vector.dataset.layer}: vector and slot coordinates diverge`);
            }
          }
        }
        if (document.documentElement.scrollWidth > window.innerWidth) issues.push('Horizontal page overflow');
        return issues;
      });
      issues.push(...await checkRenderedInheritance(pages, inheritance));
      issues.push(...await checkFixedAssets(page, requiredAssets));
      const screenshots = {};
      if (!issues.length && width === 1200) {
        for (const slide of await pages.all()) {
          const id = await slide.getAttribute('id');
          const png = await slide.screenshot({ animations: 'disabled' });
          screenshots[id] = createHash('sha256').update(png).digest('hex');
        }
      }
      checks.push({ width, pages: await pages.count(), requiredFixedAssetChecks: requiredAssets.length, issues, screenshots });
    }
    const passed = errors.length === 0 && checks.every(check => check.issues.length === 0);
    console.log(JSON.stringify({ passed, browser: browser.version(), errors, checks }, null, 2));
    if (!passed) process.exitCode = 2;
  } finally {
    await browser.close();
  }
}

main().catch(error => {
  console.error(error.message);
  process.exitCode = 2;
});
