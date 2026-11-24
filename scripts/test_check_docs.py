import tempfile
import unittest
from pathlib import Path

from check_docs import check


class DocumentationLinksTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.write("README.md", "# Home\n[Guide](ppt-design-system/references/guide.en.md#usage)")
        self.write("ppt-design-system/references/guide.md",
                   "# 指南\n[English](guide.en.md)\n## 用法")
        self.write("ppt-design-system/references/guide.en.md",
                   "# Guide\n[简体中文](guide.md)\n## Usage")

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def test_valid_pair_and_explicit_language_switch(self):
        self.assertEqual(check(self.root)[0], [])

    def test_invalid_repository_does_not_report_success(self):
        self.assertTrue(check(self.root / "missing")[0])

    def test_missing_file(self):
        self.write("README.md", "# Home\n[Guide](missing.en.md)")
        self.assertTrue(any("missing.en.md" in x for x in check(self.root)[0]))

    def test_missing_anchor(self):
        self.write("README.md", "# Home\n[Guide](ppt-design-system/references/guide.en.md#absent)")
        self.assertTrue(any("#absent" in x for x in check(self.root)[0]))

    def test_nested_english_page_cannot_fall_back_to_chinese(self):
        self.write("ppt-design-system/references/guide.en.md",
                   "# Guide\n[简体中文](guide.md)\n## Usage\n[Details](guide.md#用法)")
        self.assertTrue(any("English link targets Chinese" in x for x in check(self.root)[0]))

    def test_new_chinese_reference_needs_translation(self):
        self.write("ppt-design-system/references/new.md", "# 新说明")
        self.assertTrue(any("missing English counterpart" in x for x in check(self.root)[0]))

    def test_pair_needs_return_language_link(self):
        self.write("ppt-design-system/references/guide.md", "# 指南\n## 用法")
        self.assertTrue(any("reciprocal" in x for x in check(self.root)[0]))

    def test_code_examples_are_not_live_links(self):
        self.write("README.md", "# Home\n```md\n[Example](not-real.md)\n```")
        self.assertEqual(check(self.root)[0], [])

    def test_duplicate_heading_anchor(self):
        self.write("README.md", "# Home\n## Usage\n## Usage\n[Second](#usage-1)")
        self.assertEqual(check(self.root)[0], [])


if __name__ == "__main__":
    unittest.main()
