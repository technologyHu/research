"""Classified report destinations and reviewable, non-destructive cleanup previews."""

import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_task_workflow as fixtures
from test_task_workflow import task, results


class ClassificationAndCleanup(unittest.TestCase):
    setUp = fixtures.TaskWorkflow.setUp
    create = fixtures.TaskWorkflow.create
    populate = fixtures.TaskWorkflow.populate
    write_report = fixtures.TaskWorkflow.write_report

    def test_single_object_is_grouped_by_actual_type_theme_and_id(self):
        job = task.create_task(self.workspace, "示例项目架构", "topic", items=["library:open-source=示例库"], theme="Agent Memory")
        self.assertEqual(Path(job["output_dir"]).relative_to(self.workspace).as_posix(), "open-source/agent-memory/library")
        self.assertEqual(job["classification"], {"type": "open-source", "theme": "agent-memory", "target": "library"})
        self.assertFalse((Path(job["output_dir"]) / "report.md").exists())

    def test_same_type_and_mixed_type_comparisons_have_distinct_placement(self):
        same = self.create(items=["a=论文 A", "b=论文 B"], theme="agent-memory")
        mixed = self.create(items=["a:paper=论文", "b:open-source=代码库"], theme="agent-memory")
        self.assertEqual(same["classification"]["type"], "paper")
        self.assertEqual(mixed["classification"]["type"], "topic")
        for job in (same, mixed):
            self.assertTrue(job["classification"]["target"].startswith("compare-"))
            self.assertEqual(Path(job["output_dir"]).parent.name, "agent-memory")

    def test_existing_output_and_classification_survive_derivation(self):
        job = self.create(items=["example=示例论文"], theme="agent-memory", output="reports/legacy-location")
        path, outline, report = self.write_report(job)
        before = report.read_bytes()
        child = task.derive_task(path)
        self.assertEqual(child["output_dir"], outline["output_dir"])
        self.assertEqual(child["classification"], job["classification"])
        self.assertEqual(report.read_bytes(), before)

    def test_theme_cannot_be_used_as_a_path(self):
        for value in ("../outside", "/absolute", "..", "a\\b", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.create(theme=value)
        self.assertFalse(self.store.exists())

    def test_cleanup_preview_requires_confirmation_and_does_not_delete_or_modify(self):
        path, _, report = self.write_report(self.create())
        task.verify_task(path)
        before = {p.relative_to(path).as_posix(): p.read_bytes() for p in path.rglob("*") if p.is_file()}
        first = task.cleanup_plan(path)
        second = task.cleanup_plan(path)
        self.assertTrue(first["requires_confirmation"])
        self.assertEqual(first["plan_id"], second["plan_id"])
        self.assertEqual(first["files_to_remove"], len(before))
        self.assertEqual(first["bytes_to_remove"], sum(len(value) for value in before.values()))
        self.assertEqual(before, {p.relative_to(path).as_posix(): p.read_bytes() for p in path.rglob("*") if p.is_file()})
        self.assertTrue(report.is_file())

    def test_added_temporary_file_changes_the_confirmation_plan(self):
        path, _, _ = self.write_report(self.create())
        task.verify_task(path)
        original = task.cleanup_plan(path)
        scratch = path / "scratch"
        scratch.mkdir()
        (scratch / "extra.txt").write_bytes(b"new temporary evidence")
        changed = task.cleanup_plan(path)
        self.assertNotEqual(original["plan_id"], changed["plan_id"])
        self.assertEqual(changed["files_to_remove"], original["files_to_remove"] + 1)
        self.assertEqual(changed["bytes_to_remove"], original["bytes_to_remove"] + 22)
        other = self.create()
        self.assertEqual(changed["plan_id"], task.cleanup_plan(path)["plan_id"])
        self.assertTrue(Path(other["work_dir"]).is_dir())

    def test_cli_exposes_classification_and_relative_cleanup_scope(self):
        script = str(Path(task.__file__).resolve())
        command = [sys.executable, "-X", "utf8", "-B", script, "create", "--workspace", ".", "--topic", "对象调研", "--type", "paper", "--theme", "agent-memory", "--item", "paper-a=论文 A"]
        run = subprocess.run(command, cwd=self.workspace, text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        created = json.loads(run.stdout)
        self.assertEqual(created["output_dir"], "paper/agent-memory/paper-a")
        path, _, _ = self.write_report(task.describe_task(self.workspace / created["work_dir"]))
        task.verify_task(path)
        preview = subprocess.run(command[:5] + ["cleanup-plan", "--work-dir", created["work_dir"]], cwd=self.workspace, text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
        plan = json.loads(preview.stdout)
        self.assertTrue(plan["requires_confirmation"])
        self.assertEqual(plan["work_dir"], created["work_dir"])
        self.assertEqual(plan["preserve_output_dir"], created["output_dir"])


if __name__ == "__main__":
    unittest.main()
