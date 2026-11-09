"""Evidence reuse, real configuration paths and complete disclosure of unknowns."""

import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import test_task_workflow as fixtures
from test_task_workflow import context, task, results, reports, SOURCE
import research_update as updates


class IncrementalDeliveryChecks(unittest.TestCase):
    setUp = fixtures.TaskWorkflow.setUp
    create = fixtures.TaskWorkflow.create
    populate = fixtures.TaskWorkflow.populate
    write_report = fixtures.TaskWorkflow.write_report

    def write_current_report(self, path, outline):
        report = Path(outline["output_dir"]) / "report.md"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text("# 对比报告\n\n" + context.render_report_note(context.report_context(path / "outline.json")) +
                          "\n> 调研日期：2025-01-02\n\n## 比较\n\nA、B 的原有比较。[依据](https://example.org/original)\n\n## 原有分析\n\n仅适用于旧版本，资料日期 2025-01-02。\n", encoding="utf-8")
        task.sync_report_note(path)
        return report

    def add_non_core_unknown(self, path):
        fields = results.load_document(path / "fields.json")
        field = {"id": "extra", "description": "附加部署指标是什么？", "display_question": "部署后如何衡量效果", "core": False}
        fields["fields"].append(field)
        task.write_json(path / "fields.json", fields)
        outline = results.load_document(path / "outline.json")
        for item in outline["items"]:
            record_path = path / "results" / f"{item['id']}.json"
            data = results.load_document(record_path)
            data["fields"]["extra"] = {"status": "unknown", "value": None, "reason": "缺少部署测量数据", "evidence": [], "input_fingerprint": results.input_fingerprint(outline, item, field)}
            task.write_json(record_path, data)
        return outline

    def test_non_core_unknown_is_visible_without_lowering_completion(self):
        path, _ = self.populate(self.create())
        outline = self.add_non_core_unknown(path)
        expected = context.report_context(path / "outline.json")
        self.assertEqual(expected["completion"], "complete")
        self.assertEqual(expected["core_gaps"], [])
        self.assertEqual(expected["non_core_gaps"][0]["reason"], "缺少部署测量数据")
        report = self.write_current_report(path, outline)
        self.assertTrue(task.verify_task(path)["verified"])
        self.assertIn("> 其他待确认事项：部署后如何衡量效果", report.read_text(encoding="utf-8"))
        report.write_text("\n".join(line for line in report.read_text(encoding="utf-8").splitlines() if not line.startswith("> 其他待确认事项：")), encoding="utf-8")
        self.assertFalse(reports.validate(report.parent, path / "outline.json")["valid"])

    def test_core_and_non_core_unknowns_remain_distinct(self):
        path, _ = self.populate(self.create(), partial=True)
        outline = self.add_non_core_unknown(path)
        expected = context.report_context(path / "outline.json")
        self.assertEqual(expected["completion"], "partial")
        self.assertEqual(len(expected["core_gaps"]), 1)
        self.assertEqual(len(expected["non_core_gaps"]), 1)
        self.write_current_report(path, outline)
        self.assertEqual(task.verify_task(path)["completion"], "partial")

    def test_light_non_core_gaps_must_be_visible_but_allow_completion(self):
        path, outline = self.populate(self.create(depth="brief"))
        outline["assessment"]["non_core_gaps"] = ["没有边缘环境测试数据"]
        task.write_json(path / "outline.json", outline)
        expected = context.report_context(path / "outline.json")
        self.assertEqual(expected["completion"], "complete")
        report = self.write_current_report(path, outline)
        self.assertTrue(task.verify_task(path)["verified"])
        report.write_text(report.read_text(encoding="utf-8").replace("其他待确认事项：没有边缘环境测试数据", "其他待确认事项：无"), encoding="utf-8")
        self.assertFalse(reports.validate(report.parent, path / "outline.json")["valid"])
        outline["assessment"]["non_core_gaps"] = "not a list"
        task.write_json(path / "outline.json", outline)
        self.assertFalse(context.validate_light(path / "outline.json")["valid"])

    def test_later_update_preserves_unreviewed_non_core_gap(self):
        path, _ = self.populate(self.create())
        outline = self.add_non_core_unknown(path)
        report = self.write_current_report(path, outline)
        job = self.create(output=report.parent)
        task.begin_update(job["work_dir"], ["## 比较"])
        child, _ = self.populate(job)
        task.apply_update(child, {"## 比较": "## 比较\n\n[新分析](https://example.org/original)"})
        self.assertTrue(task.verify_task(child)["verified"])
        self.assertNotIn("缺少部署测量数据", report.read_text(encoding="utf-8"))
        self.assertIn("缺少部署测量数据", task.catalog.report_summary(report)["update"]["baseline_gaps"])

    def test_show_returns_the_existing_fields_path_and_rejects_ambiguity(self):
        job = self.create()
        path = Path(job["work_dir"])
        config = path / "fields.json"
        yaml_path = config.with_suffix(".yaml")
        config.rename(yaml_path)
        self.assertEqual(task.describe_task(path)["fields"], str(yaml_path))
        config.write_bytes(yaml_path.read_bytes())
        with self.assertRaisesRegex(ValueError, "one fields configuration"):
            task.describe_task(path)
        with self.assertRaises(ValueError):
            context.report_context(path / "outline.json")

    def test_promotion_does_not_create_a_second_configuration_beside_existing_yaml(self):
        job = self.create(depth="brief")
        path = Path(job["work_dir"])
        (path / "fields.yaml").write_text("schema_version: 2\nfields: []\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            task.promote_task(path)
        self.assertFalse((path / "fields.json").exists())
        self.assertEqual(task.describe_task(path)["workflow"], "light")

    def test_delivery_scope_keeps_semantic_fingerprints_but_invalidates_report_note(self):
        for light in (False, True):
            with self.subTest(light=light):
                path, outline, report = self.write_report(self.create(depth="brief" if light else "standard", output=self.workspace / "research-reports" / "general" / "paper" / ("light-20261108-120000" if light else "full-20261108-120000")))
                if light:
                    before = context.light_fingerprint(outline)
                else:
                    field = results.load_document(path / "fields.json")["fields"][0]
                    before = results.input_fingerprint(outline, outline["items"][0], field)
                task.begin_update(path, ["## 分析"])
                changed = results.load_document(path / "outline.json")
                after = context.light_fingerprint(changed) if light else results.input_fingerprint(changed, changed["items"][0], field)
                self.assertEqual(before, after)
                self.assertTrue(context.report_context(path / "outline.json")["completion"] == "complete")
                # Delivery settings still change report consistency and scope checks.
                self.assertFalse(reports.validate(report.parent, path / "outline.json")["valid"])
                task.apply_update(path, {"## 分析": "## 分析\n\n[保留依据](https://example.org/original)"})
                self.assertTrue(task.verify_task(path)["verified"])

    def test_completed_comparison_can_add_one_object_without_rechecking_old_results(self):
        path, outline = self.populate(self.create(items=["a=对象 A", "b=对象 B"]))
        original_records = {}
        for item in outline["items"]:
            record_path = path / "results" / f"{item['id']}.json"
            data = results.load_document(record_path)
            data["sources"][0]["accessed_at"] = "2025-01-02"
            task.write_json(record_path, data)
            original_records[item["id"]] = data
        report = self.write_current_report(path, outline)
        task.verify_task(path)
        parent_files = {p.relative_to(path).as_posix(): p.read_bytes() for p in path.rglob("*") if p.is_file()}
        old_section = updates.selected_spans(updates.text(report), ["## 原有分析"])[0]
        old_prose = updates.text(report)[old_section["start"]:old_section["end"]]
        child_job = task.derive_task(path)
        child = Path(child_job["work_dir"])
        self.assertFalse((child / "verified.json").exists())
        task.begin_update(child, ["## 比较"], added=["## 对象 C"])
        next_outline = results.load_document(child / "outline.json")
        next_outline["items"].append({"id": "c", "name": "对象 C", "type": "paper", "version": "v1", "seed_sources": []})
        next_outline["revision"] += 1
        task.write_json(child / "outline.json", next_outline)
        pending = results.validate(child / "outline.json", child / "fields.json")
        self.assertFalse(pending["valid"])
        self.assertFalse(any("stale input_fingerprint" in error for error in pending["errors"]))
        field = results.load_document(child / "fields.json")["fields"][0]
        item = next_outline["items"][-1]
        task.write_json(child / "results/c.json", {"schema_version": 2, "item_id": "c", "type": "paper", "version": "v1", "sources": [{**SOURCE, "url": "https://example.org/c", "title": "C 的原始资料"}], "fields": {
            field["id"]: {"status": "confirmed", "value": "对象 C 的有据结论", "evidence": [{"source_id": "s1", "locator": "原文方法章节"}], "input_fingerprint": results.input_fingerprint(next_outline, item, field)}}})
        task.apply_update(child, {"## 比较": "## 比较\n\n在 A、B 的[原有资料](https://example.org/original)基础上，加入 C 的[新证据](https://example.org/c)。",
                                  "## 对象 C": "## 对象 C\n\n本次新增分析：[原文](https://example.org/c)。"})
        self.assertEqual(task.verify_task(child)["completion"], "complete")
        for key, data in original_records.items():
            self.assertEqual(results.load_document(child / "results" / f"{key}.json"), data)
        self.assertEqual(parent_files, {p.relative_to(path).as_posix(): p.read_bytes() for p in path.rglob("*") if p.is_file()})
        new_section = updates.selected_spans(updates.text(report), ["## 原有分析"])[0]
        self.assertEqual(old_prose.strip(), updates.text(report)[new_section["start"]:new_section["end"]].strip())
        self.assertNotIn("原访问日期 2025-01-02", updates.text(report))
        self.assertTrue(any(source["accessed_at"] == "2025-01-02" for source in task.catalog.report_summary(report)["derived_from"]["sources"]))
        self.assertTrue(task.cleanup_plan(child)["eligible"])

    def test_derive_rejects_stale_evidence_and_light_notes(self):
        path, outline = self.populate(self.create())
        outline["goal"] = "不同的研究目标"
        task.write_json(path / "outline.json", outline)
        with self.assertRaises(ValueError):
            task.derive_task(path)
        with self.assertRaises(ValueError):
            task.derive_task(self.create(depth="brief")["work_dir"])

    def test_derivation_detects_concurrent_source_changes_before_creating_a_child(self):
        path, _ = self.populate(self.create())
        real_validate = results.validate

        def concurrent_change(*args, **kwargs):
            checked = real_validate(*args, **kwargs)
            record_path = path / "results/item-1.json"
            data = results.load_document(record_path)
            data["fields"]["overview"]["value"] = "另一个编辑者的并发修改"
            task.write_json(record_path, data)
            return checked

        with patch.object(results, "validate", side_effect=concurrent_change):
            with self.assertRaisesRegex(ValueError, "changed during derivation"):
                task.derive_task(path)
        self.assertEqual(len(task.list_tasks(self.workspace)["tasks"]), 1)

    def test_legacy_light_fingerprint_is_accepted_only_for_the_same_question(self):
        path, outline, _ = self.write_report(self.create(depth="brief"))
        task.begin_update(path, ["## 分析"])
        outline = results.load_document(path / "outline.json")
        outline["assessment"]["input_fingerprint"] = context.light_fingerprint(outline, legacy_update=True)
        task.write_json(path / "outline.json", outline)
        self.assertTrue(context.validate_light(path / "outline.json")["valid"])
        outline["goal"] = "实际改变研究问题"
        task.write_json(path / "outline.json", outline)
        self.assertFalse(context.validate_light(path / "outline.json")["valid"])

    def test_legacy_update_fingerprints_can_be_checked_and_migrated_without_changing_facts(self):
        path, outline, _ = self.write_report(self.create())
        task.begin_update(path, ["## 分析"])
        outline = results.load_document(path / "outline.json")
        field = results.load_document(path / "fields.json")["fields"][0]
        data = results.load_document(path / "results/item-1.json")
        record = data["fields"][field["id"]]
        record["input_fingerprint"] = results.input_fingerprint(outline, outline["items"][0], field, legacy_update=True)
        task.write_json(path / "results/item-1.json", data)
        self.assertTrue(results.validate(path / "outline.json", path / "fields.json")["valid"])
        derived = Path(task.derive_task(path)["work_dir"])
        inherited = results.load_document(derived / "outline.json")
        self.assertNotIn("update", inherited)
        self.assertEqual(inherited["derived_from"]["canonicalized_fingerprints"], 1)
        copied = results.load_document(derived / "results/item-1.json")
        expected = copy.deepcopy(data)
        expected["fields"][field["id"]]["input_fingerprint"] = results.input_fingerprint(inherited, inherited["items"][0], field)
        self.assertEqual(copied, expected)
        self.assertTrue(results.validate(derived / "outline.json", derived / "fields.json")["valid"])


if __name__ == "__main__":
    unittest.main()
