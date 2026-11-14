/* Validate reviewed layers in the browser, including automatic line wrapping. */
const { readFileSync } = require('node:fs');
const { dirname, resolve } = require('node:path');

function readOptionalReport(input, name) {
  try {
    return JSON.parse(readFileSync(resolve(dirname(resolve(input)), name), 'utf8'));
  } catch (error) {
    if (error.code === 'ENOENT') return {};
    throw error;
  }
}

async function checkRenderedInheritance(pages, inheritance) {
  if (!Object.keys(inheritance).length) return [];
  return pages.evaluateAll((slides, inheritance) => {
    const issues = [];
    for (const slide of slides) {
      const review = inheritance[slide.dataset.pattern];
      if (review?.background) {
        const channels = review.background.slice(1).match(/../g).map(value => parseInt(value, 16));
        const expected = `rgb(${channels.join(', ')})`;
        const actual = getComputedStyle(slide).backgroundColor;
        if (actual !== expected) issues.push(`${slide.id}: expected background ${review.background}, got ${actual}`);
      }
      const bindings = review?.layers || {};
      for (const [name, binding] of Object.entries(bindings)) {
        if (!('lines' in binding)) continue;
        const target = binding.target || name;
        const layer = slide.querySelector(`:scope > .text[data-layer="${target}"]`);
        if (!layer) {
          issues.push(`${slide.id}/${target}: reviewed text layer is missing`);
          continue;
        }
        const transform = layer.style.transform;
        let count;
        try {
          layer.style.transform = 'none';
          const span = layer.querySelector('span');
          const range = document.createRange();
          range.selectNodeContents(span);
          const centers = [...range.getClientRects()].filter(rect => rect.width > 0)
            .map(rect => rect.top + rect.height / 2).sort((a, b) => a - b);
          const tolerance = parseFloat(getComputedStyle(span).lineHeight) / 2;
          count = 0;
          let previous = -Infinity;
          for (const center of centers) {
            if (center - previous < tolerance) continue;
            count++;
            previous = center;
          }
        } finally {
          layer.style.transform = transform;
        }
        if (count !== binding.lines) {
          issues.push(`${slide.id}/${target}: expected ${binding.lines} rendered lines, got ${count}`);
        }
      }
    }
    return issues;
  }, inheritance);
}

module.exports = { checkRenderedInheritance, readOptionalReport };
