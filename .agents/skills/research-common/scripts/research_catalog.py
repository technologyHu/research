"""Shared theme vocabulary and dated report names; no machine-specific paths."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re

SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
# Report subjects join slug segments with __; retain legacy -- names unchanged.
# Theme and object IDs stay single slugs.
TARGET = re.compile(r"[a-z0-9]+(?:(?:-{1,2}|__)[a-z0-9]+)*\Z")
DATED = re.compile(r"(?P<base>.+?)(?P<separator>__|-)(?P<stamp>\d{8}-\d{6})\Z")
LOCAL_TIME = timezone(timedelta(hours=8), "Asia/Shanghai")
REGISTRY = "themes.yaml"
LOCAL_REVIEW_LABELS = {
    "complete": "局部复查完成",
    "partial": "局部复查部分完成",
    "blocked": "局部复查受阻",
}


def now():
    return datetime.now(LOCAL_TIME).replace(microsecond=0)


def stamp(value):
    value = datetime.fromisoformat(value) if isinstance(value, str) else value
    if value.tzinfo is None:
        raise ValueError("Report timestamps require a timezone")
    return value.astimezone(LOCAL_TIME).strftime("%Y%m%d-%H%M%S")


def split_name(value):
    match = DATED.fullmatch(value)
    if not match:
        return value, None
    try:
        moment = datetime.strptime(match["stamp"], "%Y%m%d-%H%M%S").replace(tzinfo=LOCAL_TIME)
    except ValueError as error:
        raise ValueError("Invalid report directory timestamp") from error
    return match["base"], moment.isoformat()


def date_separator(value):
    """Preserve existing timestamp boundaries; new report names default to __."""
    match = DATED.fullmatch(value)
    return match["separator"] if match else "__"


def read_registry(workspace, required=True):
    path = Path(workspace) / REGISTRY
    if not path.is_file():
        if not required:
            return {}
        raise ValueError("themes.yaml is required; initialize or register the theme before creating a report")
    if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
        raise ValueError("Theme registry cannot be a linked file")
    text = path.read_text(encoding="utf-8-sig")
    try:
        data = json.loads(text)
    except ValueError:
        try:
            import yaml
        except ImportError as error:
            raise ValueError("Reading themes.yaml requires PyYAML") from error
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as error:
            raise ValueError("Invalid themes.yaml: " + str(error)) from error
    return validate_registry(data)


def validate_registry(data):
    if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("themes"), list):
        raise ValueError("themes.yaml needs schema_version=1 and a themes list")
    entries = {}
    for raw in data["themes"]:
        if not isinstance(raw, dict):
            raise ValueError("Each theme must be a mapping")
        key, slug, name = (raw.get(field) for field in ("id", "slug", "name"))
        if not isinstance(key, str) or not SLUG.fullmatch(key) or key in entries:
            raise ValueError("Theme IDs must be unique English slugs")
        if not isinstance(slug, str) or not SLUG.fullmatch(slug) or not isinstance(name, str) or not name.strip():
            raise ValueError("Each theme needs a slug and display name")
        aliases = raw.get("aliases", [])
        parent = raw.get("parent")
        if parent is not None and (not isinstance(parent, str) or not SLUG.fullmatch(parent)):
            raise ValueError("Theme parent must be a registered ID or null")
        if slug in {"con", "prn", "aux", "nul"} or re.fullmatch(r"(?:com|lpt)[1-9]", slug):
            raise ValueError("Reserved directory name in theme registry")
        if not isinstance(aliases, list) or any(not isinstance(v, str) or not v.strip() for v in aliases):
            raise ValueError("Theme aliases must be nonempty strings")
        entries[key] = {**raw, "parent": raw.get("parent"), "aliases": aliases}
    visiting, completed, paths = set(), set(), {}

    def resolve(key):
        if key in visiting:
            raise ValueError("Theme parent cycle")
        if key in completed:
            return entries[key]
        if key not in entries:
            raise ValueError("Unknown parent theme: " + str(key))
        visiting.add(key)
        entry = entries[key]
        parent = resolve(entry["parent"]) if entry["parent"] is not None else None
        entry["path"] = (parent["path"] if parent else []) + [entry["slug"]]
        entry["names"] = (parent["names"] if parent else []) + [entry["name"]]
        entry["directory"] = "-".join(entry["path"])
        entry["label"] = " / ".join(entry["names"])
        if len(entry["directory"]) > 96 or entry["directory"] in paths:
            raise ValueError("Flattened theme names must be unique and at most 96 characters")
        paths[entry["directory"]] = key
        visiting.remove(key)
        completed.add(key)
        return entry

    aliases = {}
    for key in entries:
        entry = resolve(key)
        for value in [key, entry["directory"], *entry["aliases"]]:
            normalized = normalize_theme(value)
            if normalized in aliases and aliases[normalized] != key:
                raise ValueError("Ambiguous theme name or alias: " + value)
            aliases[normalized] = key
    return entries


def normalize_theme(value):
    return re.sub(r"[\s_]+", "-", value.strip().lower())


def theme_entry(workspace, value):
    entries = read_registry(workspace)
    value = normalize_theme(value)
    for entry in entries.values():
        if value in {normalize_theme(v) for v in [entry["id"], entry["directory"], *entry["aliases"]]}:
            return entry
    raise ValueError("Unknown theme; register it in themes.yaml: " + value)


def analysis_theme(entry):
    """Flatten registered theme levels without merging words within each slug."""
    return "__".join(entry["path"])


def analysis_subject(base, entry):
    """Return the subject and naming style, preserving legacy analysis names."""
    for theme, separator, legacy in ((analysis_theme(entry), "__", False), (entry["directory"], "-", True)):
        if base == theme:
            return entry["directory"], legacy
        if base.startswith(theme + separator) and base[len(theme + separator):]:
            return base[len(theme + separator):], legacy
    raise ValueError("Analysis directory must begin with its registered theme name")


def report_base(kind, theme_slug, target, *, analysis_name=None, legacy_analysis=False):
    if kind != "analysis":
        return target
    theme = theme_slug if legacy_analysis else analysis_name or theme_slug
    if target in {theme_slug, theme}:
        return theme
    return theme + ("-" if legacy_analysis else "__") + target


def report_directory(workspace, kind, theme_slug, target, timestamp, *, separator="__", legacy_analysis=False):
    if separator not in {"__", "-"}:
        raise ValueError("Report timestamp separator must be __ or legacy -")
    analysis_name = analysis_theme(theme_entry(workspace, theme_slug)) if kind == "analysis" else None
    leaf = report_base(kind, theme_slug, target, analysis_name=analysis_name,
                       legacy_analysis=legacy_analysis) + separator + stamp(timestamp)
    if kind == "analysis":
        return Path(workspace) / "analysis-reports" / leaf
    return Path(workspace) / "research-reports" / theme_slug / kind / leaf


def report_metadata_path(report):
    return Path(report).with_suffix(".meta.json")


def has_generated_report_opening(text):
    """Recognize the compact opening, including its quote paragraph separator."""
    front_matter = re.match(r"\A---[ \t]*\r?\n.*?^---[ \t]*\r?\n", text, re.S | re.M)
    if front_matter:
        text = text[front_matter.end():]
    return bool(re.match(
        r"\A\s*(?:# [^\r\n]+\r?\n\s*)?> 调研状态：[^\r\n]+\r?\n>\r?\n> 采用版本：",
        text,
    ))


def report_summary(path):
    path = Path(path)
    if not path.is_file():
        return {}
    metadata = report_metadata_path(path)
    if metadata.is_symlink() or getattr(metadata, "is_junction", lambda: False)():
        raise ValueError("Report metadata must be a regular file")
    if metadata.exists():
        value = json.loads(metadata.read_text(encoding="utf-8-sig"))
        if not isinstance(value, dict):
            raise ValueError("Report metadata must be a JSON object")
        return value
    matches = re.findall(r"<!--\s*research-summary\s*\n(.*?)-->", path.read_text(encoding="utf-8-sig"), re.S)
    if len(matches) != 1:
        return {}
    value = json.loads(matches[0])
    return value if isinstance(value, dict) else {}


def initialize_registry(workspace):
    target = Path(workspace) / REGISTRY
    if target.exists():
        raise ValueError("Theme registry already exists")
    data = {"schema_version": 1, "themes": [{"id": "general", "slug": "general", "name": "通用", "parent": None}]}
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"registry": str(target)}


def register_theme(workspace, key, slug, name, parent=None, aliases=()):
    entries = read_registry(workspace)
    if key in entries:
        raise ValueError("Theme already exists; update its stable entry in themes.yaml")
    computed = {"path", "names", "directory", "label"}
    data = {"schema_version": 1, "themes": [{field: value for field, value in entry.items() if field not in computed}
                                           for entry in entries.values()]}
    data["themes"].append({"id": key, "slug": slug, "name": name, "parent": parent, "aliases": list(aliases)})
    validate_registry(data)
    target = Path(workspace) / REGISTRY
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"registry": str(target), "theme_id": key}
