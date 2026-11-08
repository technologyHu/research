"""Offline regression checks for automatic article archive validation.

Run: python -X utf8 -m unittest discover -s <skill>/scripts -p test_fetch_article.py
"""

import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

import fetch_article as fetcher


URL = "https://example.org/article"
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/h9sAAAAASUVORK5CYII=")
PAGE = ('<h1>测试/文章?</h1><div id="js_content"><p>开头：' + '完整中文原文。' * 10
        + '</p><img data-src="/good.png" alt="原图"><p>中段</p>'
        '<img src="/good.png" alt="重复图"><p>末段</p>'
        '<a href="/good.png">网页链接</a></div><p>微信界面控件</p>')


class ArchiveValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="article-validation-")
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name)
        self.result = self.fetch()
        self.root = (self.output / self.result["article_path"]).parent

    def fetch(self, page=PAGE, url=URL, **kwargs):
        client = MagicMock()
        client.__enter__.return_value = client
        client.get.side_effect = lambda url, **options: SimpleNamespace(
            content=PNG if url.endswith("good.png") else b"<html>Image error</html>",
            raise_for_status=lambda: None)
        with patch.object(fetcher, "fetch_html", return_value=(page, url, "http")), patch.object(fetcher, "session", return_value=client):
            return fetcher.fetch_to_directory(url, self.output, image_policy="all", **kwargs)

    def metadata(self):
        return json.loads((self.root / "metadata.json").read_text(encoding="utf-8"))

    def write_metadata(self, metadata):
        (self.root / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")

    def assert_failed(self, check):
        report = fetcher.validate_archive(self.root)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["checks"][check]["status"], "failed")
        self.assertTrue(report["requires_review"])

    def test_fetch_automatically_saves_four_checks_and_portable_metadata(self):
        report = self.result["validation"]
        self.assertEqual(self.result["status"], "fetched")
        self.assertEqual(self.root.name, "测试_文章_")
        self.assertEqual(report["status"], "passed")
        self.assertEqual(len(report["checks"]), 4)
        self.assertTrue(all(check["status"] == "passed" for check in report["checks"].values()))
        self.assertEqual(report["counts"]["image_references"], 2)
        self.assertEqual(report["counts"]["downloaded_images"], 1)
        metadata = self.metadata()
        self.assertEqual(metadata["validation"], report)
        self.assertEqual(metadata["article_path"], "article.md")
        self.assertTrue(metadata["images"][0]["path"].startswith("assets/images/"))
        self.assertTrue((self.output / self.result["images"][0]["path"]).is_file())
        body = (self.root / "article.md").read_text(encoding="utf-8")
        self.assertNotIn("微信界面控件", body)
        self.assertLess(body.index("开头"), body.index("![原图]"))
        self.assertLess(body.index("![原图]"), body.index("中段"))
        self.assertLess(body.index("中段"), body.index("![重复图]"))
        self.assertIn("[网页链接](https://example.org/good.png)", body)

    def test_local_asset_destinations_avoid_pycharm_angle_bracket_bug(self):
        metadata = self.metadata()
        relative = metadata["images"][0]["path"]
        article = self.root / "article.md"
        body = article.read_text(encoding="utf-8")
        self.assertIn("![原图](" + relative + ")", body)
        self.assertNotIn("(<assets/images/", body)
        article.write_text(body.replace("](" + relative + ")", "](<" + relative + ">)"), encoding="utf-8")
        metadata["content_sha256"] = hashlib.sha256(article.read_bytes()).hexdigest()
        self.write_metadata(metadata)
        self.assert_failed("image_references")

    def test_wrong_title_directory_is_detected(self):
        renamed = self.output / "错误目录"
        self.assertEqual(self.root.resolve().parent, self.output.resolve())
        self.root.rename(renamed)
        self.root = renamed
        self.assert_failed("directory_name")

    def test_explicit_directory_is_allowed(self):
        result = self.fetch(directory_name="用户指定目录")
        self.assertEqual(result["validation"]["status"], "passed")

    def test_explicit_name_does_not_overwrite_another_source(self):
        first = self.fetch(directory_name="指定文章")
        original = self.output / first["article_path"]
        before = original.read_bytes()
        second = self.fetch(url=URL + "-other", directory_name="指定文章")
        self.assertNotEqual(first["article_path"], second["article_path"])
        self.assertEqual(before, original.read_bytes())
        self.assertEqual("fetched", second["status"])
        self.assertEqual(second["article_path"], self.fetch(url=URL + "-other", directory_name="指定文章")["article_path"])

    def test_collision_archive_remains_valid_and_reusable_when_base_disappears(self):
        second = self.fetch(url=URL + "-other")
        second_root = (self.output / second["article_path"]).parent
        # Remove only the temporary competing fixture, never a real archive.
        import shutil
        self.assertTrue(self.root.resolve().is_relative_to(self.output.resolve()))
        self.assertNotEqual(self.root.resolve(), self.output.resolve())
        shutil.rmtree(self.root)
        self.assertEqual("passed", fetcher.validate_archive(second_root)["status"])
        self.assertEqual(second["article_path"], self.fetch(url=URL + "-other")["article_path"])

    def test_unknown_custom_directory_is_preserved(self):
        target = self.output / "指定文章"
        target.mkdir()
        note = target / "article.md"
        note.write_text("Unknown local content", encoding="utf-8")
        result = self.fetch(directory_name="指定文章")
        self.assertEqual("Unknown local content", note.read_text(encoding="utf-8"))
        self.assertNotEqual("指定文章/article.md", result["article_path"])
        self.assertEqual("fetched", result["status"])

    def test_english_category_keeps_original_title_and_chinese_topic(self):
        self.output = self.output / "openjiuwen/中文主题/refs/competitor-articles"
        page = PAGE.replace("测试/文章?", "Claude Code 的「乐高」模式")
        result = self.fetch(page)
        self.assertEqual("Claude Code 的「乐高」模式/article.md", result["article_path"])
        self.assertEqual("fetched", result["status"])

    def test_missing_title_uses_source_identifier(self):
        result = self.fetch(PAGE.replace("<h1>测试/文章?</h1>", ""))
        self.assertEqual(fetcher.article_id(URL) + "/article.md", result["article_path"])
        self.assertEqual("fetched", result["status"])

    def test_explicit_name_is_sanitized_without_changing_article_title(self):
        result = self.fetch(directory_name="指定:文章? ")
        self.assertEqual("指定_文章_/article.md", result["article_path"])
        self.assertEqual("指定_文章_", result["directory_name"])
        self.assertEqual("测试/文章?", result["title"])
        self.assertEqual("fetched", result["status"])

    def test_windows_reserved_and_long_titles_keep_the_original_heading(self):
        for title in ["CON", "中文长标题" * 25]:
            with self.subTest(title=title):
                result = self.fetch(PAGE.replace("测试/文章?", title))
                self.assertEqual("fetched", result["status"])
                self.assertEqual(title, result["title"])
                article = self.output / result["article_path"]
                self.assertTrue(article.read_text(encoding="utf-8").startswith("# " + title + "\n"))
                self.assertNotEqual("CON", article.parent.name)
                self.assertLessEqual(len(article.parent.name), 90)

    def test_explicit_name_is_not_a_parent_path(self):
        before = {p: p.read_bytes() for p in self.output.rglob("*") if p.is_file()}
        for name in ["", ".", "..", "nested\\name"]:
            with self.subTest(name=name):
                result = self.fetch(directory_name=name)
                self.assertEqual("failed", result["status"])
                self.assertIn("one nonempty folder name", result["error"])
        self.assertEqual(before, {p: p.read_bytes() for p in self.output.rglob("*") if p.is_file()})

    def test_managed_version_path_remains_valid_and_reusable(self):
        folder = "article-test/versions/" + "a" * 32
        result = self.fetch(directory_name=folder)
        self.assertEqual(folder + "/article.md", result["article_path"])
        self.assertEqual("fetched", result["status"])
        self.assertEqual("a" * 32, result["directory_name"])
        self.assertEqual(result["article_path"], self.fetch(directory_name=folder)["article_path"])
        root = (self.output / result["article_path"]).parent
        self.assertTrue(all((self.output / image["path"]).is_file() for image in result["images"]))
        # Existing managed archives stored the complete relative version path.
        metadata_path = root / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["directory_name"] = folder
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        self.assertEqual("passed", fetcher.validate_archive(root)["status"])

    def test_unsafe_managed_paths_fail_before_fetching_or_writing(self):
        before = {p: p.read_bytes() for p in self.output.rglob("*") if p.is_file()}
        for name in ["../outside", "/outside/name", "nested/../name", "nested//name", "nested/./name", "C:/outside/name"]:
            with self.subTest(name=name), patch.object(fetcher, "fetch_html") as request:
                result = fetcher.fetch_to_directory(URL, self.output, directory_name=name)
                self.assertEqual("failed", result["status"])
                request.assert_not_called()
        self.assertEqual(before, {p: p.read_bytes() for p in self.output.rglob("*") if p.is_file()})

    def test_cli_custom_name_rejects_parent_paths(self):
        for name in ["nested/name", "nested\\name", "../outside"]:
            arguments = [str(Path(fetcher.__file__)), "--url", URL, "--output-dir", str(self.output),
                         "--directory-name", name]
            with self.subTest(name=name), patch.object(sys, "argv", arguments), \
                    patch.object(sys, "stdout", io.StringIO()) as stdout, patch.object(fetcher, "fetch_html") as request:
                self.assertEqual(1, fetcher.main())
                self.assertEqual("failed", json.loads(stdout.getvalue())["status"])
                request.assert_not_called()

    def test_numbered_conflict_suffix_is_valid_and_reused(self):
        base = "指定文章"
        conflict = base + "--" + fetcher.article_id(URL).removeprefix("article-")
        for name in [base, conflict]:
            (self.output / name).mkdir()
            (self.output / name / "unknown.txt").write_text("Keep", encoding="utf-8")
        result = self.fetch(directory_name=base)
        self.assertEqual(conflict + "-2/article.md", result["article_path"])
        self.assertEqual("fetched", result["status"])
        self.assertEqual(result["article_path"], self.fetch(directory_name=base)["article_path"])
        self.assertTrue(all((self.output / name / "unknown.txt").is_file() for name in [base, conflict]))

    def test_explicit_name_cli_runs_the_normal_archive_flow(self):
        arguments = [str(Path(fetcher.__file__)), "--url", URL, "--output-dir", str(self.output),
                     "--directory-name", "用户指定文章", "--images", "remote"]
        with patch.object(sys, "argv", arguments), patch.object(sys, "stdout", io.StringIO()) as stdout, \
                patch.object(fetcher, "fetch_html", return_value=(PAGE, URL, "http")):
            self.assertEqual(0, fetcher.main())
            result = json.loads(stdout.getvalue())
        self.assertEqual("用户指定文章/article.md", result["article_path"])
        self.assertEqual("passed", result["validation"]["status"])

    def test_missing_local_image_is_detected(self):
        (self.root / self.metadata()["images"][0]["path"]).unlink()
        self.assert_failed("image_references")
        self.assert_failed("assets_layout")
        self.assert_failed("metadata_consistency")

    def test_removed_repeated_occurrence_is_detected_even_with_updated_body_hash(self):
        article = self.root / "article.md"
        article.write_text(article.read_text(encoding="utf-8").replace("![重复图]", "[重复图]"), encoding="utf-8")
        metadata = self.metadata()
        metadata["content_sha256"] = hashlib.sha256(article.read_bytes()).hexdigest()
        self.write_metadata(metadata)
        self.assert_failed("image_references")

    def test_old_images_directory_and_orphan_asset_are_detected_without_deletion(self):
        old = self.root / "images"
        old.mkdir()
        orphan = self.root / "assets/images/unrecorded.png"
        orphan.write_bytes(PNG)
        result = self.fetch()
        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(result["validation"]["checks"]["assets_layout"]["status"], "failed")
        self.assertTrue(old.is_dir())
        self.assertTrue(orphan.is_file())
        self.assertEqual(self.metadata()["status"], "needs_review")

    def test_wrong_body_hash_is_detected(self):
        article = self.root / "article.md"
        article.write_text(article.read_text(encoding="utf-8") + "正文变化", encoding="utf-8")
        self.assert_failed("metadata_consistency")

    def test_wrong_image_hash_and_format_are_detected(self):
        image = self.root / self.metadata()["images"][0]["path"]
        image.write_bytes(b"<html>not a PNG</html>")
        self.assert_failed("metadata_consistency")

    def test_nonportable_image_path_is_detected(self):
        metadata = self.metadata()
        metadata["images"][0]["path"] = "assets/images/../../article.md"
        self.write_metadata(metadata)
        self.assert_failed("assets_layout")

    def test_source_timestamp_and_path_metadata_are_checked(self):
        for field, value in (("url", "https://example.org/other"), ("accessed_at", "2000-01-01"), ("article_path", str(self.root / "article.md"))):
            with self.subTest(field=field):
                original = self.metadata()
                self.write_metadata({**original, field: value})
                self.assert_failed("metadata_consistency")
                self.write_metadata(original)

    def test_image_download_failure_preserves_remote_embed_and_requires_review(self):
        page = PAGE.replace('<p>末段</p>', '<p>末段</p><img src="/bad.png" alt="失败图">')
        result = self.fetch(page)
        self.assertEqual(result["status"], "needs_review")
        report = result["validation"]
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["counts"]["failed_images"], 1)
        self.assertTrue(report["requires_review"])
        self.assertIn("![失败图](<https://example.org/bad.png>)", (self.root / "article.md").read_text(encoding="utf-8"))

    def test_no_images_and_remote_mode_do_not_require_assets_directory(self):
        for policy in ("remote", "selected"):
            with self.subTest(policy=policy), patch.object(fetcher, "fetch_html", return_value=(PAGE, URL, "http")):
                result = fetcher.fetch_to_directory(URL, self.output / policy, image_policy=policy)
                self.assertEqual(result["validation"]["status"], "passed")
                self.assertFalse(result["validation"]["requires_review"])
                self.assertFalse((self.output / policy / Path(result["article_path"]).parent / "assets").exists())
        result = self.fetch(PAGE.replace('<img data-src="/good.png" alt="原图">', '').replace('<img src="/good.png" alt="重复图">', ''), directory_name="无图片")
        self.assertEqual(result["validation"]["counts"]["image_references"], 0)
        self.assertFalse(result["validation"]["requires_review"])

    def test_missing_selected_image_is_explicitly_reported(self):
        with patch.object(fetcher, "fetch_html", return_value=(PAGE, URL, "http")):
            result = fetcher.fetch_to_directory(URL, self.output / "selected-missing", image_policy="selected", selected_images=["https://example.org/missing.png"])
        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(result["validation"]["status"], "passed")
        self.assertEqual(result["validation"]["counts"]["failed_images"], 1)

    def test_invalid_metadata_and_absent_archive_return_failed_reports(self):
        for value in ("{broken", "[]", '{"status": [], "images": [{"url": "https://example.org/img", "status": []}]}'):
            with self.subTest(value=value):
                (self.root / "metadata.json").write_text(value, encoding="utf-8")
                self.assertEqual(fetcher.validate_archive(self.root)["status"], "failed")
        self.assertEqual(fetcher.validate_archive(self.output / "missing")["status"], "failed")

    def test_validate_only_cli_is_read_only_and_returns_nonzero_on_failure(self):
        script = Path(fetcher.__file__)
        before = (self.root / "metadata.json").read_bytes()
        good = subprocess.run([sys.executable, "-X", "utf8", str(script), "--validate-only", str(self.root)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertEqual(json.loads(good.stdout)["status"], "passed")
        self.assertEqual((self.root / "metadata.json").read_bytes(), before)
        (self.root / "images").mkdir()
        bad = subprocess.run([sys.executable, "-X", "utf8", str(script), "--validate-only", str(self.root)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(bad.returncode, 2)
        self.assertEqual(json.loads(bad.stdout)["checks"]["assets_layout"]["status"], "failed")


WECHAT_URL = "https://mp.weixin.qq.com/s?__biz=Example&mid=100&idx=1&sn=abc"
CAPTCHA_URL = "https://mp.weixin.qq.com/mp/wappoc_appmsgcaptcha?poc_token=example"
CAPTCHA_PAGE = '<html><body><h2>环境异常</h2><p>当前环境异常，完成验证后即可继续访问。</p><a id="js_verify">去验证</a><p>' + '赞，在看，视频，小程序。' * 15 + '</p></body></html>'


class WeChatVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="wechat-verification-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.output = self.base / "articles"

    def fetch_page(self, page, final_url=WECHAT_URL):
        with patch.object(fetcher, "fetch_html", return_value=(page, final_url, "http")):
            return fetcher.fetch_to_directory(WECHAT_URL, self.output, proxy="direct")

    def snapshot(self, **overrides):
        image = "https://mp.weixin.qq.com/good.png"
        data = {"schema_version": 1, "source_url": WECHAT_URL,
                "final_url": WECHAT_URL + "&poc_token=verified", "browser_id": "iab", "tab_id": "same-tab",
                "title": "已验证的微信原文", "body_html": PAGE[PAGE.index('<div id="js_content">'):PAGE.index('</div>') + 6],
                "image_source_order": [image, image], "publisher": "测试公众号", "author": "原作者",
                "published_at": "2026-11-09T09:00:00+08:00"}
        data.update(overrides)
        path = self.base / "snapshot.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return path

    def assert_verification(self, result, expected_url):
        self.assertEqual(result["status"], "verification_required", result)
        self.assertTrue(result["requires_user_action"])
        self.assertEqual(result["final_url"], expected_url)
        self.assertEqual(result["next_action"]["resume_mode"], "same_browser_page")
        self.assertIn("手动", result["user_message"])
        self.assertEqual(result["validation"]["status"], "not_run")
        self.assertIsNone(result["article_path"])
        self.assertEqual(result["images"], [])

    def test_redirected_and_unredirected_verification_pages_are_not_archived(self):
        for final_url, page in ((CAPTCHA_URL, '<html><body>短验证页</body></html>'),
                                (WECHAT_URL, CAPTCHA_PAGE),
                                (WECHAT_URL, CAPTCHA_PAGE.replace('<h2>环境异常</h2>', '<h1>环境异常</h1>').replace('<body>', '<body><div id="js_content">').replace('</body>', '</div></body>'))):
            with self.subTest(final_url=final_url, page=page[:60]):
                result = self.fetch_page(page, final_url)
                self.assert_verification(result, final_url)
                self.assertFalse(self.output.exists())

    def test_http_200_and_403_verification_stop_before_browser_fallback(self):
        for status in (200, 403):
            response = SimpleNamespace(content=CAPTCHA_PAGE.encode("utf-8"), url=CAPTCHA_URL,
                                       status_code=status, headers={"Content-Type": "text/html"}, raise_for_status=MagicMock())
            client = MagicMock()
            client.__enter__.return_value = client
            client.get.return_value = response
            with self.subTest(status=status), patch.object(fetcher, "session", return_value=client) as session_mock:
                result = fetcher.fetch_to_directory(WECHAT_URL, self.output, proxy="direct", browser=True)
                self.assert_verification(result, CAPTCHA_URL)
                session_mock.assert_called_once_with("direct")
                response.raise_for_status.assert_not_called()
                self.assertFalse(self.output.exists())

    def test_wechat_without_article_body_cannot_fall_back_to_page_controls(self):
        result = self.fetch_page('<h1>微信公众平台</h1><article>' + '关注，赞，在看，留言。' * 20 + '</article>')
        self.assertEqual(result["status"], "failed")
        self.assertIn("#js_content", result["error"])
        self.assertFalse(self.output.exists())

    def test_real_article_discussing_verification_is_not_blocked(self):
        page = '<h1>微信验证机制分析</h1><div id="js_content"><p>' + '文章讨论：当前环境异常，完成验证后即可继续访问。' * 6 + '</p></div>'
        result = self.fetch_page(page)
        self.assertEqual(result["status"], "fetched", result)
        self.assertEqual(result["validation"]["status"], "passed")

    def test_verification_overlay_blocks_archiving_even_with_article_underneath(self):
        result = self.fetch_page(PAGE + '<a id="js_verify">去验证</a>')
        self.assert_verification(result, WECHAT_URL)
        self.assertFalse(self.output.exists())

    def test_wechat_uses_exact_article_container_and_requires_a_title(self):
        page = PAGE.replace('<div id="js_content">', '<section id="js_content">').replace('</div>', '</section>')
        result = self.fetch_page(page)
        self.assertEqual(result["status"], "fetched", result)
        body = (self.output / result["article_path"]).read_text(encoding="utf-8")
        self.assertNotIn("微信界面控件", body)
        missing_title = self.fetch_page(page.replace('<h1>测试/文章?</h1>', ''))
        self.assertEqual(missing_title["status"], "failed")
        self.assertIn("title", missing_title["error"])

    def test_failed_retry_leaves_existing_archive_untouched(self):
        good = self.fetch_page(PAGE)
        self.assertEqual(good["status"], "fetched")
        before = {p.relative_to(self.output): p.read_bytes() for p in self.output.rglob("*") if p.is_file()}
        result = self.fetch_page(CAPTCHA_PAGE, CAPTCHA_URL)
        self.assert_verification(result, CAPTCHA_URL)
        after = {p.relative_to(self.output): p.read_bytes() for p in self.output.rglob("*") if p.is_file()}
        self.assertEqual(after, before)

    def test_verified_snapshot_imports_same_tab_and_downloads_images_without_refetching_article(self):
        path = self.snapshot()
        client = MagicMock()
        client.__enter__.return_value = client
        client.get.return_value = SimpleNamespace(content=PNG, raise_for_status=lambda: None)
        with patch.object(fetcher, "fetch_html", side_effect=AssertionError("Must not refetch article HTML")) as fetch_mock, patch.object(fetcher, "session", return_value=client) as session_mock:
            result = fetcher.fetch_to_directory(WECHAT_URL, self.output, image_policy="all", proxy="direct", browser_snapshot=path)
        self.assertEqual(result["status"], "fetched", result)
        fetch_mock.assert_not_called()
        session_mock.assert_called_once_with("direct")
        client.get.assert_called_once()
        self.assertEqual(client.get.call_args.args[0], "https://mp.weixin.qq.com/good.png")
        self.assertEqual(client.get.call_args.kwargs["headers"]["Referer"], WECHAT_URL + "&poc_token=verified")
        root = (self.output / result["article_path"]).parent
        metadata = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["method"], "verified-browser-dom")
        self.assertEqual(metadata["browser_context"], {"browser_id": "iab", "tab_id": "same-tab"})
        self.assertEqual(metadata["url"], WECHAT_URL)
        self.assertEqual(metadata["final_url"], WECHAT_URL + "&poc_token=verified")
        self.assertEqual(metadata["publisher"], "测试公众号")
        self.assertEqual(metadata["author"], "原作者")
        body = (root / "article.md").read_text(encoding="utf-8")
        self.assertTrue(body.startswith('# 已验证的微信原文\n'))
        self.assertIn("开头", body)
        self.assertIn("中段", body)
        self.assertIn("末段", body)
        self.assertNotIn("微信界面控件", body)
        self.assertEqual(metadata["validation"]["counts"]["image_references"], 2)
        self.assertEqual(metadata["validation"]["counts"]["downloaded_images"], 1)
        self.assertFalse(metadata["validation"]["requires_review"])

    def test_invalid_snapshot_provenance_body_or_image_order_is_rejected_without_writes(self):
        for overrides in ({"source_url": WECHAT_URL.replace("mid=100", "mid=200")},
                          {"final_url": WECHAT_URL.replace("mid=100", "mid=200")},
                          {"tab_id": ""}, {"browser_id": ""}, {"schema_version": 2},
                          {"body_html": "<article>" + "这不是微信正文。" * 10 + "</article>"},
                          {"image_source_order": []}):
            with self.subTest(overrides=overrides), patch.object(fetcher, "fetch_html", side_effect=AssertionError("No HTTP retry")) as mock:
                result = fetcher.fetch_to_directory(WECHAT_URL, self.output, browser_snapshot=self.snapshot(**overrides))
                self.assertEqual(result["status"], "failed", result)
                self.assertFalse(self.output.exists())
                mock.assert_not_called()

    def test_snapshot_still_showing_verification_requests_user_action(self):
        for title in ("环境异常", ""):
            with self.subTest(title=title):
                path = self.snapshot(final_url=CAPTCHA_URL, title=title, body_html=CAPTCHA_PAGE, image_source_order=[])
                with patch.object(fetcher, "fetch_html", side_effect=AssertionError("No HTTP retry")) as mock:
                    result = fetcher.fetch_to_directory(WECHAT_URL, self.output, browser_snapshot=path)
                self.assert_verification(result, CAPTCHA_URL)
                self.assertFalse(self.output.exists())
                mock.assert_not_called()

    def test_verification_cli_exit_code_and_manual_prompt(self):
        argv = ["fetch_article.py", "--url", WECHAT_URL, "--output-dir", str(self.output), "--proxy", "direct"]
        with patch.object(sys, "argv", argv), patch.object(fetcher, "fetch_html", return_value=(CAPTCHA_PAGE, CAPTCHA_URL, "http")), patch.object(sys, "stdout", io.StringIO()) as stream:
            code = fetcher.main()
        self.assertEqual(code, 3)
        result = json.loads(stream.getvalue())
        self.assert_verification(result, CAPTCHA_URL)
        self.assertFalse(self.output.exists())

    def test_snapshot_cli_successfully_resumes_without_network_requests(self):
        path = self.snapshot()
        result = subprocess.run([sys.executable, "-X", "utf8", str(Path(fetcher.__file__)),
                                 "--url", WECHAT_URL, "--output-dir", str(self.output), "--images", "remote",
                                 "--proxy", "direct", "--browser-snapshot", str(path)],
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["method"], "verified-browser-dom")
        self.assertEqual(data["validation"]["counts"]["remote_images"], 1)

    def test_managed_verification_uses_legacy_status_with_manual_handoff(self):
        folder = "article-test/versions/" + "a" * 32
        with patch.object(fetcher, "fetch_html", return_value=(CAPTCHA_PAGE, CAPTCHA_URL, "http")):
            result = fetcher.fetch_to_directory(WECHAT_URL, self.output, directory_name=folder)
        self.assertEqual("failed", result["status"])
        self.assertTrue(result["requires_user_action"])
        self.assertEqual("same_browser_page", result["next_action"]["resume_mode"])
        self.assertEqual("not_run", result["validation"]["status"])
        self.assertFalse(self.output.exists())

    def test_snapshot_import_keeps_managed_version_paths_without_http_requests(self):
        folder = "article-test/versions/" + "a" * 32
        with patch.object(fetcher, "fetch_html", side_effect=AssertionError("No HTTP retry")) as request:
            result = fetcher.fetch_to_directory(WECHAT_URL, self.output, directory_name=folder,
                                                browser_snapshot=self.snapshot())
        request.assert_not_called()
        self.assertEqual("fetched", result["status"], result)
        self.assertEqual(folder + "/article.md", result["article_path"])
        self.assertEqual("passed", result["validation"]["status"])

    def test_research_refresh_preserves_accepted_body_when_verification_is_required(self):
        import importlib.util

        path = Path(fetcher.__file__).resolve().parents[2] / "research-common/scripts/research_articles.py"
        spec = importlib.util.spec_from_file_location("research_verification_test", path)
        articles = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(articles)
        work = self.base / "work"
        work.mkdir()
        outline = {"work_dir": str(work), "run_id": "verification-test", "reference_articles": [WECHAT_URL]}
        with patch.object(articles, "fetcher", return_value=fetcher), \
                patch.object(fetcher, "fetch_html", return_value=(PAGE, WECHAT_URL, "http")):
            articles.acquire(outline, proxy="direct")
        key = articles.requirements(outline)[0]["id"]
        data = articles.load_manifest(outline)
        record = data["articles"][key]
        record["review_status"] = "accepted"
        articles.save_manifest(outline, data)
        previous = dict(record)
        body = work / record["local_path"]
        before = body.read_bytes()
        with patch.object(articles, "fetcher", return_value=fetcher), \
                patch.object(fetcher, "fetch_html", return_value=(CAPTCHA_PAGE, CAPTCHA_URL, "http")):
            state = articles.acquire(outline, proxy="direct", refresh=True)
        current = articles.load_manifest(outline)["articles"][key]
        for field in ("status", "review_status", "local_path", "content_sha256", "fetched_at", "accessed_at", "archive"):
            self.assertEqual(previous[field], current[field], field)
        self.assertEqual(before, body.read_bytes())
        self.assertEqual("failed", current["last_fetch_attempt"]["status"])
        self.assertTrue(current["refresh_gap"])
        self.assertTrue(state["gaps"])

    def test_validator_rejects_legacy_archive_pointing_to_verification_url(self):
        result = self.fetch_page(PAGE)
        root = (self.output / result["article_path"]).parent
        path = root / "metadata.json"
        metadata = json.loads(path.read_text(encoding="utf-8"))
        metadata["final_url"] = CAPTCHA_URL
        path.write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")
        report = fetcher.validate_archive(root)
        self.assertEqual(report["checks"]["metadata_consistency"]["status"], "failed")
        self.assertTrue(report["requires_review"])


if __name__ == "__main__":
    unittest.main()
