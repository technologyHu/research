"""Exercise bounded updates and disagreement handling against real temporary reports."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_task_workflow as fixtures
from test_task_workflow import context, task, results, reports, SOURCE
import research_update as updates


class UpdateAndConflictChecks(unittest.TestCase):
    setUp = fixtures.TaskWorkflow.setUp
    create = fixtures.TaskWorkflow.create
    populate = fixtures.TaskWorkflow.populate
    write_report = fixtures.TaskWorkflow.write_report

    def prepare_update(self, light=False, **options):
        _, original, report = self.write_report(self.create(), partial=True)
        report.write_text(report.read_text(encoding="utf-8").replace("\n## 分析", "\n> 调研日期：2025-01-02\n\n## 分析", 1) + "\n## 保留分析\n\n原章节使用 v1，资料日期 2025-01-02。\n", encoding="utf-8")
        job = self.create(depth="brief" if light else "standard", output=Path(original["output_dir"]))
        task.begin_update(job["work_dir"], sections=["## 分析"], **options)
        path, outline = self.populate(job)
        return path, outline, report

    def test_update_preserves_old_prose_versions_gaps_and_limits_completion(self):
        path, outline, report = self.prepare_update()
        outline["items"][0]["version"] = "v2"
        task.write_json(path / "outline.json", outline)
        data = results.load_document(path / "results/item-1.json")
        data["version"] = "v2"
        for field in results.load_document(path / "fields.json")["fields"]:
            data["fields"][field["id"]]["input_fingerprint"] = results.input_fingerprint(outline, outline["items"][0], field)
        task.write_json(path / "results/item-1.json", data)
        task.apply_update(path, {"## 分析": "## 分析\n\n本次复核后的结论：[依据](https://example.org/original)。"})
        checked = task.verify_task(path)
        text = report.read_text(encoding="utf-8")
        self.assertTrue(checked["verified"])
        self.assertIn("> 调研状态：局部复查完成", text)
        self.assertNotIn("> 调研状态：完整", text)
        self.assertNotIn("> 本次更新：", text)
        self.assertIn("原章节使用 v1，资料日期 2025-01-02。", text)
        self.assertNotIn("未复核部分原缺口", text)
        self.assertNotIn("<!-- research-summary", text)
        self.assertIn("> 采用版本：示例调研（v2）", text)
        summary = task.catalog.report_summary(report)
        self.assertIn("核心适用边界是什么？：附录未公开", summary["update"]["baseline_gaps"])
        self.assertEqual(summary["update"]["baseline_version"], "示例调研（v1）")
        self.assertEqual(summary["update"]["baseline_date"], "2025-01-02")
        self.assertIn("> 调研日期：2025-01-02", text)
        self.assertEqual(updates.check_update(outline), [])
        self.assertTrue(task.cleanup_plan(path)["eligible"])

    def test_sync_note_is_idempotent_and_preserves_update_boundaries(self):
        path, outline, report = self.prepare_update()
        task.apply_update(path, {"## 分析": "## 分析\n\n[本次依据](https://example.org/original)\n\n> 调研状态：章节内引用的旧状态\n"})
        before = report.read_text(encoding="utf-8")
        report.write_text(before.replace("> 调研状态：局部复查完成", "> 调研状态：过期摘要", 1), encoding="utf-8")
        command = [sys.executable, "-X", "utf8", "-B", str(Path(task.__file__).resolve()), "sync-report-note", "--work-dir", str(path)]
        completed = subprocess.run(command, cwd=self.workspace, text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        result = json.loads(completed.stdout)
        after = report.read_text(encoding="utf-8")
        self.assertTrue(result["updated"])
        self.assertEqual(after, before)
        self.assertIn("> 调研状态：章节内引用的旧状态", after)
        self.assertFalse(task.sync_report_note(path)["updated"])
        report.write_text(after.replace("原章节使用 v1", "范围外改动"), encoding="utf-8")
        modified = report.read_bytes()
        with self.assertRaises(ValueError):
            task.sync_report_note(path)
        self.assertEqual(report.read_bytes(), modified)

    def test_light_update_rechecks_only_the_requested_scope(self):
        path, _, report = self.prepare_update(light=True)
        task.apply_update(path, {"## 分析": "## 分析\n\n简短复查：[依据](https://example.org/original)。"})
        self.assertTrue(task.verify_task(path)["verified"])
        self.assertIn("> 调研状态：局部复查完成", report.read_text(encoding="utf-8"))

    def test_sync_note_preserves_preamble_quotes_and_report_encoding(self):
        path, _, report = self.write_report(self.create())
        intro = "示例引用\n\n> 调研状态：外部原文\n\n```text\n> 核心缺口：代码示例\n```\n\n"
        expected = report.read_text(encoding="utf-8").replace("## 分析", intro + "## 分析", 1)
        stale = expected.replace("> 调研状态：完整", "> 调研状态：过期摘要", 1)
        report.write_bytes(stale.replace("\n", "\r\n").encode("utf-8-sig"))
        self.assertTrue(task.sync_report_note(path)["updated"])
        self.assertEqual(report.read_bytes(), expected.replace("\n", "\r\n").encode("utf-8-sig"))
        self.assertFalse(task.sync_report_note(path)["updated"])

    def test_sync_migrates_legacy_opening_to_one_visible_note(self):
        path, outline = self.populate(self.create(), partial=True)
        report = Path(outline["output_dir"]) / "report.md"
        summary = context.report_context(path / "outline.json")
        body = "\n## 分析\n\n[依据](https://example.org/original)。\n"
        legacy = "<!-- research-summary\n" + json.dumps(summary) + "\n-->\n"
        report.write_text("# 报告\n\n" + legacy + "\n".join(context.legacy_visible_note(summary)) + "\n" + body, encoding="utf-8")
        self.assertTrue(task.verify_task(path)["verified"])
        self.assertTrue(task.sync_report_note(path)["updated"])
        text = report.read_text(encoding="utf-8")
        self.assertNotIn("<!-- research-summary", text)
        self.assertEqual(text.count("> 调研状态："), 1)
        self.assertTrue(text.endswith(body))
        self.assertEqual(task.catalog.report_summary(report), {**summary, "opening_version": context.OPENING_VERSION})
        self.assertTrue(task.verify_task(path)["verified"])

    def test_previous_compact_opening_verifies_and_can_upgrade(self):
        path, outline = self.populate(self.create(researcher="调研员甲"), partial=True)
        report = Path(outline["output_dir"]) / "report.md"
        summary = context.report_context(path / "outline.json")
        task.catalog.report_metadata_path(report).write_text(json.dumps(summary), encoding="utf-8")
        report.write_text("# 报告\n\n" + context.render_report_note(summary, 1)
                          + "\n## 分析\n\n[依据](https://example.org/original)。\n", encoding="utf-8")
        self.assertTrue(task.verify_task(path)["verified"])
        self.assertTrue(task.sync_report_note(path)["updated"])
        text = report.read_text(encoding="utf-8")
        self.assertIn("> 调研人：调研员甲", text)
        self.assertIn("> 调研时间：2026-11-08 12:00:00（北京时间）", text)
        self.assertIn("> 主要待确认事项：核心适用边界是什么", text)
        self.assertTrue(task.verify_task(path)["verified"])

    def test_new_section_can_be_added_without_rewriting_old_sections(self):
        path, _, report = self.prepare_update(added=["## 新版本影响"])
        task.apply_update(path, {"## 新版本影响": "## 新版本影响\n\n[来源](https://example.org/original)解释变化。"})
        self.assertTrue(task.verify_task(path)["verified"])
        self.assertIn("原章节使用 v1", report.read_text(encoding="utf-8"))

    def test_v2_local_review_can_verify_and_upgrade(self):
        path, _, report = self.prepare_update()
        task.apply_update(path, {"## 分析": "## 分析\n\n[复查依据](https://example.org/original)。"})
        current = report.read_text(encoding="utf-8")
        summary = context.report_context(path / "outline.json")
        old_note = context.render_report_note(summary, 2)
        self.assertIn("> 调研状态：完整", old_note)
        report.write_text(updates.with_report_note(current, old_note), encoding="utf-8")
        task.catalog.report_metadata_path(report).write_text(json.dumps({**summary, "opening_version": 2}), encoding="utf-8")
        self.assertTrue(task.verify_task(path)["verified"])
        self.assertTrue(task.sync_report_note(path)["updated"])
        self.assertEqual(report.read_text(encoding="utf-8"), current)
        self.assertTrue(task.verify_task(path)["verified"])

    def test_intro_only_update_protects_title_and_body(self):
        _, _, report = self.write_report(self.create())
        original = report.read_text(encoding="utf-8").replace("## 分析", "资料在 11 月 8 日查阅。\n\n## 分析", 1)
        report.write_text(original, encoding="utf-8")
        job = self.create(output=report.parent)
        task.begin_update(job["work_dir"], sections=[updates.INTRO])
        path, outline = self.populate(job)
        task.apply_update(path, {updates.INTRO: "资料分别在 11 月 8 日和 9 日查阅。"})
        text = report.read_text(encoding="utf-8")
        self.assertTrue(task.verify_task(path)["verified"])
        self.assertEqual(updates.split_preamble(text)[1], updates.split_preamble(original)[1])
        self.assertIn("资料分别在 11 月 8 日和 9 日查阅。", text)
        self.assertIn("> 调研状态：局部复查完成", text)
        self.assertNotIn(updates.INTRO, text)
        self.assertTrue(updates.check_update(outline, text.replace("# 示例调研报告", "# 改过的标题")))
        self.assertTrue(updates.check_update(outline, text.replace("解释主要机制", "改写机制")))

    def test_outside_scope_edit_and_replacement_are_rejected_without_overwrite(self):
        path, _, report = self.prepare_update()
        before = report.read_bytes()
        with self.assertRaises(ValueError):
            task.apply_update(path, {"## 保留分析": "## 保留分析\n\n擅自重写"})
        self.assertEqual(report.read_bytes(), before)
        report.write_bytes(before.replace("原章节".encode(), "其他章节".encode()))
        with self.assertRaises(ValueError):
            task.apply_update(path, {"## 分析": "## 分析\n\n复查"})
        self.assertFalse(reports.validate(report.parent, path / "outline.json")["valid"])

    def test_baseline_and_existing_related_files_are_protected(self):
        path, outline, report = self.prepare_update()
        baseline = path / "baseline/report.md"
        baseline.write_bytes(baseline.read_bytes() + b"changed")
        with self.assertRaises(ValueError):
            updates.check_update(outline)
        self.assertFalse(reports.validate(report.parent, path / "outline.json")["valid"])

    def test_associated_file_requires_exact_allowance(self):
        _, old, report = self.write_report(self.create())
        reference = report.parent / "references/source.md"
        reference.parent.mkdir()
        reference.write_text("# 参考资料\n", encoding="utf-8")
        report.write_text(report.read_text(encoding="utf-8") + "\n[资料](references/source.md)\n", encoding="utf-8")
        job = self.create(output=report.parent)
        task.begin_update(job["work_dir"], ["## 分析"])
        path, outline = self.populate(job)
        reference.write_text("# 已变更的资料\n", encoding="utf-8")
        self.assertTrue(any("outside update scope" in error for error in updates.check_update(outline)))
        allowed = self.create(output=report.parent)
        task.begin_update(allowed["work_dir"], ["## 分析"], allow_files=["references/source.md"])
        path2, outline2 = self.populate(allowed)
        reference.write_text("# 获准更新的资料\n", encoding="utf-8")
        task.apply_update(path2, {"## 分析": "## 分析\n\n[原文](https://example.org/original)与[资料](references/source.md)"})
        self.assertTrue(task.verify_task(path2)["verified"])

    def test_heading_selection_rejects_ambiguity_and_parent_child_overlap(self):
        content = "# 报告\n\n## 方法\n\n### 细节\n内容\n\n## 方法\n重复标题\n"
        for names in (["## 方法"], ["# 报告"], ["## 不存在"]):
            with self.subTest(names=names), self.assertRaises(ValueError):
                updates.selected_spans(content, names)
        with self.assertRaises(ValueError):
            updates.selected_spans(content.replace("## 方法\n重复标题", "## 其他\n结尾"), ["## 方法", "### 细节"])
        fenced = "# 报告\n\n## 方法\n\n```md\n## 方法\n```\n\n## 其他\n"
        self.assertEqual(len(updates.selected_spans(fenced, ["## 方法"])), 1)

    def test_second_update_retains_earlier_unreviewed_limits(self):
        path, _, report = self.prepare_update()
        task.apply_update(path, {"## 分析": "## 分析\n\n[首次复查](https://example.org/original)"})
        report.write_text(report.read_text(encoding="utf-8").replace("> 调研日期：2025-01-02\n", ""), encoding="utf-8")
        second = self.create(output=report.parent)
        task.begin_update(second["work_dir"], ["## 分析"])
        path2, _ = self.populate(second)
        task.apply_update(path2, {"## 分析": "## 分析\n\n[再次复查](https://example.org/original)"})
        self.assertTrue(task.verify_task(path2)["verified"])
        text = report.read_text(encoding="utf-8")
        self.assertNotIn("更早记录", text)
        update = task.catalog.report_summary(report)["update"]
        self.assertIn("更早记录：核心适用边界是什么？：附录未公开", update["baseline_gaps"])
        self.assertEqual(update["baseline_date"], "2025-01-02")

    def test_research_scope_changes_make_old_fingerprints_stale(self):
        path, outline, _ = self.prepare_update(light=True)
        outline["goal"] = "改为核实其他研究问题"
        task.write_json(path / "outline.json", outline)
        self.assertFalse(context.validate_light(path / "outline.json")["valid"])

    def conflict(self, resolution="version_difference"):
        return {"id": "version-conflict", "issue": "是否支持功能 A", "positions": [
            {"source_id": "s1", "claim": "v1 尚未支持 A", "version": "v1", "conditions": "默认模式", "locator": "v1 功能说明"},
            {"source_id": "s2", "claim": "v2 已支持 A", "version": "v2", "conditions": "默认模式", "locator": "v2 发布说明"}],
            "resolution": resolution, "selected_source_ids": ["s2"] if resolution == "prefer_source" else [],
            "rationale": "两份来源覆盖不同版本；报告分别说明，不能用 v2 结论覆盖 v1。" if resolution != "unresolved" else "未找到能解释同条件差异的原始资料，继续核实。"}

    def conflict_task(self, resolution="version_difference"):
        path, outline = self.populate(self.create(fields=["overview=主要结论", "capability=功能 A 是否支持？"]))
        record_path = path / "results/item-1.json"
        data = results.load_document(record_path)
        data["sources"].append({**SOURCE, "id": "s2", "url": "https://example.org/release-v2", "title": "新版本说明"})
        field = data["fields"]["capability"]
        field["conflicts"] = [self.conflict(resolution)]
        if resolution == "unresolved":
            field.update(status="unknown", value=None, evidence=[], reason="冲突尚未解决")
        elif resolution == "prefer_source":
            field["evidence"] = [{"source_id": "s2", "locator": "v2 发布说明"}]
        task.write_json(record_path, data)
        return path, outline, record_path, data

    def emit_conflict_report(self, path, outline, opposing=True):
        report = Path(outline["output_dir"]) / "report.md"
        report.parent.mkdir(parents=True, exist_ok=True)
        note = context.render_report_note(context.report_context(path / "outline.json"))
        body = "# 冲突证据报告\n\n" + note + "\n## 条件与版本\n\n[旧资料](https://example.org/original)。\n"
        if opposing:
            body += "[新资料](https://example.org/release-v2)。两者版本有差异，分别列出适用边界。\n"
        report.write_text(body, encoding="utf-8")
        task.sync_report_note(path)
        return report

    def test_version_difference_keeps_both_sources_and_visible_resolution(self):
        path, outline, _, _ = self.conflict_task()
        report = self.emit_conflict_report(path, outline)
        self.assertTrue(task.verify_task(path)["verified"])
        self.assertIn("两者版本有差异", report.read_text(encoding="utf-8"))
        self.assertNotIn("> 证据冲突：", report.read_text(encoding="utf-8"))

    def test_unresolved_core_conflict_is_partial_and_cannot_be_declared_settled(self):
        path, outline, record_path, data = self.conflict_task("unresolved")
        checked = results.validate(path / "outline.json", path / "fields.json")
        self.assertTrue(checked["valid"])
        self.assertEqual(checked["completion"], "partial")
        self.emit_conflict_report(path, outline)
        self.assertEqual(task.verify_task(path)["completion"], "partial")
        data["fields"]["capability"].update(status="confirmed", value="已确定支持 A", evidence=[{"source_id": "s1", "locator": "正文"}])
        task.write_json(record_path, data)
        self.assertFalse(results.validate(path / "outline.json", path / "fields.json")["valid"])

    def test_opposing_source_cannot_be_hidden_in_metadata(self):
        path, outline, record_path, data = self.conflict_task("prefer_source")
        data["sources"].append({**SOURCE, "id": "s3", "url": "https://example.org/opposing-only"})
        data["fields"]["capability"]["conflicts"][0]["positions"][0]["source_id"] = "s3"
        task.write_json(record_path, data)
        report = self.emit_conflict_report(path, outline)
        check = reports.validate(report.parent, path / "outline.json")
        self.assertFalse(check["valid"])
        self.assertTrue(any("not cited" in error and "opposing-only" in error for error in check["errors"]))

    def test_malformed_conflicts_fail_with_actionable_errors(self):
        path, _, record_path, original = self.conflict_task()
        mutations = [
            lambda c: c.pop("rationale"),
            lambda c: c["positions"][0].pop("locator"),
            lambda c: c["positions"][0].pop("conditions"),
            lambda c: c["positions"][0].pop("version"),
            lambda c: c["positions"][0].update(source_id="missing"),
            lambda c: c.update(resolution="prefer_source", selected_source_ids=["s2"]),
            lambda c: c.update(resolution="prefer_source", selected_source_ids=["unknown"]),
        ]
        for mutate in mutations:
            data = copy.deepcopy(original)
            mutate(data["fields"]["capability"]["conflicts"][0])
            task.write_json(record_path, data)
            with self.subTest(mutate=mutate):
                self.assertFalse(results.validate(path / "outline.json", path / "fields.json")["valid"])

    def test_light_conflict_requests_full_workflow_instead_of_ignoring_it(self):
        path, outline = self.populate(self.create(depth="brief"))
        outline["assessment"]["conflicts"] = [self.conflict()]
        task.write_json(path / "outline.json", outline)
        checked = context.validate_light(path / "outline.json")
        self.assertFalse(checked["valid"])
        self.assertTrue(any("promotion" in error for error in checked["errors"]))

    def test_cli_exposes_bounded_update_commands(self):
        command = subprocess.run([sys.executable, "-X", "utf8", "-B", str(task.__file__), "begin-update", "--help"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(command.returncode, 0, command.stderr)
        self.assertIn("--section", command.stdout)


if __name__ == "__main__":
    unittest.main()
