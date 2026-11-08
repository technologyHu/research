"""Regression coverage for uncited/unread distinctions and non-destructive refresh."""

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_task_workflow as fixtures
from test_task_workflow import task, results, reports
import test_articles as article_fixtures
from test_articles import Handler
import research_articles as articles


class ArticleRefresh(unittest.TestCase):
    setUp = fixtures.TaskWorkflow.setUp
    create = fixtures.TaskWorkflow.create
    populate = fixtures.TaskWorkflow.populate
    setup_articles = article_fixtures.ArticleWorkflow.setup_articles
    acquire_review = article_fixtures.ArticleWorkflow.acquire_review
    write_report = article_fixtures.ArticleWorkflow.write_report

    @classmethod
    def setUpClass(cls):
        article_fixtures.ArticleWorkflow.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        article_fixtures.ArticleWorkflow.tearDownClass.__func__(cls)

    def archived_pair(self):
        path, outline = self.setup_articles(("/articles/one", "/articles/two"))
        self.acquire_review(path, outline)
        wanted = articles.requirements(outline)
        self.write_report(path, outline, "\n".join(f"[正文依据]({item['url']})" for item in wanted))
        saved = [articles.archive(outline, item["id"], ["report.md#分析"]) for item in wanted]
        body = "\n".join(f"[本地原文]({item['path']})" for item in saved)
        self.write_report(path, outline, body)
        task.verify_task(path)
        return path, outline, wanted, body

    def test_unfetched_optional_article_cited_in_body_is_rejected(self):
        path, _ = self.populate(self.create())
        task.add_articles(path, [self.base + "/articles/one"], required=False)
        outline = results.load_document(path / "outline.json")
        report = self.write_report(path, outline, f"背景判断来自[未读补充文章]({self.base}/articles/one)。")
        check = reports.validate(report.parent, path / "outline.json")
        self.assertFalse(check["valid"])
        self.assertTrue(any("no accepted body" in error for error in check["errors"]))
        self.assertEqual(results.validate(path / "outline.json", path / "fields.json")["completion"], "complete")

    def test_obtained_but_unreviewed_optional_article_is_rejected_when_cited(self):
        path, _ = self.populate(self.create())
        task.add_articles(path, [self.base + "/articles/one"], required=False)
        outline = results.load_document(path / "outline.json")
        articles.acquire(outline)
        report = self.write_report(path, outline, f"[尚未核对的文章]({self.base}/articles/one)")
        self.assertFalse(reports.validate(report.parent, path / "outline.json")["valid"])

    def test_unreviewed_article_cannot_bypass_validation_by_copying_its_archive(self):
        path, _ = self.populate(self.create())
        task.add_articles(path, [self.base + "/articles/one"], required=False)
        outline = results.load_document(path / "outline.json")
        articles.acquire(outline)
        record = next(iter(articles.load_manifest(outline)["articles"].values()))
        target = Path(outline["output_dir"]) / "references/manual-copy.md"
        target.parent.mkdir()
        target.write_bytes((path / record["local_path"]).read_bytes())
        report = self.write_report(path, outline, "[手工复制的未读原文](references/manual-copy.md)")
        self.assertFalse(reports.validate(report.parent, path / "outline.json")["valid"])

    def test_failed_article_can_be_listed_in_a_gap_source_index_without_becoming_evidence(self):
        path, outline = self.setup_articles(("/blocked",))
        articles.acquire(outline)
        source_index = Path(outline["output_dir"]) / "references/sources.md"
        source_index.parent.mkdir()
        source_index.write_text(f"# 获取缺口\n\n[未取得正文的链接]({self.base}/blocked)，未作为结论依据。\n", encoding="utf-8")
        self.write_report(path, outline, "指定文章未取得正文，情况见[获取缺口](references/sources.md)。")
        self.assertEqual(task.verify_task(path)["completion"], "partial")

    def test_image_download_does_not_fetch_body_reset_review_or_drop_archives(self):
        path, outline, wanted, body = self.archived_pair()
        before = articles.load_manifest(outline)
        record = before["articles"][wanted[0]["id"]]
        original_bytes = (path / record["local_path"]).read_bytes()
        counts = {url: Handler.counts[url] for url in ("/articles/one", "/articles/two")}
        result = articles.download_images(outline, wanted[0]["id"], [self.base + "/good.png"])
        self.assertFalse(result["failures"])
        current = articles.load_manifest(outline)
        updated = current["articles"][wanted[0]["id"]]
        self.assertEqual(updated["reviewed_at"], record["reviewed_at"])
        self.assertEqual(updated["archive"], record["archive"])
        self.assertEqual(updated["content_sha256"], record["content_sha256"])
        self.assertEqual(original_bytes, (path / updated["local_path"]).read_bytes())
        self.assertEqual(current["articles"][wanted[1]["id"]], before["articles"][wanted[1]["id"]])
        self.assertEqual(counts, {url: Handler.counts[url] for url in counts})
        self.write_report(path, outline, body)
        self.assertTrue(task.verify_task(path)["verified"])

    def test_unchanged_scoped_refresh_preserves_snapshot_review_and_archive(self):
        path, outline, wanted, body = self.archived_pair()
        before = articles.load_manifest(outline)
        counts = {url: Handler.counts[url] for url in ("/articles/one", "/articles/two")}
        articles.acquire(outline, refresh=True, article_ids=[wanted[0]["id"]])
        after = articles.load_manifest(outline)
        old, current = before["articles"][wanted[0]["id"]], after["articles"][wanted[0]["id"]]
        for key in ("local_path", "content_sha256", "accessed_at", "review_status", "reviewed_at", "archive"):
            self.assertEqual(current[key], old[key])
        self.assertEqual(current["last_fetch_attempt"]["status"], "unchanged")
        self.assertEqual(after["articles"][wanted[1]["id"]], before["articles"][wanted[1]["id"]])
        self.assertEqual(Handler.counts["/articles/one"], counts["/articles/one"] + 1)
        self.assertEqual(Handler.counts["/articles/two"], counts["/articles/two"])
        self.write_report(path, outline, body)
        self.assertTrue(task.verify_task(path)["verified"])

    def test_failed_refresh_retains_valid_evidence_and_discloses_freshness_gap(self):
        path, outline, wanted, body = self.archived_pair()
        before = articles.load_manifest(outline)
        engine = articles.fetcher()
        calls = []

        def fail(url, *args, **kwargs):
            calls.append(url)
            return {"url": url, "final_url": url, "status": "failed", "article_path": None, "images": [], "error": "模拟网络失败"}

        with patch.object(articles, "fetcher", return_value=engine), patch.object(engine, "fetch_to_directory", side_effect=fail):
            state = articles.acquire(outline, refresh=True, article_ids=[wanted[0]["id"]])
        self.assertEqual(calls, [wanted[0]["url"]])
        self.assertTrue(state["gaps"])
        after = articles.load_manifest(outline)
        old, current = before["articles"][wanted[0]["id"]], after["articles"][wanted[0]["id"]]
        self.assertEqual(current["review_status"], "accepted")
        self.assertEqual(current["archive"], old["archive"])
        self.assertEqual(current["local_path"], old["local_path"])
        self.assertTrue((path / old["local_path"]).is_file())
        self.assertEqual(after["articles"][wanted[1]["id"]], before["articles"][wanted[1]["id"]])
        report = self.write_report(path, outline, body)
        self.assertIn("刷新失败", report.read_text(encoding="utf-8"))
        self.assertEqual(task.verify_task(path)["completion"], "partial")
        self.assertFalse(articles.acquire(outline, refresh=True, article_ids=[wanted[0]["id"]])["gaps"])

    def test_changed_body_creates_a_new_version_and_rechecks_only_that_article(self):
        path, outline, wanted, _ = self.archived_pair()
        before = articles.load_manifest(outline)
        old = before["articles"][wanted[0]["id"]]
        old_bytes = (path / old["local_path"]).read_bytes()
        engine = articles.fetcher()
        real_fetch = engine.fetch_html

        def changed(url, *args, **kwargs):
            html, final, method = real_fetch(url, *args, **kwargs)
            return html.replace("</article>", "<p>新版本增加了不同的执行边界与约束。</p></article>"), final, method

        with patch.object(articles, "fetcher", return_value=engine), patch.object(engine, "fetch_html", side_effect=changed):
            articles.acquire(outline, refresh=True, article_ids=[wanted[0]["id"]])
        after = articles.load_manifest(outline)
        current = after["articles"][wanted[0]["id"]]
        self.assertEqual(current["review_status"], "pending")
        self.assertIsNone(current["archive"])
        self.assertNotEqual(current["local_path"], old["local_path"])
        self.assertEqual(current["previous_versions"][-1], old)
        self.assertEqual((path / old["local_path"]).read_bytes(), old_bytes)
        self.assertEqual(after["articles"][wanted[1]["id"]], before["articles"][wanted[1]["id"]])
        child = Path(task.derive_task(path)["work_dir"])
        self.assertEqual((child / old["local_path"]).read_bytes(), old_bytes)
        self.assertEqual((child / current["local_path"]).read_bytes(), (path / current["local_path"]).read_bytes())

    def test_http_body_changes_invalidate_findings_but_image_and_unchanged_refresh_do_not(self):
        path, outline = self.setup_articles()
        self.acquire_review(path, outline)
        wanted = articles.requirements(outline)[0]
        file = path / "results" / (outline["items"][0]["id"] + ".json")
        data = json.loads(file.read_text(encoding="utf-8"))
        data["sources"][0]["url"] = wanted["url"]
        task.write_json(file, data)
        self.assertTrue(results.validate(path / "outline.json", path / "fields.json")["report_ready"])
        articles.download_images(outline, wanted["id"], [self.base + "/good.png"])
        articles.acquire(outline, refresh=True)
        self.assertTrue(results.validate(path / "outline.json", path / "fields.json")["report_ready"])
        engine = articles.fetcher()
        with patch.object(articles, "fetcher", return_value=engine), patch.object(engine, "fetch_to_directory", return_value={"url": wanted["url"], "status": "failed", "error": "模拟网络失败", "images": []}):
            articles.acquire(outline, refresh=True)
        checked = results.validate(path / "outline.json", path / "fields.json")
        self.assertTrue(checked["report_ready"])
        self.assertEqual(checked["completion"], "partial")
        real_fetch = engine.fetch_html

        def changed(url, *args, **kwargs):
            html, final, method = real_fetch(url, *args, **kwargs)
            return html.replace("</article>", "<p>新版修改了方法的执行条件。</p></article>"), final, method

        original = file.read_bytes()
        with patch.object(articles, "fetcher", return_value=engine), patch.object(engine, "fetch_html", side_effect=changed):
            articles.acquire(outline, refresh=True)
        articles.review(outline, wanted["id"], "accept", "核对新版正文")
        checked = results.validate(path / "outline.json", path / "fields.json")
        self.assertFalse(checked["report_ready"])
        self.assertIn(wanted["id"], next(iter(checked["stale_article_fields"][outline["items"][0]["id"]].values())))
        self.assertEqual(original, file.read_bytes())

    def test_failed_image_refresh_keeps_the_previously_downloaded_image(self):
        path, outline = self.setup_articles()
        self.acquire_review(path, outline)
        key = articles.requirements(outline)[0]["id"]
        articles.download_images(outline, key, [self.base + "/good.png"])
        previous = articles.load_manifest(outline)["articles"][key]
        image = next(item for item in previous["images"] if item["status"] == "downloaded")
        content = (path / image["path"]).read_bytes()
        engine = articles.fetcher()
        with patch.object(articles, "fetcher", return_value=engine), patch.object(engine, "download_image", return_value={"id": image["id"], "url": image["url"], "status": "failed", "path": None, "error": "网络失败"}):
            result = articles.download_images(outline, key, [image["url"]], refresh=True)
        self.assertTrue(result["failures"])
        current = articles.load_manifest(outline)["articles"][key]
        retained = next(item for item in current["images"] if item["id"] == image["id"])
        self.assertEqual(retained["status"], "downloaded")
        self.assertEqual(retained["path"], image["path"])
        self.assertEqual(retained["last_download_attempt"]["status"], "failed")
        self.assertEqual((path / image["path"]).read_bytes(), content)
        self.assertEqual(current["reviewed_at"], previous["reviewed_at"])

    def test_legacy_localized_image_links_survive_image_only_refresh_and_archiving(self):
        path, outline = self.setup_articles()
        articles.acquire(outline, image_policy="all")
        key = articles.requirements(outline)[0]["id"]
        data = articles.load_manifest(outline)
        record = data["articles"][key]
        image = next(item for item in record["images"] if item["status"] == "downloaded")
        source = path / record["local_path"]
        relative = Path(os.path.relpath(path / image["path"], source.parent)).as_posix()
        source.write_text(articles.fetcher().image_links(source.read_text(encoding="utf-8"), {image["url"]: relative}), encoding="utf-8")
        record["content_sha256"] = articles.sha(source)
        articles.save_manifest(outline, data)
        articles.review(outline, key, "accept", "已核对旧版正文和本地图片")
        self.write_report(path, outline, f"[来源]({record['url']})")
        articles.download_images(outline, key, [image["url"]], refresh=True)
        saved = articles.archive(outline, key, ["report.md#分析"], [image["id"]])
        archived = (Path(outline["output_dir"]) / saved["path"]).read_text(encoding="utf-8")
        self.assertNotIn("image-downloads/", archived)
        self.assertIn("../assets/", archived)
        self.write_report(path, outline, f"[原文]({saved['path']})\n\n![图]({saved['images'][0]['path']})")
        self.assertTrue(task.verify_task(path)["verified"])

    def test_cli_can_download_images_and_scope_a_body_refresh(self):
        path, outline = self.setup_articles()
        self.acquire_review(path, outline)
        key = articles.requirements(outline)[0]["id"]
        command = [sys.executable, "-X", "utf8", "-B", str(Path(task.__file__).resolve())]
        relative = path.relative_to(self.workspace).as_posix()
        for args in (["download-article-images", "--id", key, "--image-url", self.base + "/good.png"], ["fetch-articles", "--id", key, "--refresh"]):
            result = subprocess.run(command + args + ["--work-dir", relative], cwd=self.workspace, text=True, encoding="utf-8", capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(Path(json.loads(result.stdout)["manifest"]).is_absolute())
        self.assertEqual(articles.load_manifest(outline)["articles"][key]["review_status"], "accepted")


if __name__ == "__main__":
    unittest.main()
