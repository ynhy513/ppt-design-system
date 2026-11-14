const assert = require('node:assert/strict');
const { execFile } = require('node:child_process');
const { mkdtemp, readFile, rm, writeFile } = require('node:fs/promises');
const { tmpdir } = require('node:os');
const { join } = require('node:path');
const { test } = require('node:test');
const { promisify } = require('node:util');

const run = promisify(execFile);

test('PDF export rejects extra rendered lines under review and allows corrected text', async () => {
  const folder = await mkdtemp(join(tmpdir(), 'deck-pdf-'));
  const input = join(folder, 'replay.html');
  const output = join(folder, 'deck.pdf');
  const exportPdf = () => run(process.execPath, [join(__dirname, 'export_pdf.cjs'), input, output]);
  const writeSlide = title => writeFile(input, `<!doctype html><meta charset="utf-8">
    <style>.text { width: 130px; font: 20px/24px monospace; white-space: pre-wrap; }</style>
    <main><article id="cover" data-pattern="cover" style="background:#E8ECE7">
    <div class="text" data-layer="title"><span>${title}</span></div>
    </article></main>`);
  try {
    await writeSlide('Book Desk\nDepartment of Information and Document Services');
    await writeFile(join(folder, 'inheritance-report.json'), JSON.stringify({
      cover: { background: '#E8ECE7', layers: { title: { lines: 2 } } },
    }));
    await assert.rejects(exportPdf, error => {
      assert.equal(error.code, 2);
      assert.match(error.stderr, /cover\/title: expected 2 rendered lines, got [3-9]/);
      return true;
    });
    await assert.rejects(readFile(output), { code: 'ENOENT' });

    await writeSlide('Book Desk\nOpen Daily');
    await exportPdf();
    assert.equal((await readFile(output)).subarray(0, 5).toString(), '%PDF-');
  } finally {
    await rm(folder, { recursive: true, force: true });
  }
});
