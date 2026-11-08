"""Keep tasks beside their report while excluding them from delivery and snapshots."""

import json
from pathlib import Path
import unittest

import test_task_workflow as fixtures
from test_task_workflow import task, reports, results
from research_paths import delivery_entries


class ReportLocalTasks(unittest.TestCase):
    setUp = fixtures.TaskWorkflow.setUp
    create = fixtures.TaskWorkflow.create
    populate = fixtures.TaskWorkflow.populate
    write_report = fixtures.TaskWorkflow.write_report

    def test_default_tree_has_no_reports_layer_and_owns_its_local_tmp(self):
        job = self.create(items=["paper-a=论文 A"], theme="agent-memory")
        output, work = Path(job["output_dir"]), Path(job["work_dir"])
        self.assertEqual(output.relative_to(self.workspace).as_posix(), "research-reports/agent-memory/paper/paper-a")
        self.assertEqual(work.parent, output / ".tmp")
        self.assertFalse((self.workspace / ".tmp").exists())
        self.assertFalse((self.workspace / "reports").exists())
        owner = json.loads((work / "owner.json").read_text(encoding="utf-8"))
        self.assertEqual(owner["output_dir"], "research-reports/agent-memory/paper/paper-a")

    def test_listing_discovers_separate_reports_and_multiple_runs_without_scanning_code(self):
        first = self.create(items=["a=论文 A"], theme="memory")
        second = self.create(items=["b:product=产品 B"], theme="coding")
        third = self.create(items=["a=论文 A"], theme="memory")
        nested = Path(first["work_dir"]) / "code/fake/.tmp/fake-task"
        nested.mkdir(parents=True)
        (nested / "owner.json").write_text("not an owned task", encoding="utf-8")
        listed = task.list_tasks(self.workspace)
        self.assertEqual({entry["run_id"] for entry in listed["tasks"]}, {first["run_id"], second["run_id"], third["run_id"]})
        self.assertEqual(listed["errors"], [])

    def test_delivery_verification_ignores_local_tmp_and_does_not_seal_it(self):
        path, outline, report = self.write_report(self.create())
        (path / "code").mkdir()
        (path / "code/unrelated.py").write_text("temporary only", encoding="utf-8")
        self.assertTrue(reports.validate(report.parent)["valid"])
        verified = task.verify_task(path)
        self.assertEqual(set(verified["files"]), {"report.md"})
        delivered = {entry.relative_to(report.parent).as_posix() for entry in delivery_entries(report.parent) if entry.is_file()}
        self.assertEqual(delivered, {"report.md"})
        self.assertTrue(task.cleanup_plan(path)["requires_confirmation"])

    def test_baseline_does_not_recursively_capture_current_or_sibling_tasks(self):
        parent, _, report = self.write_report(self.create())
        child = Path(task.derive_task(parent)["work_dir"])
        task.begin_update(child, ["## 分析"])
        manifest = json.loads((child / "baseline/files.json").read_text(encoding="utf-8"))
        self.assertEqual(set(manifest), {"report.md"})
        task.apply_update(child, {"## 分析": "## 分析\n\n[原始资料](https://example.org/original)支持新分析。"})
        self.assertTrue(task.verify_task(child)["verified"])
        self.assertTrue(parent.is_dir())
        self.assertTrue(report.is_file())

    def test_report_cannot_depend_on_files_that_will_be_cleaned(self):
        path, _, report = self.write_report(self.create())
        notes = path / "private.md"
        notes.write_text("# Temporary notes\n", encoding="utf-8")
        relative = notes.relative_to(report.parent).as_posix()
        report.write_text(report.read_text(encoding="utf-8") + f"\n[临时笔记]({relative})\n", encoding="utf-8")
        checked = reports.validate(report.parent, path / "outline.json")
        self.assertFalse(checked["valid"])
        self.assertTrue(any("temporary files" in error for error in checked["errors"]))

    def test_relative_central_tasks_remain_readable_in_their_existing_directory(self):
        # Build a small old-layout task without moving or rewriting current tasks.
        import shutil
        path, outline = self.populate(self.create())
        central = self.workspace / ".tmp/research" / outline["run_id"]
        shutil.copytree(path, central)
        outline.pop("task_layout")
        outline["work_dir"] = str(central)
        task.write_json(central / "outline.json", outline)
        owner = json.loads((path / "owner.json").read_text(encoding="utf-8"))
        owner.update(schema_version=2, workspace="../../..")
        task.write_json(central / "owner.json", owner)
        opened, _, _ = task.open_task(central)
        self.assertEqual(opened, central)
        self.assertTrue(results.validate(central / "outline.json", central / "fields.json")["valid"])
        self.assertEqual(len(task.list_tasks(self.workspace)["tasks"]), 2)


if __name__ == "__main__":
    unittest.main()
