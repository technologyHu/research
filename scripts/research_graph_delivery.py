"""Prepare an owned bundle before publishing; roll back on replacement failures.

Individual replacements are atomic, the multi-file bundle is not. Ordinary
generation/validation failures leave all published files untouched. A failed
commit restores the previous bytes; if restoration itself fails, retain the
transaction manifest and original backups for recovery instead of deleting them.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile


class ArtifactRollbackError(RuntimeError):
    pass


def target_path(root: Path, relative: str) -> Path:
    path = root / relative
    path.resolve().relative_to(root.resolve())
    parts = path.relative_to(root).parts
    if any(root.joinpath(*parts[:i]).is_symlink() for i in range(1, len(parts) + 1)):
        raise ValueError(f"Refusing output symlink: {relative}")
    return path


def read_bytes(path: Path) -> bytes | None:
    return path.read_bytes() if path.exists() else None


def replace_file(source: Path, target: Path):
    os.replace(source, target)


def commit_bundle(root: Path, stage: Path, paths: list[str], originals: dict):
    candidates = {rel: (stage / "new" / rel).read_bytes() for rel in paths}
    changed = [rel for rel in paths if candidates[rel] != originals[rel]]
    for rel in paths:
        if read_bytes(target_path(root, rel)) != originals[rel]:
            raise RuntimeError(f"Output changed during generation; retry without overwriting: {rel}")
    records = []
    for rel in changed:
        old = originals[rel]
        if old is not None:
            backup = stage / "backup" / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(old)
        records.append({"path": rel, "hadOriginal": old is not None,
                        "before": hashlib.sha256(old).hexdigest() if old is not None else None,
                        "after": hashlib.sha256(candidates[rel]).hexdigest()})
    (stage / "transaction.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    installed = []
    created_dirs = []
    try:
        for rel in changed:
            target = target_path(root, rel)
            if read_bytes(target) != originals[rel]:
                raise RuntimeError(f"Output changed during publication: {rel}")
            missing = []
            parent = target.parent
            while not parent.exists():
                missing.append(parent)
                parent = parent.parent
            target.parent.mkdir(parents=True, exist_ok=True)
            created_dirs.extend(reversed(missing))
            replace_file(stage / "new" / rel, target)
            installed.append(rel)
    except BaseException:
        errors = []
        for rel in reversed(installed):
            try:
                target = target_path(root, rel)
                if read_bytes(target) != candidates[rel]:
                    raise RuntimeError(f"Published file was externally modified: {rel}")
                if originals[rel] is None:
                    target.unlink()
                else:
                    replace_file(stage / "backup" / rel, target)
            except BaseException as error:
                errors.append(f"{rel}: {error}")
        for path in reversed(created_dirs):
            try:
                path.rmdir()  # Only remove empty directories created by this transaction.
            except OSError:
                pass
        if errors:
            recovery = stage.relative_to(root).as_posix()
            raise ArtifactRollbackError(f"Rollback incomplete; originals retained in {recovery}/backup; " + "; ".join(errors))
        raise


def publish_bundle(root: Path, paths: list[str], prepare):
    """prepare(stage_root) writes and validates every selected artifact first."""
    root = root.resolve()
    originals = {rel: read_bytes(target_path(root, rel)) for rel in paths}
    area = target_path(root, ".tmp/research-graph")
    area.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="build-", dir=area))
    keep_recovery = False
    try:
        candidate_root = stage / "new"
        candidate_root.mkdir()
        # Preserve manual README content while rendering the generated block.
        if originals.get("README.md") is not None:
            (candidate_root / "README.md").write_bytes(originals["README.md"])
        prepare(candidate_root)
        commit_bundle(root, stage, paths, originals)
    except ArtifactRollbackError:
        keep_recovery = True
        raise
    finally:
        if not keep_recovery:
            # Explicit containment check before recursive cleanup on Windows.
            if stage.is_symlink() or stage.resolve().parent != area.resolve() or not stage.name.startswith("build-"):
                raise RuntimeError("Refusing to clean unexpected staging path")
            shutil.rmtree(stage)
