#!/usr/bin/env python3
"""Read-only checks for Markdown reports, referenced articles and embedded images."""

import argparse
from collections import Counter, deque
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

from research_context import delivery_config, report_context, visible_note
from research_update import check_update
from research_paths import delivery_entries, relative as project_relative, repo_report_path
import research_articles as articles
from validate_results import load_document

IMAGES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".avif", ".bmp", ".tif", ".tiff"}


def without_code(text):
    """Ignore fenced blocks and inline code; keep line structure for headings."""
    lines, fence = [], None
    for line in text.splitlines():
        match = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= fence[1] and not match[2].strip():
                fence = None
            lines.append("")
        elif match:
            fence = (match[1][0], len(match[1]))
            lines.append("")
        else:
            lines.append(line)
    return re.sub(r"<!--.*?-->", "", "\n".join(lines), flags=re.S)


def target_end(text, pos):
    """Require a closing parenthesis after optional whitespace and link title."""
    while pos < len(text) and text[pos].isspace():
        pos += 1
    if pos < len(text) and text[pos] == ")":
        return pos + 1
    if pos >= len(text) or text[pos] not in {'"', "'", "("}:
        return None
    closer = ")" if text[pos] == "(" else text[pos]
    pos += 1
    while pos < len(text):
        if text[pos] == "\\":
            pos += 2
            continue
        if text[pos] == closer:
            pos += 1
            while pos < len(text) and text[pos].isspace():
                pos += 1
            return pos + 1 if pos < len(text) and text[pos] == ")" else None
        pos += 1
    return None


def destination(text, pos):
    """Read an inline destination, including angle paths or balanced parentheses."""
    if pos >= len(text) or text[pos] != "(":
        return None, pos
    pos += 1
    while pos < len(text) and text[pos].isspace():
        pos += 1
    if pos < len(text) and text[pos] == "<":
        end = text.find(">", pos + 1)
        finish = target_end(text, end + 1) if end >= 0 else None
        return (text[pos + 1:end], finish) if finish else (None, pos)
    start, depth = pos, 0
    while pos < len(text):
        char = text[pos]
        if char == "\\" and pos + 1 < len(text):
            pos += 2
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            if depth == 0:
                return text[start:pos], pos + 1
            depth -= 1
        elif char.isspace() and depth == 0:
            finish = target_end(text, pos)
            return (text[start:pos], finish) if finish else (None, pos)
        pos += 1
    return None, pos


class HTMLLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.ids, self.anchors, self.headings = [], set(), [], []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
            self.anchors.append((attrs["id"], self.getpos(), len(self.get_starttag_text())))
        if re.fullmatch(r"h[1-6]", tag):
            self.headings.append((attrs.get("id"), int(tag[1]), self.getpos()))
        if tag == "img" and "src" in attrs:
            self.links.append((True, attrs["src"]))
        elif tag == "a" and "href" in attrs:
            self.links.append((False, attrs["href"]))


def normalize_label(value):
    return " ".join(value.split()).casefold()


def extract_links(text):
    clean = without_code(text)
    footnote_pattern = re.compile(r"^ {0,3}\[\^([^\]\n]+)\]:[ \t]*(.*)$", re.M)
    footnotes = {normalize_label(match[1]) for match in footnote_pattern.finditer(clean)}
    # Footnote bodies remain visible so real links and images inside them are checked.
    clean = footnote_pattern.sub(lambda match: match[2], clean)
    definitions = {}
    definition_pattern = re.compile(r"^ {0,3}\[(?!\^)([^\]\n]+)\]:\s*(<[^>]*>|\S+).*$", re.M)
    for match in definition_pattern.finditer(clean):
        definitions[normalize_label(match[1])] = match[2].strip("<>")
    clean = definition_pattern.sub("", clean)
    clean = re.sub(r"(`+)([^`]*?)\1", "", clean)
    links, errors = [], []
    for match in re.finditer(r"(!?)\[([^\]\n]*)\]", clean):
        image, label, end = bool(match[1]), match[2], match.end()
        preceding = clean[:match.start()]
        if (len(preceding) - len(preceding.rstrip("\\"))) % 2:
            continue
        if not image and label.startswith("^") and (end == len(clean) or clean[end] not in "(["):
            if normalize_label(label[1:]) not in footnotes:
                errors.append(f"Undefined footnote: {label[1:]}")
            continue
        if end < len(clean) and clean[end] == "(":
            target, _ = destination(clean, end)
            if target is None:
                errors.append(f"Unclosed link destination: {label}")
            else:
                links.append((image, target))
        elif end < len(clean) and clean[end] == "[":
            ref_end = clean.find("]", end + 1)
            if ref_end >= 0:
                ref = normalize_label(clean[end + 1:ref_end] or label)
                if ref in definitions:
                    links.append((image, definitions[ref]))
                else:
                    errors.append(f"Undefined reference link: {ref}")
        elif normalize_label(label) in definitions:
            links.append((image, definitions[normalize_label(label)]))
    html = HTMLLinks()
    html.feed(clean)
    links.extend(html.links)
    return links, errors


