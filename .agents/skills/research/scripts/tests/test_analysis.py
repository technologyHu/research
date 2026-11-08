"""End-to-end analysis evidence, local citations and classification regressions."""

import hashlib
import json
from pathlib import Path
import shutil
import unittest

import test_task_workflow as fixtures
from test_task_workflow import task, context, results, reports


class AnalysisWorkflow(unittest.TestCase):
    setUp = fixtures.TaskWorkflow.setUp

    def analysis(self, depth="standard"):
        adopted = self.workspace / "agent-memory/paper/survey-memory/report.md"
        adopted.parent.mkdir(parents=True, exist_ok=True)
        adopted.write_text("# 综述论文调研\n\n## 分类体系\n\n已核对的论文分类与限制。\n", encoding="utf-8")
        source = {"id": "prior", "title": "已有论文调研", "url": "repo:agent-memory/paper/survey-memory/report.md",
                  "kind": "secondary", "version": "2026-11-07", "accessed_at": "2026-11-07",
                  "sha256": hashlib.sha256(adopted.read_bytes()).hexdigest(), "locator": "分类体系"}
        job = task.create_task(self.workspace, "记忆服务取舍", "analysis", theme="agent-memory",
                               target="memory-selection", depth=depth, fields=["judgment=什么条件下需要独立记忆服务？"])
        work, _, outline = task.open_task(job["work_dir"])
        if depth == "brief":
            (work / "notes.md").write_text("已有事实、贡献者假设及有条件推导，均记录采用范围。\n", encoding="utf-8")
            outline["assessment"] = {"input_fingerprint": context.light_fingerprint(outline), "status": "complete",
                                     "version": None, "core_gaps": [], "sources": [source]}
            task.write_json(work / "outline.json", outline)
        else:
            item = outline["items"][0]
            field = results.load_document(work / "fields.json")["fields"][0]
            data = {"schema_version": 2, "item_id": item["id"], "type": "analysis", "version": None,
                    "sources": [source], "fields": {"judgment": {
                        "input_fingerprint": results.input_fingerprint(outline, item, field),
                        "status": "inferred", "value": "在给定隔离约束下，独立服务可能值得采用。",
                        "reason": "已有调研事实与本次场景约束共同支持条件性判断。",
                        "evidence": [{"source_id": "prior", "locator": "分类体系"}]}}}
            task.write_json(work / "results" / f"{item['id']}.json", data)
        report = Path(outline["output_dir"]) / "report.md"
        note = context.render_report_note(context.report_context(work / "outline.json"))
        report.write_text("# 分析判断\n\n" + note + "\n## 判断\n\n根据[已有调研](../../paper/survey-memory/report.md#分类体系)，在给定约束下作条件性判断。\n", encoding="utf-8")
        return work, outline, report, adopted

    def test_full_and_light_analysis_cite_local_reports_without_copying_them(self):
        for depth in ("standard", "brief"):
            with self.subTest(depth=depth):
                work, outline, report, adopted = self.analysis(depth)
                checked = task.verify_task(work)
                self.assertTrue(checked["verified"], checked)
                self.assertEqual(reports.validate(outline["output_dir"], work / "outline.json")["documents"], 1)
                independent = reports.validate(outline["output_dir"])
                self.assertTrue(independent["valid"], independent)
                self.assertFalse(independent["consistency_checked"])
                self.assertTrue(adopted.is_file())
                self.assertNotIn(str(self.workspace), report.read_text(encoding="utf-8"))
                self.assertEqual(outline["classification"]["type"], "analysis")

    def test_changed_adopted_report_blocks_existing_analysis(self):
        work, _, _, adopted = self.analysis()
        task.verify_task(work)
        adopted.write_text(adopted.read_text(encoding="utf-8") + "新版本改变了结论。\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Adopted report changed"):
            task.verify_task(work)

    def test_adopted_report_references_survive_project_relocation(self):
        work, _, _, _ = self.analysis()
        moved = self.root / "relocated-project"
        shutil.copytree(self.workspace, moved)
        self.assertTrue(task.verify_task(moved / work.relative_to(self.workspace))["verified"])

    def test_missing_anchor_and_unregistered_report_are_rejected(self):
        work, outline, report, _ = self.analysis()
        original = report.read_text(encoding="utf-8")
        report.write_text(original.replace("#分类体系)", "#不存在)"), encoding="utf-8")
        checked = reports.validate(outline["output_dir"], work / "outline.json")
        self.assertFalse(checked["valid"])
        self.assertTrue(any("missing adopted report anchor" in e for e in checked["errors"]))
        other = self.workspace / "agent-memory/paper/other/report.md"
        other.parent.mkdir(parents=True)
        other.write_text("# 未采用的报告\n", encoding="utf-8")
        report.write_text(original + "\n[未登记](../../paper/other/report.md)\n", encoding="utf-8")
        checked = reports.validate(outline["output_dir"], work / "outline.json")
        self.assertFalse(checked["valid"])
        self.assertTrue(any("target outside output" in e for e in checked["errors"]))

    def test_repo_sources_do_not_relax_ordinary_report_or_temporary_file_boundaries(self):
        work, outline, _, _ = self.analysis()
        data_path = next((work / "results").glob("*.json"))
        data = json.loads(data_path.read_text(encoding="utf-8"))
        item = outline["items"][0]
        field = results.load_document(work / "fields.json")["fields"][0]
        outline["object_type"] = item["type"] = data["type"] = "paper"
        data["fields"]["judgment"]["input_fingerprint"] = results.input_fingerprint(outline, item, field)
        task.write_json(work / "outline.json", outline)
        task.write_json(data_path, data)
        checked = results.validate(work / "outline.json", work / "fields.json")
        self.assertFalse(checked["valid"])
        self.assertTrue(any("limited to analysis" in e for e in checked["errors"]))
        for value in ("repo:../outside/report.md", "repo:agent-memory/.tmp/run/notes.md", "repo:agent-memory/plan.md",
                      "repo:agent-memory/.TMP/run/notes.md", "repo:agent-memory/paper/PLAN.md"):
            self.assertFalse(results.valid_url(value), value)

    def test_removed_topic_and_mixed_sources_do_not_create_a_fallback_type(self):
        with self.assertRaises(ValueError):
            task.create_task(self.workspace, "旧分类", "topic", target="old")
        for kind, items in (("paper", ["a:paper=论文", "b:product=产品"]),
                            ("analysis", ["a:paper=论文", "b:product=产品"]),
                            ("analysis", ["a:paper=论文"])):
            with self.subTest(kind=kind, items=items), self.assertRaisesRegex(ValueError, "separate tasks"):
                task.create_task(self.workspace, "混合对象", kind, target="mixed", items=items)
        self.assertEqual(list(self.workspace.iterdir()), [])

    def test_survey_directory_preserves_paper_classification(self):
        job = task.create_task(self.workspace, "综述论文", "paper", theme="agent-memory", target="survey-memory")
        self.assertEqual(Path(job["output_dir"]).relative_to(self.workspace).as_posix(), "agent-memory/paper/survey-memory")
        self.assertEqual(job["classification"]["type"], "paper")


if __name__ == "__main__":
    unittest.main()
