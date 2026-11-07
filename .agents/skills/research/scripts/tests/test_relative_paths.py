"""Test portable configuration, centralized scratch files and legacy read compatibility."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_task_workflow as fixtures
from test_task_workflow import context, task, results
from research_paths import MODE


class RelativePaths(unittest.TestCase):
    setUp = fixtures.TaskWorkflow.setUp
    create = fixtures.TaskWorkflow.create
    populate = fixtures.TaskWorkflow.populate
    write_report = fixtures.TaskWorkflow.write_report

    def test_new_owner_outline_and_receipt_store_only_relative_project_paths(self):
        path, _, _ = self.write_report(self.create())
        raw = json.loads((path / "outline.json").read_text(encoding="utf-8"))
        self.assertEqual(raw["path_mode"], MODE)
        self.assertEqual((path / raw["workspace"]).resolve(), self.workspace)
        self.assertEqual(raw["work_dir"], path.relative_to(self.workspace).as_posix())
        self.assertTrue(raw["output_dir"].startswith("general/paper/"))
        for key in ("workspace", "work_dir", "output_dir"):
            self.assertFalse(Path(raw[key]).is_absolute())
        owner = json.loads((path / "owner.json").read_text(encoding="utf-8"))
        self.assertEqual(owner["schema_version"], 3)
        self.assertFalse(Path(owner["workspace"]).is_absolute())
        task.verify_task(path)
        receipt = json.loads((path / "verified.json").read_text(encoding="utf-8"))
        self.assertFalse(Path(receipt["output_dir"]).is_absolute())
        self.assertTrue(task.cleanup_plan(path)["eligible"])

    def test_cli_paths_are_relative_and_output_is_relative_to_workspace(self):
        command = [sys.executable, "-X", "utf8", "-B", str(Path(task.__file__).resolve()), "create", "--workspace", ".", "--topic", "相对路径", "--type", "paper", "--output", "method-analysis/paper/custom"]
        run = subprocess.run(command, cwd=self.workspace, text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        job = json.loads(run.stdout)
        self.assertEqual(Path(job["work_dir"]).parent.as_posix(), job["output_dir"] + "/.tmp")
        self.assertEqual(job["output_dir"], "method-analysis/paper/custom")
        for key in ("work_dir", "outline", "fields", "output_dir"):
            self.assertFalse(Path(job[key]).is_absolute())
        self.assertTrue((self.workspace / job["outline"]).is_file())
        listing = subprocess.run(command[:5] + ["list", "--workspace", "."], cwd=self.workspace, text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(listing.returncode, 0, listing.stdout + listing.stderr)
        self.assertEqual(json.loads(listing.stdout)["workspace"], ".")

    def test_project_can_be_copied_and_verified_without_rewriting_paths(self):
        path, outline, report = self.write_report(self.create())
        task.verify_task(path)
        original = report.read_bytes()
        copied = self.root / "relocated-project"
        shutil.copytree(self.workspace, copied)
        relocated_task = copied / path.relative_to(self.workspace)
        _, _, relocated = task.open_task(relocated_task)
        self.assertEqual(Path(relocated["workspace"]), copied)
        self.assertEqual(Path(relocated["output_dir"]), copied / Path(outline["output_dir"]).relative_to(self.workspace))
        self.assertTrue(task.cleanup_plan(relocated_task)["eligible"])
        self.assertTrue(task.verify_task(relocated_task)["verified"])
        self.assertEqual((Path(relocated["output_dir"]) / "report.md").read_bytes(), original)

    def test_update_temporary_file_is_inside_the_same_task(self):
        path, _, _ = self.write_report(self.create())
        task.begin_update(path, ["## 分析"])
        real = task.tempfile.NamedTemporaryFile
        seen = []

        def inspect(*args, **kwargs):
            seen.append(Path(kwargs["dir"]))
            return real(*args, **kwargs)

        with patch.object(task.tempfile, "NamedTemporaryFile", side_effect=inspect):
            task.apply_update(path, {"## 分析": "## 分析\n\n[资料](https://example.org/original)支持本次结论。"})
        self.assertEqual(seen, [path / "scratch"])
        self.assertEqual(list((path / "scratch").iterdir()), [])
        self.assertTrue(task.verify_task(path)["verified"])

    def test_new_config_rejects_path_escape_and_hardcoded_absolute_paths(self):
        path, _ = self.populate(self.create())
        original = json.loads((path / "outline.json").read_text(encoding="utf-8"))
        for key, value in (("output_dir", "../outside"), ("work_dir", "reports/wrong"), ("output_dir", ".tmp/research/wrong"), ("workspace", str(self.workspace))):
            raw = {**original, key: value}
            (path / "outline.json").write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
            with self.subTest(key=key, value=value):
                self.assertFalse(results.validate(path / "outline.json", path / "fields.json")["valid"])
        self.assertFalse((self.root / "outside").exists())

    def test_derived_task_provenance_is_relative_and_survives_relocation(self):
        path, _, _ = self.write_report(self.create())
        child = Path(task.derive_task(path)["work_dir"])
        raw = json.loads((child / "outline.json").read_text(encoding="utf-8"))
        self.assertEqual(raw["derived_from"]["work_dir"], path.relative_to(self.workspace).as_posix())
        self.assertFalse(Path(raw["derived_from"]["work_dir"]).is_absolute())
        copied = self.root / "derived-project-copy"
        shutil.copytree(self.workspace, copied)
        relocated = copied / child.relative_to(self.workspace)
        self.assertEqual(context.report_context(relocated / "outline.json")["completion"], "complete")

    def test_legacy_system_temporary_task_can_still_be_read_without_migration(self):
        path, outline = self.populate(self.create())
        legacy_root = self.root / "legacy-temp"
        legacy = legacy_root / "research" / task.workspace_key(self.workspace) / outline["run_id"]
        shutil.copytree(path, legacy)
        outline.pop("path_mode")
        outline["work_dir"] = str(legacy)
        task.write_json(legacy / "outline.json", outline)
        owner = json.loads((path / "owner.json").read_text(encoding="utf-8"))
        owner.update(schema_version=1, workspace=str(self.workspace), workspace_key=task.workspace_key(self.workspace))
        task.write_json(legacy / "owner.json", owner)
        with patch.object(task.tempfile, "gettempdir", return_value=str(legacy_root)):
            opened, _, data = task.open_task(legacy)
            self.assertEqual(opened, legacy)
            self.assertTrue(results.validate(legacy / "outline.json", legacy / "fields.json")["valid"])
        self.assertNotIn("path_mode", data)
        self.assertTrue(path.is_dir())


if __name__ == "__main__":
    unittest.main()