def heading_spans(clean):
    entries, counts = [], Counter()
    for match in re.finditer(r"^ {0,3}(#{1,6})\s+(.+?)(?:\s+#+\s*)?$", clean, re.M):
        label = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", match[2])
        label = unescape(re.sub(r"<[^>]*>", "", label)).lower()
        base = re.sub(r"[^\w\-\s]", "", label).strip()
        base = re.sub(r"\s", "-", base)
        suffix = counts[base]
        entries.append({"anchor": base if not suffix else f"{base}-{suffix}", "level": len(match[1]), "start": match.start()})
        counts[base] += 1
    html = HTMLLinks()
    html.feed(re.sub(r"(`+)([^`]*?)\1", lambda match: re.sub(r"[^\n]", " ", match[0]), clean))
    lines = clean.splitlines(keepends=True)
    for anchor, level, (row, column) in html.headings:
        entries.append({"anchor": anchor, "level": level, "start": sum(len(line) for line in lines[:row - 1]) + column})
    entries.sort(key=lambda entry: entry["start"])
    for index, entry in enumerate(entries):
        entry["end"] = next((other["start"] for other in entries[index + 1:] if other["level"] <= entry["level"]), len(clean))
    return entries


def heading_ids(text):
    clean = without_code(text)
    html = HTMLLinks()
    html.feed(clean)
    return {entry["anchor"] for entry in heading_spans(clean) if entry["anchor"] is not None} | html.ids


def citation_links(text, anchor=""):
    """Return links used in the declared section, resolving document-wide definitions.

    Definitions are not citation occurrences. Footnote links belong to the section
    containing the footnote call, even when the definition is at the document end.
    None means that the declared anchor does not exist.
    """
    clean = without_code(text)
    lines, footnotes, index = clean.splitlines(keepends=True), {}, 0
    masked = []
    while index < len(lines):
        line = lines[index]
        match = re.match(r"^ {0,3}\[\^([^\]\n]+)\]:[ \t]*(.*)", line)
        if not match:
            masked.append(line)
            index += 1
            continue
        end = index + 1
        while end < len(lines) and (not lines[end].strip() or lines[end].startswith(("    ", "\t"))):
            end += 1
        footnotes[normalize_label(match[1])] = match[2] + "\n" + "".join(lines[index + 1:end])
        masked.append(re.sub(r"[^\n]", " ", "".join(lines[index:end])))
        index = end
    clean = "".join(masked)
    entries = heading_spans(clean)
    start, end = 0, len(clean)
    if anchor:
        anchor = unquote(anchor)
        selected = next((entry for entry in entries if entry["anchor"] == anchor), None)
        if selected:
            start, end = selected["start"], selected["end"]
        else:
            html = HTMLLinks()
            html.feed(re.sub(r"(`+)([^`]*?)\1", lambda match: re.sub(r"[^\n]", " ", match[0]), clean))
            matches = [entry for entry in html.anchors if entry[0] == anchor]
            if len(matches) != 1:
                return None
            _, (row, column), tag_length = matches[0]
            start = sum(len(line) for line in clean.splitlines(keepends=True)[:row - 1]) + column
            following = next((entry for entry in entries if entry["start"] >= start), None)
            if following and re.fullmatch(r"(?:\s|</[A-Za-z][A-Za-z0-9:-]*\s*>)*", clean[start + tag_length:following["start"]]):
                end = following["end"]
            else:
                enclosing = [entry for entry in entries if entry["start"] <= start < entry["end"]]
                end = enclosing[-1]["end"] if enclosing else (following["start"] if following else len(clean))
    definitions = "\n".join(match[0] for match in re.finditer(r"^ {0,3}\[(?!\^)([^\]\n]+)\]:[^\n]*", clean, re.M))
    selected = clean[start:end]
    pending, included = [selected], set()
    while pending:
        fragment = re.sub(r"(`+)([^`]*?)\1", "", pending.pop())
        for match in re.finditer(r"\[\^([^\]\n]+)\](?![:(\[])", fragment):
            preceding = fragment[:match.start()]
            if preceding.endswith("!") or (len(preceding) - len(preceding.rstrip("\\"))) % 2:
                continue
            key = normalize_label(match[1])
            if key in footnotes and key not in included:
                included.add(key)
                pending.append(footnotes[key])
    return extract_links(selected + "\n" + definitions + "\n" + "\n".join(footnotes[key] for key in sorted(included)))[0]


