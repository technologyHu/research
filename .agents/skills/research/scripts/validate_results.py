#!/usr/bin/env python3
"""Read-only validation of research v2 plans and evidence records (Python 3.10+)."""

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

from research_evidence import validate_conflicts
from research_paths import checked_paths, resolve_outline, repo_report_parts, check_repo_source
import research_articles as articles
import research_dependencies as dependencies

TYPES = {"paper", "open-source", "product", "benchmark", "analysis"}
STATUSES = {"confirmed", "inferred", "unknown", "not_applicable"}
ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
FIELD_FILES = ("fields.json", "fields.yaml", "fields.yml")


def load_document(path):
    path = Path(path)
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".json":
        return resolve_outline(json.loads(text), path)
    try:
        import yaml
    except ImportError as exc:
        raise ValueError("YAML requires PyYAML; equivalent .json plans need no dependency") from exc
    try:
        return resolve_outline(yaml.safe_load(text), path)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc


def nonempty(value):
    return value is not None and value not in ("", [], {}) and (
        not isinstance(value, str) or bool(value.strip())
    )


def valid_url(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        if parsed.scheme in {"http", "https"}:
            return bool(parsed.netloc)
        if parsed.scheme == "repo":
            repo_report_parts(value)
            return True
        return parsed.scheme == "file" and parsed.path.startswith("/")
    except ValueError:
        return False


def find_fields(outline_path):
    """Discover one field configuration; never silently select between duplicates."""
    candidates = [Path(outline_path).parent / name for name in FIELD_FILES]
    found = [path for path in candidates if path.is_file()]
    if len(found) != 1:
        raise ValueError("Full workflow needs one fields configuration; found " + str([str(path) for path in found]) + ". Use the existing file, or pass --fields explicitly to validators.")
    return found[0]


def input_fingerprint(outline, item, field, legacy_update=False):
    """Bind a field result to its question, target and research scope, not batch revision."""
    payload = {
        "field": {"id": field["id"], "description": field["description"].strip()},
        "item": {
            "id": item["id"], "name": item["name"],
            "type": item.get("type", outline["object_type"]),
            "version": item.get("version"),
        },
        "context": {key: outline.get(key) for key in ("topic", "depth", "goal", "time_range")},
    }
    if legacy_update and "update" in outline:
        payload["update"] = outline["update"]
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def matches_fingerprint(record, outline, item, field):
    expected = {input_fingerprint(outline, item, field)}
    if "update" in outline:
        expected.add(input_fingerprint(outline, item, field, legacy_update=True))
    return isinstance(record.get("input_fingerprint"), str) and record["input_fingerprint"] in expected


def applicable_fields(field_map, item_id, kind, item_map):
    return {
        key for key, field in field_map.items()
        if kind in field.get("applies_to", TYPES)
        and item_id in field.get("item_ids", item_map)
    }


def validate(outline_path, fields_path, results_dir=None, item_ids=None, progress_path=None, fingerprints_only=False):
    errors, warnings = [], []
    checked = 0
    item_completion = {}
    planned_items = 0
    article_state = None
    stale_article_fields = {}

    def outcome():
        states = [entry["status"] for entry in item_completion.values()]
        if errors or not states or all(state == "blocked" for state in states):
            completion = "blocked"
        elif all(state == "complete" for state in states):
            completion = "complete"
        else:
            completion = "partial"
        if completion == "complete" and article_state and article_state["gaps"]:
            completion = "partial"
        result = {
            "valid": not errors, "completion": completion,
            "report_ready": not errors and completion != "blocked",
            "scope": "selected" if item_ids else "all", "planned_items": planned_items,
            "checked_items": checked, "item_completion": item_completion,
            "errors": errors, "warnings": warnings,
        }
        if article_state and article_state["entries"]:
            result["article_gaps"] = article_state["gaps"]
        if stale_article_fields:
            result["stale_article_fields"] = stale_article_fields
        return result

    def require(condition, message):
        if not condition:
            errors.append(message)

    try:
        outline = load_document(outline_path)
        fields_doc = load_document(fields_path)
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
        return outcome()
    if not isinstance(outline, dict) or not isinstance(fields_doc, dict):
        errors.append("Plans must be mappings")
        return outcome()
    require(outline.get("schema_version") == 2, "outline.schema_version must be 2")
    require(outline.get("workflow", "full") == "full", "Full result validation requires workflow=full")
    require(fields_doc.get("schema_version") == 2, "fields.schema_version must be 2")
    for key in ("run_id", "topic"):
        require(isinstance(outline.get(key), str) and bool(outline[key].strip()), f"outline.{key} is required")
    revision = outline.get("revision")
    require(type(revision) is int and revision >= 1, "outline.revision must be a positive integer")
    require(isinstance(outline.get("object_type"), str) and outline["object_type"] in TYPES, "Invalid outline.object_type")
    require(isinstance(outline.get("mode"), str) and outline["mode"] in {"single", "comparison"}, "Invalid outline.mode")
    require(isinstance(outline.get("depth"), str) and outline["depth"] in {"brief", "standard", "detailed"}, "Invalid outline.depth")
    for key in ("goal", "time_range"):
        require(outline.get(key) is None or isinstance(outline[key], str), f"outline.{key} must be a string or null")
    paths, path_errors = checked_paths(outline)
    errors.extend(path_errors)
    items = outline.get("items")
    fields = fields_doc.get("fields")
    if not isinstance(items, list) or not items or not isinstance(fields, list) or not fields:
        errors.append("items and fields must both be nonempty lists")
        return outcome()
    planned_items = len(items)
    require(outline.get("mode") != "single" or len(items) == 1, "single mode requires exactly one item")
    require(outline.get("mode") != "comparison" or len(items) >= 2, "comparison mode requires at least two items")
    item_map = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not ID.fullmatch(item["id"]):
            errors.append("Every item needs a path-safe lowercase id")
            continue
        key = item["id"]
        require(key not in item_map, f"Duplicate item id: {key}")
        item_map[key] = item
        require(isinstance(item.get("name"), str) and bool(item["name"].strip()), f"{key}: name is required")
        item_type = item.get("type", outline.get("object_type"))
        require(isinstance(item_type, str) and item_type in TYPES, f"{key}: invalid type")
        require((outline.get("object_type") == "analysis") == (item_type == "analysis"), f"{key}: analysis tasks must use analysis questions, not source objects")
        require(item.get("version") is None or isinstance(item.get("version"), str), f"{key}: version must be a string or null")
    require(len({item.get("type", outline.get("object_type")) for item in item_map.values() if isinstance(item.get("type", outline.get("object_type")), str)}) <= 1,
            "Different object types require separate tasks; use prior reports as analysis sources")
    field_map = {}
    for field in fields:
        if not isinstance(field, dict) or not isinstance(field.get("id"), str) or not ID.fullmatch(field["id"]):
            errors.append("Every field needs a path-safe lowercase id")
            continue
        key = field["id"]
        require(key not in field_map, f"Duplicate field id: {key}")
        field_map[key] = field
        require(isinstance(field.get("description"), str) and bool(field["description"].strip()), f"{key}: description is required")
        require(type(field.get("core", True)) is bool, f"{key}: core must be a boolean")
        for scope, allowed in (("applies_to", TYPES), ("item_ids", set(item_map))):
            if scope in field:
                value = field[scope]
                require(isinstance(value, list) and bool(value) and all(isinstance(x, str) and x in allowed for x in value), f"{key}: invalid {scope}")
    selected = list(item_ids) if item_ids else list(item_map)
    require(bool(selected), "No items selected")
    for key in selected:
        require(key in item_map, f"Unknown selected item: {key}")
    if errors:
        return outcome()
    expected_by_item = {
        item_id: applicable_fields(field_map, item_id, item_map[item_id].get("type", outline["object_type"]), item_map)
        for item_id in selected
    }
    for item_id, expected in expected_by_item.items():
        require(bool(expected), f"{item_id}: no applicable fields")
    if errors:
        return outcome()
    try:
        articles.requirements(outline)
        article_state = articles.assessment(outline)
        article_dependencies = dependencies.state(outline)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        errors.append(str(exc))
        return outcome()
    if fingerprints_only:
        return {
            "mode": "fingerprints", "valid": True,
            "input_fingerprints": {
                item_id: {
                    key: input_fingerprint(outline, item_map[item_id], field_map[key])
                    for key in sorted(expected_by_item[item_id])
                } for item_id in selected
            },
            "article_fingerprints": dependencies.fingerprints(article_dependencies),
        }
    progress = {}
    progress_file = Path(progress_path) if progress_path else paths["work_dir"] / "progress.json"
    if progress_path or progress_file.exists():
        try:
            progress = json.loads(progress_file.read_text(encoding="utf-8-sig"))
            if not isinstance(progress, dict):
                raise ValueError("progress must map item ids to field states")
        except (OSError, ValueError) as exc:
            errors.append(f"Invalid progress file: {exc}")
            return outcome()
    folder = Path(results_dir) if results_dir else paths["work_dir"] / "results"
    for item_id in selected:
        before_errors = len(errors)
        item_completion[item_id] = {"status": "blocked", "answered_fields": 0, "unknown_fields": [], "core_unknown_fields": []}
        item = item_map[item_id]
        kind = item.get("type", outline["object_type"])
        expected = expected_by_item[item_id]
        item_progress = progress.get(item_id, {})
        if not isinstance(item_progress, dict):
            errors.append(f"{item_id}: progress must map field ids to state records")
            item_progress = {}
        for key in sorted(expected & item_progress.keys()):
            state = item_progress[key]
            if not isinstance(state, dict) or not isinstance(state.get("status"), str) or state["status"] not in {"pending", "stale", "done"}:
                errors.append(f"{item_id}/{key}: invalid progress state")
            elif state["status"] != "done":
                errors.append(f"{item_id}/{key}: progress is {state['status']}; review before reporting")
        try:
            data = json.loads((folder / f"{item_id}.json").read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            errors.append(f"{item_id}: {exc}")
            continue
        checked += 1
        if not isinstance(data, dict):
            errors.append(f"{item_id}: result must be a mapping")
            continue
        require(data.get("schema_version") == 2, f"{item_id}: schema_version must be 2")
        require(data.get("item_id") == item_id, f"{item_id}: mismatched result item_id")
        require(data.get("type") == kind, f"{item_id}: mismatched result type")
        require(data.get("version") is None or isinstance(data.get("version"), str), f"{item_id}: version must be a string or null")
        if item.get("version") is not None:
            require(data.get("version") == item["version"], f"{item_id}: requested version does not match result")
        source_ids = set()
        sources = data.get("sources")
        if not isinstance(sources, list):
            errors.append(f"{item_id}: sources must be a list")
            sources = []
        for source in sources:
            if not isinstance(source, dict) or not isinstance(source.get("id"), str) or not source["id"].strip():
                errors.append(f"{item_id}: invalid source record")
                continue
            sid = source["id"]
            require(sid not in source_ids, f"{item_id}: duplicate source id {sid}")
            source_ids.add(sid)
            require(isinstance(source.get("title"), str) and bool(source["title"].strip()), f"{item_id}/{sid}: missing title")
            require(valid_url(source.get("url")), f"{item_id}/{sid}: invalid source URL")
            require(isinstance(source.get("kind"), str) and source["kind"] in {"primary", "secondary"}, f"{item_id}/{sid}: invalid source kind")
            errors.extend(f"{item_id}/{sid}: {error}" for error in check_repo_source(source, outline, kind))
            try:
                date.fromisoformat(source.get("accessed_at", ""))
            except (TypeError, ValueError):
                errors.append(f"{item_id}/{sid}: accessed_at must be an ISO date string")
        values = data.get("fields")
        if not isinstance(values, dict):
            errors.append(f"{item_id}: fields must be a mapping")
            continue
        for key in sorted(expected - values.keys()):
            errors.append(f"{item_id}: missing field {key}")
        for key in sorted(values.keys() - expected):
            warnings.append(f"{item_id}: unselected field {key}; exclude it from the report unless requested")
        answered, unknown, core_unknown = [], [], []
        for key in sorted(expected & values.keys()):
            record = values[key]
            prefix = f"{item_id}/{key}"
            if not isinstance(record, dict) or not isinstance(record.get("status"), str) or record["status"] not in STATUSES:
                errors.append(f"{prefix}: invalid status record")
                continue
            status = record["status"]
            require(
                matches_fingerprint(record, outline, item, field_map[key]),
                f"{prefix}: missing or stale input_fingerprint; review this field against the current question and scope",
            )
            if status in {"confirmed", "inferred"}:
                answered.append(key)
            elif status == "unknown":
                unknown.append(key)
                if field_map[key].get("core", True):
                    core_unknown.append(key)
            evidence = record.get("evidence", [])
            errors.extend(validate_conflicts(record, source_ids, prefix))
            dependency_errors, stale = dependencies.check(record, dependencies.referenced_urls(record, sources), article_dependencies, prefix)
            errors.extend(dependency_errors)
            if stale:
                stale_article_fields.setdefault(item_id, {})[key] = stale
            require(isinstance(evidence, list), f"{prefix}: evidence must be a list")
            if status in {"confirmed", "inferred"}:
                require(nonempty(record.get("value")), f"{prefix}: supported value must not be empty")
                require(isinstance(evidence, list) and bool(evidence), f"{prefix}: supported value needs evidence")
            else:
                require(record.get("value") is None, f"{prefix}: unresolved value must be null")
                warnings.append(f"{prefix}: {status}; preserve the reason in the report")
            if status != "confirmed":
                require(isinstance(record.get("reason"), str) and bool(record["reason"].strip()), f"{prefix}: {status} needs a reason")
            for entry in evidence if isinstance(evidence, list) else []:
                if not isinstance(entry, dict):
                    errors.append(f"{prefix}: invalid evidence entry")
                    continue
                sid = entry.get("source_id")
                require(isinstance(sid, str) and sid in source_ids, f"{prefix}: evidence references an unknown source")
                require(isinstance(entry.get("locator"), str) and bool(entry["locator"].strip()), f"{prefix}: evidence needs a locator")
                for detail in ("supports", "conditions"):
                    if detail in entry:
                        require(isinstance(entry[detail], str) and bool(entry[detail].strip()), f"{prefix}: evidence {detail} must be a nonempty string")
        if len(errors) > before_errors or not answered:
            status = "blocked"
        elif core_unknown:
            status = "partial"
        else:
            status = "complete"
        item_completion[item_id] = {
            "status": status, "answered_fields": len(answered),
            "unknown_fields": unknown, "core_unknown_fields": core_unknown,
        }
    return outcome()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outline", required=True, type=Path)
    parser.add_argument("--fields", type=Path, help="Required for full workflow; omitted for light workflow")
    parser.add_argument("--results", type=Path)
    parser.add_argument("--item", action="append", dest="items")
    parser.add_argument("--progress", type=Path, help="Defaults to work_dir/progress.json when present")
    parser.add_argument("--fingerprints", action="store_true", help="Print current field fingerprints without reading results")
    args = parser.parse_args()
    try:
        outline = load_document(args.outline)
        if isinstance(outline, dict) and outline.get("workflow") == "light":
            from research_context import validate_light
            if args.fields or args.results or args.items or args.progress:
                raise ValueError("Light workflow does not use --fields, --results, --item or --progress; promote it for incremental work")
            result = validate_light(args.outline, args.fingerprints)
        else:
            if args.fields is None:
                raise ValueError("Full workflow requires --fields")
            result = validate(args.outline, args.fields, args.results, args.items, args.progress, args.fingerprints)
    except (OSError, ValueError, TypeError) as exc:
        result = {"valid": False, "completion": "blocked", "report_ready": False, "checked_items": 0, "errors": [str(exc)], "warnings": []}
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["valid"]:
        return 1
    if args.fingerprints:
        return 0
    return {"complete": 0, "partial": 2, "blocked": 3}[result["completion"]]


if __name__ == "__main__":
    raise SystemExit(main())
