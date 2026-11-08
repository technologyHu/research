#!/usr/bin/env python3
"""Create, find and verify owned research workspaces; never recursively delete files."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import uuid

from research_context import delivery_config, light_fingerprint, render_report_note, report_context
import validate_report
import validate_results
import research_update
import research_articles as articles
from research_paths import MODE, TEMP, LOCAL_LAYOUT, checked_paths, delivery_entries, display_paths, encode_outline, relative


def store_root(output_dir=None):
    return Path(output_dir or Path.cwd()).resolve() / ".tmp"


def workspace_key(workspace):
    return hashlib.sha256(os.path.normcase(str(Path(workspace).resolve())).encode("utf-8")).hexdigest()[:16]


def no_links(path, boundary):
    path, boundary = Path(path).absolute(), Path(boundary).absolute()
    if not path.is_relative_to(boundary):
        raise ValueError("Path is outside the research task store")
    for entry in (path, *path.parents):
        if entry.is_symlink() or getattr(entry, "is_junction", lambda: False)():
            raise ValueError(f"Linked task paths are not accepted: {entry}")
        if entry == boundary:
            break


def write_json(path, value):
    value = encode_outline(value, path)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def open_task(work_dir):
    path = Path(work_dir).absolute()
    no_links(path, path.parent)
    for name in ("owner.json", "outline.json"):
        no_links(path / name, path.parent)
        if not (path / name).is_file():
            raise ValueError("Not an owned research task: owner.json and outline.json are required")
    owner = json.loads((path / "owner.json").read_text(encoding="utf-8"))
    outline = validate_results.load_document(path / "outline.json")
    if not isinstance(owner, dict) or not isinstance(outline, dict):
        raise ValueError("Task owner and outline must be mappings")
    if outline.get("workflow") not in {"light", "full"}:
        raise ValueError("Owned task needs a known workflow")
    if owner.get("schema_version") in {2, 3}:
        raw_workspace = owner.get("workspace")
        if not isinstance(raw_workspace, str) or Path(raw_workspace).is_absolute():
            raise ValueError("Task owner needs a project-relative workspace")
        workspace = (path / raw_workspace).resolve()
        if owner["schema_version"] == 3:
            raw_output = owner.get("output_dir")
            if not isinstance(raw_output, str) or Path(raw_output).is_absolute():
                raise ValueError("Task owner needs a relative report directory")
            output = (workspace / raw_output).resolve()
            boundary = store_root(output)
            if outline.get("task_layout") != LOCAL_LAYOUT or Path(outline["output_dir"]) != output:
                raise ValueError("Report-local task does not match its report directory")
        else:
            boundary = workspace / TEMP
        expected = boundary / owner.get("run_id", "")
        no_links(path, workspace)
    elif owner.get("schema_version") == 1:
        workspace = Path(owner.get("workspace", "")).resolve()
        boundary = Path(tempfile.gettempdir()).resolve() / "research"
        expected = boundary / workspace_key(workspace) / owner.get("run_id", "")
        no_links(path, boundary)
        if owner.get("workspace_key") != workspace_key(workspace):
            raise ValueError("Legacy task workspace key does not match")
    else:
        raise ValueError("Unknown task ownership format")
    run_id = owner.get("run_id", "")
    if not isinstance(run_id, str) or not validate_results.ID.fullmatch(run_id):
        raise ValueError("Invalid task run id")
    if path.resolve() != expected or not owner.get("token"):
        raise ValueError("Task ownership marker does not match its directory")
    if outline.get("run_id") != run_id or Path(outline.get("workspace", "")).resolve() != workspace or Path(outline.get("work_dir", "")).resolve() != expected:
        raise ValueError("Outline does not match the owned task")
    for entry in path.rglob("*"):
        if entry.is_symlink() or getattr(entry, "is_junction", lambda: False)() or not entry.resolve().is_relative_to(expected):
            raise ValueError(f"Task contains a linked or escaping entry: {entry}")
    return path, owner, outline


def parse_item(value, default_type):
    key, sep, name = value.partition("=")
    item_id, _, kind = key.partition(":")
    kind = kind or default_type
    if not sep or not name.strip() or not validate_results.ID.fullmatch(item_id) or kind not in validate_results.TYPES:
        raise ValueError("Items use id[:type]=name")
    return {"id": item_id, "name": name.strip(), "type": kind, "version": None, "seed_sources": []}


def parse_fields(values, goal):
    fields = []
    for value in values or [f"overview={goal}"]:
        key, sep, description = value.partition("=")
        if not sep or not validate_results.ID.fullmatch(key) or not description.strip():
            raise ValueError("Fields use id=question")
        if any(field["id"] == key for field in fields):
            raise ValueError(f"Duplicate field: {key}")
        fields.append({"id": key, "description": description.strip(), "core": True})
    return {"schema_version": 2, "fields": fields}


def english_directory(value, label):
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an English directory name")
    value = re.sub(r"[\s_]+", "-", value.strip().lower())
    if not validate_results.ID.fullmatch(value) or len(value) > 64:
        raise ValueError(f"{label} must use an English slug (lowercase letters, digits and hyphens); provide --theme/--target rather than a Chinese research title")
    if value in {"con", "prn", "aux", "nul", "docs", "scripts", "tests", "plans", "reports", "assets", "references", "archive"} or re.fullmatch(r"(?:com|lpt)[1-9]", value):
        raise ValueError(f"Reserved directory name for {label}: {value}")
    return value


def native_directory(value):
    # The caller explicitly declares an official Chinese product/project name;
    # ordinary translated topic titles must still use an English directory.
    if not isinstance(value, str) or not re.search(r"[\u3400-\u9fff]", value) or not re.fullmatch(r"[A-Za-z0-9\u3400-\u9fff]+(?:-[A-Za-z0-9\u3400-\u9fff]+)*", value) or len(value) > 64:
        raise ValueError("--native-target-name must be a Chinese official name without path separators or punctuation")
    return value


def create_task(workspace, topic, kind, depth="standard", workflow="auto", items=None, fields=None, output=None, goal=None, extras=None, report="report.md", theme=None, references=None, target=None, native_target_name=None):
    workspace = Path(workspace).resolve()
    if not workspace.is_dir() or not topic.strip() or kind not in validate_results.TYPES or depth not in {"brief", "standard", "detailed"}:
        raise ValueError("An existing workspace, topic, type and valid depth are required")
    parsed = [parse_item(value, kind) for value in items or [f"item-1={topic}"]]
    if len({item["id"] for item in parsed}) != len(parsed):
        raise ValueError("Duplicate item id")
    if workflow == "auto":
        workflow = "light" if depth == "brief" and len(parsed) == 1 else "full"
    if workflow not in {"light", "full"} or (workflow == "light" and (depth != "brief" or len(parsed) != 1)):
        raise ValueError("Light workflow is limited to one brief object")
    kinds = {item["type"] for item in parsed}
    if len(kinds) != 1 or (kind == "analysis") != (kinds == {"analysis"}):
        raise ValueError("Use separate tasks for different object types; analysis tasks contain judgments based on prior reports, not mixed source objects")
    category = next(iter(kinds))
    if theme is not None:
        theme = english_directory(theme, "theme")
    if target is not None:
        target = english_directory(target, "target")
    if native_target_name is not None:
        native_target_name = native_directory(native_target_name)
    if target is not None and native_target_name is not None:
        raise ValueError("Use --target or --native-target-name, not both")
    output = (workspace / output).resolve() if output else None
    if output:
        try:
            output_parts = output.relative_to(workspace).parts
        except ValueError as error:
            raise ValueError("output_dir must remain inside the project") from error
    else:
        output_parts = ()
    existing_report = bool(output and (output / report).is_file())
    standard_output = len(output_parts) == 3 and output_parts[1] in validate_results.TYPES
    if output and not standard_output and not existing_report:
        raise ValueError("New output directories must be <theme>/<type>/<target>; existing reports may be reused in place")
    theme_value = theme or (output_parts[0] if standard_output else "general")
    theme_slug = theme_value if existing_report and theme is None else english_directory(theme_value, "theme")
    if existing_report:
        declared = native_directory(native_target_name) if native_target_name else english_directory(target, "target") if target else None
        if declared and declared != output.name:
            raise ValueError("Existing report directory must be reused without renaming")
        target = output.name
        directory_layout = "existing"
    else:
        if standard_output and (output_parts[0] != theme_slug or output_parts[1] != category):
            raise ValueError("--output must match the theme and actual object type")
        chosen = native_target_name or target or (output_parts[2] if standard_output else None)
        chosen = chosen or (parsed[0]["id"] if items and len(parsed) == 1 else topic)
        target = native_directory(chosen) if native_target_name else english_directory(chosen, "target")
        if len(parsed) > 1 and not target.startswith("compare-"):
            target = "compare-" + target
        if len(target) > 64:
            raise ValueError("target including compare- must not exceed 64 characters")
        if standard_output and output_parts[2] != target:
            raise ValueError("--output target does not match the normalized directory name")
        output = output or workspace / theme_slug / category / target
        directory_layout = "theme-first"
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dt%H%M%Sz").lower() + "-" + uuid.uuid4().hex[:8]
    path = store_root(output) / run_id
    no_links(path, workspace)
    _, path_errors = checked_paths({"path_mode": MODE, "task_layout": LOCAL_LAYOUT, "workspace": str(workspace), "work_dir": str(path), "output_dir": str(output)})
    if path_errors:
        raise ValueError("; ".join(path_errors))
    delivery = {"report": report, "extra_files": extras or []}
    outline = {
        "schema_version": 2, "path_mode": MODE, "task_layout": LOCAL_LAYOUT, "run_id": run_id, "revision": 1,
        "workspace": str(workspace), "work_dir": str(path), "output_dir": str(output),
        "topic": topic.strip(), "goal": goal or topic.strip(), "object_type": kind,
        "mode": "single" if len(parsed) == 1 else "comparison", "depth": depth,
        "workflow": workflow, "items": parsed, "delivery": delivery,
        "classification": {"type": category, "theme": theme_slug, "target": target},
        "directory_layout": directory_layout,
    }
    if native_target_name:
        outline["directory_naming"] = {"native_target_name": native_target_name, "exception": "official Chinese name"}
    delivery_config(outline)
    if references:
        outline["reference_articles"] = articles.requirements({"reference_articles": references})
    field_config = parse_fields(fields, outline["goal"])
    path.mkdir(parents=True, exist_ok=False)
    write_json(path / "owner.json", {"schema_version": 3, "run_id": run_id, "workspace": relative(workspace, path), "output_dir": relative(output, workspace), "token": uuid.uuid4().hex, "created_at": datetime.now(timezone.utc).isoformat()})
    write_json(path / "outline.json", outline)
    if workflow == "full":
        write_json(path / "fields.json", field_config)
        (path / "results").mkdir()
    return describe_task(path)


def describe_task(work_dir):
    path, owner, outline = open_task(work_dir)
    result = {"run_id": owner["run_id"], "topic": outline["topic"], "workflow": outline["workflow"], "work_dir": str(path), "outline": str(path / "outline.json"), "output_dir": outline["output_dir"], "created_at": owner["created_at"]}
    if outline["workflow"] == "light":
        result.update(notes=str(path / "notes.md"), input_fingerprint=light_fingerprint(outline))
    else:
        result["fields"] = str(validate_results.find_fields(path / "outline.json"))
    result["verification_receipt_present"] = (path / "verified.json").is_file()
    if "classification" in outline:
        result["classification"] = outline["classification"]
    if outline.get("reference_articles"):
        result["reference_articles"] = articles.requirements(outline)
        result["manifest"] = str(path / "articles.json")
    return result


def list_tasks(workspace, topic=None):
    workspace = Path(workspace).resolve()
    tasks, errors = [], []
    for folder, dirs, _ in os.walk(workspace, followlinks=False):
        folder = Path(folder)
        for name in dirs[:]:
            entry = folder / name
            if name in {".git", ".agents"} or entry.is_symlink() or getattr(entry, "is_junction", lambda: False)():
                dirs.remove(name)
        if ".tmp" in dirs:
            dirs.remove(".tmp")
            temporary = folder / ".tmp"
            candidates = list(temporary.iterdir())
            if folder == workspace and (temporary / "research").is_dir():
                candidates.extend((temporary / "research").iterdir())
            for path in sorted(candidates):
                if not path.is_dir() or not (path / "owner.json").is_file():
                    continue
                try:
                    task = describe_task(path)
                    if Path(open_task(path)[2]["workspace"]).resolve() != workspace:
                        continue
                    if topic is None or topic.casefold() in task["topic"].casefold():
                        tasks.append(task)
                except (OSError, ValueError, TypeError, KeyError) as exc:
                    errors.append({"work_dir": str(path), "error": str(exc)})
    return {"workspace": str(workspace), "tasks": tasks, "errors": errors}


def promote_task(work_dir, fields=None):
    path, _, outline = open_task(work_dir)
    if outline["workflow"] != "light":
        raise ValueError("Task is already full; no files were changed")
    config = parse_fields(fields, outline.get("goal", outline["topic"]))
    if any((path / name).exists() for name in validate_results.FIELD_FILES) or (path / "results").exists():
        raise ValueError("Existing full-workflow files would be overwritten")
    write_json(path / "fields.json", config)
    (path / "results").mkdir()
    outline["workflow"] = "full"
    outline["revision"] += 1
    write_json(path / "outline.json", outline)
    return describe_task(path)


def add_articles(work_dir, urls, required=True):
    path, _, outline = open_task(work_dir)
    outline["reference_articles"] = articles.requirements({"reference_articles": [*outline.get("reference_articles", []), *({"url": url, "required": required} for url in urls)]})
    outline["revision"] += 1
    write_json(path / "outline.json", outline)
    return describe_task(path)


def derive_task(work_dir):
    """Continue a checked full task in a new run without implying fresh source access."""
    path, _, outline = open_task(work_dir)
    if outline["workflow"] != "full":
        raise ValueError("Derivation needs a full task; promote light notes and check field-level evidence first")
    fields_path = validate_results.find_fields(path / "outline.json")
    article_manifest = articles.load_manifest(outline) if (path / "articles.json").is_file() else None
    article_files = {}
    if article_manifest:
        for record in article_manifest["articles"].values():
            for version in [record, *record.get("previous_versions", [])]:
                names = [version.get("local_path"), *(image.get(field) for image in version.get("images", []) for field in ("path", "body_path"))]
                for name in names:
                    if name:
                        source = articles.local(path, name)
                        if source.is_file():
                            article_files[name] = source.read_bytes()
    inputs = [path / "outline.json", fields_path, *(path / "results" / f"{item['id']}.json" for item in outline["items"]), path / "progress.json", path / "articles.json", *(path / name for name in article_files)]
    source_hashes = {entry: research_update.sha(entry) if entry.is_file() else None for entry in inputs}
    checked = validate_results.validate(path / "outline.json", fields_path)
    if not checked["report_ready"]:
        raise ValueError(f"Source task needs valid, report-ready evidence before derivation: {checked}")
    fields = validate_results.load_document(fields_path)
    field_map = {field["id"]: field for field in fields["fields"]}
    item_map = {item["id"]: item for item in outline["items"]}
    records, originals, sources, migrated = {}, {}, {}, 0
    for item in outline["items"]:
        source_path = path / "results" / f"{item['id']}.json"
        originals[item["id"]] = source_hashes[source_path]
        data = validate_results.load_document(source_path)
        selected = validate_results.applicable_fields(field_map, item["id"], item.get("type", outline["object_type"]), item_map)
        for field_id in sorted(selected):
            field = field_map[field_id]
            record = data["fields"][field_id]
            canonical = validate_results.input_fingerprint(outline, item, field)
            if record["input_fingerprint"] != canonical:
                # Source validation checked the legacy fingerprint against the same question.
                # This converts its format, not its facts or source access dates.
                record["input_fingerprint"] = canonical
                migrated += 1
        records[item["id"]] = data
        for source in data["sources"]:
            entry = {key: source.get(key) for key in ("title", "url", "accessed_at")}
            sources[(entry["url"], entry["accessed_at"])] = entry
    progress = (path / "progress.json").read_bytes() if source_hashes[path / "progress.json"] is not None else None
    if any((research_update.sha(entry) if entry.is_file() else None) != expected for entry, expected in source_hashes.items()):
        raise ValueError("Source research changed during derivation; inspect concurrent edits before retrying")
    job = create_task(outline["workspace"], outline["topic"], outline["object_type"], outline["depth"], "full",
                      [f"{item['id']}:{item.get('type', outline['object_type'])}={item['name']}" for item in outline["items"]],
                      [f"{field['id']}={field['description']}" for field in fields["fields"]],
                      outline["output_dir"], outline.get("goal"), delivery_config(outline)["extra_files"], delivery_config(outline)["report"])
    child = Path(job["work_dir"])
    inherited = {key: value for key, value in outline.items() if key not in {"update", "derived_from"}}
    inherited.update(path_mode=MODE, task_layout=LOCAL_LAYOUT, run_id=job["run_id"], work_dir=str(child), revision=1)
    inherited["derived_from"] = {"run_id": outline["run_id"], "work_dir": str(path), "outline_sha256": source_hashes[path / "outline.json"],
                                 "fields_sha256": source_hashes[fields_path], "result_sha256": originals,
                                 "canonicalized_fingerprints": migrated, "sources": list(sources.values())}
    write_json(child / "outline.json", inherited)
    write_json(child / "fields.json", fields)
    for key, data in records.items():
        write_json(child / "results" / f"{key}.json", data)
    if progress is not None:
        (child / "progress.json").write_bytes(progress)
    if article_manifest:
        article_manifest["run_id"] = job["run_id"]
        for name, content in article_files.items():
            target = articles.local(child, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        articles.save_manifest(inherited, article_manifest)
    return describe_task(child)


def output_hashes(root):
    root = Path(root).resolve()
    hashes = {}
    for path in delivery_entries(root):
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)() or not path.resolve().is_relative_to(root):
            raise ValueError("Cannot seal linked output files")
        if path.is_file():
            hashes[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def begin_update(work_dir, sections=None, added=None, allow_files=None, baseline_date=None, baseline_version=None):
    path, _, outline = open_task(work_dir)
    if "update" in outline:
        raise ValueError("Task already has an update scope; create a fresh task to change it")
    report = Path(outline["output_dir"]) / delivery_config(outline)["report"]
    no_links(report, Path(outline["output_dir"]))
    outline["update"] = research_update.capture(path, report, sections, added, allow_files, baseline_date, baseline_version)
    outline["revision"] += 1
    write_json(path / "outline.json", outline)
    return describe_task(path)


def apply_update(work_dir, replacements):
    path, _, outline = open_task(work_dir)
    report = Path(outline["output_dir"]) / delivery_config(outline)["report"]
    no_links(report, Path(outline["output_dir"]))
    previous = research_update.sha(report)
    report, content = research_update.compose_update(outline, replacements, render_report_note(report_context(path / "outline.json")))
    temporary = None
    try:
        scratch = path / "scratch" if outline.get("path_mode") == MODE else report.parent
        scratch.mkdir(exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", prefix=".research-update-", dir=scratch, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        if research_update.sha(report) != previous:
            raise ValueError("Report changed while composing the update; inspect concurrent edits before retrying")
        no_links(report, Path(outline["output_dir"]))
        temporary.replace(report)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return {"updated": True, "report": str(report), "scope": outline["update"]["sections"] + outline["update"]["added_sections"], "note": "Run verify after reviewing the updated prose and citations."}


def verify_task(work_dir):
    path, _, outline = open_task(work_dir)
    check = validate_report.validate(outline["output_dir"], outline_path=path / "outline.json")
    if not check["valid"]:
        raise ValueError(f"Delivery verification failed: {check['errors']}")
    context = report_context(path / "outline.json")
    receipt = {"run_id": outline["run_id"], "completion": context["completion"], "research_digest": context["research_digest"], "output_dir": outline["output_dir"], "files": output_hashes(outline["output_dir"])}
    stored = display_paths(receipt, outline["workspace"]) if outline.get("path_mode") == MODE else receipt
    write_json(path / "verified.json", stored)
    return {"verified": True, **receipt}


def cleanup_plan(work_dir):
    path, owner, outline = open_task(work_dir)
    receipt = json.loads((path / "verified.json").read_text(encoding="utf-8"))
    if outline.get("path_mode") == MODE and isinstance(receipt.get("output_dir"), str):
        receipt["output_dir"] = str((Path(outline["workspace"]) / receipt["output_dir"]).resolve())
    context = report_context(path / "outline.json")
    check = validate_report.validate(outline["output_dir"], outline_path=path / "outline.json")
    if not check["valid"] or receipt.get("run_id") != outline["run_id"] or receipt.get("research_digest") != context["research_digest"] or receipt.get("output_dir") != outline["output_dir"] or receipt.get("files") != output_hashes(outline["output_dir"]):
        raise ValueError("Research or delivered files changed since verification; verify again")
    inventory = []
    for entry in sorted(path.rglob("*")):
        if entry.is_file():
            info = entry.stat()
            inventory.append({"path": entry.relative_to(path).as_posix(), "size": info.st_size, "mtime_ns": info.st_mtime_ns})
    encoded = json.dumps({"run_id": outline["run_id"], "owner_token": owner["token"], "receipt": receipt, "inventory": inventory}, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return {"eligible": True, "requires_confirmation": True, "plan_id": hashlib.sha256(encoded).hexdigest(),
            "work_dir": str(path), "preserve_output_dir": outline["output_dir"], "completion": context["completion"],
            "files_to_remove": len(inventory), "bytes_to_remove": sum(entry["size"] for entry in inventory),
            "note": "Plan only; eligible is not permission to delete. Obtain user confirmation for this exact task directory, then recheck plan_id and promptly use the native filesystem workflow. No files were deleted."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("--workspace", required=True, type=Path)
    create.add_argument("--topic", required=True)
    create.add_argument("--type", required=True, choices=sorted(validate_results.TYPES), dest="kind")
    create.add_argument("--depth", choices=("brief", "standard", "detailed"), default="standard")
    create.add_argument("--workflow", choices=("auto", "light", "full"), default="auto")
    create.add_argument("--item", action="append", dest="items")
    create.add_argument("--field", action="append", dest="fields")
    create.add_argument("--goal")
    create.add_argument("--theme", help="Classification theme such as agent-memory; defaults to general")
    create.add_argument("--target", help="English directory slug; for comparisons the compare- prefix is added when needed")
    create.add_argument("--native-target-name", help="Official Chinese product/project name, retained as an explicit directory naming exception")
    create.add_argument("--reference", action="append", dest="references", help="User-specified article URL; acquisition and body review are mandatory")
    create.add_argument("--output", type=Path)
    create.add_argument("--report", default="report.md")
    create.add_argument("--extra", action="append", default=[], help="Exact path=reason for a user-requested extra file")
    listing = commands.add_parser("list")
    listing.add_argument("--workspace", required=True, type=Path)
    listing.add_argument("--topic")
    for name in ("show", "promote", "derive", "report-note", "verify", "cleanup-plan", "begin-update", "apply-update", "add-article", "fetch-articles", "download-article-images", "import-article", "review-article", "archive-article"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--work-dir", required=True, type=Path)
        if name == "promote":
            cmd.add_argument("--field", action="append", dest="fields")
        if name == "begin-update":
            cmd.add_argument("--section", action="append", dest="sections")
            cmd.add_argument("--add-section", action="append", dest="added")
            cmd.add_argument("--allow-file", action="append", dest="allow_files")
            cmd.add_argument("--baseline-date")
            cmd.add_argument("--baseline-version")
        if name == "apply-update":
            cmd.add_argument("--sections-file", required=True, type=Path)
        if name == "add-article":
            cmd.add_argument("--url", action="append", required=True)
            cmd.add_argument("--optional", action="store_true")
        if name == "fetch-articles":
            cmd.add_argument("--id", action="append", dest="article_ids")
            cmd.add_argument("--images", choices=("remote", "all", "selected"), default="remote")
            cmd.add_argument("--image-url", action="append", default=[])
            cmd.add_argument("--proxy", choices=("env", "direct"), default="env")
            cmd.add_argument("--browser", action="store_true")
            cmd.add_argument("--refresh", action="store_true")
        if name == "download-article-images":
            cmd.add_argument("--id", required=True)
            selection = cmd.add_mutually_exclusive_group(required=True)
            selection.add_argument("--image-url", action="append", default=[])
            selection.add_argument("--all", action="store_true", dest="all_images")
            cmd.add_argument("--proxy", choices=("env", "direct"), default="env")
            cmd.add_argument("--refresh", action="store_true", help="Refresh selected images only; does not fetch or change the article body")
        if name == "import-article":
            cmd.add_argument("--url", required=True)
            cmd.add_argument("--file", required=True, type=Path)
            cmd.add_argument("--title", required=True)
            cmd.add_argument("--method", choices=("browser", "pdf", "provided"), default="provided")
            cmd.add_argument("--final-url")
        if name in {"review-article", "archive-article"}:
            cmd.add_argument("--id", required=True)
        if name == "review-article":
            cmd.add_argument("--decision", choices=("accept", "reject"), required=True)
            cmd.add_argument("--reason", required=True)
        if name == "archive-article":
            cmd.add_argument("--citation", action="append", required=True)
            cmd.add_argument("--image", action="append", default=[])
            cmd.add_argument("--exception")
            cmd.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        if args.command == "create":
            extras = []
            for value in args.extra:
                path, sep, reason = value.partition("=")
                if not sep:
                    raise ValueError("--extra uses path=reason")
                extras.append({"path": path, "reason": reason})
            result = create_task(args.workspace, args.topic, args.kind, args.depth, args.workflow, args.items, args.fields, args.output, args.goal, extras, args.report, args.theme, args.references, args.target, args.native_target_name)
        elif args.command == "list":
            result = list_tasks(args.workspace, args.topic)
        elif args.command == "show":
            result = describe_task(args.work_dir)
        elif args.command == "promote":
            result = promote_task(args.work_dir, args.fields)
        elif args.command == "derive":
            result = derive_task(args.work_dir)
        elif args.command == "begin-update":
            result = begin_update(args.work_dir, args.sections, args.added, args.allow_files, args.baseline_date, args.baseline_version)
        elif args.command == "apply-update":
            result = apply_update(args.work_dir, validate_results.load_document(args.sections_file))
        elif args.command == "add-article":
            result = add_articles(args.work_dir, args.url, not args.optional)
        elif args.command in {"fetch-articles", "download-article-images", "import-article", "review-article", "archive-article"}:
            path, _, outline = open_task(args.work_dir)
            if args.command == "fetch-articles":
                result = articles.acquire(outline, args.images, args.image_url, args.proxy, args.browser, args.refresh, args.article_ids)
            elif args.command == "download-article-images":
                result = articles.download_images(outline, args.id, args.image_url, args.proxy, args.refresh, args.all_images)
            elif args.command == "import-article":
                result = articles.import_body(outline, args.url, args.file, args.title, args.method, args.final_url)
            elif args.command == "review-article":
                result = articles.review(outline, args.id, args.decision, args.reason)
            else:
                result = articles.archive(outline, args.id, args.citation, args.image, args.exception, args.replace)
            result["manifest"] = str(path / "articles.json")
        elif args.command == "report-note":
            path, _, _ = open_task(args.work_dir)
            print(render_report_note(report_context(path / "outline.json")))
            return 0
        elif args.command == "verify":
            result = verify_task(args.work_dir)
        else:
            result = cleanup_plan(args.work_dir)
        workspace = args.workspace.resolve() if args.command in {"create", "list"} else Path(open_task(args.work_dir)[2]["workspace"])
        print(json.dumps(display_paths(result, workspace), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
