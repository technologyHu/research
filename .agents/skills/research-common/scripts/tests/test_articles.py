"""Offline HTTP fixtures exercise article acquisition, review, archiving and delivery."""

from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import threading
import unittest

import test_task_workflow as fixtures
from test_task_workflow import context, task, results, reports
from test_validation import PNG
import research_articles as articles


class Handler(BaseHTTPRequestHandler):
    counts = Counter()

    def log_message(self, *args):
        pass

    def do_GET(self):
        self.counts[self.path] += 1
        status, kind = 200, "text/html; charset=utf-8"
        if self.path == "/good.png":
            body, kind = PNG, "image/png"
        elif self.path == "/bad.png":
            body = ("<html>not an image</html>" * 100).encode()
        elif self.path == "/blocked":
            body = b"<html><title>Security check</title><body>captcha verification required</body></html>"
        elif self.path == "/missing":
            status, body = 404, b"missing"
        elif self.path == "/plain":
            body = ("<html><title>普通页面</title><body>" + "可阅读的正文需要人工核对与筛选。" * 20 + "</body></html>").encode()
        elif self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/articles/one")
            self.end_headers()
            return
        else:
            body = ("<html><head><title>同名技术文章</title><meta name='author' content='测试作者'></head><body><article><h1>同名技术文章</h1><p>" + "这是用于离线验证的完整中文技术正文，包含适用条件和限制。" * 12 +
                    "</p><a href='/details?q=version'>相关资料</a><img data-src='../good.png' alt='../../outside.png'><img src='../bad.png' alt='失败图'></article></body></html>").encode()
        self.send_response(status)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class ArticleWorkflow(unittest.TestCase):
    setUp = fixtures.TaskWorkflow.setUp
    create = fixtures.TaskWorkflow.create
    populate = fixtures.TaskWorkflow.populate

    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def setup_articles(self, suffixes=("/articles/one",), light=False):
        path, outline = self.populate(self.create(depth="brief" if light else "standard", references=[self.base + suffix for suffix in suffixes]))
        return path, outline

    def acquire_review(self, path, outline, images="remote"):
        articles.acquire(outline, image_policy=images)
        for item in articles.requirements(outline):
            articles.review(outline, item["id"], "accept", "已核对正文、标题、来源链接和适用条件")

    def write_report(self, path, outline, body):
        report = Path(outline["output_dir"]) / "report.md"
        report.write_text("# 调研报告\n\n" + context.render_report_note(context.report_context(path / "outline.json")) + "\n## 分析\n\n根据[既有证据](https://example.org/original)分析。\n" + body + "\n", encoding="utf-8")
        task.sync_report_note(path)
        return report

    def test_required_articles_are_deduplicated_fetched_and_need_body_review(self):
        path, outline = self.setup_articles(("/articles/one", "/articles/one#method", "/articles/two"))
        self.assertEqual(len(articles.requirements(outline)), 2)
        checked = results.validate(path / "outline.json", path / "fields.json")
        self.assertEqual(checked["completion"], "partial")
        acquired = articles.acquire(outline)
        self.assertEqual(len(acquired["gaps"]), 2)
        records = articles.load_manifest(outline)["articles"]
        self.assertEqual(len(records), 2)
        self.assertEqual({record["status"] for record in records.values()}, {"fetched"})
        self.assertEqual(len({record["local_path"] for record in records.values()}), 2)
        for key, record in records.items():
            self.assertIn("完整中文技术正文", (path / record["local_path"]).read_text(encoding="utf-8"))
            articles.review(outline, key, "accept", "正文与原页面对应，未混入导航和验证内容")
        self.assertEqual(results.validate(path / "outline.json", path / "fields.json")["completion"], "complete")

    def test_cache_reuse_preserves_dates_and_review_without_network(self):
        path, outline = self.setup_articles()
        self.acquire_review(path, outline)
        before = (path / "articles.json").read_bytes()
        count = Handler.counts["/articles/one"]
        articles.acquire(outline)
        self.assertEqual(count, Handler.counts["/articles/one"])
        self.assertEqual(before, (path / "articles.json").read_bytes())

    def test_failed_required_article_keeps_a_visible_gap_in_a_partial_report(self):
        path, outline = self.setup_articles(("/blocked",))
        state = articles.acquire(outline)
        self.assertEqual(len(state["gaps"]), 1)
        record = next(iter(articles.load_manifest(outline)["articles"].values()))
        self.assertEqual(record["status"], "failed")
        self.assertIsNone(record["local_path"])
        report = self.write_report(path, outline, "指定文章未获得正文，相关判断不作结论。")
        self.assertIn("未能核对的参考资料：" + record["url"], report.read_text(encoding="utf-8"))
        self.assertEqual(task.verify_task(path)["completion"], "partial")

    def test_body_fallback_requires_explicit_review_and_rejection_keeps_gap(self):
        path, outline = self.setup_articles(("/plain",))
        articles.acquire(outline)
        key = articles.requirements(outline)[0]["id"]
        self.assertEqual(articles.load_manifest(outline)["articles"][key]["status"], "needs_review")
        self.assertTrue(articles.review(outline, key, "reject", "正文边界仍不能确认")["gaps"])
        self.assertFalse(articles.review(outline, key, "accept", "人工核对后确认该页面全部为目标正文")["gaps"])

    def test_optional_failed_article_does_not_lower_completion(self):
        path, outline = self.populate(self.create())
        task.add_articles(path, [self.base + "/missing"], required=False)
        outline = results.load_document(path / "outline.json")
        articles.acquire(outline)
        self.assertEqual(results.validate(path / "outline.json", path / "fields.json")["completion"], "complete")

    def test_light_workflow_obeys_the_same_reference_requirements(self):
        path, outline = self.setup_articles(light=True)
        self.assertEqual(context.validate_light(path / "outline.json")["completion"], "partial")
        self.acquire_review(path, outline)
        self.assertEqual(context.validate_light(path / "outline.json")["completion"], "complete")

    def test_images_are_validated_failed_links_stay_remote_and_cited_material_is_archived(self):
        path, outline = self.setup_articles()
        self.acquire_review(path, outline, "all")
        key = articles.requirements(outline)[0]["id"]
        record = articles.load_manifest(outline)["articles"][key]
        good = next(image for image in record["images"] if image["status"] == "downloaded")
        bad = next(image for image in record["images"] if image["status"] == "failed")
        self.assertIsNone(bad["path"])
        original = (path / record["local_path"]).read_text(encoding="utf-8")
        self.assertIn(self.base + "/bad.png", original)
        self.assertIn(self.base + "/details?q=version", original)
        self.assertFalse((path / "outside.png").exists())
        report = self.write_report(path, outline, "[文章原文](" + self.base + "/articles/one)")
        saved = articles.archive(outline, key, ["report.md#分析"], [good["id"]])
        archived = (report.parent / saved["path"]).read_text(encoding="utf-8")
        self.assertIn("../assets/", archived)
        self.assertIn(self.base + "/bad.png", archived)
        self.assertNotIn(".tmp/", archived)
        self.write_report(path, outline, f"[本地原文]({saved['path']})\n\n![机制]({saved['images'][0]['path']})")
        self.assertTrue(task.verify_task(path)["verified"])
        self.assertTrue(task.cleanup_plan(path)["requires_confirmation"])

    def test_cited_article_cannot_skip_archive_or_use_only_source_index(self):
        path, outline = self.setup_articles()
        self.acquire_review(path, outline)
        key = articles.requirements(outline)[0]["id"]
        report = self.write_report(path, outline, "[文章依据](" + self.base + "/articles/one)")
        self.assertFalse(reports.validate(report.parent, path / "outline.json")["valid"])
        saved = articles.archive(outline, key, ["report.md#分析"])
        self.write_report(path, outline, f"[本地原文]({saved['path']})")
        self.assertTrue(task.verify_task(path)["verified"])
        (report.parent / "references/sources.md").write_text(f"# 来源\n\n[原文]({self.base}/articles/one)\n\n[存档]({key}.md)\n", encoding="utf-8")
        self.write_report(path, outline, "[仅列来源清单](references/sources.md)")
        check = reports.validate(report.parent, path / "outline.json")
        self.assertFalse(check["valid"])
        self.assertTrue(any("visible report citation" in error for error in check["errors"]))

    def test_unused_required_article_remains_temporary(self):
        path, outline = self.setup_articles()
        self.acquire_review(path, outline)
        report = self.write_report(path, outline, "已阅读指定文章，但它没有支持本次结论，因此未引用。")
        self.assertTrue(task.verify_task(path)["verified"])
        self.assertFalse((report.parent / "references").exists())
        self.assertTrue((path / "sources/articles").is_dir())

    def test_body_changes_invalidate_evidence_and_archive_changes_invalidate_delivery(self):
        path, outline = self.setup_articles()
        self.acquire_review(path, outline)
        key = articles.requirements(outline)[0]["id"]
        self.write_report(path, outline, "[原文](" + self.base + "/articles/one)")
        saved = articles.archive(outline, key, ["report.md#分析"])
        report = self.write_report(path, outline, f"[存档]({saved['path']})")
        task.verify_task(path)
        archive_path = report.parent / saved["path"]
        original = archive_path.read_bytes()
        archive_path.write_bytes(original + b"changed")
        self.assertFalse(reports.validate(report.parent, path / "outline.json")["valid"])
        archive_path.write_bytes(original)
        record = articles.load_manifest(outline)["articles"][key]
        (path / record["local_path"]).write_bytes(b"not the obtained body")
        self.assertFalse(results.validate(path / "outline.json", path / "fields.json")["valid"])

    def test_pdf_or_browser_markdown_can_be_imported_and_reviewed(self):
        path, outline = self.setup_articles()
        extracted = path / "scratch/extracted.md"
        extracted.parent.mkdir()
        extracted.write_text("# 提取原文\n\n" + "这是从用户提供资料中实际提取的正文。" * 15, encoding="utf-8")
        wanted = articles.import_body(outline, self.base + "/articles/one", extracted, "提取原文", "pdf")
        self.assertTrue(articles.assessment(outline)["gaps"])
        articles.review(outline, wanted["id"], "accept", "已对照 PDF 正文核实提取结果")
        self.assertFalse(articles.assessment(outline)["gaps"])
        with self.assertRaises(ValueError):
            articles.import_body(outline, self.base + "/articles/one", self.workspace / "outside.md", "外部文件")

    def test_imported_images_can_be_downloaded_and_archived_without_refetching_body(self):
        path, outline = self.setup_articles()
        extracted = path / "scratch/extracted.md"
        extracted.parent.mkdir()
        url = self.base + "/good.png"
        extracted.write_text("# 原文\n\n" + "实际提取的原始正文。" * 20 + f"\n\n![界面]({url})\n\n![重复]({url})", encoding="utf-8")
        key = articles.import_body(outline, self.base + "/articles/one", extracted, "原文", "browser")["id"]
        record = articles.load_manifest(outline)["articles"][key]
        self.assertEqual(len(record["images"]), 1)
        # Older imports did not register images. Reimport must repair only that metadata.
        data = articles.load_manifest(outline)
        data["articles"][key]["images"] = []
        articles.save_manifest(outline, data)
        articles.review(outline, key, "accept", "已核对正文及界面原图来源")
        articles.import_body(outline, self.base + "/articles/one", extracted, "原文", "browser")
        repaired = articles.load_manifest(outline)["articles"][key]
        self.assertEqual(repaired["local_path"], record["local_path"])
        self.assertEqual(repaired["review_status"], "accepted")
        self.assertEqual(len(repaired["images"]), 1)
        downloaded = articles.download_images(outline, key, [url], proxy="direct")
        self.assertFalse(downloaded["failures"])
        image = articles.load_manifest(outline)["articles"][key]["images"][0]
        self.write_report(path, outline, "[原文](" + self.base + "/articles/one)")
        saved = articles.archive(outline, key, ["report.md#分析"], [image["id"]])
        self.assertEqual((Path(outline["output_dir"]) / saved["images"][0]["path"]).read_bytes(), PNG)
        articles.import_body(outline, self.base + "/articles/one", extracted, "原文", "browser")
        retained = articles.load_manifest(outline)["articles"][key]
        self.assertEqual(retained["images"][0]["status"], "downloaded")
        self.assertEqual(retained["archive"], saved)

    def test_import_resolves_relative_links_against_final_url_and_retains_cached_assets(self):
        path, outline = self.setup_articles()
        extracted = path / "scratch/extracted.md"
        extracted.parent.mkdir()
        body = "# 原文\n\n" + "实际提取的原始正文。" * 20
        body += '\n\n[详情](../details) ![界面](../good.png#preview)\n`![代码](../not-an-asset.png)`\n'
        extracted.write_text(body, encoding="utf-8")
        key = articles.import_body(outline, self.base + "/articles/one", extracted, "原文", "http", self.base + "/redirected/page")["id"]
        record = articles.load_manifest(outline)["articles"][key]
        saved = (path / record["local_path"]).read_text(encoding="utf-8")
        self.assertIn(f"[详情]({self.base}/details)", saved)
        self.assertIn(f"![界面]({self.base}/good.png#preview)", saved)
        self.assertIn('`![代码](../not-an-asset.png)`', saved)
        self.assertEqual(record["method"], "http")
        image_url = self.base + "/good.png#preview"
        self.assertEqual([image["url"] for image in record["images"]], [image_url])
        articles.review(outline, key, "accept", "已对照原页面核对正文与原图")
        self.assertFalse(articles.download_images(outline, key, [image_url], proxy="direct")["failures"])
        old = articles.load_manifest(outline)["articles"][key]
        extracted.write_text(articles.fetcher().normalize_markdown_links(body, old["final_url"]), encoding="utf-8")
        articles.import_body(outline, self.base + "/articles/one", extracted, "原文", "http", old["final_url"])
        current = articles.load_manifest(outline)["articles"][key]
        self.assertEqual(current["local_path"], old["local_path"])
        self.assertEqual(current["accessed_at"], old["accessed_at"])
        self.assertEqual(current["review_status"], "accepted")
        self.assertEqual(current["images"], old["images"])

    def test_article_that_failed_acquisition_cannot_support_a_confirmed_claim(self):
        path, outline = self.setup_articles(("/blocked",))
        articles.acquire(outline)
        record_path = path / "results/item-1.json"
        data = results.load_document(record_path)
        data["sources"][0]["url"] = self.base + "/blocked"
        task.write_json(record_path, data)
        report = self.write_report(path, outline, "[伪称已读正文](" + self.base + "/blocked)")
        check = reports.validate(report.parent, path / "outline.json")
        self.assertFalse(check["valid"])
        self.assertTrue(any("no accepted body" in error for error in check["errors"]))

    def test_archive_exception_must_be_visible_in_report(self):
        path, outline = self.setup_articles()
        self.acquire_review(path, outline)
        key = articles.requirements(outline)[0]["id"]
        self.write_report(path, outline, "[原文](" + self.base + "/articles/one)")
        reason = "仅允许引用链接，不随报告保存全文"
        articles.archive(outline, key, ["report.md#分析"], exception=reason)
        report = self.write_report(path, outline, "[原文](" + self.base + "/articles/one)\n\n<!-- " + reason + " -->")
        self.assertFalse(reports.validate(report.parent, path / "outline.json")["valid"])
        self.write_report(path, outline, "[原文](" + self.base + "/articles/one)\n\n归档限制：" + reason)
        self.assertTrue(task.verify_task(path)["verified"])

    def test_existing_archive_cannot_be_overwritten_implicitly(self):
        path, outline = self.setup_articles()
        self.acquire_review(path, outline)
        key = articles.requirements(outline)[0]["id"]
        self.write_report(path, outline, "[原文](" + self.base + "/articles/one)")
        saved = articles.archive(outline, key, ["report.md#分析"])
        destination = Path(outline["output_dir"]) / saved["path"]
        destination.write_text("用户已有的修改", encoding="utf-8")
        with self.assertRaises(ValueError):
            articles.archive(outline, key, ["report.md#分析"])
        self.assertEqual(destination.read_text(encoding="utf-8"), "用户已有的修改")

    def test_redirect_keeps_original_and_final_source_urls(self):
        path, outline = self.setup_articles(("/redirect",))
        self.acquire_review(path, outline)
        key = articles.requirements(outline)[0]["id"]
        record = articles.load_manifest(outline)["articles"][key]
        self.assertEqual(record["url"], self.base + "/redirect")
        self.assertEqual(record["final_url"], self.base + "/articles/one")
        self.write_report(path, outline, "[最终原文](" + self.base + "/articles/one)")
        saved = articles.archive(outline, key, ["report.md#分析"])
        self.write_report(path, outline, f"[本地原文]({saved['path']})")
        self.assertTrue(task.verify_task(path)["verified"])

    def test_malformed_manifest_is_an_error_instead_of_a_missing_article(self):
        path, outline = self.setup_articles()
        data = articles.load_manifest(outline)
        key = articles.requirements(outline)[0]["id"]
        data["articles"][key] = None
        articles.save_manifest(outline, data)
        checked = results.validate(path / "outline.json", path / "fields.json")
        self.assertFalse(checked["valid"])
        self.assertTrue(any("manifest record" in error for error in checked["errors"]))

    def test_derivation_copies_reviewed_article_cache_without_revisiting_sources(self):
        path, outline = self.setup_articles()
        self.acquire_review(path, outline)
        count = Handler.counts["/articles/one"]
        original = articles.load_manifest(outline)
        child = Path(task.derive_task(path)["work_dir"])
        inherited = results.load_document(child / "outline.json")
        cloned = articles.load_manifest(inherited)
        self.assertEqual(cloned["articles"], original["articles"])
        self.assertNotEqual(cloned["run_id"], original["run_id"])
        articles.acquire(inherited)
        self.assertEqual(count, Handler.counts["/articles/one"])

    def test_cli_add_fetch_and_review_return_relative_manifest_path(self):
        path, outline = self.populate(self.create())
        command = [sys.executable, "-X", "utf8", "-B", str(Path(task.__file__).resolve())]
        relative = path.relative_to(self.workspace).as_posix()
        for args in (["add-article", "--url", self.base + "/articles/one"], ["fetch-articles"]):
            run = subprocess.run(command + args + ["--work-dir", relative], cwd=self.workspace, text=True, encoding="utf-8", capture_output=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertFalse(Path(json.loads(run.stdout)["manifest"]).is_absolute())
        self.assertTrue(articles.assessment(results.load_document(path / "outline.json"))["gaps"])


if __name__ == "__main__":
    unittest.main()
