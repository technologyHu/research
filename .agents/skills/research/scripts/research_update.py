"""Bounded section updates with an immutable baseline and explicit inherited limits."""

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from research_paths import delivery_entries

NOTE_PREFIXES = (
    "> 调研状态：", "> 采用版本：", "> 核心缺口：", "> 无实质结果的对象：",
    "> 附加交付：", "> 证据冲突：", "> 本次更新范围：", "> 未复核部分原版本：",
    "> 未复核部分原日期：", "> 未复核部分原缺口：",
    "> 本次采用版本：", "> 本次核心缺口：", "> 本次无实质结果的对象：",
    "> 非核心缺口：", "> 本次非核心缺口：", "> 证据沿用：",
    "> 参考文章缺口：", "> 本次参考文章缺口：",
)


def text(path):
    return Path(path).read_bytes().decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def headings(content):
    entries, fence, offset = [], None, 0
    for line in content.splitlines(keepends=True):
        match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line.rstrip("\n"))
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= fence[1] and not match[2].strip():
                fence = None
        elif match:
            fence = (match[1][0], len(match[1]))
        else:
            heading = re.match(r"^ {0,3}(#{1,6})\s+(.+?)\s*$", line.rstrip("\n"))
            if heading:
                entries.append({"heading": line.strip(), "level": len(heading[1]), "start": offset})
        offset += len(line)
    for index, entry in enumerate(entries):
        entry["end"] = next((other["start"] for other in entries[index + 1:] if other["level"] <= entry["level"]), len(content))
    return entries


def selected_spans(content, names):
    entries, chosen = headings(content), []
    for name in names:
        matches = [entry for entry in entries if entry["heading"] == name]
        if len(matches) != 1:
            raise ValueError(f"Section heading must occur exactly once: {name}")
        if matches[0]["level"] == 1:
            raise ValueError("Select report sections, not the report title")
        chosen.append(matches[0])
    chosen.sort(key=lambda entry: entry["start"])
    if any(left["end"] > right["start"] for left, right in zip(chosen, chosen[1:])):
        raise ValueError("Update sections must not overlap")
    return chosen


def strip_note(content):
    # Only the root preamble is managed. Quoted statuses inside sections remain protected.
    boundary = next((entry["start"] for entry in headings(content) if entry["level"] >= 2), len(content))
    prefix, rest = content[:boundary], content[boundary:]
    prefix = re.sub(r"<!--\s*research-summary\s*\n.*?-->\n?", "", prefix, flags=re.S)
    prefix = "\n".join(line for line in prefix.split("\n") if not line.startswith(NOTE_PREFIXES))
    return prefix, rest


def skeleton(content, names):
    spans = selected_spans(content, names)
    for entry in reversed(spans):
        content = content[:entry["start"]] + content[entry["end"]:]
    prefix, rest = strip_note(content)
    # Blank-line differences immediately around the generated header are immaterial.
    prefix = re.sub(r"\n{3,}", "\n\n", prefix)
    return (prefix.rstrip() + "\n\n" + rest.lstrip("\n")).strip("\n")


def safe_relative(value):
    if not isinstance(value, str) or not value:
        raise ValueError("Associated file must have an exact relative path")
    path = PurePosixPath(value)
    if not path.parts or path.is_absolute() or str(path) != value or any(c in value for c in "\\:*?\0") or any(p.casefold() in {"..", ".git", ".agents", ".tmp"} for p in path.parts):
        raise ValueError(f"Unsafe associated file path: {value}")
    return value


def capture(work_dir, report, sections, added=None, allow_files=None, baseline_date=None, baseline_version=None):
    work, report = Path(work_dir), Path(report)
    sections, added = list(sections or []), list(added or [])
    if not sections and not added:
        raise ValueError("Select at least one section to update or add")
    if len(set(sections + added)) != len(sections + added):
        raise ValueError("Duplicate section selection")
    original = text(report)
    selected_spans(original, sections)
    existing = {entry["heading"] for entry in headings(original)}
    for name in added:
        if name in existing or not re.fullmatch(r"## [^\n]+", name):
            raise ValueError(f"New section must be an unused level-two ATX heading: {name}")
    allowed = [safe_relative(value) for value in allow_files or []]
    if report.name in allowed:
        raise ValueError("The main report is governed by section selections, not allow-file")
    folder = work / "baseline"
    if folder.exists():
        raise ValueError("This task already has a baseline; create another task for a different update")
    files = {}
    for entry in delivery_entries(report.parent):
        if entry.is_symlink() or getattr(entry, "is_junction", lambda: False)() or not entry.resolve().is_relative_to(report.parent.resolve()):
            raise ValueError("Cannot snapshot linked report assets")
        if entry.is_file():
            files[entry.relative_to(report.parent).as_posix()] = sha(entry)
    preamble = original[:next((entry["start"] for entry in headings(original) if entry["level"] >= 2), len(original))]

    def labelled(label):
        match = re.search(r"^> " + re.escape(label) + r"：(.+)$", preamble, re.M)
        return match[1] if match else None

    version = baseline_version or labelled("本次采用版本") or labelled("采用版本") or labelled("调研版本") or "原报告未标注"
    inherited = labelled("未复核部分原版本")
    if inherited:
        version += "；更早未复核记录：" + inherited
    reviewed = baseline_date or labelled("调研日期") or labelled("资料日期") or labelled("未复核部分原日期") or "原报告未单独标注；原文日期说明保留"
    gaps = labelled("本次核心缺口") or labelled("核心缺口") or "原报告未单独标注"
    other_gaps = labelled("本次非核心缺口") or labelled("非核心缺口")
    if other_gaps:
        gaps += "；非核心缺口：" + other_gaps
    article_gaps = labelled("本次参考文章缺口") or labelled("参考文章缺口")
    if article_gaps:
        gaps += "；参考文章缺口：" + article_gaps
    inherited_gaps = labelled("未复核部分原缺口")
    if inherited_gaps:
        gaps += "；更早记录：" + inherited_gaps
    plan = {"baseline_sha256": sha(report), "sections": sections, "added_sections": added, "allow_files": allowed, "baseline_version": version, "baseline_date": reviewed, "baseline_gaps": gaps}
    folder.mkdir()
    (folder / "report.md").write_bytes(report.read_bytes())
    (folder / "files.json").write_text(json.dumps(files, ensure_ascii=False, indent=2), encoding="utf-8")
    plan["files_sha256"] = sha(folder / "files.json")
    return plan


