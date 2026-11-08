"""Portable project-relative task files with resolved paths used only during execution."""

from copy import deepcopy
import hashlib
import os
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

MODE = "project-relative"
TEMP = Path(".tmp") / "research"
LOCAL_LAYOUT = "report-local"
PATH_KEYS = {"workspace", "work_dir", "output_dir", "outline", "fields", "notes", "report", "preserve_output_dir", "manifest"}


def repo_report_parts(value):
    parsed = urlsplit(value)
    decoded = unquote(parsed.path)
    path = PurePosixPath(decoded)
    if (parsed.scheme != "repo" or parsed.netloc or parsed.query or parsed.fragment
            or not decoded or path.is_absolute() or str(path) != decoded
            or any(char in decoded for char in "\\:*?\0")
            or any(part.casefold() in {"..", ".tmp", ".git", ".agents", "docs", "scripts", "tests", "archive"} for part in path.parts)
            or len(path.parts) < 3 or path.suffix.lower() != ".md" or path.name.casefold() == "plan.md"):
        raise ValueError("repo: sources must identify a project-relative research report")
    return path


def repo_report_path(value, workspace):
    parts = repo_report_parts(value)
    workspace = Path(workspace).resolve()
    path = workspace.joinpath(*parts.parts)
    for entry in (path, *path.parents):
        if entry.is_symlink() or getattr(entry, "is_junction", lambda: False)():
            raise ValueError("repo: sources cannot use linked paths")
        if entry == workspace:
            break
    if not path.resolve().is_relative_to(workspace) or not path.is_file():
        raise ValueError("repo: source report is missing or outside the project")
    return path.resolve()


def check_repo_source(source, outline, kind):
    """Validate adopted local reports without persisting machine-specific file URIs."""
    value = source.get("url", "")
    if not isinstance(value, str):
        return []
    try:
        if urlsplit(value).scheme != "repo":
            return []
        if kind != "analysis" or outline.get("object_type") != "analysis":
            raise ValueError("repo: sources are limited to analysis tasks")
        if source.get("kind") != "secondary":
            raise ValueError("An adopted report is a secondary source")
        if not isinstance(source.get("version"), str) or not source["version"].strip():
            raise ValueError("Record the adopted report's actual version or date")
        path = repo_report_path(value, outline["workspace"])
        if path.is_relative_to(Path(outline["output_dir"]).resolve()):
            raise ValueError("An analysis cannot cite its own deliverables as prior evidence")
        expected = hashlib.sha256(path.read_bytes()).hexdigest()
        if source.get("sha256") != expected:
            raise ValueError("Adopted report changed or has no sha256; review affected conclusions before accepting it")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return [str(exc)]
    return []


def relative(path, workspace):
    return Path(os.path.relpath(path, workspace)).as_posix()


def resolve_outline(data, config_path):
    if not isinstance(data, dict) or data.get("path_mode") != MODE:
        return data
    result = deepcopy(data)
    for key in ("workspace", "work_dir", "output_dir"):
        value = data.get(key)
        if not isinstance(value, str) or not value or Path(value).is_absolute():
            raise ValueError(f"project-relative {key} must be a nonempty relative path")
    workspace = (Path(config_path).resolve().parent / data["workspace"]).resolve()
    result["workspace"] = str(workspace)
    for key in ("work_dir", "output_dir"):
        result[key] = str((workspace / data[key]).resolve())
    if isinstance(result.get("derived_from"), dict) and result["derived_from"].get("work_dir"):
        result["derived_from"]["work_dir"] = str((workspace / result["derived_from"]["work_dir"]).resolve())
    return result


def encode_outline(data, config_path):
    if not isinstance(data, dict) or data.get("path_mode") != MODE:
        return data
    result = deepcopy(data)
    config_dir = Path(config_path).resolve().parent
    workspace = (config_dir / data["workspace"]).resolve()
    result["workspace"] = relative(workspace, config_dir)
    for key in ("work_dir", "output_dir"):
        result[key] = relative((workspace / data[key]).resolve(), workspace)
    if isinstance(result.get("derived_from"), dict) and result["derived_from"].get("work_dir"):
        origin = (workspace / result["derived_from"]["work_dir"]).resolve()
        if origin.is_relative_to(workspace):
            result["derived_from"]["work_dir"] = relative(origin, workspace)
        else:
            result["derived_from"].pop("work_dir")
            result["derived_from"]["legacy_external"] = True
    return result


def checked_paths(outline):
    errors, paths = [], {}
    for key in ("workspace", "work_dir", "output_dir"):
        value = outline.get(key)
        if isinstance(value, str) and value and Path(value).is_absolute():
            paths[key] = Path(value).resolve()
        else:
            errors.append(f"Cannot resolve {key} from the plan")
    if len(paths) != 3:
        return paths, errors
    workspace, work, output = (paths[key] for key in ("workspace", "work_dir", "output_dir"))
    if outline.get("path_mode") == MODE:
        if outline.get("task_layout") == LOCAL_LAYOUT:
            if work.parent != output / ".tmp":
                errors.append("work_dir must be a single task directory under output_dir/.tmp")
        elif outline.get("task_layout") is None:
            boundary = workspace / TEMP
            if work == boundary or not work.is_relative_to(boundary):
                errors.append("Legacy relative work_dir must be under .tmp/research")
        else:
            errors.append("Unknown task_layout")
        if output == workspace or not output.is_relative_to(workspace):
            errors.append("output_dir must be a directory within the project")
        protected = (".git", ".agents", ".tmp")
    else:
        if work.is_relative_to(workspace) or workspace.is_relative_to(work):
            errors.append("Legacy work_dir must be outside workspace")
        protected = (".git", ".agents")
    if output.is_relative_to(work) or (work.is_relative_to(output) and outline.get("task_layout") != LOCAL_LAYOUT):
        errors.append("Work and output directories must be separate")
    if workspace.is_relative_to(output) or any(output.is_relative_to(workspace / part) for part in protected):
        errors.append("Unsafe output directory")
    if outline.get("path_mode") == MODE and output.is_relative_to(workspace) and any(part in {".tmp", ".git", ".agents"} for part in output.relative_to(workspace).parts):
        errors.append("Report directories cannot be inside reserved directories")
    return paths, errors


def delivery_entries(root):
    """Walk delivered files without descending into the report's temporary directory."""
    root = Path(root)
    for folder, dirs, files in os.walk(root, followlinks=False):
        folder = Path(folder)
        for name in sorted(dirs[:]):
            entry = folder / name
            linked = entry.is_symlink() or getattr(entry, "is_junction", lambda: False)()
            if linked:
                dirs.remove(name)
            elif folder == root and name == ".tmp":
                dirs.remove(name)
                continue
            yield entry
        for name in sorted(files):
            yield folder / name


def display_paths(value, workspace):
    if isinstance(value, list):
        return [display_paths(entry, workspace) for entry in value]
    if not isinstance(value, dict):
        return value
    return {key: relative(entry, workspace) if key in PATH_KEYS and isinstance(entry, str) and Path(entry).is_absolute()
            else display_paths(entry, workspace) for key, entry in value.items()}
