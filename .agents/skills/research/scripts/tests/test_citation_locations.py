"""Citation declarations must resolve to actual uses within their section."""

from pathlib import Path
import unittest
from urllib.parse import quote

import test_task_workflow as fixtures
import test_article_dependencies as article_fixtures
from test_task_workflow import context, task, reports
import research_articles as articles


URL = article_fixtures.URL


class CitationLocations(unittest.TestCase):
    setUp = fixtures.TaskWorkflow.setUp
    create = fixtures.TaskWorkflow.create
    populate = fixtures.TaskWorkflow.populate
    imported = article_fixtures.ArticleDependencies.imported

    def prepare(self, body):
        path, outline, key, _ = self.imported()
        report = Path(outline["output_dir"]) / "report.md"
        report.write_text("# 报告\n\n" + body, encoding="utf-8")
        return path, outline, key, report

    def deliver(self, path, report, body):
        note = context.render_report_note(context.report_context(path / "outline.json"))
        report.write_text("# 报告\n\n" + note + "\n" + body + "\n\n[边界依据](https://example.org/original)\n", encoding="utf-8")
        return reports.validate(report.parent, path / "outline.json")

    def test_archive_rejects_wrong_section_before_writing_anything(self):
        path, outline, key, report = self.prepare(f"## 章节 A\n无引用。\n\n## 章节 B\n[依据]({URL})\n")
        before = (path / "articles.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "declared section"):
            articles.archive(outline, key, ["report.md#章节-a"])
        self.assertEqual((path / "articles.json").read_bytes(), before)
        self.assertFalse((report.parent / "references").exists())
        saved = articles.archive(outline, key, ["report.md#章节-b"])
        checked = self.deliver(path, report, f"## 章节 A\n无引用。\n\n## 章节 B\n[原文]({saved['path']})\n")
        self.assertTrue(checked["valid"], checked)

    def test_verify_detects_link_moved_outside_declared_section(self):
        path, outline, key, report = self.prepare(f"## 分析\n[依据]({URL})\n\n## 附录\n")
        saved = articles.archive(outline, key, ["report.md#分析"])
        checked = self.deliver(path, report, f"## 分析\n原章节的链接已移走。\n\n## 附录\n[原文]({saved['path']})\n")
        self.assertFalse(checked["valid"])
        self.assertTrue(any("report.md#分析" in error and "declared section" in error for error in checked["errors"]))
        with self.assertRaisesRegex(ValueError, "declared section"):
            task.verify_task(path)

    def test_parent_includes_children_but_child_excludes_siblings(self):
        _, outline, key, _ = self.prepare(f"## 方法\n### 实现\n[依据]({URL})\n### 局限\n无引用。\n## 实验\n无引用。\n")
        articles.archive(outline, key, ["report.md#方法", "report.md#实现"])
        for anchor in ("局限", "实验"):
            with self.subTest(anchor=anchor), self.assertRaises(ValueError):
                articles.archive(outline, key, ["report.md#" + anchor])

    def test_duplicate_and_percent_encoded_anchors_resolve_to_exact_occurrence(self):
        _, outline, key, _ = self.prepare(f"## 分析\n无引用。\n## 分析\n[依据]({URL})\n")
        with self.assertRaises(ValueError):
            articles.archive(outline, key, ["report.md#分析"])
        articles.archive(outline, key, ["report.md#" + quote("分析-1")])

    def test_each_declared_citation_is_required_even_when_another_is_correct(self):
        path, outline, key, report = self.prepare(f"## 正确\n[依据]({URL})\n## 错误\n无引用。\n")
        before = (path / "articles.json").read_bytes()
        with self.assertRaises(ValueError):
            articles.archive(outline, key, ["report.md#正确", "report.md#错误"])
        self.assertEqual((path / "articles.json").read_bytes(), before)
        saved = articles.archive(outline, key, ["report.md#正确"])
        manifest = articles.load_manifest(outline)
        manifest["articles"][key]["archive"]["citations"].append("report.md#错误")
        articles.save_manifest(outline, manifest)
        checked = self.deliver(path, report, f"## 正确\n[原文]({saved['path']})\n## 错误\n无引用。\n")
        self.assertFalse(checked["valid"])
        self.assertTrue(any("report.md#错误" in error for error in checked["errors"]))

    def test_reference_definition_outside_section_resolves_at_the_use(self):
        path, outline, key, report = self.prepare(f"## 方法\n参见[依据][source]。\n## 附录\n[source]: {URL}\n")
        saved = articles.archive(outline, key, ["report.md#方法"])
        checked = self.deliver(path, report, f"## 方法\n参见[依据][source]。\n## 附录\n[source]: {saved['path']}\n")
        self.assertTrue(checked["valid"], checked)
        with self.assertRaises(ValueError):
            articles.archive(outline, key, ["report.md#附录"])

    def test_footnote_citation_belongs_to_call_site_not_definition_section(self):
        path, outline, key, report = self.prepare(f"## 方法\n证据见[^来源]。\n## 附录\n[^来源]: 适用条件见下文。\n    [原文]({URL})\n")
        saved = articles.archive(outline, key, ["report.md#方法"])
        checked = self.deliver(path, report, f"## 方法\n证据见[^来源]。\n## 附录\n[^来源]: 适用条件见下文。\n    [原文]({saved['path']})\n")
        self.assertTrue(checked["valid"], checked)
        with self.assertRaises(ValueError):
            articles.archive(outline, key, ["report.md#附录"])

    def test_unreferenced_and_escaped_footnotes_do_not_supply_citations(self):
        for call in ("无引用。", r"示例 \[^来源]", "`[^来源]`", "![^来源]"):
            with self.subTest(call=call):
                _, outline, key, _ = self.prepare(f"## 方法\n{call}\n## 附录\n[^来源]: [原文]({URL})\n")
                for citation in ("report.md#方法", "report.md#附录", "report.md"):
                    with self.assertRaises(ValueError):
                        articles.archive(outline, key, [citation])

    def test_comments_code_images_and_nonexistent_anchors_do_not_supply_citations(self):
        for body in (f"<!-- [原文]({URL}) -->", f"`[原文]({URL})`", f"```md\n[原文]({URL})\n```", f"![图]({URL})"):
            with self.subTest(body=body):
                _, outline, key, _ = self.prepare(f"## 方法\n{body}\n## 其他\n[依据]({URL})\n")
                with self.assertRaises(ValueError):
                    articles.archive(outline, key, ["report.md#方法"])
                with self.assertRaises(ValueError):
                    articles.archive(outline, key, ["report.md#不存在"])

    def test_inline_code_in_heading_and_html_link_are_supported(self):
        _, outline, key, _ = self.prepare(f'## `API` 分析\n<a href="{URL}">依据</a>\n## 其他\n')
        articles.archive(outline, key, ["report.md#api-分析"])

    def test_custom_html_anchor_is_bounded_by_its_section(self):
        _, outline, key, _ = self.prepare(f'<a id="custom"></a>\n## 方法\n[依据]({URL})\n## 其他\n无引用。\n')
        articles.archive(outline, key, ["report.md#custom"])
        _, outline, key, _ = self.prepare(f'<a id="custom"></a>\n## 方法\n无引用。\n## 其他\n[依据]({URL})\n')
        with self.assertRaises(ValueError):
            articles.archive(outline, key, ["report.md#custom"])

    def test_unanchored_declaration_allows_document_level_use(self):
        path, outline, key, report = self.prepare(f"## 方法\n无引用。\n## 其他\n[依据]({URL})\n")
        saved = articles.archive(outline, key, ["report.md"])
        checked = self.deliver(path, report, f"## 方法\n无引用。\n## 其他\n[依据]({saved['path']})\n")
        self.assertTrue(checked["valid"], checked)

    def test_html_heading_sections_cannot_borrow_a_sibling_citation(self):
        _, outline, key, _ = self.prepare(f'<h2 id="method">方法</h2>\n无引用。\n<h2 id="other">其他</h2>\n[依据]({URL})\n')
        with self.assertRaises(ValueError):
            articles.archive(outline, key, ["report.md#method"])
        articles.archive(outline, key, ["report.md#other"])

    def test_archive_exception_still_requires_a_citation_in_declared_section(self):
        _, outline, key, _ = self.prepare(f"## 方法\n无引用。\n## 其他\n[依据]({URL})\n")
        with self.assertRaises(ValueError):
            articles.archive(outline, key, ["report.md#方法"], exception="不允许存档原文")


if __name__ == "__main__":
    unittest.main()
