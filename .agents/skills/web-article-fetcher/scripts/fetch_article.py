#!/usr/bin/env python3
"""Fetch an article into a caller-selected directory; imports and network are lazy."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urljoin, urlsplit, urlunsplit
import xml.etree.ElementTree as ET

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ArticleReader/1.0)", "Accept": "text/html,application/xhtml+xml", "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"}
IMAGE_PATTERN = r"!\[([^\]\n]*)\]\(\s*(?:<([^>]+)>|([^\s)]+))\s*\)"


def article_id(url):
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("Article URL must be HTTP(S) without embedded credentials")
    canonical = urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path, parsed.query, ""))
    return "article-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def clean_filename(name):
    value = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", name).strip(" .")[:90].rstrip(" .")
    if re.fullmatch(r"CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³]", value.split(".", 1)[0], re.I):
        value = "_" + value
    return value or "article"


def article_folder(output_dir, title, url):
    """Use a readable title, reusing only folders belonging to this URL."""
    key = article_id(url)
    base = clean_filename(title) if title.strip() and title.strip() != "untitled" else key
    candidate, index = base, 0
    while True:
        target = safe_target(Path(output_dir), candidate)
        if not target.exists():
            return candidate
        article = safe_target(target, "article.md") if target.is_dir() else None
        if article and article.is_file():
            try:
                saved = article.read_text(encoding="utf-8")
                source = re.search(r"^Source: (.+)$", saved, re.M)
                if source and article_id(source[1].strip()) == key:
                    return candidate
            except (OSError, UnicodeError, ValueError):
                pass
        index += 1
        candidate = base + "--" + key.removeprefix("article-")
        if index > 1:
            candidate += "-" + str(index)


def safe_target(root, relative):
    root = Path(root).resolve()
    target = root / relative
    if target.is_absolute() and not target.resolve().is_relative_to(root):
        raise ValueError("Output path escapes the selected directory")
    for entry in (target, *target.parents):
        if entry.is_symlink() or getattr(entry, "is_junction", lambda: False)():
            raise ValueError("Linked output paths are not accepted")
        if entry == root:
            break
    return target


def session(proxy="env"):
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("Missing requests; use an available environment or install it in the task's temporary environment") from exc
    client = requests.Session()
    client.trust_env = proxy != "direct"
    return client


def fetch_html(url, proxy="env", browser=False):
    with session(proxy) as client:
        response = client.get(url, headers=HEADERS, timeout=30)
        if response.status_code == 403 and browser:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as engine:
                instance = engine.chromium.launch(headless=True)
                try:
                    page = instance.new_page()
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    return page.content(), page.url, "browser"
                finally:
                    instance.close()
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").lower()
        if content_type and not any(kind in content_type for kind in ("text/html", "application/xhtml")):
            raise ValueError("Expected HTML; route PDF or other documents through their reader")
        try:
            html = response.content.decode("utf-8-sig")
        except UnicodeDecodeError:
            html = response.text
        return html, response.url, "http"


def image_extension(data):
    if data.startswith(b"\x89PNG\r\n\x1a\n"): return "png"
    if data.startswith(b"\xff\xd8\xff"): return "jpg"
    if data.startswith((b"GIF87a", b"GIF89a")): return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP": return "webp"
    if data.startswith(b"BM"): return "bmp"
    if data.startswith((b"II*\x00", b"MM\x00*")): return "tiff"
    if data[4:8] == b"ftyp" and data[8:12] in {b"avif", b"avis"}: return "avif"
    try:
        if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper(): return None
        element = ET.fromstring(data)
        if element.tag.rsplit("}", 1)[-1] == "svg": return "svg"
    except (ET.ParseError, ValueError):
        pass
    return None


def download_image(url, root, referer="", proxy="env"):
    record = {"id": "image-" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:16], "url": url, "status": "failed", "path": None}
    try:
        article_id(url)
        with session(proxy) as client:
            response = client.get(url, headers={**HEADERS, "Referer": referer}, timeout=30)
            response.raise_for_status()
            data = response.content
        extension = image_extension(data)
        if not extension:
            raise ValueError("Response is not a recognized image (HTML error pages are rejected)")
        local = "assets/images/" + record["id"] + "." + extension
        target = safe_target(root, local)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        record.update(status="downloaded", path=local, sha256=hashlib.sha256(data).hexdigest())
    except Exception as exc:
        record["error"] = str(exc)
    return record


def extract_title(soup: BeautifulSoup) -> str:
    """Extract the article title from the page."""
    # Try h1 first (most common for article titles)
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    else:
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else "untitled"

    # Remove common suffixes that CSDN/Zhihu/Juejin add
    for suffix in ["-CSDN.NET", "-CSDN博客", " - 知乎", " - 掘金"]:
        title = title.replace(suffix, "")
    return title.strip()


def _is_raw_markdown(text: str) -> bool:
    """Detect whether text is already markdown rather than HTML.

    Nuxt/Vue SSR sites sometimes render article content as raw markdown
    inside a v-html div, using &gt; for blockquote markers and keeping
    ## headings intact. Running markdownify on this would double-process
    it into garbled output.
    """
    lines = text.strip().splitlines()
    markdown_indicators = 0
    for line in lines[:10]:
        stripped = line.strip()
        if stripped.startswith("&gt;") or stripped.startswith(">"):
            markdown_indicators += 1
        if stripped.startswith("##") or stripped.startswith("# "):
            markdown_indicators += 1
    # If 3+ of the first 10 lines look like markdown, treat it as pre-formatted
    return markdown_indicators >= 3


def convert_lazy_images(soup: BeautifulSoup) -> None:
    """Convert lazy-loaded images (data-src) to regular images (src).

    Many Chinese sites (WeChat MP, CSDN, etc.) use data-src for lazy loading.
    This converts them to src so markdownify can extract them properly.
    Modifies soup in-place.
    """
    for img in soup.find_all("img"):
        data_src = img.get("data-src") or img.get("data-original")
        if data_src and not img.get("src"):
            img["src"] = data_src
            # Clean up data attributes
            for attr in ["data-src", "data-original", "data-type"]:
                if img.has_attr(attr):
                    del img[attr]


def extract_content(soup: BeautifulSoup) -> tuple:
    """Extract the main article content area from the page.

    Returns (content_element, is_raw_markdown). When is_raw_markdown is True,
    the caller should skip markdownify and use get_text() directly (with
    HTML entity cleanup) instead.
    """
    # First, convert lazy-loaded images so they can be extracted
    convert_lazy_images(soup)

    # Site-specific selectors
    selectors = [
        ("div", {"id": "js_content"}),                # WeChat MP
        ("div", {"id": "article_content"}),           # CSDN
        ("div", {"class": "article_content"}),        # CSDN
        ("div", {"class": "Post-RichTextContainer"}), # 知乎专栏
        ("article", {}),                              # Generic
        ("div", {"class": "Post-Main"}),              # 知乎旧版
        ("div", {"class": "main-content"}),           # 通用
        ("div", {"class": lambda c: c and "article" in str(c).lower() if c else False}),
    ]

    for tag, attrs in selectors:
        result = soup.find(tag, **attrs)
        if result and len(result.get_text(strip=True)) > 40:
            text = result.get_text()
            if _is_raw_markdown(text):
                return result, True
            return result, False

    # Fallback for Nuxt/Vue SSR sites (showapi.com etc):
    # These render article content as raw markdown text inside bare divs
    # (no class, no id), often with data-v-* scoped style attributes.
    # The text starts with ">" or "##" and is already valid markdown.
    for div in soup.find_all("div"):
        if not div.get("class") and not div.get("id"):
            text = div.get_text()
            if len(text.strip()) > 500:
                if _is_raw_markdown(text):
                    return div, True
                if text.strip().startswith(">"):
                    return div, True

    # Fallback: use the body
    return soup.body or soup, False


def image_links(markdown, replacements):
    # Only image targets change; ordinary hyperlinks to the same URL stay intact.
    def replace(match):
        target = replacements.get(match[2] or match[3], match[2] or match[3])
        # PyCharm 2026.1 can treat angle brackets as part of a local path.
        # Generated asset names need no destination delimiters.
        if not urlsplit(target).scheme and not re.search(r"[\s()<>]", target):
            return "![" + match[1] + "](" + target + ")"
        return "![" + match[1] + "](<" + target + ">)"
    return re.sub(IMAGE_PATTERN, replace, markdown)


def image_targets(markdown):
    return [match[2] or match[3] for match in re.finditer(IMAGE_PATTERN, markdown)]


def validate_archive(article_dir):
    """Check the saved archive without network access or changing its files."""
    root = Path(article_dir).absolute()
    checks = {name: {"status": "passed", "errors": []} for name in (
        "directory_name", "image_references", "assets_layout", "metadata_consistency")}
    report = {"status": "passed", "checked_at": datetime.now(timezone.utc).isoformat(),
              "checks": checks, "warnings": [], "counts": {
                  "image_references": 0, "downloaded_images": 0, "failed_images": 0, "remote_images": 0}}

    def fail(check, message):
        checks[check]["status"] = "failed"
        checks[check]["errors"].append(message)

    def finish():
        report["status"] = "failed" if any(item["errors"] for item in checks.values()) else "passed"
        report["requires_review"] = report["status"] == "failed" or bool(report["warnings"])
        return report

    try:
        metadata = json.loads(safe_target(root, "metadata.json").read_text(encoding="utf-8"))
        if not isinstance(metadata, dict):
            raise ValueError("metadata.json must contain an object")
        article = safe_target(root, "article.md")
        markdown = article.read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        for check in checks:
            fail(check, "Cannot read archive: " + str(exc))
        return finish()

    try:
        key = article_id(metadata["url"])
        article_id(metadata["final_url"])
        title = metadata["title"]
        if not isinstance(title, str):
            raise ValueError("title must be a string")
        explicit = metadata.get("directory_name")
        expected = Path(explicit).name if explicit else article_folder(root.parent, title, metadata["url"])
        if root.name != expected:
            fail("directory_name", "Expected directory name: " + expected)
        if metadata.get("id") != key:
            fail("metadata_consistency", "Article ID does not match source URL")
        if not markdown.startswith("# " + title + "\n"):
            fail("metadata_consistency", "Article heading does not match metadata title")
        if not re.search(r"^Source: " + re.escape(metadata["url"]) + r"$", markdown, re.M):
            fail("metadata_consistency", "Article source URL does not match metadata")
        fetched = datetime.fromisoformat(metadata["fetched_at"])
        if fetched.tzinfo is None or fetched.astimezone(timezone.utc).date().isoformat() != metadata["accessed_at"]:
            fail("metadata_consistency", "Fetch timestamp and UTC access date disagree")
        if not re.search(r"^Accessed \(UTC\): " + re.escape(metadata["accessed_at"]) + r"$", markdown, re.M):
            fail("metadata_consistency", "Article access date does not match metadata")
    except (KeyError, TypeError, ValueError, OSError) as exc:
        fail("directory_name", "Cannot verify title directory: " + str(exc))
        fail("metadata_consistency", "Invalid source or timestamp metadata: " + str(exc))

    if metadata.get("article_path") != "article.md":
        fail("metadata_consistency", "article_path must be relative to the article directory: article.md")
    if metadata.get("content_sha256") != hashlib.sha256(article.read_bytes()).hexdigest():
        fail("metadata_consistency", "Article SHA-256 does not match saved bytes")
    if metadata.get("schema_version") != 1 or not isinstance(metadata.get("status"), str) or metadata["status"] not in {"fetched", "needs_review"}:
        fail("metadata_consistency", "Invalid metadata schema version or extraction status")
    if metadata.get("quality") == "body-fallback":
        report["warnings"].append("Full-page extraction still requires a manual body-boundary review")

    records = metadata.get("images")
    if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
        fail("metadata_consistency", "images must be a list of image records")
        records = []
    by_url, downloaded_paths = {}, set()
    for image in records:
        url, status, relative = image.get("url"), image.get("status"), image.get("path")
        if not isinstance(url, str) or url in by_url:
            fail("metadata_consistency", "Missing or duplicate image URL: " + str(url))
            continue
        by_url[url] = image
        try:
            article_id(url)
        except ValueError as exc:
            fail("metadata_consistency", "Invalid image URL: " + str(exc))
        count_key = {"downloaded": "downloaded_images", "failed": "failed_images", "remote": "remote_images"}.get(status) if isinstance(status, str) else None
        if not count_key:
            fail("metadata_consistency", "Invalid image status: " + str(status))
            continue
        report["counts"][count_key] += 1
        if status != "downloaded":
            if relative is not None:
                fail("metadata_consistency", "Undownloaded image must not declare a local path: " + url)
            if status == "failed":
                report["warnings"].append("Image download failed: " + url)
                if not image.get("error"):
                    fail("metadata_consistency", "Failed image is missing its error reason: " + url)
            continue
        try:
            if not isinstance(relative, str) or not relative.startswith("assets/images/") or "\\" in relative or ".." in Path(relative).parts:
                raise ValueError("Image path must be portable and inside assets/images/")
            path = safe_target(root, relative)
            downloaded_paths.add(relative)
            data = path.read_bytes()
            if not image_extension(data) or image_extension(data) != path.suffix[1:].lower():
                fail("metadata_consistency", "Image format does not match its extension: " + relative)
            if image.get("sha256") != hashlib.sha256(data).hexdigest():
                fail("metadata_consistency", "Image SHA-256 does not match saved bytes: " + relative)
        except (OSError, ValueError) as exc:
            fail("image_references", "Invalid local image " + str(relative) + ": " + str(exc))
            fail("assets_layout", "Invalid local image " + str(relative) + ": " + str(exc))
            fail("metadata_consistency", "Invalid local image " + str(relative) + ": " + str(exc))

    targets = image_targets(markdown)
    for match in re.finditer(IMAGE_PATTERN, markdown):
        if match[2] in downloaded_paths and not re.search(r"[\s()<>]", match[2]):
            fail("image_references", "Local asset references must use plain relative paths for IDE compatibility: " + match[2])
    report["counts"]["image_references"] = len(targets)
    source_order = metadata.get("image_source_order")
    if not isinstance(source_order, list) or not all(isinstance(url, str) for url in source_order):
        fail("metadata_consistency", "Missing image_source_order; refetch to record all source image occurrences")
        source_order = [url for url, image in by_url.items() if image.get("in_article", True)]
    expected_targets = []
    for url in source_order:
        image = by_url.get(url)
        if image is None:
            fail("metadata_consistency", "Source image has no metadata record: " + url)
            continue
        expected_targets.append(image.get("path") if image.get("status") == "downloaded" else url)
    for url, image in by_url.items():
        if url not in source_order and image.get("in_article", True):
            fail("metadata_consistency", "Image record does not occur in source body: " + url)
    if targets != expected_targets:
        fail("image_references", "Image references differ from source occurrence order or recorded download paths")

    try:
        for entry in root.iterdir():
            if entry.name not in {"article.md", "metadata.json", "assets"}:
                fail("assets_layout", "Unexpected file or directory outside assets/: " + entry.name)
        assets = safe_target(root, "assets")
        if assets.exists() and not assets.is_dir():
            fail("assets_layout", "assets must be a directory")
        saved_images = set()
        for entry in assets.rglob("*"):
            relative = entry.relative_to(root).as_posix()
            safe_target(root, relative)
            if entry.is_file() and relative.startswith("assets/images/"):
                saved_images.add(relative)
        for relative in sorted(saved_images - downloaded_paths):
            fail("assets_layout", "Unrecorded image asset: " + relative)
        for relative in sorted(downloaded_paths - saved_images):
            fail("assets_layout", "Recorded image asset is missing: " + relative)
    except (OSError, ValueError) as exc:
        fail("assets_layout", str(exc))
    return finish()


def parse_html(html, final_url):
    try:
        from bs4 import BeautifulSoup, NavigableString
        from markdownify import markdownify
    except ImportError as exc:
        raise RuntimeError("Missing beautifulsoup4 or markdownify; use a suitable temporary environment") from exc
    soup = BeautifulSoup(html, "html.parser")
    title = extract_title(soup)
    content, raw = extract_content(soup)
    fallback = content is soup.body or content is soup
    if fallback and re.search(r"captcha|just a moment|security check|访问验证|安全验证|人机验证|登录后.*阅读", title + " " + content.get_text(" "), re.I):
        raise ValueError("Login or verification page; article body was not obtained")
    for tag in content.find_all(["script", "style", "nav", "footer", "noscript"]):
        tag.decompose()
    for link in content.find_all("a", href=True):
        value = urljoin(final_url, link["href"])
        if urlsplit(value).scheme in {"http", "https", "mailto"}:
            link["href"] = value
        else:
            link.attrs.pop("href", None)
    urls, tokens = [], {}
    for index, image in enumerate(list(content.find_all("img"))):
        source = image.get("data-src") or image.get("data-original") or image.get("src", "")
        url = urljoin(final_url, source)
        if urlsplit(url).scheme not in {"http", "https"}:
            image.decompose()
            continue
        if url not in urls: urls.append(url)
        alt = str(image.get("alt", "")).replace("[", "").replace("]", "").replace("\n", " ")
        marker = "ARTICLEIMAGE" + str(index) + "TOKEN"
        tokens[marker] = "![" + alt + "](<" + url + ">)"
        image.replace_with(NavigableString(marker))
    markdown = content.get_text() if raw else markdownify(str(content), heading_style="ATX")
    for marker, image in tokens.items(): markdown = markdown.replace(marker, image)
    lines = markdown.strip().splitlines()
    if lines and lines[0].strip() == "# " + title:
        markdown = "\n".join(lines[1:]).lstrip()
    # Raw Markdown sources can contain image syntax without HTML img tags.
    for match in re.finditer(r"!\[[^\]]*\]\((?:<([^>]+)>|([^\s)]+))\)", markdown):
        source = match[1] or match[2]
        url = urljoin(final_url, source)
        if urlsplit(url).scheme in {"http", "https"}:
            if url not in urls: urls.append(url)
            markdown = image_links(markdown, {source: url})
    if len(markdown.strip()) < 40:
        raise ValueError("Extracted body is too short; save and review it through the manual import path")
    published = soup.find("meta", attrs={"property": "article:published_time"})
    author = soup.find("meta", attrs={"name": "author"})
    return {"title": title, "body": markdown.strip(), "image_urls": urls, "quality": "body-fallback" if fallback else "article-selector",
            "published_at": published.get("content") if published else None, "author": author.get("content") if author else None}


def fetch_to_directory(url, output_dir, image_policy="remote", selected_images=(), proxy="env", browser=False, directory_name=None):
    key = article_id(url)
    now = datetime.now(timezone.utc)
    result = {"schema_version": 1, "id": key, "url": url, "final_url": url, "status": "failed", "title": "",
              "accessed_at": now.date().isoformat(), "fetched_at": now.isoformat(), "article_path": None, "images": []}
    try:
        if image_policy not in {"remote", "all", "selected"}: raise ValueError("Invalid image policy")
        html, final_url, method = fetch_html(url, proxy, browser)
        parsed = parse_html(html, final_url)
        folder = directory_name or article_folder(output_dir, parsed["title"], url)
        root = safe_target(Path(output_dir), folder)
        root.mkdir(parents=True, exist_ok=True)
        body = parsed.pop("body")
        result.update(image_source_order=image_targets(body), image_policy=image_policy, directory_name=directory_name)
        urls = parsed.pop("image_urls")
        selected = set(selected_images)
        replacements = {}
        for image_url in urls:
            if image_policy == "all" or (image_policy == "selected" and image_url in selected):
                image = download_image(image_url, root, final_url, proxy)
                if image["status"] == "downloaded": replacements[image_url] = image["path"]
            else:
                image = {"id": "image-" + hashlib.sha256(image_url.encode("utf-8")).hexdigest()[:16], "url": image_url, "status": "remote", "path": None}
            result["images"].append(image)
        for missing in sorted(selected - set(urls)):
            result["images"].append({"url": missing, "status": "failed", "path": None, "in_article": False, "error": "Selected image was not found in the article"})
        markdown = "# " + parsed["title"] + "\n\nSource: " + url + "\n\nAccessed (UTC): " + result["accessed_at"] + "\n\n" + image_links(body, replacements) + "\n"
        target = safe_target(root, "article.md")
        target.write_text(markdown, encoding="utf-8")
        result.update(parsed, final_url=final_url, method=method, status="needs_review" if parsed["quality"] == "body-fallback" else "fetched",
                      article_path=folder + "/article.md", content_sha256=hashlib.sha256(target.read_bytes()).hexdigest())
        # Keep the archive portable; stdout paths remain relative to output_dir.
        metadata = {**result, "article_path": "article.md", "images": [dict(image) for image in result["images"]]}
        safe_target(root, "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result["validation"] = validate_archive(root)
        if result["validation"]["requires_review"]:
            result["status"] = "needs_review"
        metadata.update(status=result["status"], validation=result["validation"])
        safe_target(root, "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        for image in result["images"]:
            if image.get("path"): image["path"] = folder + "/" + image["path"]
    except Exception as exc:
        result["status"] = "failed"
        result["error"] = str(exc)
        result["validation"] = {"status": "not_run", "reason": "Article archive was not completed successfully"}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--validate-only", type=Path, help="Check an existing article directory without fetching or writing")
    parser.add_argument("--images", choices=("remote", "all", "selected"), default="all")
    parser.add_argument("--image-url", action="append", default=[])
    parser.add_argument("--proxy", choices=("env", "direct"), default="env")
    parser.add_argument("--browser", action="store_true", help="Allow an available Playwright browser fallback on HTTP 403")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    if args.validate_only:
        if args.url or args.output_dir:
            parser.error("--validate-only cannot be combined with --url or --output-dir")
        report = validate_archive(args.validate_only)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2 if report["requires_review"] else 0
    if not args.url or not args.output_dir:
        parser.error("--url and --output-dir are required for fetching")
    try:
        result = fetch_to_directory(args.url, args.output_dir, args.images, args.image_url, args.proxy, args.browser)
    except (OSError, ValueError) as exc:
        result = {"status": "failed", "error": str(exc), "validation": {"status": "not_run", "reason": "Article archive was not produced"}}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "fetched" else 2 if result["status"] == "needs_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
