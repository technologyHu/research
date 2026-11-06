"""Task-local article acquisition, explicit body review and cited-source archiving."""

from datetime import datetime, timezone
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import os
import tempfile
import uuid
from urllib.parse import urlsplit, urlunsplit, unquote


def canonical(url):
    if not isinstance(url, str):
        raise ValueError("Reference article URL must be a string")
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError("Reference article URL must be HTTP(S), without embedded credentials")
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path, parsed.query, ""))


def requirements(outline):
    entries = outline.get("reference_articles", [])
    if not isinstance(entries, list):
        raise ValueError("reference_articles must be a list")
    output, urls, ids = [], {}, set()
    for raw in entries:
        raw = {"url": raw} if isinstance(raw, str) else raw
        if not isinstance(raw, dict):
            raise ValueError("Each reference article needs a URL")
        url = canonical(raw.get("url"))
        required = raw.get("required", True)
        if type(required) is not bool:
            raise ValueError("Article required must be a boolean")
        if url in urls:
            urls[url]["required"] |= required
            continue
        key = raw.get("id", "article-" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:16])
        if not isinstance(key, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", key) or key in ids:
            raise ValueError("Reference articles need unique path-safe ids")
        record = {"id": key, "url": url, "required": required}
        ids.add(key)
        urls[url] = record
        output.append(record)
    return output


def local(root, value):
    if not isinstance(value, str) or not value:
        raise ValueError("Article file needs a relative path")
    name = PurePosixPath(value)
    if name.is_absolute() or str(name) != value or any(char in value for char in "\\:*?\0") or any(part in {"..", ".git", ".agents"} for part in name.parts):
        raise ValueError("Unsafe article file path")
    root = Path(root).resolve()
    target = root / value
    if not target.resolve().is_relative_to(root):
        raise ValueError("Article file escapes its root")
    for entry in (target, *target.parents):
        if entry.is_symlink() or getattr(entry, "is_junction", lambda: False)():
            raise ValueError("Linked article files are not accepted")
        if entry == root:
            break
    return target


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_manifest(outline):
    path = local(outline["work_dir"], "articles.json")
    if not path.exists():
        return {"schema_version": 1, "run_id": outline["run_id"], "articles": {}}
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or data.get("schema_version") != 1 or data.get("run_id") != outline["run_id"] or not isinstance(data.get("articles"), dict):
        raise ValueError("Invalid articles.json or mismatched task run_id")
    for record in data["articles"].values():
        if not isinstance(record, dict):
            raise ValueError("Each article manifest record must be a mapping")
        canonical(record.get("url"))
        if not isinstance(record.get("images", []), list) or any(not isinstance(image, dict) for image in record.get("images", [])):
            raise ValueError("Article image records must be a list of mappings")
        history = record.get("previous_versions", [])
        if not isinstance(history, list) or any(not isinstance(version, dict) or not isinstance(version.get("images", []), list) or any(not isinstance(image, dict) for image in version.get("images", [])) for version in history):
            raise ValueError("Invalid previous article versions")
        if "requires_result_review" in record and type(record["requires_result_review"]) is not bool:
            raise ValueError("requires_result_review must be a boolean")
    return data


def save_manifest(outline, data):
    target = local(outline["work_dir"], "articles.json")
    scratch = local(outline["work_dir"], "scratch")
    scratch.mkdir(exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", prefix=".articles-", dir=scratch, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        temporary.replace(target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def fetcher():
    path = Path(__file__).resolve().parents[2] / "web-article-fetcher/scripts/fetch_article.py"
    spec = importlib.util.spec_from_file_location("research_article_fetcher", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assessment(outline):
    requested = requirements(outline)
    data = load_manifest(outline)
    gaps, entries = [], []
    for wanted in requested:
        record = data["articles"].get(wanted["id"])
        if record is not None and (not isinstance(record, dict) or canonical(record.get("url")) != wanted["url"]):
            raise ValueError("Article record does not match its requested URL")
        status = record.get("status", "pending") if record else "pending"
        if status not in {"pending", "fetched", "needs_review", "failed"}:
            raise ValueError("Invalid article acquisition status")
        accepted = bool(record and status == "fetched" and record.get("review_status") == "accepted")
        if record and status in {"fetched", "needs_review"}:
            body = local(outline["work_dir"], record.get("local_path"))
            if not body.is_relative_to(Path(outline["work_dir"]) / "sources/articles") or not body.is_file() or sha(body) != record.get("content_sha256"):
                raise ValueError(f"Missing or changed article body: {wanted['id']}")
            try:
                datetime.fromisoformat(record["fetched_at"])
                datetime.strptime(record["accessed_at"], "%Y-%m-%d")
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("Fetched article needs actual access timestamps") from exc
        if wanted["required"] and not accepted:
            reason = record.get("error") or record.get("review_reason") or "正文尚未核对" if record else "尚未抓取"
            gaps.append({"id": wanted["id"], "url": wanted["url"], "reason": reason})
        elif record and record.get("refresh_gap"):
            gaps.append({"id": wanted["id"], "url": wanted["url"], "reason": record["refresh_gap"]})
        entries.append({**wanted, "status": status, "review_status": record.get("review_status", "pending") if record else "pending"})
    digest = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return {"entries": entries, "gaps": gaps, "manifest_digest": digest}


def remote_markdown(outline, record):
    work = Path(outline["work_dir"])
    source = local(work, record["local_path"])
    replacements = {}
    for image in record.get("images", []):
        for field in ("path", "body_path"):
            if image.get(field):
                target = local(work, image[field])
                replacements[Path(os.path.relpath(target, source.parent)).as_posix()] = image["url"]
    return fetcher().image_links(source.read_text(encoding="utf-8-sig"), replacements)


def body_fingerprint(outline, record):
    # Retrieval headers and image-cache locations do not change the source body.
    text = remote_markdown(outline, record).replace("\r\n", "\n")
    text = re.sub(r"\A(# [^\n]+\n\nSource: [^\n]+\n\n)Accessed(?: \(UTC\))?: [^\n]+\n\n", r"\1", text, count=1)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def commit_candidate(outline, data, key, result):
    """Commit an already-written candidate; no active body file is overwritten."""
    previous = data["articles"].get(key, {})
    obtained_before = previous.get("status") in {"fetched", "needs_review"} and bool(previous.get("local_path"))
    valid_previous = False
    if obtained_before:
        source = local(outline["work_dir"], previous["local_path"])
        valid_previous = source.is_file() and sha(source) == previous.get("content_sha256")
    attempt = {name: result.get(name) for name in ("status", "error", "fetched_at", "accessed_at", "final_url")}
    if valid_previous and result.get("status") == "failed":
        previous["last_fetch_attempt"] = attempt
        previous["refresh_gap"] = "刷新失败，沿用原访问日期 " + previous.get("accessed_at", "未知") + " 的旧版本：" + str(result.get("error", "未取得正文"))
    elif valid_previous and result.get("status") in {"fetched", "needs_review"} and body_fingerprint(outline, previous) == body_fingerprint(outline, result):
        previous["last_fetch_attempt"] = {**attempt, "status": "unchanged"}
        previous.pop("refresh_gap", None)
    else:
        result.update(review_status="pending", archive=None)
        result["requires_result_review"] = bool(previous.get("requires_result_review") or obtained_before)
        if previous:
            result["previous_versions"] = [*previous.get("previous_versions", []), {name: value for name, value in deepcopy(previous).items() if name != "previous_versions"}]
        data["articles"][key] = result
    save_manifest(outline, data)


def download_images(outline, key, urls=(), proxy="env", refresh=False, all_images=False):
    assessment(outline)
    data = load_manifest(outline)
    record = data["articles"].get(key)
    if not record or record.get("status") not in {"fetched", "needs_review"}:
        raise ValueError("Obtain the article body before downloading its images")
    images = {image["url"]: image for image in record.get("images", [])}
    selected = list(images) if all_images else list(dict.fromkeys(urls))
    if all_images and not selected:
        return {"id": key, "attempts": [], "failures": []}
    if not selected or not set(selected) <= images.keys():
        raise ValueError("Select image URLs actually listed in this article, or use --all")
    engine, attempts = fetcher(), []
    prefix = f"sources/articles/{key}/image-downloads/{uuid.uuid4().hex}"
    root = local(outline["work_dir"], prefix)
    for url in selected:
        previous = images[url]
        path = local(outline["work_dir"], previous["path"]) if previous.get("path") else None
        valid = previous.get("status") == "downloaded" and path is not None and path.is_file() and sha(path) == previous.get("sha256")
        if valid and not refresh:
            continue
        result = engine.download_image(url, root, record.get("final_url", record["url"]), proxy)
        result["attempted_at"] = datetime.now(timezone.utc).isoformat()
        attempts.append(result)
        if result.get("status") == "downloaded":
            result["path"] = prefix + "/" + result["path"]
            if previous.get("body_path") or previous.get("path"):
                result["body_path"] = previous.get("body_path") or previous["path"]
            images[url] = result
        elif valid:
            images[url] = {**previous, "last_download_attempt": result}
        else:
            images[url] = result
    if attempts:
        record["images"] = list(images.values())
        save_manifest(outline, data)
    return {"id": key, "attempts": attempts, "failures": [attempt for attempt in attempts if attempt.get("status") != "downloaded"]}


def acquire(outline, image_policy="remote", image_urls=(), proxy="env", browser=False, refresh=False, article_ids=None):
    if image_policy not in {"remote", "all", "selected"}:
        raise ValueError("Invalid image policy")
    data = load_manifest(outline)
    root = local(outline["work_dir"], "sources/articles")
    root.mkdir(parents=True, exist_ok=True)
    engine = fetcher()
    requested = requirements(outline)
    if article_ids is not None and (not article_ids or not set(article_ids) <= {item["id"] for item in requested}):
        raise ValueError("Requested article id is not in the reference list")
    image_jobs, matched_images = [], set()
    for wanted in requested:
        if article_ids is not None and wanted["id"] not in article_ids:
            continue
        previous = data["articles"].get(wanted["id"], {})
        if not refresh and previous.get("status") == "fetched":
            assessment(outline)  # Verify cached bytes; do not refresh dates on cache reuse.
        else:
            folder = wanted["id"] + "/versions/" + uuid.uuid4().hex
            result = engine.fetch_to_directory(wanted["url"], root, "remote", (), proxy, browser, directory_name=folder)
            result.pop("id", None)
            result["local_path"] = "sources/articles/" + result.pop("article_path") if result.get("article_path") else None
            result.pop("article_path", None)
            for image in result.get("images", []):
                if image.get("path"):
                    image["path"] = "sources/articles/" + image["path"]
            commit_candidate(outline, data, wanted["id"], result)
        current = data["articles"].get(wanted["id"], {})
        if current.get("status") in {"fetched", "needs_review"} and image_policy != "remote":
            known = {image["url"] for image in current.get("images", [])}
            selected = set(image_urls) & known
            matched_images.update(selected)
            if image_policy == "all" or selected:
                image_jobs.append((wanted["id"], selected))
    if image_policy == "selected" and set(image_urls) - matched_images:
        raise ValueError("Selected image URL was not found in the selected article(s)")
    image_failures = []
    for key, selected in image_jobs:
        image_failures.extend(download_images(outline, key, selected, proxy, all_images=image_policy == "all")["failures"])
    state = assessment(outline)
    if image_failures:
        state["image_failures"] = image_failures
    return state


def import_body(outline, url, file, title, method="provided", final_url=None):
    resolved_url = canonical(final_url or url)
    if method not in {"browser", "pdf", "provided"} or not isinstance(title, str) or not title.strip():
        raise ValueError("Import needs a title and a supported acquisition method")
    wanted = next((item for item in requirements(outline) if item["url"] == canonical(url)), None)
    if wanted is None:
        raise ValueError("Register the article URL before importing its body")
    data = load_manifest(outline)
    source = Path(file).resolve()
    work = Path(outline["work_dir"]).resolve()
    if not source.is_relative_to(work):
        raise ValueError("Save extracted Markdown in the current task before importing")
    source = local(work, source.relative_to(work).as_posix())
    body = source.read_text(encoding="utf-8-sig").strip()
    if len(body) < 40 or not title.strip():
        raise ValueError("Import needs a substantive body and title")
    now = datetime.now(timezone.utc)
    destination = local(work, "sources/articles/" + wanted["id"] + "/versions/" + uuid.uuid4().hex + "/article.md")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(f"# {title}\n\nSource: {wanted['url']}\n\nAccessed (UTC): {now.date().isoformat()}\n\n{body}\n", encoding="utf-8")
    candidate = {"url": wanted["url"], "final_url": resolved_url, "title": title,
        "status": "fetched", "review_status": "pending", "method": method, "accessed_at": now.date().isoformat(), "fetched_at": now.isoformat(),
        "local_path": destination.relative_to(work).as_posix(), "content_sha256": sha(destination), "images": [], "archive": None}
    commit_candidate(outline, data, wanted["id"], candidate)
    return wanted


def review(outline, key, decision, reason):
    if decision not in {"accept", "reject"} or not reason.strip():
        raise ValueError("Review needs accept/reject and a substantive reason")
    assessment(outline)
    data = load_manifest(outline)
    record = data["articles"].get(key)
    if not record or record.get("status") not in {"fetched", "needs_review"}:
        raise ValueError("No obtained article body is available for review")
    record.update(review_status="accepted" if decision == "accept" else "rejected", review_reason=reason,
                  reviewed_at=datetime.now(timezone.utc).isoformat())
    if decision == "accept":
        record["status"] = "fetched"
    save_manifest(outline, data)
    return assessment(outline)


def citation_matches(text, path, anchor, urls, archive_path):
    from validate_report import citation_links
    links = citation_links(text, anchor)
    if links is None:
        return False
    for image, url in links:
        if image:
            continue
        parsed = urlsplit(url)
        if parsed.scheme in {"http", "https"} and canonical(url) in urls:
            return True
        if archive_path is not None and not parsed.scheme and not parsed.netloc and parsed.path and (path.parent / unquote(parsed.path)).resolve() == archive_path:
            return True
    return False


def archive(outline, key, citations, image_ids=(), exception=None, replace=False):
    assessment(outline)
    data = load_manifest(outline)
    record = data["articles"].get(key)
    if not record or record.get("review_status") != "accepted" or record.get("status") != "fetched":
        raise ValueError("Read and accept the obtained body before archiving")
    if not citations:
        raise ValueError("Record at least one report citation location")
    output, work = Path(outline["output_dir"]), Path(outline["work_dir"])
    urls = {canonical(record["url"]), canonical(record.get("final_url", record["url"]))}
    expected_archive = None if exception else local(output, "references/" + key + ".md")
    for citation in citations:
        document, _, anchor = citation.partition("#")
        target = local(output, document)
        if target.parent != output or target.suffix.lower() != ".md" or not target.is_file():
            raise ValueError("Citation locations must be existing root-level report Markdown files")
        if not citation_matches(target.read_text(encoding="utf-8-sig"), target, anchor, urls, expected_archive):
            raise ValueError(f"Article citation location does not cite {key} in the declared section: {citation}")
    if exception:
        if not exception.strip() or image_ids:
            raise ValueError("An archive exception needs a reason and cannot archive images")
        record["archive"] = {"path": None, "exception": exception.strip(), "citations": citations, "images": []}
        save_manifest(outline, data)
        return record["archive"]
    engine = fetcher()
    article = remote_markdown(outline, record)
    images = {image.get("id"): image for image in record.get("images", [])}
    selected = set(image_ids)
    if not selected <= images.keys():
        raise ValueError("Selected image id is not in the article manifest")
    candidates, archived_images = {}, []
    for image in record.get("images", []):
        if image.get("id") in selected:
            if image.get("status") != "downloaded":
                raise ValueError("Download and verify the selected image before archiving it")
            source = local(work, image.get("path"))
            if image.get("status") != "downloaded" or not source.is_file() or sha(source) != image.get("sha256"):
                raise ValueError("Only successfully downloaded, unchanged images can be archived")
            relative = "assets/" + key + "-" + source.name
            candidates[relative] = source.read_bytes()
            archived_images.append({"id": image["id"], "url": image["url"], "path": relative, "sha256": sha(source)})
    article = engine.image_links(article, {image["url"]: "../" + image["path"] for image in archived_images})
    relative = "references/" + key + ".md"
    candidates[relative] = article.encode("utf-8")
    for name, content in candidates.items():
        target = local(output, name)
        if target.exists() and target.read_bytes() != content:
            if not replace or (outline.get("update") and name not in outline["update"]["allow_files"]):
                raise ValueError("Existing archive differs; explicitly allow replacement and include it in update scope")
    for name, content in candidates.items():
        target = local(output, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    record["archive"] = {"path": relative, "sha256": sha(local(output, relative)), "original_sha256": record["content_sha256"], "citations": citations, "images": archived_images}
    save_manifest(outline, data)
    return record["archive"]


def validate_delivery(outline, context, documents, reachable):
    from validate_report import extract_links, without_code
    requested = requirements(outline)
    if not requested:
        return []
    assessment(outline)
    data, errors = load_manifest(outline), []
    root = Path(outline["output_dir"])
    evidence = set()
    for url in context["source_urls"]:
        if urlsplit(url).scheme in {"http", "https"}: evidence.add(canonical(url))
    reports = {path: extract_links(documents[path])[0] for path in reachable if path.parent == root}
    for wanted in requested:
        record = data["articles"].get(wanted["id"], {})
        urls = {wanted["url"], canonical(record.get("final_url", wanted["url"]))}
        accepted = record.get("status") == "fetched" and record.get("review_status") == "accepted"
        direct = {path for path, links in reports.items() if any(not image and urlsplit(url).scheme in {"http", "https"} and canonical(url) in urls for image, url in links)}
        saved = record.get("archive")
        expected_archive = local(root, saved["path"] if isinstance(saved, dict) and saved.get("path") else "references/" + wanted["id"] + ".md")
        local_references = set()
        for path, links in reports.items():
            for image, url in links:
                if image or urlsplit(url).scheme:
                    continue
                target = (path.parent / unquote(urlsplit(url).path)).resolve()
                if target == expected_archive:
                    local_references.add(path)
                elif target in documents and target.is_relative_to(root / "references"):
                    marker = re.search(r"^Source:\s+(https?://\S+)\s*$", without_code(documents[target]), re.M)
                    if marker and canonical(marker[1]) in urls:
                        local_references.add(path)
        used = bool(urls & evidence) or bool(direct) or bool(local_references) or bool(saved)
        if not used:
            continue
        if not accepted:
            errors.append(f"Article used as evidence has no accepted body: {wanted['id']}")
            continue
        if not isinstance(saved, dict):
            errors.append(f"Cited article has not been archived: {wanted['id']}")
            continue
        archive_path = local(root, saved["path"]) if saved.get("path") else None
        citations_valid = False
        for location in saved.get("citations", []):
            name, _, anchor = location.partition("#")
            path = local(root, name)
            if path in reports and citation_matches(documents[path], path, anchor, urls, archive_path):
                citations_valid = True
            else:
                errors.append(f"Article citation location does not cite {wanted['id']} in the declared section: {location}")
        if not citations_valid:
            errors.append(f"Article needs a visible report citation, not only a source index: {wanted['id']}")
        if saved.get("exception"):
            if saved["exception"] not in "\n".join(without_code(documents[path]) for path in reports):
                errors.append(f"Article archive exception is not disclosed in report: {wanted['id']}")
            continue
        if archive_path is None or archive_path not in reachable or not archive_path.is_file() or sha(archive_path) != saved.get("sha256"):
            errors.append(f"Article archive is missing, changed or not linked from report: {wanted['id']}")
        for image in saved.get("images", []):
            target = local(root, image["path"])
            if not target.is_file() or sha(target) != image["sha256"]:
                errors.append(f"Archived article image changed: {image['path']}")
    return errors
