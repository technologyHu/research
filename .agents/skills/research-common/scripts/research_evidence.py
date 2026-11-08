"""Validate recorded disagreements; this does not decide whether a claim is true."""

RESOLUTIONS = {"unresolved", "version_difference", "condition_difference", "prefer_source", "coexist"}
LABELS = {"unresolved": "未解决", "version_difference": "版本差异", "condition_difference": "条件差异", "prefer_source": "择源采纳", "coexist": "限定并列"}


def nonblank(value):
    return isinstance(value, str) and bool(value.strip())


def validate_conflicts(record, source_ids, prefix):
    errors, seen = [], set()
    conflicts = record.get("conflicts", [])
    if not isinstance(conflicts, list):
        return [f"{prefix}: conflicts must be a list"]
    for conflict in conflicts:
        label = f"{prefix}/conflict"
        if not isinstance(conflict, dict):
            errors.append(f"{label}: expected a mapping")
            continue
        key = conflict.get("id")
        if not nonblank(key) or key in seen:
            errors.append(f"{label}: a unique conflict id is required")
        if isinstance(key, str):
            seen.add(key)
        for name in ("issue", "rationale"):
            if not nonblank(conflict.get(name)):
                errors.append(f"{label}: {name} is required")
        resolution = conflict.get("resolution")
        if not isinstance(resolution, str) or resolution not in RESOLUTIONS:
            errors.append(f"{label}: invalid resolution")
        if resolution == "unresolved" and record.get("status") != "unknown":
            errors.append(f"{label}: unresolved conflict requires an unknown field, not a settled conclusion")
        positions = conflict.get("positions", [])
        if not isinstance(positions, list):
            errors.append(f"{label}: positions must be a list")
            positions = []
        position_ids = set()
        for position in positions:
            if not isinstance(position, dict):
                errors.append(f"{label}: position must be a mapping")
                continue
            sid = position.get("source_id")
            if not isinstance(sid, str) or sid not in source_ids:
                errors.append(f"{label}: position references an unknown source")
            else:
                position_ids.add(sid)
            for name in ("claim", "locator", "conditions"):
                if not nonblank(position.get(name)):
                    errors.append(f"{label}: each position needs {name}")
            if "version" not in position or (position["version"] is not None and not nonblank(position["version"])):
                errors.append(f"{label}: each position needs a version string or explicit null")
        if len(position_ids) < 2:
            errors.append(f"{label}: record at least two distinct sources")
        selected = conflict.get("selected_source_ids", [])
        if not isinstance(selected, list) or not all(isinstance(sid, str) and sid in position_ids for sid in selected):
            errors.append(f"{label}: selected_source_ids must refer to recorded positions")
            selected = []
        if resolution == "prefer_source":
            if not selected:
                errors.append(f"{label}: prefer_source needs selected_source_ids")
            evidence = record.get("evidence", [])
            support = {entry.get("source_id") for entry in evidence if isinstance(entry, dict) and isinstance(entry.get("source_id"), str)} if isinstance(evidence, list) else set()
            if record.get("status") in {"confirmed", "inferred"} and not set(selected) <= support:
                errors.append(f"{label}: chosen sources must support the field's evidence")
    return errors


def summaries(record, item_id, field_id, source_map):
    return [{**conflict, "item_id": item_id, "field_id": field_id,
             "positions": [{**position, "url": source_map[position["source_id"]]} for position in conflict["positions"]]}
            for conflict in record.get("conflicts", [])]
