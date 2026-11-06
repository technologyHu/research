#!/usr/bin/env python3
"""Snapshot authored drafts and compare protected content after language editing."""

import argparse
from difflib import unified_diff
import hashlib
import json
from pathlib import Path
import re
import sys
import uuid

import research_articles as articles
import research_update as updates
from research_paths import relative
from validate_report import HTMLLinks, extract_links, without_code


def digest(data):
    return hashlib.sha256(data).hexdigest()


def documents(data, kind):
    text = data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    if kind == "markdown":
        return {"document": text}
    value = json.loads(text)
    if not isinstance(value, dict) or not value or any(not isinstance(key, str) or not isinstance(body, str) for key, body in value.items()):
        raise ValueError("Section drafts must be a nonempty heading-to-Markdown mapping")
    return value


def protected(text):
    """Conservative comparison of common Markdown; semantic checks remain manual."""
    result = {"headings": [], "code_blocks": [], "tables": []}
    # Preserve fenced examples exactly, while ignoring their apparent Markdown.
    lines, remaining, fence, block = text.splitlines(keepends=True), [], None, []
    for line in lines:
        match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\n"))
        if fence:
            block.append(line)
            remaining.append("\n")
            if match and match[1][0] == fence[0] and len(match[1]) >= fence[1] and not match[2].strip():
                result["code_blocks"].append("".join(block))
                fence, block = None, []
        elif match:
            fence, block = (match[1][0], len(match[1])), [line]
            remaining.append("\n")
        else:
            remaining.append(line)
    if block:
        result["code_blocks"].append("".join(block))
    text = "".join(remaining)
    frontmatter = re.match(r"\A---\n.*?\n(?:---|\.\.\.)\s*(?:\n|$)", text, re.S)
    result["frontmatter"] = frontmatter[0] if frontmatter else None
    result["summary"] = re.findall(r"<!--\s*research-summary\s*\n.*?-->", text, re.S)
    result["state_notes"] = [line for line in text.splitlines() if line.startswith(updates.NOTE_PREFIXES)]
    clean = without_code(text)
    result["headings"] = [entry["heading"] for entry in updates.headings(clean)]
    result["setext_headings"] = re.findall(r"^([^\n]+)\n {0,3}(?:=+|-+)\s*$", clean, re.M)
    html = HTMLLinks()
    html.feed(clean)
    result["anchors"] = [entry[0] for entry in html.anchors]
    result["html_targets"] = re.findall(r"<(?:a|img|h[1-6]|span|div)\b[^>]*(?:href|src|id)\s*=[^>]*>", clean, re.I)
    result["inline_code"] = re.findall(r"(`+)([^`]*?)\1", clean)
    result["indented_code"] = re.findall(r"^(?:(?: {4}|\t)[^\n]*(?:\n|$))+", clean, re.M)
    result["math"] = [match[0] for match in re.finditer(r"\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]|(?<![\\$])\$(?!\$)[^\n$]+(?<!\\)\$|\\\([^\n]*?\\\)", clean)]
    result["links"] = extract_links(text)[0]
    result["link_markers"] = re.findall(r"!?\[[^\]\n]*\](?:\[[^\]\n]*\])?", clean)
    result["definitions"] = re.findall(r"^ {0,3}\[(?!\^)[^\]\n]+\]:[^\n]*$", clean, re.M)
    result["quotes"] = re.findall(r"^\s*>[^\n]*$|“[^”]*”|「[^」]*」|\"[^\"\n]*\"", clean, re.M)
    result["numbers"] = re.findall(r"(?<![A-Za-z0-9_])(?:[vV])?[+-]?\d+(?:[.,]\d+)*(?:[eE][+-]?\d+)?(?:%|％)?", clean)
    rows = clean.splitlines()
    separator = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
    index = 0
    while index + 1 < len(rows):
        if "|" in rows[index] and separator.fullmatch(rows[index + 1]):
            end = index + 2
            while end < len(rows) and rows[end].strip() and "|" in rows[end]:
                end += 1
            result["tables"].append("\n".join(rows[index:end]))
            index = end
        else:
            index += 1
    return result


