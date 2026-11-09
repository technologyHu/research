"""Article replacement must preserve active files and invalidate dependent findings."""

import json
from pathlib import Path
import unittest
from unittest.mock import patch

import test_task_workflow as fixtures
from test_task_workflow import context, task, results, reports
import research_articles as articles
import research_dependencies as dependencies


URL = "https://example.org/article"
BODY = "## 方法\n\n当前方法采用 8 个工作单元。" + "此原始资料同时给出适用条件、实验设置及其限制。" * 5


class ArticleDependencies(unittest.TestCase):
    setUp = fixtures.TaskWorkflow.setUp
    create = fixtures.TaskWorkflow.create
    populate = fixtures.TaskWorkflow.populate

    def imported(self, light=False):
        kwargs = {"depth": "brief"} if light else {"fields": ["method=工作单元数量？", "boundary=适用条件？"]}
        path, outline = self.populate(self.create(references=[URL], **kwargs))
        source = path / "scratch/extracted.md"
        source.parent.mkdir(exist_ok=True)
        source.write_text(BODY, encoding="utf-8")
        wanted = articles.import_body(outline, URL, source, "方法原文")
        articles.review(outline, wanted["id"], "accept", "已核对原文与实验条件")
        if light:
            outline["assessment"]["sources"][0] = {**fixtures.SOURCE, "url": URL}
            task.write_json(path / "outline.json", outline)
        else:
            result = path / "results" / (outline["items"][0]["id"] + ".json")
            data = json.loads(result.read_text(encoding="utf-8"))
            data["sources"].append({**fixtures.SOURCE, "id": "article", "url": URL})
            data["fields"]["method"].update(value="8 个工作单元", evidence=[{"source_id": "article", "locator": "方法"}])
            task.write_json(result, data)
        return path, outline, wanted["id"], source

    def check(self, path, light=False, fingerprints=False):
        if light:
            return context.validate_light(path / "outline.json", fingerprints)
        return results.validate(path / "outline.json", path / "fields.json", fingerprints_only=fingerprints)

    def replace(self, outline, source, body=BODY.replace("8 个", "16 个"), **kwargs):
        source.write_text(body, encoding="utf-8")
        return articles.import_body(outline, URL, source, "方法原文", **kwargs)

    def bind(self, path, outline, key, light=False):
        bindings = {key: self.check(path, light, fingerprints=True)["article_fingerprints"][key]}
        if light:
            outline["assessment"]["article_fingerprints"] = bindings
            (path / "notes.md").write_text("已重读方法章节：工作单元数量变更为 16；原适用边界仍成立。", encoding="utf-8")
            task.write_json(path / "outline.json", outline)
        else:
            file = path / "results" / (outline["items"][0]["id"] + ".json")
            data = json.loads(file.read_text(encoding="utf-8"))
            data["fields"]["method"].update(value="16 个工作单元", article_fingerprints=bindings)
            task.write_json(file, data)
        return bindings

    def test_changed_body_blocks_only_dependent_fields_even_after_review_and_archive(self):
        path, outline, key, source = self.imported()
        self.assertTrue(self.check(path)["report_ready"])
        file = path / "results" / (outline["items"][0]["id"] + ".json")
        old_result = file.read_bytes()
        self.replace(outline, source)
        articles.review(outline, key, "accept", "已重读新版正文")
        report = Path(outline["output_dir"]) / "report.md"
        report.write_text(f"# 报告\n\n## 分析\n\n依照[原文]({URL})，8 个工作单元。", encoding="utf-8")
        saved = articles.archive(outline, key, ["report.md#分析"])
        report.write_text(report.read_text(encoding="utf-8") + f"\n[本地原文]({saved['path']})\n", encoding="utf-8")
        checked = self.check(path)
        item = outline["items"][0]["id"]
        self.assertEqual(checked["stale_article_fields"], {item: {"method": [key]}})
        self.assertFalse(checked["report_ready"])
        self.assertEqual(file.read_bytes(), old_result)
        with self.assertRaisesRegex(ValueError, "stale article dependency"):
            context.report_context(path / "outline.json")
        self.assertFalse(reports.validate(report.parent, path / "outline.json")["valid"])
        self.bind(path, outline, key)
        self.assertEqual(self.check(path)["completion"], "complete")
        note = context.render_report_note(context.report_context(path / "outline.json"))
        report.write_text(f"# 报告\n\n{note}\n## 分析\n\n16 个工作单元，见[原文]({saved['path']})。边界见[依据](https://example.org/original)。\n", encoding="utf-8")
        task.sync_report_note(path)
        self.assertTrue(task.verify_task(path)["verified"])

    def test_second_change_invalidates_a_previous_explicit_binding(self):
        path, outline, key, source = self.imported()
        self.bind(path, outline, key)
        self.replace(outline, source)
        self.assertIn(key, self.check(path)["stale_article_fields"][outline["items"][0]["id"]]["method"])
        self.bind(path, outline, key)
        self.replace(outline, source, BODY.replace("8 个", "32 个"))
        self.assertFalse(self.check(path)["report_ready"])

    def test_light_brief_requires_reassessment_after_source_change(self):
        path, outline, key, source = self.imported(light=True)
        self.replace(outline, source)
        articles.review(outline, key, "accept", "已重读新版正文")
        checked = self.check(path, light=True)
        self.assertEqual(checked["stale_articles"], [key])
        self.assertFalse(checked["report_ready"])
        self.bind(path, outline, key, light=True)
        self.assertEqual(self.check(path, light=True)["completion"], "complete")

    def test_import_retains_history_and_old_bytes(self):
        path, outline, key, source = self.imported()
        old = articles.load_manifest(outline)["articles"][key]
        old_bytes = (path / old["local_path"]).read_bytes()
        self.replace(outline, source)
        current = articles.load_manifest(outline)["articles"][key]
        self.assertNotEqual(current["local_path"], old["local_path"])
        self.assertEqual(current["previous_versions"], [old])
        self.assertEqual(current["review_status"], "pending")
        self.assertTrue(current["requires_result_review"])
        self.assertEqual((path / old["local_path"]).read_bytes(), old_bytes)

    def test_unchanged_import_preserves_review_archive_and_active_snapshot(self):
        path, outline, key, source = self.imported()
        report = Path(outline["output_dir"]) / "report.md"
        report.write_text(f"# 报告\n\n## 分析\n\n[依据]({URL})", encoding="utf-8")
        articles.archive(outline, key, ["report.md#分析"])
        old = articles.load_manifest(outline)["articles"][key]
        self.replace(outline, source, BODY)
        current = articles.load_manifest(outline)["articles"][key]
        self.assertEqual({k: v for k, v in current.items() if k != "last_fetch_attempt"}, old)
        self.assertEqual(current["last_fetch_attempt"]["status"], "unchanged")
        self.assertEqual(self.check(path)["completion"], "complete")

    def test_invalid_import_arguments_do_not_touch_body_or_manifest(self):
        path, outline, key, source = self.imported()
        record = articles.load_manifest(outline)["articles"][key]
        original = (path / record["local_path"]).read_bytes()
        manifest = (path / "articles.json").read_bytes()
        files = set((path / "sources").rglob("article.md"))
        for kwargs in ({"final_url": "not-a-url"}, {"method": "invalid"}, {"title": " "}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                articles.import_body(outline, URL, source, **({"title": "方法原文"} | kwargs))
            self.assertEqual((path / "articles.json").read_bytes(), manifest)
            self.assertEqual((path / record["local_path"]).read_bytes(), original)
            self.assertEqual(set((path / "sources").rglob("article.md")), files)

    def test_corrupt_manifest_or_unreadable_source_is_rejected_before_writes(self):
        path, outline, key, source = self.imported()
        record = articles.load_manifest(outline)["articles"][key]
        original = (path / record["local_path"]).read_bytes()
        files = set((path / "sources").rglob("article.md"))
        with self.assertRaises(OSError):
            articles.import_body(outline, URL, path / "scratch/missing.md", "方法原文")
        (path / "articles.json").write_text("broken", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.replace(outline, source)
        self.assertEqual((path / "articles.json").read_text(encoding="utf-8"), "broken")
        self.assertEqual((path / record["local_path"]).read_bytes(), original)
        self.assertEqual(set((path / "sources").rglob("article.md")), files)

    def test_manifest_commit_failure_does_not_overwrite_active_body(self):
        path, outline, key, source = self.imported()
        record = articles.load_manifest(outline)["articles"][key]
        original = (path / record["local_path"]).read_bytes()
        manifest = (path / "articles.json").read_bytes()
        with patch.object(Path, "replace", side_effect=OSError("模拟清单提交失败")), self.assertRaises(OSError):
            self.replace(outline, source)
        self.assertEqual((path / "articles.json").read_bytes(), manifest)
        self.assertEqual((path / record["local_path"]).read_bytes(), original)
        self.assertFalse(list((path / "scratch").glob(".articles-*")))
        self.assertTrue(self.check(path)["report_ready"])

    def test_legacy_history_without_change_marker_still_invalidates_findings(self):
        path, outline, key, source = self.imported()
        self.replace(outline, source)
        data = articles.load_manifest(outline)
        data["articles"][key].pop("requires_result_review")
        articles.save_manifest(outline, data)
        self.assertFalse(self.check(path)["report_ready"])

    def test_dependencies_include_redirect_aliases_and_conflicting_sources(self):
        path, outline, key, source = self.imported()
        old = articles.load_manifest(outline)["articles"][key]
        self.replace(outline, source, final_url="https://example.org/redirected")
        state = dependencies.state(outline)
        record = {"evidence": [], "conflicts": [{"positions": [{"source_id": "redirect"}]}]}
        urls = dependencies.referenced_urls(record, [{"id": "redirect", "url": "https://example.org/redirected#method"}])
        errors, stale = dependencies.check(record, urls, state, "field")
        self.assertTrue(errors)
        self.assertEqual(stale, [key])
        self.assertEqual(dependencies.check({}, [(path / old["local_path"]).as_uri()], state, "field")[1], [key])
        self.assertFalse(dependencies.check(record, ["https://example.org/unrelated"], state, "field")[0])

    def test_fingerprints_mode_never_reads_results_and_rejects_bad_bindings(self):
        path, outline, key, source = self.imported()
        result = path / "results" / (outline["items"][0]["id"] + ".json")
        result.write_text("broken", encoding="utf-8")
        fingerprints = self.check(path, fingerprints=True)
        self.assertTrue(fingerprints["valid"])
        self.assertIn(key, fingerprints["article_fingerprints"])
        for bad in (None, [], {key: "bad"}, {"unknown-article": "a" * 64}):
            self.assertTrue(dependencies.check({"article_fingerprints": bad}, [], dependencies.state(outline), "field")[0])


if __name__ == "__main__":
    unittest.main()
