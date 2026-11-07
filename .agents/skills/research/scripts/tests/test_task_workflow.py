"""Isolated end-to-end lifecycle tests; no network access and no workspace deletion."""

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import research_context as context
import research_task as task
import validate_report as reports
import validate_results as results

SOURCE = {"id": "s1", "title": "原始资料", "url": "https://example.org/original", "kind": "primary", "accessed_at": "2026-11-05", "locator": "核心章节"}


class TaskWorkflow(unittest.TestCase):
    def setUp(self):
        # Keep fixture roots short enough for nested article/image paths on Windows.
        self.temp = tempfile.TemporaryDirectory(prefix="rs-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "project"
        self.workspace.mkdir()
        self.store = self.workspace / "general/paper/example-research/.tmp"

    def create(self, **kwargs):
        if not kwargs.get("output") and not kwargs.get("target") and not kwargs.get("native_target_name"):
            if not kwargs.get("items") or len(kwargs["items"]) > 1:
                kwargs["target"] = "example-research"
        return task.create_task(self.workspace, "示例调研", "paper", **kwargs)

    def populate(self, job, partial=False):
        path, _, outline = task.open_task(job["work_dir"])
        outline["items"][0]["version"] = "v1"
        if outline["workflow"] == "light":
            (path / "notes.md").write_text("# 证据笔记\n主要结论及其边界来自[原文](https://example.org/original)。\n", encoding="utf-8")
            outline["assessment"] = {"input_fingerprint": context.light_fingerprint(outline), "status": "partial" if partial else "complete", "version": "v1", "core_gaps": ["未获得附录，无法判断完整适用边界"] if partial else [], "sources": [SOURCE]}
            task.write_json(path / "outline.json", outline)
        else:
            task.write_json(path / "outline.json", outline)
            fields = results.load_document(path / "fields.json")
            if partial:
                fields["fields"].append({"id": "limitations", "description": "核心适用边界是什么？", "core": True})
                task.write_json(path / "fields.json", fields)
            for item in outline["items"]:
                data = {"schema_version": 2, "item_id": item["id"], "type": item["type"], "version": item.get("version"), "sources": [SOURCE], "fields": {}}
                for field in fields["fields"]:
                    record = {"status": "confirmed", "value": "对核心问题有证据支持的回答。", "evidence": [{"source_id": "s1", "locator": "核心章节"}], "input_fingerprint": results.input_fingerprint(outline, item, field)}
                    if field["id"] == "limitations":
                        record.update(status="unknown", value=None, reason="附录未公开", evidence=[])
                    data["fields"][field["id"]] = record
                task.write_json(path / "results" / f"{item['id']}.json", data)
        return path, outline

    def write_report(self, job, partial=False):
        path, outline = self.populate(job, partial)
        output = Path(outline["output_dir"])
        output.mkdir(parents=True, exist_ok=True)
        expected = context.report_context(path / "outline.json")
        report = output / expected["delivery"]["report"]
        report.write_text("# 示例调研报告\n\n" + context.render_report_note(expected) + "\n## 分析\n\n根据[原始资料](https://example.org/original)，解释主要机制和适用条件。\n", encoding="utf-8")
        return path, outline, report

    def test_create_isolated_full_task(self):
        job = self.create(fields=["method=方法如何工作？"])
        self.assertEqual(job["workflow"], "full")
        self.assertTrue(Path(job["fields"]).is_file())
        self.assertTrue(Path(job["output_dir"]).is_dir())
        self.assertFalse((Path(job["output_dir"]) / "report.md").exists())
        self.assertEqual([entry.name for entry in self.workspace.iterdir()], ["general"])

    def test_auto_brief_uses_light_without_fields_or_results(self):
        job = self.create(depth="brief")
        self.assertEqual(job["workflow"], "light")
        path = Path(job["work_dir"])
        self.assertFalse((path / "fields.json").exists())
        self.assertFalse((path / "results").exists())

    def test_comparison_auto_uses_full_and_retains_types(self):
        job = self.create(depth="brief", items=["paper:paper=论文", "sdk:open-source=集成包"])
        _, _, outline = task.open_task(job["work_dir"])
        self.assertEqual(job["workflow"], "full")
        self.assertEqual(outline["mode"], "comparison")
        self.assertEqual(outline["items"][1]["type"], "open-source")

    def test_list_keeps_multiple_tasks_and_separates_workspaces(self):
        self.create()
        self.create()
        found = task.list_tasks(self.workspace)
        self.assertEqual(len(found["tasks"]), 2)
        other = self.root / "other-project"
        other.mkdir()
        self.assertEqual(task.list_tasks(other)["tasks"], [])

    def test_outside_directory_and_changed_ownership_are_rejected(self):
        with self.assertRaises(ValueError):
            task.open_task(self.workspace)
        job = self.create()
        path = Path(job["work_dir"])
        owner = json.loads((path / "owner.json").read_text(encoding="utf-8"))
        owner["workspace"] = str(self.root / "wrong-project")
        task.write_json(path / "owner.json", owner)
        with self.assertRaises(ValueError):
            task.open_task(path)

    def test_invalid_configuration_does_not_create_task(self):
        with self.assertRaises(ValueError):
            self.create(output=self.workspace)
        with self.assertRaises(ValueError):
            self.create(workflow="light", items=["a=一", "b=二"])
        with self.assertRaises(ValueError):
            self.create(extras=[{"path": "report.pdf", "reason": ""}])
        self.assertFalse(self.store.exists())

    def test_promote_preserves_notes_and_does_not_invent_results(self):
        job = self.create(depth="brief")
        path, _ = self.populate(job)
        old = (path / "notes.md").read_bytes()
        promoted = task.promote_task(path, ["method=核对方法实现"])
        self.assertEqual(promoted["workflow"], "full")
        self.assertEqual((path / "notes.md").read_bytes(), old)
        self.assertEqual(list((path / "results").iterdir()), [])

    def test_full_report_verification_and_non_destructive_cleanup_plan(self):
        job = self.create()
        path, outline, report = self.write_report(job)
        verified = task.verify_task(path)
        self.assertTrue(verified["verified"])
        self.assertEqual(verified["completion"], "complete")
        before = {str(p): p.read_bytes() for p in path.rglob("*") if p.is_file()}
        plan = task.cleanup_plan(path)
        self.assertTrue(plan["eligible"])
        self.assertEqual(before, {str(p): p.read_bytes() for p in path.rglob("*") if p.is_file()})
        self.assertTrue(report.is_file())

    def test_cleanup_plan_requires_verified_unchanged_delivery(self):
        job = self.create()
        path, _, report = self.write_report(job)
        with self.assertRaises(OSError):
            task.cleanup_plan(path)
        task.verify_task(path)
        report.write_text(report.read_text(encoding="utf-8") + "\n后续修改\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            task.cleanup_plan(path)

    def test_report_cannot_claim_complete_when_results_are_partial(self):
        path, outline, report = self.write_report(self.create(), partial=True)
        self.assertTrue(reports.validate(outline["output_dir"], outline_path=path / "outline.json")["valid"])
        report.write_text(report.read_text(encoding="utf-8").replace("> 调研状态：部分完成", "> 调研状态：完整"), encoding="utf-8")
        checked = reports.validate(outline["output_dir"], outline_path=path / "outline.json")
        self.assertFalse(checked["valid"])

    def test_version_and_gap_summary_cannot_be_silently_removed(self):
        path, outline, report = self.write_report(self.create(), partial=True)
        text = report.read_text(encoding="utf-8")
        report.write_text("\n".join(line for line in text.splitlines() if not line.startswith(("> 采用版本：", "> 核心缺口："))), encoding="utf-8")
        self.assertFalse(reports.validate(outline["output_dir"], outline_path=path / "outline.json")["valid"])

    def test_metadata_does_not_count_as_a_visible_source_citation(self):
        path, outline, report = self.write_report(self.create())
        report.write_text(report.read_text(encoding="utf-8").replace("[原始资料](https://example.org/original)", "原始资料"), encoding="utf-8")
        checked = reports.validate(outline["output_dir"], outline_path=path / "outline.json")
        self.assertFalse(checked["valid"])
        self.assertTrue(any("not cited" in error for error in checked["errors"]))

    def test_changed_evidence_invalidates_report_note(self):
        path, outline, _ = self.write_report(self.create())
        item = outline["items"][0]
        record_path = path / "results" / f"{item['id']}.json"
        data = json.loads(record_path.read_text(encoding="utf-8"))
        data["fields"]["overview"]["value"] = "复查后的不同结论"
        task.write_json(record_path, data)
        checked = reports.validate(outline["output_dir"], outline_path=path / "outline.json")
        self.assertFalse(checked["valid"])
        self.assertTrue(any("summary is stale" in message for message in checked["errors"]))

    def test_explicit_extra_files_and_custom_report_name(self):
        job = self.create(report="分析.md", extras=[{"path": "exports/report.pdf", "reason": "用户明确要求 PDF"}])
        path, outline, report = self.write_report(job)
        extra = Path(outline["output_dir"]) / "exports/report.pdf"
        extra.parent.mkdir()
        extra.write_bytes(b"%PDF-1.4\n")
        self.assertEqual(report.name, "分析.md")
        self.assertTrue(reports.validate(outline["output_dir"], outline_path=path / "outline.json")["valid"])
        self.assertFalse(reports.validate(outline["output_dir"])["valid"])
        extra.with_name("unrequested.py").write_text("extra", encoding="utf-8")
        self.assertFalse(reports.validate(outline["output_dir"], outline_path=path / "outline.json")["valid"])

    def test_explicit_extra_file_must_exist_and_cannot_escape(self):
        job = self.create(extras=[{"path": "report.html", "reason": "用户要求 HTML"}])
        path, outline, _ = self.write_report(job)
        self.assertFalse(reports.validate(outline["output_dir"], outline_path=path / "outline.json")["valid"])
        for value in ("../outside", ".git/config", "/absolute", "folder/*", "."):
            with self.subTest(value=value), self.assertRaises(ValueError):
                context.delivery_config({"delivery": {"extra_files": [{"path": value, "reason": "requested"}]}})

    def test_light_report_and_scope_changes(self):
        path, outline, _ = self.write_report(self.create(depth="brief"))
        checked = context.validate_light(path / "outline.json")
        self.assertEqual(checked["completion"], "complete")
        self.assertTrue(task.verify_task(path)["verified"])
        outline["goal"] = "改为另一个研究问题"
        task.write_json(path / "outline.json", outline)
        self.assertFalse(context.validate_light(path / "outline.json")["valid"])

    def test_light_gap_and_missing_sources_do_not_claim_completion(self):
        path, outline = self.populate(self.create(depth="brief"), partial=True)
        self.assertEqual(context.validate_light(path / "outline.json")["completion"], "partial")
        outline["assessment"]["sources"] = []
        task.write_json(path / "outline.json", outline)
        checked = context.validate_light(path / "outline.json")
        self.assertEqual(checked["completion"], "blocked")
        self.assertFalse(checked["report_ready"])

    def test_light_requested_version_must_match_assessment(self):
        path, outline = self.populate(self.create(depth="brief"))
        outline["assessment"]["version"] = "v2"
        task.write_json(path / "outline.json", outline)
        self.assertFalse(context.validate_light(path / "outline.json")["valid"])


if __name__ == "__main__":
    unittest.main()