def target_file(outline, value):
    path = Path(value).absolute()
    workspace, work, output = (Path(outline[key]).resolve() for key in ("workspace", "work_dir", "output_dir"))
    if not path.is_relative_to(workspace):
        raise ValueError("Draft must belong to the current project")
    path = articles.local(workspace, path.relative_to(workspace).as_posix())
    if not path.is_file():
        raise ValueError("Draft does not exist")
    if path.parent == output and path.suffix.lower() == ".md":
        if outline.get("update"):
            raise ValueError("For a local update, snapshot the selected sections JSON before apply-update")
        return path, "markdown"
    scratch = work / "scratch"
    if path.is_relative_to(scratch) and not path.is_relative_to(scratch / "polish") and path.suffix.lower() == ".json" and outline.get("update"):
        return path, "sections"
    raise ValueError("Use a root report Markdown draft or this update's scratch sections JSON; source articles are excluded")


def validate_scope(outline, docs, kind):
    if kind != "sections":
        return
    plan = updates.update_summary(outline)
    if not plan or not docs.keys() <= set(plan["sections"] + plan["added_sections"]):
        raise ValueError("Section draft is outside the registered update scope")
    for heading, body in docs.items():
        entries = updates.headings(body)
        if not body.startswith(heading + "\n") or not entries or entries[0]["heading"] != heading or any(entry["level"] <= entries[0]["level"] for entry in entries[1:]):
            raise ValueError("Each draft must contain only its registered section: " + heading)


def snapshot(work_dir, file):
    from research_task import open_task
    work, _, outline = open_task(work_dir)
    target, kind = target_file(outline, file)
    before = target.read_bytes()
    docs = documents(before, kind)
    validate_scope(outline, docs, kind)
    folder = articles.local(work, "scratch/polish/" + uuid.uuid4().hex)
    folder.mkdir(parents=True)
    name = "before.md" if kind == "markdown" else "before.json"
    (folder / name).write_bytes(before)
    manifest = {"schema_version": 1, "run_id": outline["run_id"], "target": target.relative_to(Path(outline["workspace"])).as_posix(), "kind": kind, "before": name, "before_sha256": digest(before)}
    (folder / "snapshot.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"snapshot": str(folder), "target": str(target), "documents": list(docs), "note": "Edit the target prose, then run check with this snapshot; do not replace the snapshot to accept a mismatch."}


def check(work_dir, folder):
    from research_task import open_task
    work, _, outline = open_task(work_dir)
    folder = Path(folder).absolute()
    if not folder.is_relative_to(work / "scratch/polish"):
        raise ValueError("Snapshot must be inside this task's scratch/polish directory")
    folder = articles.local(work, folder.relative_to(work).as_posix())
    metadata = json.loads(articles.local(folder, "snapshot.json").read_text(encoding="utf-8"))
    if not isinstance(metadata, dict) or metadata.get("schema_version") != 1 or metadata.get("run_id") != outline["run_id"] or metadata.get("kind") not in {"markdown", "sections"}:
        raise ValueError("Invalid polish snapshot or mismatched task")
    before = articles.local(folder, metadata["before"]).read_bytes()
    if digest(before) != metadata["before_sha256"]:
        raise ValueError("Polish snapshot body changed")
    target, kind = target_file(outline, articles.local(outline["workspace"], metadata["target"]))
    if kind != metadata["kind"]:
        raise ValueError("Draft kind differs from snapshot")
    after = target.read_bytes()
    previous, current = documents(before, kind), documents(after, kind)
    validate_scope(outline, current, kind)
    changed = {}
    if list(previous) != list(current):
        changed["sections"] = ["section keys or order"]
    for name in previous.keys() & current.keys():
        old, new = protected(previous[name]), protected(current[name])
        differences = [category for category in old if old[category] != new[category]]
        if differences:
            changed[name] = differences
    diff = list(unified_diff(before.decode("utf-8-sig").splitlines(), after.decode("utf-8-sig").splitlines(), fromfile="before", tofile="after", lineterm=""))
    return {"valid": not changed, "target": str(target), "snapshot": str(folder), "changed_protected_content": changed, "diff": diff, "limitations": "Compares common Markdown structures and numeric tokens, not semantic equivalence, prose units, factual accuracy or whether humanizer ran. Review the diff and evidence, then run task verify."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("snapshot", "check"):
        command = commands.add_parser(name)
        command.add_argument("--work-dir", type=Path, required=True)
        command.add_argument("--file" if name == "snapshot" else "--snapshot", type=Path, required=True)
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        from research_task import open_task
        result = snapshot(args.work_dir, args.file) if args.command == "snapshot" else check(args.work_dir, args.snapshot)
        outline = open_task(args.work_dir)[2]
        for key in ("target", "snapshot"):
            result[key] = relative(result[key], outline["workspace"])
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("valid", True) else 1
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
