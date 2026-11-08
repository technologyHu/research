"""Canonical themes, flat dated reports, stable identity and reference repair."""

from contextlib import redirect_stdout
from datetime import datetime
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_task_workflow as fixtures
from test_task_workflow import task
import research_catalog as catalog
import research_revision as revision


class CatalogAndRevision(unittest.TestCase):
    setUp = fixtures.TaskWorkflow.setUp
    create = fixtures.TaskWorkflow.create
    populate = fixtures.TaskWorkflow.populate
    write_report = fixtures.TaskWorkflow.write_report

    def test_parent_tree_and_alias_drive_both_entrypoint_names(self):
        catalog.register_theme(self.workspace, "lt-memory", "long-term", "长期记忆", "agent-memory", ["长期记忆"])
        research = task.create_task(self.workspace, "论文", "paper", theme="长期记忆", target="survey-memory")
        analysis = task.create_task(self.workspace, "分析", "analysis", theme="lt-memory")
        self.assertEqual(research["theme_id"], analysis["theme_id"])
        self.assertEqual(research["theme_slug"], "agent-memory-long-term")
        self.assertEqual(Path(research["output_dir"]).relative_to(self.workspace).as_posix(),
                         "research-reports/agent-memory-long-term/paper/survey-memory-20261108-120000")
        self.assertEqual(Path(analysis["output_dir"]).relative_to(self.workspace).as_posix(),
                         "analysis-reports/agent-memory-long-term-20261108-120000")

    def test_invalid_registry_updates_leave_the_file_unchanged(self):
        path = self.workspace / "themes.yaml"
        original = path.read_bytes()
        for key, slug, parent, aliases in (("duplicate-path", "agent-memory", None, []),
                                            ("alias-conflict", "other", None, ["agent-memory"]),
                                            ("missing-parent", "other", "not-registered", [])):
            with self.subTest(key=key), self.assertRaises(ValueError):
                catalog.register_theme(self.workspace, key, slug, key, parent, aliases)
            self.assertEqual(path.read_bytes(), original)
        data = json.loads(original)
        entry = next(v for v in data["themes"] if v["id"] == "agent")
        entry["parent"] = "agent-memory"
        with self.assertRaisesRegex(ValueError, "cycle"):
            catalog.validate_registry(data)

    def test_unknown_theme_and_undated_output_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown theme"):
            self.create(theme="unregistered")
        with self.assertRaisesRegex(ValueError, "timestamp|YYYYMMDD"):
            self.create(output="research-reports/general/paper/new")
        self.assertEqual({p.name for p in self.workspace.iterdir()}, {"themes.yaml"})

    def test_existing_flat_analysis_keeps_its_theme_identity(self):
        job = task.create_task(self.workspace, "分析", "analysis", theme="agent-memory")
        _, _, report = self.write_report(job)
        with self.assertRaisesRegex(ValueError, "retain.*theme"):
            task.create_task(self.workspace, "改主题", "analysis", theme="agent-orchestration", output=report.parent)

    def test_legacy_registered_alias_stays_in_its_original_directory(self):
        registry = self.workspace / "themes.yaml"
        data = json.loads(registry.read_text())
        next(entry for entry in data["themes"] if entry["id"] == "agent-memory")["aliases"] = ["old-memory"]
        registry.write_text(json.dumps(data), encoding="utf8")
        old = self.workspace / "research-reports/old-memory/paper/legacy"
        old.mkdir(parents=True)
        (old / "report.md").write_text("# 旧报告\n", encoding="utf8")
        job = self.create(output=old)
        self.assertEqual(Path(job["output_dir"]), old)
        self.assertEqual(job["classification"]["theme"], "agent-memory")
        self.assertNotIn("report_id", job)

    def test_scoped_revision_keeps_baseline_and_partial_status_after_rename(self):
        _, _, report = self.write_report(self.create(), partial=True)
        child = self.create(output=report.parent)
        task.begin_update(child["work_dir"], ["## 分析"])
        work, _ = self.populate(child, partial=True)
        baseline = (work / "baseline/report.md").read_bytes()
        task.apply_update(work, {"## 分析": "## 分析\n\n[新依据](https://example.org/original) 支持修订后的解释。"})
        changed = revision.stamp_report(work, "2026-11-09T05:14:15+00:00")
        new_work = Path(changed["work_dir"])
        self.assertEqual(changed["updated_at"], "2026-11-09T13:14:15+08:00")
        self.assertEqual((new_work / "baseline/report.md").read_bytes(), baseline)
        checked = task.verify_task(new_work)
        self.assertTrue(checked["verified"])
        self.assertEqual(checked["completion"], "partial")

    def test_stamp_cli_returns_the_new_portable_work_directory(self):
        work, _, report = self.write_report(self.create())
        output = io.StringIO()
        with patch.object(sys, "argv", ["research_task.py", "stamp-report", "--work-dir", str(work)]), \
             patch.object(catalog, "now", return_value=datetime.fromisoformat("2026-11-09T13:14:15+08:00")), \
             redirect_stdout(output):
            self.assertEqual(task.main(), 0, output.getvalue())
        changed = json.loads(output.getvalue())
        self.assertFalse(Path(changed["work_dir"]).is_absolute())
        new_work = self.workspace / changed["work_dir"]
        self.assertFalse(report.exists())
        self.assertTrue(task.verify_task(new_work)["verified"])

    def test_revision_moves_one_delivery_and_updates_encoded_links_and_task_bindings(self):
        work, outline, report = self.write_report(self.create())
        task.verify_task(work)
        identity, created = outline["report_id"], outline["created_at"]
        old_relative = Path(outline["output_dir"]).relative_to(self.workspace).as_posix()
        plan = self.workspace / "research-reports/general/plan.md"
        plan.write_text(f"# 计划\n\n[成果](paper/{report.parent.name}/report.md#分析)\n", encoding="utf8")
        other = self.workspace / "analysis-reports/consumer-20261108-120000"
        other.mkdir(parents=True)
        citing = other / "report.md"
        citing.write_text(f"# 引用\n\n[报告](../../{old_relative}/report.md#分析)\n\n`../../{old_relative}/report.md`\n", encoding="utf8")
        consumer = task.create_task(self.workspace, "采用", "analysis", theme="agent-memory")
        consumer_work, _, consumer_outline = task.open_task(consumer["work_dir"])
        source = {"id": "s1", "url": "repo:" + old_relative + "/report.md", "sha256": "old-evidence-hash"}
        task.write_json(consumer_work / "results/item-1.json", {"sources": [source]})
        result = revision.stamp_report(work, "2026-11-09T13:14:15+08:00")
        new_work, _, updated = task.open_task(result["work_dir"])
        self.assertFalse(report.parent.exists())
        self.assertEqual(updated["report_id"], identity)
        self.assertEqual(updated["created_at"], created)
        self.assertTrue(Path(updated["output_dir"]).name.endswith("20261109-131415"))
        self.assertIn("20261109-131415/report.md#分析", plan.read_text(encoding="utf8"))
        body = citing.read_text(encoding="utf8")
        self.assertIn("20261109-131415/report.md#分析", body)
        self.assertIn("`../../" + old_relative + "/report.md`", body)
        adopted = json.loads((consumer_work / "results/item-1.json").read_text())["sources"][0]
        self.assertIn("20261109-131415", adopted["url"])
        self.assertEqual(adopted["sha256"], "old-evidence-hash")
        self.assertTrue(task.verify_task(new_work)["verified"])

    def test_conflicting_destination_and_failed_writes_preserve_originals(self):
        work, outline, report = self.write_report(self.create())
        original = report.read_bytes()
        parent = self.workspace / "research-reports/general/paper"
        conflict = parent / "example-research-20261109-131415"
        conflict.mkdir()
        with self.assertRaisesRegex(ValueError, "already exists"):
            revision.stamp_report(work, "2026-11-09T13:14:15+08:00")
        self.assertEqual(report.read_bytes(), original)
        with patch.object(task, "report_context", side_effect=ValueError("injected context failure")):
            with self.assertRaisesRegex(ValueError, "injected"):
                revision.stamp_report(work, "2026-11-10T13:14:15+08:00")
        self.assertEqual(report.read_bytes(), original)
        self.assertEqual(task.open_task(work)[2]["updated_at"], outline["updated_at"])
        self.assertFalse((parent / "example-research-20261110-131415").exists())

    def test_revision_preserves_manual_quotes_next_to_generated_notes(self):
        work, _, report = self.write_report(self.create())
        remarks = "> 调研日期：2026-11-08（贡献者记录）\n>\n> 本轮限制：未访问私有资料。\n"
        report.write_text(report.read_text(encoding="utf8").replace("\n\n## 分析", "\n" + remarks + "\n## 分析"), encoding="utf8")
        self.assertTrue(task.verify_task(work)["verified"])
        changed = revision.stamp_report(work, "2026-11-09T13:14:15+08:00")
        content = (Path(changed["output_dir"]) / "report.md").read_text(encoding="utf8")
        self.assertIn(remarks, content)
        self.assertEqual(content.count("> 调研状态："), 1)
        self.assertTrue(task.verify_task(changed["work_dir"])["verified"])

    def test_interrupted_reference_write_restores_files_directory_and_task(self):
        work, outline, report = self.write_report(self.create())
        readme = self.workspace / "README.md"
        readme.write_text(f"[成果]({report.relative_to(self.workspace).as_posix()})\n", encoding="utf8")
        originals = {file.relative_to(self.workspace): file.read_bytes() for file in self.workspace.rglob("*") if file.is_file()}
        write = Path.write_bytes
        injected = False

        def interrupt(file, content):
            nonlocal injected
            if not injected and (file == readme or (file.parent == readme.parent and file.name.startswith(".research-revision-"))):
                injected = True
                write(file, b"PARTIAL")
                raise OSError("injected interrupted reference write")
            return write(file, content)

        with patch.object(Path, "write_bytes", interrupt), self.assertRaisesRegex(OSError, "interrupted"):
            revision.stamp_report(work, "2026-11-09T13:14:15+08:00")
        self.assertTrue(injected)
        current = {file.relative_to(self.workspace): file.read_bytes() for file in self.workspace.rglob("*") if file.is_file()}
        self.assertEqual(current, originals)
        self.assertEqual(task.open_task(work)[2]["updated_at"], outline["updated_at"])
        self.assertTrue(task.verify_task(work)["verified"])

    def test_late_replacement_failure_restores_already_installed_files(self):
        work, _, report = self.write_report(self.create())
        readme = self.workspace / "README.md"
        readme.write_text(f"[成果]({report.relative_to(self.workspace).as_posix()})\n", encoding="utf8")
        for failure in ("outline", "summary"):
            with self.subTest(failure=failure):
                originals = {file.relative_to(self.workspace): file.read_bytes() for file in self.workspace.rglob("*") if file.is_file()}
                atomic = revision.write_atomic
                injected, report_writes = False, 0

                def interrupt(target, content):
                    nonlocal injected, report_writes
                    atomic(target, content)
                    if target.name == "report.md":
                        report_writes += 1
                    chosen = target.name == "outline.json" if failure == "outline" else target.name == "report.md" and report_writes == 2
                    if chosen and not injected:
                        injected = True
                        raise OSError("injected failure after replacement")

                with patch.object(revision, "write_atomic", interrupt), self.assertRaisesRegex(OSError, "after replacement"):
                    revision.stamp_report(work, "2026-11-09T13:14:15+08:00")
                self.assertTrue(injected)
                current = {file.relative_to(self.workspace): file.read_bytes() for file in self.workspace.rglob("*") if file.is_file()}
                self.assertEqual(current, originals)
                self.assertTrue(task.verify_task(work)["verified"])

    def test_registry_cli_initializes_and_registers_without_creating_reports(self):
        root = self.root / "fresh"
        root.mkdir()
        entry = Path(task.__file__)
        for args in (("init-themes",), ("add-theme", "--id", "agent", "--slug", "agent", "--name", "Agent", "--alias", "智能体")):
            result = subprocess.run([sys.executable, "-X", "utf8", "-B", str(entry), *args, "--workspace", "."],
                                    cwd=root, capture_output=True, text=True, encoding="utf8")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(catalog.theme_entry(root, "智能体")["id"], "agent")
        self.assertEqual({p.name for p in root.iterdir()}, {"themes.yaml"})


if __name__ == "__main__":
    unittest.main()
