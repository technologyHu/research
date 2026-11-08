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
        job = task.create_task(self.workspace, "示例项目架构", "open-source", items=["library:open-source=示例库"], theme="Agent Memory")
        self.assertEqual(Path(job["output_dir"]).relative_to(self.workspace).as_posix(), "research-reports/agent-memory/open-source/library")
        self.assertEqual(job["classification"], {"type": "open-source", "theme": "agent-memory", "target": "library"})
        self.assertFalse((Path(job["output_dir"]) / "report.md").exists())

    def test_report_roots_separate_object_research_from_analysis(self):
        for kind in ("paper", "open-source", "product", "benchmark", "analysis"):
            with self.subTest(kind=kind):
                job = task.create_task(self.workspace, "研究", kind, theme="memory", target="example")
                expected_root = "analysis-reports" if kind == "analysis" else "research-reports"
                self.assertEqual(Path(job["output_dir"]).relative_to(self.workspace).parts,
                                 (expected_root, "memory", kind, "example"))
                self.assertEqual(task.open_task(job["work_dir"])[2]["directory_layout"], "report-root")

    def test_new_outputs_cannot_cross_roots_or_use_the_old_top_level(self):
        for kind, destination in (("paper", "analysis-reports/memory/paper/example"),
                                  ("analysis", "research-reports/memory/analysis/example"),
                                  ("paper", "memory/paper/example")):
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                task.create_task(self.workspace, "研究", kind, output=destination)

    def test_existing_theme_first_report_remains_readable_without_moving(self):
        legacy = self.workspace / "memory/paper/old"
        legacy.mkdir(parents=True)
        (legacy / "report.md").write_text("# 旧报告\n", encoding="utf8")
        job = task.create_task(self.workspace, "续查", "paper", output=legacy)
        self.assertEqual(Path(job["output_dir"]), legacy)
        self.assertEqual(job["classification"]["theme"], "memory")

    def test_existing_report_in_a_new_root_keeps_its_type_and_theme(self):
        destination = self.workspace / "analysis-reports/memory/analysis/example"
        destination.mkdir(parents=True)
        (destination / "report.md").write_text("# 洞察\n", encoding="utf8")
        with self.assertRaises(ValueError):
            task.create_task(self.workspace, "续查", "paper", output=destination)
        with self.assertRaises(ValueError):
            task.create_task(self.workspace, "续查", "analysis", theme="other", output=destination)

    def test_saved_new_layout_is_checked_again_when_configuration_changes(self):
        job = task.create_task(self.workspace, "研究", "paper", theme="memory", target="example")
        _, _, outline = task.open_task(job["work_dir"])
        for classification in ({"type": "analysis", "theme": "memory", "target": "example"},
                               {"type": [], "theme": "memory", "target": "example"}, None):
            with self.subTest(classification=classification):
                _, errors = task.checked_paths({**outline, "classification": classification})
                self.assertTrue(any("Report path" in error for error in errors))

    def test_same_type_comparison_is_placed_and_mixed_types_are_rejected(self):
        same = self.create(items=["a=论文 A", "b=论文 B"], theme="agent-memory")
        self.assertEqual(same["classification"]["type"], "paper")
        self.assertTrue(same["classification"]["target"].startswith("compare-"))
        self.assertEqual(Path(same["output_dir"]).parent.parent.name, "agent-memory")
        with self.assertRaisesRegex(ValueError, "separate tasks"):
            self.create(items=["a:paper=论文", "b:open-source=代码库"], theme="agent-memory")

    def test_existing_output_and_classification_survive_derivation(self):
        legacy = self.workspace / "reports/legacy-location"
        legacy.mkdir(parents=True)
        (legacy / "report.md").write_text("# Existing report\n", encoding="utf-8")
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
        self.assertEqual(created["output_dir"], "research-reports/agent-memory/paper/paper-a")
        path, _, _ = self.write_report(task.describe_task(self.workspace / created["work_dir"]))
        task.verify_task(path)
        preview = subprocess.run(command[:5] + ["cleanup-plan", "--work-dir", created["work_dir"]], cwd=self.workspace, text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
        plan = json.loads(preview.stdout)
        self.assertTrue(plan["requires_confirmation"])
        self.assertEqual(plan["work_dir"], created["work_dir"])
        self.assertEqual(plan["preserve_output_dir"], created["output_dir"])

    def test_chinese_research_title_requires_an_english_directory_target(self):
        with self.assertRaisesRegex(ValueError, "English slug"):
            task.create_task(self.workspace, "记忆机制调研", "paper", theme="agent-memory")
        self.assertEqual(list(self.workspace.iterdir()), [])
        job = task.create_task(self.workspace, "记忆机制调研", "paper", theme="agent-memory", target="memory-method")
        self.assertEqual(Path(job["output_dir"]).relative_to(self.workspace).as_posix(), "research-reports/agent-memory/paper/memory-method")
        _, _, outline = task.open_task(job["work_dir"])
        self.assertEqual(outline["topic"], "记忆机制调研")

    def test_chinese_official_product_name_is_an_explicit_exception(self):
        job = task.create_task(self.workspace, "中文产品能力调研", "product", theme="coding-agent",
                               items=["coze:product=扣子"], native_target_name="扣子")
        self.assertEqual(Path(job["output_dir"]).relative_to(self.workspace).as_posix(), "research-reports/coding-agent/product/扣子")
        _, _, outline = task.open_task(job["work_dir"])
        self.assertEqual(outline["items"][0]["id"], "coze")
        self.assertEqual(outline["directory_naming"]["native_target_name"], "扣子")
        with self.assertRaises(ValueError):
            task.create_task(self.workspace, "中文标题", "product", theme="coding-agent", target="普通研究标题")

    def test_new_custom_output_must_use_theme_type_target(self):
        for destination in ("paper/agent-memory/project", "reports/custom", "agent-memory/paper/普通研究标题", "agent-memory/product/project"):
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                task.create_task(self.workspace, "研究", "paper", output=destination)
        job = task.create_task(self.workspace, "研究", "paper", output="research-reports/agent-memory/paper/project")
        self.assertEqual(job["classification"], {"type": "paper", "theme": "agent-memory", "target": "project"})

    def test_english_comparison_name_is_independent_of_chinese_report_title(self):
        job = task.create_task(self.workspace, "多个记忆方法比较", "paper", theme="agent-memory",
                               items=["a=方法甲", "b=方法乙"], target="memory-methods")
        self.assertEqual(Path(job["output_dir"]).relative_to(self.workspace).as_posix(), "research-reports/agent-memory/paper/compare-memory-methods")

    def test_existing_chinese_named_report_can_be_reused_in_place(self):
        destination = self.workspace / "existing-theme/product/中文产品"
        destination.mkdir(parents=True)
        report = destination / "report.md"
        report.write_text("# 既有产品报告\n", encoding="utf-8")
        job = task.create_task(self.workspace, "补查产品", "product", output=destination)
        self.assertEqual(Path(job["output_dir"]), destination)
        self.assertEqual(report.read_text(encoding="utf-8"), "# 既有产品报告\n")


if __name__ == "__main__":
    unittest.main()
