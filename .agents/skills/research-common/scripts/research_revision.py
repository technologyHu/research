"""Rename a dated delivery and repair local references without accepting new evidence."""

import base64
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
from urllib.parse import quote, unquote, urlsplit

import research_catalog as catalog


def write_atomic(target, content, staging_dir=None):
    """Stage beside the target so interrupted writes never truncate its contents."""
    descriptor, name = tempfile.mkstemp(prefix=".research-revision-", dir=staging_dir or target.parent)
    os.close(descriptor)
    temporary = Path(name)
    try:
        if temporary.write_bytes(content) != len(content):
            raise OSError("Incomplete report revision write")
        if target.exists():
            os.chmod(temporary, stat.S_IMODE(target.stat().st_mode))
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def move_directory(source, destination, workspace):
    source, destination, workspace = map(lambda p: Path(p).absolute(), (source, destination, workspace))
    for path in (source, destination):
        if path == workspace or not path.resolve().is_relative_to(workspace.resolve()):
            raise ValueError("Report move must remain within its workspace")
        for entry in (path, *path.parents):
            if entry.is_symlink() or getattr(entry, "is_junction", lambda: False)():
                raise ValueError("Cannot move linked report paths")
            if entry == workspace:
                break
    if destination.exists():
        raise ValueError("Report timestamp destination already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        # Single-quoted PowerShell literals preserve spaces, $, backticks and apostrophes.
        literal = lambda value: "'" + str(value).replace("'", "''") + "'"
        command = ("$ErrorActionPreference='Stop'; "
                   f"$src={literal(source)}; $dst={literal(destination)}; "
                   "$item=Get-Item -LiteralPath $src -Force; "
                   "if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Linked source' }; "
                   "if (Test-Path -LiteralPath $dst) { throw 'Destination exists' }; "
                   "Move-Item -LiteralPath $src -Destination $dst")
        encoded = base64.b64encode(command.encode("utf-16le")).decode("ascii")
        result = subprocess.run(["pwsh", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                                capture_output=True)
        if result.returncode:
            raise OSError((result.stdout + result.stderr).decode("utf-8", errors="replace"))
    else:
        source.rename(destination)


def markdown_links(text, source, destination, old, new):
    """Rewrite destination spans, leaving code examples and visible link labels intact."""
    from validate_report import destination as parse_destination
    masked, fence = [], None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            masked.append(re.sub(r"[^\n]", " ", line))
        elif fence:
            masked.append(re.sub(r"[^\n]", " ", line))
        else:
            masked.append(line)
    clean = re.sub(r"<!--.*?-->|(`+)([^`]*?)\1", lambda m: re.sub(r"[^\n]", " ", m[0]), "".join(masked), flags=re.S)
    spans = []
    for match in re.finditer(r"!?\[[^\]\n]*\]\(", clean):
        start = match.end() - 1
        target, end = parse_destination(clean, start)
        if target:
            offset = clean.find(target, start + 1, end)
            spans.append((offset, offset + len(target), target))
    for match in re.finditer(r"^\s{0,3}\[[^\]\n]+\]:\s*(?:<([^>]+)>|(\S+))", clean, re.M):
        group = 1 if match[1] is not None else 2
        spans.append((*match.span(group), match[group]))
    for match in re.finditer(r"\b(?:href|src)\s*=\s*([\"'])(.*?)\1", clean, re.I):
        spans.append((*match.span(2), match[2]))
    for start, end, value in sorted(set(spans), reverse=True):
        parsed = urlsplit(value)
        if parsed.scheme or parsed.netloc or not parsed.path or Path(unquote(parsed.path)).is_absolute():
            continue
        target = (source.parent / unquote(parsed.path)).resolve()
        if target.is_relative_to(old):
            target = new / target.relative_to(old)
        elif destination == source:
            continue
        relative = os.path.relpath(target, destination.parent).replace(os.sep, "/")
        replacement = quote(relative, safe="/-._~")
        if parsed.query:
            replacement += "?" + parsed.query
        if parsed.fragment:
            replacement += "#" + parsed.fragment
        text = text[:start] + replacement + text[end:]
    return text


def project_strings(value, old_relative, new_relative):
    if isinstance(value, str):
        prefix = "repo:" if value.startswith("repo:") else ""
        raw = unquote(value[len(prefix):])
        if raw == old_relative or raw.startswith(old_relative + "/"):
            return prefix + new_relative + raw[len(old_relative):]
        return value
    if isinstance(value, list):
        return [project_strings(v, old_relative, new_relative) for v in value]
    if isinstance(value, dict):
        return {project_strings(k, old_relative, new_relative): project_strings(v, old_relative, new_relative)
                for k, v in value.items()}
    return value


def stamp_report(work_dir, at=None):
    import research_task as task
    _, _, outline = task.open_task(work_dir)
    with task.delivery_lock(Path(outline["output_dir"]), Path(outline["workspace"])):
        return _stamp_report(work_dir, at)


def _stamp_report(work_dir, at=None):
    import research_task as task
    from research_paths import relative
    path, _, outline = task.open_task(work_dir)
    if outline.get("directory_layout") != "dated-flat":
        raise ValueError("Legacy report layouts stay in place; use their existing paths")
    workspace, old = Path(outline["workspace"]), Path(outline["output_dir"])
    report_name = task.delivery_config(outline)["report"]
    report = old / report_name
    if not report.is_file():
        raise ValueError("Write the report before stamping a revision")
    from datetime import datetime
    moment = datetime.fromisoformat(at) if at else catalog.now()
    if moment.tzinfo is None:
        raise ValueError("Report timestamps require a timezone")
    moment = moment.astimezone(catalog.LOCAL_TIME).replace(microsecond=0).isoformat()
    if datetime.fromisoformat(moment) < datetime.fromisoformat(outline["updated_at"]):
        raise ValueError("Report revision time cannot move backwards")
    entry = catalog.theme_entry(workspace, outline["theme_id"])
    kind = outline["classification"]["type"]
    legacy_analysis = catalog.analysis_subject(catalog.split_name(old.name)[0], entry)[1] if kind == "analysis" else False
    new = catalog.report_directory(workspace, kind, entry["directory"], outline["classification"]["target"], moment,
                                   separator=catalog.date_separator(old.name), legacy_analysis=legacy_analysis)
    task.no_links(old, workspace)
    task.no_links(new, workspace)
    for child in old.rglob("*"):
        if child.is_symlink() or getattr(child, "is_junction", lambda: False)():
            raise ValueError("Cannot rename a report containing linked entries")
    if new != old and new.exists():
        raise ValueError("Report timestamp destination already exists")
    old_relative, new_relative = relative(old, workspace), relative(new, workspace)
    tasks = task.list_tasks(workspace)
    if tasks["errors"]:
        raise ValueError("Resolve task ownership errors before updating report references")
    files = set()
    for folder, dirs, names in os.walk(workspace, followlinks=False):
        dirs[:] = [name for name in dirs if name not in {".git", ".agents", ".tmp", "node_modules", "references", "assets"}
                   and not (Path(folder) / name).is_symlink() and not getattr(Path(folder) / name, "is_junction", lambda: False)()]
        files.update(Path(folder) / name for name in names if name.lower().endswith(".md"))
    for job in tasks["tasks"]:
        work = Path(job["work_dir"])
        files.update(work / name for name in ("owner.json", "outline.json", "fields.json", "notes.md") if (work / name).is_file())
        files.update((work / "results").glob("*.json"))
    originals, updates = {}, {}
    for file in sorted(files):
        if file.is_symlink() or getattr(file, "is_junction", lambda: False)():
            raise ValueError("Cannot rewrite linked reference files")
        original = file.read_bytes()
        source = original.decode("utf-8-sig")
        destination = new / file.relative_to(old) if file.is_relative_to(old) else file
        if file.suffix == ".json":
            raw = json.loads(source)
            updated = project_strings(raw, old_relative, new_relative)
            content = json.dumps(updated, ensure_ascii=False, indent=2) + "\n" if updated != raw else source
        else:
            content = markdown_links(source, file, destination, old, new)
        if content != source or file in {report, path / "outline.json"}:
            originals[file] = original
            updates[file] = content.encode("utf-8")
    # Keep all sibling runs bound to the same delivery identity and timestamp.
    for job in tasks["tasks"]:
        work = Path(job["work_dir"])
        file = work / "outline.json"
        raw = json.loads(file.read_text(encoding="utf-8-sig"))
        if raw.get("report_id") == outline["report_id"]:
            raw = project_strings(raw, old_relative, new_relative)
            raw.update(updated_at=moment, theme_slug=entry["directory"], theme_name=entry["label"], theme_path=entry["path"])
            originals.setdefault(file, file.read_bytes())
            updates[file] = (json.dumps(raw, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if any(file.read_bytes() != content for file, content in originals.items()):
        raise ValueError("References changed during revision preparation")
    moved, written = False, []
    try:
        if new != old:
            move_directory(old, new, workspace)
            moved = True
        for file, content in updates.items():
            target = new / file.relative_to(old) if file.is_relative_to(old) else file
            written.append((file, target))
            write_atomic(target, content)
        new_work = new / path.relative_to(old)
        context = task.report_context(new_work / "outline.json")
        target = new / report_name
        content = target.read_text(encoding="utf-8-sig")
        from research_context import report_metadata_bytes
        from research_update import with_report_note
        content = with_report_note(content, task.render_report_note(context))
        metadata = catalog.report_metadata_path(target)
        task.no_links(metadata, workspace)
        write_atomic(target, content.encode("utf-8"))
        write_atomic(metadata, report_metadata_bytes(context))
    except Exception:
        for file, target in reversed(written):
            if target.read_bytes() != originals[file]:
                write_atomic(target, originals[file])
        if moved:
            move_directory(new, old, workspace)
        raise
    return {"stamped": True, "report_id": outline["report_id"], "created_at": outline["created_at"],
            "updated_at": moment, "work_dir": str(new_work), "output_dir": str(new),
            "updated_references": [relative(new / file.relative_to(old) if file.is_relative_to(old) else file, workspace) for file in updates] + [relative(metadata, workspace)],
            "note": "Verify this task again; dependent reports keep their old evidence hashes and require review. Rebuild the graph after tracking deliverables."}
