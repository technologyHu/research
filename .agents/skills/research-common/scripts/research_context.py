"""Shared, read-only research assessment, delivery configuration and report notes."""

from datetime import date, datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import unicodedata

import validate_results as results
from research_catalog import LOCAL_REVIEW_LABELS, LOCAL_TIME, report_metadata_path
from research_evidence import LABELS as CONFLICT_LABELS, summaries
from research_update import update_summary
from research_paths import checked_paths, encode_outline, check_repo_source
import research_articles as articles
import research_dependencies as dependencies

LABELS = {"complete": "完整", "partial": "部分完成", "blocked": "阻塞"}
OPENING_VERSION = 3
APPLICATION_NAMES = {"codex", "openaicodex", "claudecode", "chatgpt", "githubcopilot", "geminicli", "cursor"}


def researcher_name(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("researcher must be a nonempty name")
    name = value.strip()
    key = re.sub(r"[\W_]+", "", unicodedata.normalize("NFKC", name).casefold())
    if key in APPLICATION_NAMES:
        raise ValueError("Use the user's verified GitHub/GitCode username or the name they provide, rather than an application name")
    return name


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def delivery_config(outline):
    raw = outline.get("delivery", {})
    if not isinstance(raw, dict):
        raise ValueError("delivery must be a mapping")
    report = raw.get("report", "report.md")
    if not isinstance(report, str) or not report or any(char in report for char in "/\\:*?\0") or Path(report).suffix.lower() != ".md":
        raise ValueError("delivery.report must be a root-level Markdown filename")
    extras, seen = [], {report.casefold(), report_metadata_path(report).name.casefold()}
    if not isinstance(raw.get("extra_files", []), list):
        raise ValueError("delivery.extra_files must be a list")
    for entry in raw.get("extra_files", []):
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError("Each extra file needs a path and a user-request reason")
        value = entry["path"]
        path = PurePosixPath(value)
        if not value or not path.parts or path.is_absolute() or any(char in value for char in "\\:*?\0") or any(p.casefold() in {"..", ".git", ".agents", ".tmp"} for p in path.parts) or str(path) != value:
            raise ValueError(f"Extra file must be an exact safe relative path: {value}")
        if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
            raise ValueError(f"Record the user's explicit request for extra file: {value}")
        if value.casefold() in seen:
            raise ValueError(f"Duplicate delivered path: {value}")
        seen.add(value.casefold())
        extras.append({"path": value, "reason": entry["reason"].strip()})
    return {"report": report, "extra_files": extras}


def light_fingerprint(outline, legacy_update=False):
    payload = {key: outline.get(key) for key in ("topic", "goal", "time_range", "depth", "object_type", "items")}
    if legacy_update and "update" in outline:
        payload["update"] = outline["update"]
    return digest(payload)


def validate_light(outline_path, fingerprints_only=False):
    outline = results.load_document(outline_path)
    errors, warnings = [], []
    if not isinstance(outline, dict):
        return {"valid": False, "completion": "blocked", "report_ready": False, "errors": ["outline must be a mapping"], "warnings": []}
    if outline.get("schema_version") != 2 or type(outline.get("revision")) is not int or outline["revision"] < 1:
        errors.append("Light outline needs schema_version=2 and a positive revision")
    if not isinstance(outline.get("object_type"), str) or outline["object_type"] not in results.TYPES:
        errors.append("Invalid light object_type")
    items = outline.get("items", [])
    kind = outline.get("object_type")
    if outline.get("workflow") != "light" or outline.get("mode") != "single" or outline.get("depth") != "brief" or not isinstance(items, list) or len(items) != 1:
        errors.append("Light workflow requires single mode, brief depth and exactly one item")
    if not isinstance(items, list) or not items or not isinstance(items[0], dict):
        errors.append("A light item is required")
    else:
        item = items[0]
        if not isinstance(item.get("id"), str) or not results.ID.fullmatch(item["id"]) or not isinstance(item.get("name"), str) or not item["name"].strip():
            errors.append("A valid item id and name are required")
        kind = item.get("type", outline.get("object_type"))
        if not isinstance(kind, str) or kind not in results.TYPES:
            errors.append("Invalid light object type")
        if (outline.get("object_type") == "analysis") != (kind == "analysis"):
            errors.append("Analysis tasks must use analysis subjects or questions, not source objects")
        if item.get("version") is not None and not isinstance(item["version"], str):
            errors.append("Light requested version must be a string or null")
    for key in ("topic", "run_id"):
        if not isinstance(outline.get(key), str) or not outline[key].strip():
            errors.append(f"Light {key} must be a nonempty string")
    paths, path_errors = checked_paths(outline)
    errors.extend(path_errors)
    delivery_config(outline)
    articles.requirements(outline)
    if fingerprints_only:
        current_articles = {}
        try:
            articles.assessment(outline)
            current_articles = dependencies.fingerprints(dependencies.state(outline))
        except (OSError, ValueError, TypeError, KeyError) as exc:
            errors.append(f"Invalid article acquisition records: {exc}")
        return {"mode": "fingerprints", "valid": not errors, "input_fingerprint": light_fingerprint(outline), "article_fingerprints": current_articles, "errors": errors}
    assessment = outline.get("assessment", {})
    if not isinstance(assessment, dict):
        assessment = {}
        errors.append("assessment must be a mapping")
    expected = {light_fingerprint(outline), light_fingerprint(outline, legacy_update=True)}
    if not isinstance(assessment.get("input_fingerprint"), str) or assessment["input_fingerprint"] not in expected:
        errors.append("Missing or stale light assessment input_fingerprint; review the whole brief")
    if assessment.get("conflicts"):
        errors.append("Conflicting evidence requires promotion to the full workflow and field-level adjudication")
    if not isinstance(assessment.get("status"), str) or assessment["status"] not in LABELS:
        errors.append("assessment.status must be complete, partial or blocked")
    version = assessment.get("version")
    if version is not None and not isinstance(version, str):
        errors.append("assessment.version must be a string or null")
    if isinstance(items, list) and items and isinstance(items[0], dict) and items[0].get("version") is not None and version != items[0]["version"]:
        errors.append("Light assessment does not match the requested version")
    gaps = assessment.get("core_gaps", [])
    if not isinstance(gaps, list) or not all(isinstance(x, str) and x.strip() for x in gaps):
        errors.append("assessment.core_gaps must be a list of descriptions")
        gaps = []
    other_gaps = assessment.get("non_core_gaps", [])
    if not isinstance(other_gaps, list) or not all(isinstance(x, str) and x.strip() for x in other_gaps):
        errors.append("assessment.non_core_gaps must be a list of descriptions")
    sources = assessment.get("sources", [])
    if not isinstance(sources, list):
        errors.append("assessment.sources must be a list")
        sources = []
    for source in sources:
        if not isinstance(source, dict) or not results.valid_url(source.get("url")) or not source.get("title") or source.get("kind") not in {"primary", "secondary"} or not source.get("locator"):
            errors.append("Each light source needs title, URL, kind and locator")
            continue
        try:
            date.fromisoformat(source.get("accessed_at", ""))
        except (ValueError, TypeError):
            errors.append("Each light source needs an ISO accessed_at date")
        errors.extend(check_repo_source(source, outline, kind))
    try:
        notes = (paths["work_dir"] / "notes.md").read_text(encoding="utf-8-sig")
        if not notes.strip():
            errors.append("Light workflow needs nonempty notes.md with findings, sources and gaps")
    except (OSError, KeyError) as exc:
        errors.append(f"Cannot read light notes: {exc}")
    stale_articles = []
    try:
        article_state = articles.assessment(outline)
        dependency_errors, stale_articles = dependencies.check(assessment, [source.get("url") for source in sources if isinstance(source, dict)], dependencies.state(outline), "light assessment")
        errors.extend(dependency_errors)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        errors.append(f"Invalid article acquisition records: {exc}")
        article_state = {"gaps": []}
    if errors or not sources or assessment.get("status") == "blocked":
        completion = "blocked"
    elif gaps or article_state["gaps"] or assessment.get("status") == "partial":
        completion = "partial"
    else:
        completion = "complete"
    if not sources:
        warnings.append("No source was recorded; the brief cannot be completed")
    result = {"valid": not errors, "completion": completion, "report_ready": not errors and completion != "blocked", "scope": "all", "checked_items": 1 if items else 0, "errors": errors, "warnings": warnings, "article_gaps": article_state["gaps"]}
    if stale_articles:
        result["stale_articles"] = stale_articles
    return result


def report_context(outline_path, fields_path=None):
    outline_path = Path(outline_path)
    outline = results.load_document(outline_path)
    delivery = delivery_config(outline)
    versions, gaps, other_gaps, source_urls, conflicts = [], [], [], set(), []
    update = update_summary(outline)
    if outline.get("workflow", "full") == "light":
        checked = validate_light(outline_path)
        if not checked["report_ready"]:
            raise ValueError(f"Research is not ready for a report: {checked}")
        assessment = outline["assessment"]
        item = outline["items"][0]
        versions.append({"id": item["id"], "name": item["name"], "type": item.get("type", outline["object_type"]), "version": assessment.get("version", item.get("version")), "completion": checked["completion"]})
        gaps = [{"item_id": item["id"], "question": "核心问题", "reason": gap} for gap in assessment.get("core_gaps", [])]
        other_gaps = [{"item_id": item["id"], "question": "补充问题", "reason": gap} for gap in assessment.get("non_core_gaps", [])]
        source_urls.update(source["url"] for source in assessment.get("sources", []))
        payload = {"outline": encode_outline(outline, outline_path), "notes": (Path(outline["work_dir"]) / "notes.md").read_text(encoding="utf-8-sig")}
    else:
        fields_path = Path(fields_path) if fields_path else results.find_fields(outline_path)
        checked = results.validate(outline_path, fields_path)
        if not checked["report_ready"]:
            raise ValueError(f"Research is not ready for a report: {checked}")
        fields_doc = results.load_document(fields_path)
        fields = {field["id"]: field for field in fields_doc["fields"]}
        records, current_sources = {}, set()
        for item in outline["items"]:
            key = item["id"]
            data = json.loads((Path(outline["work_dir"]) / "results" / f"{key}.json").read_text(encoding="utf-8-sig"))
            records[key] = data
            current_sources.update((source["url"], source["accessed_at"]) for source in data["sources"])
            versions.append({"id": key, "name": item["name"], "type": data["type"], "version": data.get("version"), "completion": checked["item_completion"][key]["status"]})
            for field_id in checked["item_completion"][key]["unknown_fields"]:
                target = gaps if fields[field_id].get("core", True) else other_gaps
                gap = {"item_id": key, "question": fields[field_id]["description"], "reason": data["fields"][field_id]["reason"]}
                if "display_question" in fields[field_id]:
                    gap["display_question"] = fields[field_id]["display_question"]
                target.append(gap)
            kind = item.get("type", outline["object_type"])
            selected = results.applicable_fields(fields, key, kind, {x["id"]: x for x in outline["items"]})
            source_map = {source["id"]: source["url"] for source in data["sources"]}
            for field_id in selected:
                record = data["fields"][field_id]
                if record["status"] in {"confirmed", "inferred"}:
                    source_urls.update(source_map[e["source_id"]] for e in record.get("evidence", []))
                entries = summaries(record, key, field_id, source_map)
                conflicts.extend(entries)
                source_urls.update(position["url"] for entry in entries for position in entry["positions"])
        payload = {"outline": encode_outline(outline, outline_path), "fields": fields_doc, "results": records}
    for item in versions:
        if item["version"] is not None and not isinstance(item["version"], str):
            raise ValueError("Result versions must be strings or null")
    article_state = articles.assessment(outline)
    if article_state["entries"]:
        payload["articles"] = article_state
    context = {
        "schema_version": 1, "run_id": outline["run_id"], "completion": checked["completion"],
        "workflow": outline.get("workflow", "full"), "items": versions, "core_gaps": gaps,
        "source_urls": sorted(source_urls), "delivery": delivery, "research_digest": digest(payload),
    }
    if outline.get("directory_layout") == "dated-flat":
        for key in ("directory_layout", "classification", "report_id", "created_at", "updated_at",
                    "theme_id", "theme_slug", "theme_path", "theme_name"):
            context[key] = outline[key]
    if "researcher" in outline:
        researcher = outline["researcher"]
        if not isinstance(researcher, str) or not researcher.strip():
            raise ValueError("researcher must be a nonempty name")
        context["researcher"] = researcher.strip()
    if update is not None:
        context["update"] = update
    if other_gaps:
        context["non_core_gaps"] = other_gaps
    if article_state["gaps"]:
        context["article_gaps"] = article_state["gaps"]
    if conflicts:
        context["conflicts"] = sorted(conflicts, key=lambda entry: (entry["item_id"], entry["field_id"], entry["id"]))
    if outline.get("derived_from") is not None:
        origin = outline["derived_from"]
        if outline.get("workflow", "full") != "full" or not isinstance(origin, dict) or not isinstance(origin.get("run_id"), str) or not isinstance(origin.get("sources"), list):
            raise ValueError("Invalid derived_from provenance")
        inherited = []
        for source in origin["sources"]:
            if not isinstance(source, dict) or not isinstance(source.get("title"), str) or not isinstance(source.get("url"), str) or not isinstance(source.get("accessed_at"), str):
                raise ValueError("Invalid inherited source provenance")
            if source["url"] in source_urls and (source["url"], source["accessed_at"]) in current_sources:
                inherited.append(source)
        context["derived_from"] = {"run_id": origin["run_id"], "sources": inherited}
    return context


def safe_text(value):
    value = re.sub(r"\s+", " ", str(value))
    return re.sub(r"([\\`*_\[\]<>])", r"\\\1", value)


def legacy_visible_note(context):
    versions = "；".join(f"{safe_text(item['name'])}（{safe_text(item['version'] or '未指定／未核实')}）" for item in context["items"])
    gaps = "；".join(f"{safe_text(gap['question'])}：{safe_text(gap['reason'])}" for gap in context["core_gaps"]) or "无"
    blocked = "；".join(safe_text(item["name"]) for item in context["items"] if item["completion"] == "blocked") or "无"
    scope = "本次局部更新" if "update" in context else ""
    label_prefix = "本次" if scope else ""
    lines = [f"> 调研状态：{scope}{LABELS[context['completion']]}", f"> {label_prefix}采用版本：{versions}", f"> {label_prefix}核心缺口：{gaps}", f"> {label_prefix}无实质结果的对象：{blocked}"]
    if context.get("non_core_gaps"):
        names = {item["id"]: item["name"] for item in context["items"]}
        lines.append(f"> {label_prefix}非核心缺口：" + "；".join(f"{safe_text(names[gap['item_id']])}／{safe_text(gap['question'])}：{safe_text(gap['reason'])}" for gap in context["non_core_gaps"]))
    if context.get("article_gaps"):
        lines.append(f"> {label_prefix}参考文章缺口：" + "；".join(f"{safe_text(gap['url'])}：{safe_text(gap['reason'])}" for gap in context["article_gaps"]))
    if context.get("derived_from", {}).get("sources"):
        lines.append("> 证据沿用：" + "；".join(f"{safe_text(source['title'])}（原访问日期 {safe_text(source['accessed_at'])}）" for source in context["derived_from"]["sources"]) + "；沿用不表示本次重新访问。")
    if "update" in context:
        update = context["update"]
        lines.extend([
            "> 本次更新范围：" + "；".join(safe_text(name) for name in update["sections"] + update["added_sections"]),
            "> 未复核部分原版本：" + safe_text(update["baseline_version"]),
            "> 未复核部分原日期：" + safe_text(update["baseline_date"]),
            "> 未复核部分原缺口：" + safe_text(update["baseline_gaps"]),
        ])
    if context.get("conflicts"):
        lines.append("> 证据冲突：" + "；".join(f"{safe_text(entry['issue'])}（{CONFLICT_LABELS[entry['resolution']]}）：{safe_text(entry['rationale'])}" for entry in context["conflicts"]))
    return lines


def version_note(context):
    items = context["items"]
    versions = []
    for item in items[:3]:
        version = (item["version"] or "版本待确认").replace("Public Beta", "公测版").replace("；", "，")
        versions.append(f"{safe_text(item['name'])}（{safe_text(version)}）")
    if len(items) > 3:
        versions.append(f"等 {len(items)} 个对象，详见正文")
    return "> 采用版本：" + "、".join(versions)


def compact_note_v1(context):
    completion = context["completion"]
    status = LABELS[completion]
    if "update" in context:
        status = "本次局部更新已完成" if completion == "complete" else f"本次局部更新{status}"
    lines = [f"> 调研状态：{status}", version_note(context)]
    if "update" in context:
        update = context["update"]
        sections = update["sections"] + update["added_sections"]
        labels = [safe_text(section.lstrip("# ")) for section in sections[:3]]
        scope = "、".join(labels) if len(sections) <= 3 else f"{len(sections)} 节，详见正文"
        lines.append(f"> 本次更新：{scope}")
    gaps = context["core_gaps"]
    if gaps:
        questions = [safe_text(gap["question"]) for gap in gaps[:3]]
        detail = "、".join(questions) if len(gaps) <= 3 else f"{len(gaps)} 项，详见正文"
        lines.append(f"> 主要待确认事项：{detail}")
    if context.get("non_core_gaps"):
        lines.append(f"> 其他待确认事项：{len(context['non_core_gaps'])} 项，详见正文。")
    if context.get("article_gaps"):
        lines.append(f"> 未能核对的参考资料：{len(context['article_gaps'])} 项，详见正文。")
    return lines


def visible_note(context, version=OPENING_VERSION):
    labels = LOCAL_REVIEW_LABELS if version >= 3 and "update" in context else LABELS
    lines = [f"> 调研状态：{labels[context['completion']]}", version_note(context)]
    lines.append(f"> 调研人：{safe_text(context.get('researcher', '未记录'))}")
    created = context.get("created_at")
    updated = context.get("updated_at") or created
    if updated:
        moment = datetime.fromisoformat(updated).astimezone(LOCAL_TIME).strftime("%Y-%m-%d %H:%M:%S")
        label = "最近修订时间" if updated != created else "调研时间"
        lines.append(f"> {label}：{moment}（北京时间）")
    else:
        lines.append("> 调研时间：未记录")
    names = {item["id"]: item["name"] for item in context["items"]}
    for key, label in (("core_gaps", "主要待确认事项"), ("non_core_gaps", "其他待确认事项")):
        details = []
        for gap in context.get(key, []):
            question = gap.get("display_question") or gap["question"]
            if question in {"核心问题", "补充问题"}:
                question = gap["reason"]
            prefix = f"{names[gap['item_id']]}：" if len(names) > 1 else ""
            details.append(safe_text(prefix + question).rstrip("。？?"))
        if details:
            lines.append(f"> {label}：" + "。".join(dict.fromkeys(details)) + "。")
    if context.get("article_gaps"):
        missing = [safe_text(gap.get("title") or gap["url"]) for gap in context["article_gaps"]]
        lines.append("> 未能核对的参考资料：" + "、".join(dict.fromkeys(missing)))
    return lines


def render_report_note(context, version=OPENING_VERSION):
    lines = compact_note_v1(context) if version == 1 else visible_note(context, version)
    if context["delivery"]["extra_files"]:
        lines.append("> 附加交付：" + "；".join(f"[{safe_text(entry['path'])}](<{entry['path']}>)" for entry in context["delivery"]["extra_files"]))
    return "\n>\n".join(lines) + "\n"


def report_metadata_bytes(context):
    if "researcher" in context:
        researcher_name(context["researcher"])
    metadata = {**context, "opening_version": OPENING_VERSION}
    return (json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
