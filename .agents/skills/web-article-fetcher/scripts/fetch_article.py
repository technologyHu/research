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


def article_id(url):
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("Article URL must be HTTP(S) without embedded credentials")
    canonical = urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path, parsed.query, ""))
    return "article-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def clean_filename(name):
    value = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", name).strip(" .")[:90]
    return value or "article"


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
        local = "images/" + record["id"] + "." + extension
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
    pattern = r"!\[([^\]\n]*)\]\(\s*(?:<([^>]+)>|([^\s)]+))\s*\)"
    def replace(match):
        target = match[2] or match[3]
        return "![" + match[1] + "](<" + replacements.get(target, target) + ">)"
    return re.sub(pattern, replace, markdown)


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
    folder = directory_name or key
    root = safe_target(Path(output_dir), folder)
    root.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    result = {"schema_version": 1, "id": key, "url": url, "final_url": url, "status": "failed", "title": "",
              "accessed_at": now.date().isoformat(), "fetched_at": now.isoformat(), "article_path": None, "images": []}
    try:
        if image_policy not in {"remote", "all", "selected"}: raise ValueError("Invalid image policy")
        html, final_url, method = fetch_html(url, proxy, browser)
        parsed = parse_html(html, final_url)
        body = parsed.pop("body")
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
            result["images"].append({"url": missing, "status": "failed", "path": None, "error": "Selected image was not found in the article"})
        markdown = "# " + parsed["title"] + "\n\nSource: " + url + "\n\nAccessed (UTC): " + result["accessed_at"] + "\n\n" + image_links(body, replacements) + "\n"
        target = safe_target(root, "article.md")
        target.write_text(markdown, encoding="utf-8")
        result.update(parsed, final_url=final_url, method=method, status="needs_review" if parsed["quality"] == "body-fallback" else "fetched",
                      article_path=folder + "/article.md", content_sha256=hashlib.sha256(target.read_bytes()).hexdigest())
        for image in result["images"]:
            if image.get("path"): image["path"] = folder + "/" + image["path"]
    except Exception as exc:
        result["error"] = str(exc)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--images", choices=("remote", "all", "selected"), default="all")
    parser.add_argument("--image-url", action="append", default=[])
    parser.add_argument("--proxy", choices=("env", "direct"), default="env")
    parser.add_argument("--browser", action="store_true", help="Allow an available Playwright browser fallback on HTTP 403")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    try:
        result = fetch_to_directory(args.url, args.output_dir, args.images, args.image_url, args.proxy, args.browser)
    except (OSError, ValueError) as exc:
        result = {"status": "failed", "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "fetched" else 2 if result["status"] == "needs_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
