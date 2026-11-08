"""Offline regression checks for automatic article archive validation.

Run: python -X utf8 -m unittest discover -s <skill>/scripts -p test_fetch_article.py
"""

import base64
import hashlib
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

    def fetch(self, page=PAGE, **kwargs):
        client = MagicMock()
        client.__enter__.return_value = client
        client.get.side_effect = lambda url, **options: SimpleNamespace(
            content=PNG if url.endswith("good.png") else b"<html>Image error</html>",
            raise_for_status=lambda: None)
        with patch.object(fetcher, "fetch_html", return_value=(page, URL, "http")), patch.object(fetcher, "session", return_value=client):
            return fetcher.fetch_to_directory(URL, self.output, image_policy="all", **kwargs)

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


if __name__ == "__main__":
    unittest.main()