def canonical_source(value):
    parsed = urlsplit(value)._replace(fragment="")
    return ("repo:" + unquote(parsed.path)) if parsed.scheme == "repo" else parsed.geturl().rstrip("/")


def validate(root, outline_path=None, fields_path=None):
    root = Path(root).resolve()
    errors = []
    delivery = {"report": "report.md", "extra_files": []}
    context = None
    local_sources = set()
    if outline_path is not None:
        try:
            outline = load_document(outline_path)
            delivery = delivery_config(outline)
            if Path(outline["output_dir"]).resolve() != root:
                errors.append("Output directory does not match the research plan")
            context = report_context(outline_path, fields_path)
            errors.extend(check_update(outline))
        except (OSError, ValueError, TypeError, KeyError) as exc:
            errors.append(f"Cannot establish report consistency: {exc}")
    elif fields_path is not None:
        errors.append("--fields requires --outline")
    extra_files = {root / entry["path"] for entry in delivery["extra_files"]}
    if not root.is_dir():
        return {"valid": False, "errors": ["Output directory does not exist"], "documents": 0, "images": 0}
    documents, image_files = {}, set()
    for entry in delivery_entries(root):
        if entry.is_symlink() or getattr(entry, "is_junction", lambda: False)() or not entry.resolve().is_relative_to(root):
            errors.append(f"Links outside or within output are not copied deliverables: {entry.relative_to(root)}")
            continue
        if entry.is_dir():
            if not any(entry.iterdir()):
                errors.append(f"Empty directory: {entry.relative_to(root)}")
            continue
        if not entry.is_file():
            continue
        relative = entry.relative_to(root)
        if entry.suffix.lower() == ".md" and (entry.parent == root or relative.parts[0] == "references"):
            try:
                documents[entry] = entry.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeError) as exc:
                errors.append(f"Unreadable Markdown {relative}: {exc}")
        elif relative.parts[0] == "assets" and entry.suffix.lower() in IMAGES:
            image_files.add(entry)
        elif entry not in extra_files:
            errors.append(f"Unexpected delivered file: {relative}")
    for entry in extra_files:
        if not entry.is_file():
            errors.append(f"Requested extra file is missing: {entry.relative_to(root)}")
    report = root / delivery["report"]
    if report not in documents or not documents.get(report, "").strip():
        errors.append(f"A nonempty {delivery['report']} is required")
    analysis_workspace, adopted_sources = None, set()
    if context is not None and outline.get("object_type") == "analysis":
        analysis_workspace = Path(outline["workspace"]).resolve()
        adopted_sources = {canonical_source(value) for value in context["source_urls"] if urlsplit(value).scheme == "repo"}
    elif outline_path is None and fields_path is None and root.parent.name == "analysis" and len(root.parents) >= 3:
        # A cleaned task still permits independent link checks from its saved
        # summary. This does not restore evidence or check research consistency.
        notes = re.findall(r"<!--\s*research-summary\s*\n(.*?)-->", documents.get(report, ""), re.S)
        try:
            summary = json.loads(notes[0]) if len(notes) == 1 else {}
            items = summary.get("items")
            sources = summary.get("source_urls")
            if (isinstance(items, list) and items and all(isinstance(item, dict) and item.get("type") == "analysis" for item in items)
                    and isinstance(sources, list) and all(isinstance(value, str) for value in sources)):
                analysis_workspace = root.parents[3] if root.parents[2].name == "analysis-reports" and len(root.parents) >= 4 else root.parents[2]
                adopted_sources = {canonical_source(value) for value in sources if urlsplit(value).scheme == "repo"}
        except (ValueError, TypeError, AttributeError):
            pass
    graph = {path: set() for path in documents}
    embedded_by_document = {path: set() for path in documents}
    checked_links = 0
    for path, text in documents.items():
        links, parse_errors = extract_links(text)
        errors.extend(f"{path.relative_to(root)}: {message}" for message in parse_errors)
        for is_image, raw in links:
            checked_links += 1
            target = unescape(re.sub(r"\\([()<> ])", r"\1", raw.strip()))
            try:
                parsed = urlsplit(target)
            except ValueError:
                errors.append(f"{path.relative_to(root)}: invalid URL {raw}")
                continue
            if parsed.scheme in {"http", "https", "mailto"} and not is_image:
                if not (parsed.path if parsed.scheme == "mailto" else parsed.netloc):
                    errors.append(f"{path.relative_to(root)}: invalid external URL: {raw}")
                continue
            if parsed.scheme == "file" and not is_image and context is not None and target in context["source_urls"]:
                continue
            if parsed.scheme or parsed.netloc:
                if is_image and path.parent != root and path.is_relative_to(root / "references") and parsed.scheme in {"http", "https"}:
                    continue
                errors.append(f"{path.relative_to(root)}: use a local relative path for this target: {raw}")
                continue
            if not target or (is_image and not parsed.path):
                errors.append(f"{path.relative_to(root)}: empty target")
                continue
            local_path = unquote(parsed.path)
            if local_path.startswith(("/", "\\")):
                errors.append(f"{path.relative_to(root)}: absolute local path: {raw}")
                continue
            resolved = (path.parent / local_path).resolve() if local_path else path
            if resolved.is_relative_to(root / ".tmp"):
                errors.append(f"{path.relative_to(root)}: report must not link temporary files: {raw}")
                continue
            if not resolved.is_relative_to(root):
                if (analysis_workspace is not None and not is_image
                        and resolved.is_relative_to(analysis_workspace)):
                    source = "repo:" + project_relative(resolved, analysis_workspace)
                    if source in adopted_sources:
                        try:
                            adopted = repo_report_path(source, analysis_workspace)
                            if parsed.fragment and unquote(parsed.fragment) not in heading_ids(adopted.read_text(encoding="utf-8-sig")):
                                errors.append(f"{path.relative_to(root)}: missing adopted report anchor: {raw}")
                            local_sources.add(source)
                            continue
                        except (OSError, ValueError, UnicodeError) as exc:
                            errors.append(f"{path.relative_to(root)}: invalid adopted report: {exc}")
                errors.append(f"{path.relative_to(root)}: target outside output: {raw}")
                continue
            if not resolved.is_file():
                errors.append(f"{path.relative_to(root)}: missing file: {raw}")
                continue
            if resolved in documents:
                graph[path].add(resolved)
                if parsed.fragment and unquote(parsed.fragment) not in heading_ids(documents[resolved]):
                    errors.append(f"{path.relative_to(root)}: missing Markdown anchor: {raw}")
            if is_image:
                if resolved not in image_files:
                    errors.append(f"{path.relative_to(root)}: image must be an allowed file under assets/: {raw}")
                else:
                    embedded_by_document[path].add(resolved)
    reachable, pending = set(), deque([report] if report in documents else [])
    while pending:
        path = pending.popleft()
        if path not in reachable:
            reachable.add(path)
            pending.extend(graph[path] - reachable)
    for path in documents.keys() - reachable:
        errors.append(f"Markdown is not linked from {delivery['report']}: {path.relative_to(root)}")
    report_images = set()
    for path in reachable:
        if path.parent == root:
            report_images.update(embedded_by_document[path])
    for path in image_files - report_images - extra_files:
        errors.append(f"Image is not embedded in a report: {path.relative_to(root)}")
    if context is not None and report in documents:
        text = documents[report]
        metadata = re.findall(r"<!--\s*research-summary\s*\n(.*?)-->", text, re.S)
        if len(metadata) != 1:
            errors.append("Report needs exactly one research-summary note generated from this task")
        else:
            try:
                if json.loads(metadata[0]) != context:
                    errors.append("Report summary is stale or disagrees with research completion, versions or core gaps")
            except ValueError:
                errors.append("Report research-summary is not valid JSON")
        visible = without_code(text)
        for line in visible_note(context):
            if line not in visible.splitlines():
                errors.append(f"Missing or inconsistent visible research note: {line}")
        statuses = re.findall(r"^> 调研状态：(.+)$", visible, re.M)
        if len(statuses) != 1:
            errors.append("Report must show one unambiguous research status")
        cited = set(local_sources)
        for path in reachable:
            content = without_code(documents[path])
            content = re.sub(r"(`+)([^`]*?)\1", "", content)
            links, _ = extract_links(documents[path])
            urls = [target for is_image, target in links if not is_image]
            urls.extend(re.findall(r"(?:https?|file)://[^\s<>\)\]\"']+", content))
            for target in urls:
                if urlsplit(target).scheme in {"http", "https", "file"}:
                    cited.add(canonical_source(target))
        for source in context["source_urls"]:
            if canonical_source(source) not in cited:
                errors.append(f"Evidence source is not cited in the delivered Markdown: {source}")
    if context is not None:
        try:
            errors.extend(articles.validate_delivery(outline, context, documents, reachable))
        except (OSError, ValueError, TypeError, KeyError) as exc:
            errors.append(f"Invalid article delivery: {exc}")
    return {
        "valid": not errors,
        "documents": len(documents),
        "images": len(image_files),
        "checked_links": checked_links,
        "consistency_checked": context is not None,
        "completion": context["completion"] if context else None,
        "errors": sorted(set(errors)),
        "limitations": "No network requests; checks common inline/reference/HTML links and ATX heading anchors, not factual accuracy or rendered layout.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--outline", type=Path)
    parser.add_argument("--fields", type=Path)
    args = parser.parse_args()
    try:
        result = validate(args.output_dir, args.outline, args.fields)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result = {"valid": False, "errors": [str(exc)]}
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