def update_summary(outline):
    plan = outline.get("update")
    if plan is None:
        return None
    if not isinstance(plan, dict) or any(not isinstance(plan.get(key), list) or not all(isinstance(x, str) and x.strip() for x in plan[key]) for key in ("sections", "added_sections", "allow_files")):
        raise ValueError("Invalid section update plan")
    names = plan["sections"] + plan["added_sections"]
    if not names or len(names) != len(set(names)):
        raise ValueError("Update scope must contain unique section headings")
    for value in plan["allow_files"]:
        safe_relative(value)
    for key in ("baseline_version", "baseline_date", "baseline_gaps"):
        if not isinstance(plan.get(key), str) or not plan[key].strip():
            raise ValueError(f"Update plan requires {key}")
    work = Path(outline["work_dir"])
    baseline = work / "baseline/report.md"
    if sha(baseline) != plan.get("baseline_sha256"):
        raise ValueError("Update baseline changed; do not rewrite the baseline to accept unrelated edits")
    if sha(work / "baseline/files.json") != plan.get("files_sha256"):
        raise ValueError("Update baseline file manifest changed")
    selected_spans(text(baseline), plan["sections"])
    existing = {entry["heading"] for entry in headings(text(baseline))}
    if any(name in existing or not re.fullmatch(r"## [^\n]+", name) for name in plan["added_sections"]):
        raise ValueError("Invalid added section scope")
    return plan


def check_update(outline, report_content=None, require_added=True):
    plan = update_summary(outline)
    if plan is None:
        return []
    root = Path(outline["output_dir"])
    report = root / outline.get("delivery", {}).get("report", "report.md")
    current = text(report) if report_content is None else report_content.replace("\r\n", "\n").replace("\r", "\n")
    original = text(Path(outline["work_dir"]) / "baseline/report.md")
    errors = []
    try:
        existing = {entry["heading"] for entry in headings(current)}
        added = plan["added_sections"] if require_added else [name for name in plan["added_sections"] if name in existing]
        if skeleton(original, plan["sections"]) != skeleton(current, plan["sections"] + added):
            errors.append("Report content outside the approved update sections changed")
    except ValueError as exc:
        errors.append(str(exc))
    files = json.loads((Path(outline["work_dir"]) / "baseline/files.json").read_text(encoding="utf-8"))
    for relative, expected in files.items():
        safe_relative(relative)
        if relative == report.name or relative in plan["allow_files"]:
            continue
        path = root / relative
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or sha(path) != expected:
            errors.append(f"Existing file outside update scope changed or disappeared: {relative}")
    return errors


def compose_update(outline, replacements, note):
    plan = update_summary(outline)
    if plan is None or not isinstance(replacements, dict) or not replacements:
        raise ValueError("An update plan and section replacement mapping are required")
    report = Path(outline["output_dir"]) / outline.get("delivery", {}).get("report", "report.md")
    errors = check_update(outline, require_added=False)
    if errors:
        raise ValueError("; ".join(errors))
    allowed = set(plan["sections"] + plan["added_sections"])
    if not replacements.keys() <= allowed:
        raise ValueError("Replacement includes a section outside the approved scope")
    content = text(report)
    existing = {entry["heading"] for entry in headings(content)}
    for name, value in replacements.items():
        if not isinstance(value, str) or not value.strip().startswith(name + "\n"):
            raise ValueError(f"Replacement must begin with the original heading: {name}")
        value = value.strip("\n") + "\n\n"
        entries = headings(value)
        if not entries or entries[0]["heading"] != name or any(entry["level"] <= entries[0]["level"] for entry in entries[1:]):
            raise ValueError(f"Replacement must contain only the selected section: {name}")
        if name in existing:
            span = selected_spans(content, [name])[0]
            content = content[:span["start"]] + value + content[span["end"]:]
        else:
            content = content.rstrip("\n") + "\n\n" + value
    prefix, rest = strip_note(content)
    title = next((entry for entry in headings(prefix) if entry["level"] == 1), None)
    if title:
        split = prefix.find("\n", title["start"])
        split = len(prefix) if split < 0 else split
        prefix = prefix[:split].rstrip() + "\n\n" + note.rstrip() + "\n\n" + prefix[split:].lstrip("\n")
    else:
        prefix = note.rstrip() + "\n\n" + prefix
    content = prefix.rstrip("\n") + "\n\n" + rest.lstrip("\n")
    errors = check_update(outline, content)
    if errors:
        raise ValueError("; ".join(errors))
    return report, content
