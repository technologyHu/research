"""Colliding directory names cannot alias reports with distinct research scopes."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

import test_task_workflow as fixtures
from test_task_workflow import task
import research_revision


class DeliveryIdentity(unittest.TestCase):
    setUp = fixtures.TaskWorkflow.setUp
    write_report = fixtures.TaskWorkflow.write_report
    populate = fixtures.TaskWorkflow.populate

    def snapshot(self, workspace=None):
        return {p.relative_to(workspace or self.workspace).as_posix(): p.read_bytes()
                for p in (workspace or self.workspace).rglob("*") if p.is_file()}

    def analysis(self, theme="agent-memory", target="architecture__tradeoffs", **kwargs):
        return task.create_task(self.workspace, "机制与取舍", "analysis", theme=theme, target=target, **kwargs)

    def copy_delivered_report(self):
        job = self.analysis()
        _, _, report = self.write_report(job)
        cleaned = self.root / "cleaned"
        cleaned.mkdir()
        shutil.copyfile(self.workspace / "themes.yaml", cleaned / "themes.yaml")
        destination = cleaned / report.relative_to(self.workspace)
        destination.parent.mkdir(parents=True)
        shutil.copyfile(report, destination)
        shutil.copyfile(task.catalog.report_metadata_path(report), task.catalog.report_metadata_path(destination))
        self.assertFalse((destination.parent / ".tmp").exists())
        return job, cleaned, destination

    def test_cross_theme_collisions_are_rejected_in_both_creation_orders(self):
        for reverse in (False, True):
            suffix = "reverse" if reverse else "forward"
            requests = [("agent-memory", "architecture__" + suffix), ("agent-memory-architecture", suffix)]
            if reverse:
                requests.reverse()
            first = self.analysis(*requests[0])
            before = self.snapshot()
            with self.assertRaisesRegex(ValueError, "directory collision"):
                self.analysis(*requests[1])
            self.assertEqual(self.snapshot(), before)
            self.assertEqual(task.open_task(first["work_dir"])[2]["report_id"], first["report_id"])

    def test_legacy_analysis_name_collision_cannot_alias_other_theme(self):
        destination = "analysis-reports/agent-memory-architecture-tradeoffs-20261108-120000"
        first = self.analysis(target="architecture-tradeoffs", output=destination)
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "directory collision"):
            self.analysis("agent-memory-architecture", "tradeoffs", output=destination)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(len(task.list_tasks(self.workspace)["tasks"]), 1)
        self.assertEqual(task.open_task(first["work_dir"])[2]["report_id"], first["report_id"])

    def test_delivered_report_blocks_cross_theme_claim_after_temporary_records_are_gone(self):
        _, cleaned, report = self.copy_delivered_report()
        before = self.snapshot(cleaned)
        with self.assertRaisesRegex(ValueError, "directory collision"):
            task.create_task(cleaned, "机制与取舍", "analysis", theme="agent-memory-architecture", target="tradeoffs")
        self.assertEqual(self.snapshot(cleaned), before)
        self.assertFalse((report.parent / ".tmp").exists())

    def test_matching_report_keeps_its_id_after_temporary_records_are_gone(self):
        original, cleaned, report = self.copy_delivered_report()
        before = report.read_bytes()
        restored = task.create_task(cleaned, "机制与取舍", "analysis", theme="agent-memory", target="architecture__tradeoffs")
        self.assertEqual(restored["report_id"], original["report_id"])
        self.assertEqual(restored["created_at"], original["created_at"])
        self.assertEqual(report.read_bytes(), before)

    def test_matching_pending_tasks_share_identity_and_distinct_subjects_do_not(self):
        first = self.analysis()
        second = self.analysis()
        separate = self.analysis(target="architecture__different-scope")
        self.assertEqual(first["report_id"], second["report_id"])
        self.assertNotEqual(first["work_dir"], second["work_dir"])
        self.assertNotEqual(first["report_id"], separate["report_id"])
        self.assertFalse((self.workspace / ".tmp/.report-write.lock").exists())

    def test_matching_draft_can_resume_before_metadata_is_written(self):
        first = self.analysis()
        report = Path(first["output_dir"]) / "report.md"
        report.write_text("# 草稿\n\n> 调研状态：完整\n>\n> 采用版本：v1\n", encoding="utf-8")
        resumed = self.analysis()
        self.assertEqual(resumed["report_id"], first["report_id"])

    def test_every_sibling_identity_is_checked_instead_of_accepting_the_first_one(self):
        first, second = self.analysis(), self.analysis()
        file = Path(second["outline"])
        saved = json.loads(file.read_text(encoding="utf8"))
        saved["report_id"] = "report-" + "f" * 32
        file.write_text(json.dumps(saved), encoding="utf8")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "conflicting identities"):
            self.analysis()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(task.open_task(first["work_dir"])[2]["report_id"], first["report_id"])

    def test_different_objects_cannot_implicitly_reuse_a_report_subject(self):
        first = task.create_task(self.workspace, "产品专题", "product", theme="coding-agent",
                                 items=["codex:product=Codex"], target="context-engineering")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "different objects"):
            task.create_task(self.workspace, "产品专题", "product", theme="coding-agent",
                             items=["coze:product=Coze"], target="context-engineering")
        self.assertEqual(self.snapshot(), before)
        explicit = task.create_task(self.workspace, "更新对象范围", "product", theme="coding-agent",
                                    items=["coze:product=Coze"], output=first["output_dir"])
        self.assertEqual(explicit["report_id"], first["report_id"])

    def test_changing_main_filename_cannot_bypass_a_delivered_claim(self):
        _, cleaned, report = self.copy_delivered_report()
        before = self.snapshot(cleaned)
        with self.assertRaisesRegex(ValueError, "report filename"):
            task.create_task(cleaned, "机制与取舍", "analysis", theme="agent-memory",
                             target="architecture__tradeoffs", report="insights.md")
        self.assertEqual(self.snapshot(cleaned), before)
        self.assertFalse((report.parent / ".tmp").exists())

    def test_creation_lock_cannot_be_removed_by_a_competing_creator(self):
        output = task.catalog.report_directory(self.workspace, "analysis", "agent-memory",
                                               "architecture__tradeoffs", "2026-11-08T12:00:00+08:00")
        with task.delivery_lock(output, self.workspace):
            lock = self.workspace / ".tmp/.report-write.lock"
            original = lock.read_bytes()
            with self.assertRaisesRegex(ValueError, "being claimed"):
                self.analysis()
            self.assertEqual(lock.read_bytes(), original)
        job = self.analysis()
        self.assertTrue(Path(job["outline"]).is_file())
        self.assertFalse(lock.exists())

    def test_failed_identity_check_releases_its_lock_for_retry(self):
        with patch.object(task, "claimed_metadata", side_effect=ValueError("injected collision")):
            with self.assertRaisesRegex(ValueError, "injected collision"):
                self.analysis()
        job = self.analysis()
        self.assertTrue(Path(job["outline"]).is_file())
        self.assertFalse((self.workspace / ".tmp/.report-write.lock").exists())

    def test_incomplete_existing_task_blocks_new_claims_without_hiding_the_failure(self):
        first = self.analysis()
        incomplete = Path(first["output_dir"]) / ".tmp/incomplete"
        incomplete.mkdir()
        (incomplete / "owner.json").write_text("{}", encoding="utf8")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "Not an owned research task"):
            self.analysis()
        self.assertEqual(self.snapshot(), before)

    def test_stale_supplementary_summary_does_not_change_the_main_report_identity(self):
        first = self.analysis()
        work, _, report = self.write_report(first)
        details = report.with_name("details.md")
        details.write_bytes(report.read_bytes())
        shutil.copyfile(task.catalog.report_metadata_path(report), task.catalog.report_metadata_path(details))
        revised = research_revision.stamp_report(work, "2026-11-09T13:14:15+08:00")
        supplemental = Path(revised["output_dir"]) / "details.md"
        self.assertEqual(task.catalog.report_summary(supplemental)["updated_at"], first["updated_at"])
        restored = self.analysis(output=revised["output_dir"])
        self.assertEqual(restored["report_id"], first["report_id"])
        self.assertEqual(restored["updated_at"], revised["updated_at"])

    def test_revision_cannot_move_a_delivery_during_creation(self):
        job = self.analysis()
        work, _, report = self.write_report(job)
        before = self.snapshot()
        original = task.claimed_metadata

        def try_revision(*args, **kwargs):
            metadata = original(*args, **kwargs)
            with self.assertRaisesRegex(ValueError, "being claimed"):
                research_revision.stamp_report(work, "2026-11-09T13:14:15+08:00")
            self.assertTrue(report.is_file())
            return metadata

        with patch.object(task, "claimed_metadata", side_effect=try_revision):
            second = self.analysis()
        self.assertEqual(second["report_id"], job["report_id"])
        self.assertEqual({key: value for key, value in self.snapshot().items() if key in before}, before)
        self.assertFalse((self.workspace / ".tmp/.report-write.lock").exists())
        self.assertEqual({entry["output_dir"] for entry in task.list_tasks(self.workspace)["tasks"]}, {job["output_dir"]})

    def test_creation_cannot_claim_the_moved_directory_during_revision(self):
        job = self.analysis()
        work, _, _ = self.write_report(job)
        original = task.report_context

        def try_creation(path):
            context = original(path)
            _, _, current = task.open_task(Path(path).parent)
            with self.assertRaisesRegex(ValueError, "being claimed"):
                # A new main filename must not bypass the moved directory's lock.
                self.analysis(output=current["output_dir"], report="insights.md")
            return context

        with patch.object(task, "report_context", side_effect=try_creation):
            revised = research_revision.stamp_report(work, "2026-11-09T13:14:15+08:00")
        self.assertEqual(revised["report_id"], job["report_id"])
        self.assertFalse((self.workspace / ".tmp/.report-write.lock").exists())
        restored = self.analysis(output=revised["output_dir"])
        self.assertEqual(restored["report_id"], job["report_id"])

    def test_failed_revision_restores_the_directory_and_releases_its_lock(self):
        job = self.analysis()
        work, _, report = self.write_report(job)
        original = report.read_bytes()
        with patch.object(task, "report_context", side_effect=ValueError("injected revision failure")):
            with self.assertRaisesRegex(ValueError, "injected revision failure"):
                research_revision.stamp_report(work, "2026-11-09T13:14:15+08:00")
        self.assertEqual(report.read_bytes(), original)
        self.assertFalse((self.workspace / ".tmp/.report-write.lock").exists())
        restored = self.analysis()
        self.assertEqual(restored["report_id"], job["report_id"])

    def test_old_path_cannot_be_recreated_during_revision_rollback(self):
        job = self.analysis()
        work, _, report = self.write_report(job)
        original = report.read_bytes()
        destination = report.parent.with_name(report.parent.name.replace("20261108-120000", "20261109-131415"))

        def try_old_path(_path):
            with self.assertRaisesRegex(ValueError, "being claimed"):
                self.analysis(output=job["output_dir"])
            self.assertFalse(report.parent.exists())
            raise ValueError("injected rollback after competing creation")

        with patch.object(task, "report_context", side_effect=try_old_path):
            with self.assertRaisesRegex(ValueError, "injected rollback"):
                research_revision.stamp_report(work, "2026-11-09T13:14:15+08:00")
        self.assertEqual(report.read_bytes(), original)
        self.assertFalse(destination.exists())
        self.assertFalse((self.workspace / ".tmp/.report-write.lock").exists())
        self.assertEqual(task.list_tasks(self.workspace)["errors"], [])
        self.assertEqual(self.analysis(output=job["output_dir"])["report_id"], job["report_id"])

    def test_cli_rejects_cross_theme_collision_without_creating_a_task(self):
        first = self.analysis()
        before = self.snapshot()
        run = subprocess.run([sys.executable, "-X", "utf8", "-B", task.__file__, "create", "--workspace", ".",
                              "--topic", "冲突分析", "--type", "analysis", "--theme", "agent-memory-architecture",
                              "--target", "tradeoffs", "--output", str(Path(first["output_dir"]).relative_to(self.workspace))],
                             cwd=self.workspace, capture_output=True, text=True, encoding="utf8")
        self.assertNotEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("directory collision", run.stdout + run.stderr)
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
