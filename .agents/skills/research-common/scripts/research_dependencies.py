"""Bind existing conclusions to the article bodies they actually depend on."""

import re
import os
from urllib.parse import urlsplit, urlunsplit, unquote

import research_articles as articles


def source_alias(url):
    parsed = urlsplit(url)
    if parsed.scheme == "file" and parsed.path:
        value = urlunsplit(("file", parsed.netloc.lower(), unquote(parsed.path), parsed.query, ""))
        return value.casefold() if os.name == "nt" else value
    return articles.canonical(url)


def state(outline):
    manifest, output = articles.load_manifest(outline), {}
    for wanted in articles.requirements(outline):
        record = manifest["articles"].get(wanted["id"], {})
        versions = [record, *record.get("previous_versions", [])]
        aliases = {wanted["url"]}
        for version in versions:
            for name in ("url", "final_url"):
                if version.get(name):
                    aliases.add(articles.canonical(version[name]))
            if version.get("local_path"):
                aliases.add(source_alias(articles.local(outline["work_dir"], version["local_path"]).as_uri()))
            archive = version.get("archive")
            if isinstance(archive, dict) and archive.get("path"):
                aliases.add(source_alias(articles.local(outline["output_dir"], archive["path"]).as_uri()))
        fingerprint = articles.body_fingerprint(outline, record) if record.get("status") in {"fetched", "needs_review"} else None
        changed = bool(record.get("requires_result_review"))
        # Existing versioned caches may predate the change marker. Do not silently
        # accept their old conclusions merely because the marker was not stored.
        if not changed and fingerprint:
            for old in record.get("previous_versions", []):
                if old.get("status") in {"fetched", "needs_review"} and old.get("local_path"):
                    try:
                        changed = articles.body_fingerprint(outline, old) != fingerprint
                    except (OSError, ValueError):
                        changed = True
                    if changed:
                        break
        output[wanted["id"]] = {"fingerprint": fingerprint, "requires_review": changed, "aliases": aliases}
    return output


def fingerprints(dependencies):
    return {key: entry["fingerprint"] for key, entry in dependencies.items() if entry["fingerprint"] is not None}


def referenced_urls(record, sources):
    source_map = {source["id"]: source["url"] for source in sources if isinstance(source, dict) and isinstance(source.get("id"), str) and isinstance(source.get("url"), str)}
    refs = record.get("evidence", [])
    refs = list(refs) if isinstance(refs, list) else []
    conflicts = record.get("conflicts", [])
    for conflict in conflicts if isinstance(conflicts, list) else []:
        if isinstance(conflict, dict) and isinstance(conflict.get("positions"), list):
            refs.extend(conflict["positions"])
    return [source_map[entry["source_id"]] for entry in refs if isinstance(entry, dict) and isinstance(entry.get("source_id"), str) and entry["source_id"] in source_map]


def check(record, urls, dependencies, prefix):
    errors, stale = [], []
    bindings = record.get("article_fingerprints", {})
    if not isinstance(bindings, dict) or any(not isinstance(key, str) or key not in dependencies or not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value) for key, value in bindings.items()):
        return [f"{prefix}: article_fingerprints must map registered article ids to body fingerprints"], []
    normalized = set()
    for url in urls:
        try:
            if isinstance(url, str) and urlsplit(url).scheme in {"http", "https", "file"}:
                normalized.add(source_alias(url))
        except ValueError:
            # Source format validation reports malformed URLs separately.
            continue
    for key, entry in dependencies.items():
        if key not in bindings and not normalized.intersection(entry["aliases"]):
            continue
        if key in bindings or entry["requires_review"]:
            if entry["fingerprint"] is None or bindings.get(key) != entry["fingerprint"]:
                stale.append(key)
                errors.append(f"{prefix}: stale article dependency {key}; reassess the conclusion and record its current article_fingerprints")
    return errors, stale
