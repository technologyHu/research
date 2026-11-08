import json
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from research_graph import build_graph, parse_markdown, next_steps, resolve_link, update_readme, generate_artifacts, work_ids, START, END
import research_graph_delivery as delivery
from research_graph_preview import work_labels
from research_graph_publication import publication_manifest, ASSETS
import hashlib


class ResearchGraphTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.addCleanup(self.temp.cleanup)

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def report(self, path="agents/paper/one/report.md", completion="partial", run="run-1", items=None):
        summary = {"completion": completion, "run_id": run, "items": items or []}
        return self.write(path, "# 报告一\n\n<!-- research-summary\n" + json.dumps(summary) + "\n-->\n")

    def plan(self, extra="", status="active"):
        return self.write("agents/plan.md", f"""---
theme_id: agents
title: 智能体
status: {status}
revision: 2
updated_at: 2026-11-06
---
# 主题计划
## 对象与任务
| ID | 问题 | 类型／对象 | 本次目标 | 优先级 | 前置任务 | 状态 | 实际 run_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | Q001 | paper／对象甲 | 分析方法 | P0 | 无 | done | run-1 |
| T002 | Q002 | paper／对象乙 | 对照分析 | P1 | T001 | blocked | run-2 |
## 成果索引
{extra}
""")

    def build(self):
        paths = {p.relative_to(self.root).as_posix() for p in self.root.rglob("*.md")}
        return build_graph(self.root, "owner/repo", "feature/research", input_paths=paths)

    def test_shared_report_and_independent_completion(self):
        self.report()
        self.plan("- T001、T002：[共同报告](paper/one/report.md)。")
        graph = self.build()
        self.assertEqual(graph["stats"], {"themes": 1, "reports": 1, "types": 1, "objects": 2})
        self.assertEqual(graph["reports"][0]["status"], "partial")
        self.assertTrue(all(len(n["reportIds"]) == 1 for n in graph["nodes"] if n["kind"] == "object"))
        dependency = next(e for e in graph["edges"] if e["relation"] == "depends")
        self.assertEqual(dependency["source"], "work:agents:T001")
        self.assertEqual(dependency["target"], "work:agents:T002")

    def test_does_not_scan_archives_references_or_temp(self):
        self.report()
        self.report("agents/paper/.tmp/report.md")
        self.report("agents/paper/references/report.md")
        self.write("agents/paper/one/references/copied.md", "# 原始文章")
        self.write("agents/archive/plan.md", "invalid: [")
        self.plan()
        graph = self.build()
        self.assertEqual(graph["stats"]["reports"], 1)
        self.assertEqual(graph["stats"]["themes"], 1)

    def test_analysis_and_survey_use_distinct_types_and_topic_is_not_indexed(self):
        self.report("agents/paper/survey-memory/report.md")
        self.report("agents/analysis/memory-selection/report.md")
        self.report("agents/topic/removed-category/report.md")
        graph = self.build()
        self.assertEqual(graph["stats"], {"themes": 1, "reports": 2, "types": 2, "objects": 2})
        self.assertEqual({n["type"] for n in graph["nodes"] if n["kind"] == "object"}, {"paper", "analysis"})
        self.assertEqual(graph["types"]["analysis"], "分析洞察")
        self.assertNotIn("topic", graph["types"])

    def test_report_roots_keep_plans_and_work_ids_separate_and_allow_cross_citations(self):
        research = "research-reports/memory/paper/survey-memory/report.md"
        analysis = "analysis-reports/memory/analysis/architecture/report.md"
        self.report(research)
        self.write(analysis, "# 洞察\n\n[依据](../../../../research-reports/memory/paper/survey-memory/report.md)\n")
        for group, category, target in (("research-reports", "paper", "survey-memory"),
                                        ("analysis-reports", "analysis", "architecture")):
            self.write(f"{group}/memory/plan.md", f"""---
theme_id: memory
---
# 记忆
## 对象与任务
| ID | 类型／对象 | 状态 |
| --- | --- | --- |
| T001 | {category}／示例 | done |
## 成果索引
T001：[实际成果]({category}/{target}/report.md)
""")
        graph = self.build()
        self.assertEqual(graph["stats"], {"themes": 2, "reports": 2, "types": 2, "objects": 2})
        works = {n["id"]: n for n in graph["nodes"] if n["kind"] == "object"}
        self.assertEqual(works["work:research-reports/memory:T001"]["reportIds"], ["report:" + research])
        self.assertEqual(works["work:analysis-reports/memory:T001"]["reportIds"], ["report:" + analysis])
        self.assertEqual(resolve_link(self.root, self.root / analysis,
                                     "../../../../research-reports/memory/paper/survey-memory/report.md"), research)
        self.assertEqual({row["planPath"] for row in graph["themeOverview"]},
                         {"research-reports/memory/plan.md", "analysis-reports/memory/plan.md"})

    def test_report_root_readmes_and_wrong_root_types_do_not_become_reports(self):
        self.write("research-reports/README.md", "# 调研报告\n")
        self.write("analysis-reports/README.md", "# 分析洞察报告\n")
        self.report("research-reports/memory/analysis/wrong/report.md")
        self.report("analysis-reports/memory/paper/wrong/report.md")
        self.report("research-reports/memory/paper/survey-memory/report.md")
        graph = self.build()
        self.assertEqual(graph["stats"]["reports"], 1)
        self.assertEqual(graph["stats"]["themes"], 1)

    def test_only_explicit_report_links_and_not_code_links(self):
        self.report()
        self.report("agents/product/two/report.md", run="different")
        self.plan("""- T001：[一](paper/one/report.md)。
- T002：[二](product/two/report.md)。

```markdown
T002 [不算引用](paper/one/report.md)
```
""")
        graph = self.build()
        links = {(n["id"], r) for n in graph["nodes"] if n["kind"] == "object" for r in n["reportIds"]}
        self.assertEqual(links, {("work:agents:T001", "report:agents/paper/one/report.md"),
                                 ("work:agents:T002", "report:agents/product/two/report.md")})

    def test_table_result_links_keep_their_own_task_row(self):
        self.report()
        self.report("agents/paper/two/report.md", run="run-2")
        self.plan("""| 任务 | 报告 |
| --- | --- |
| T001 | [一](paper/one/report.md) |
| T002 | [二](paper/two/report.md) |
""")
        graph = self.build()
        produced = {(n["id"], r) for n in graph["nodes"] if n["kind"] == "object" for r in n["reportIds"]}
        self.assertEqual(len(produced), 2)
        self.assertNotIn(("work:agents:T002", "report:agents/paper/one/report.md"), produced)

    def test_candidate_names_do_not_merge_distinct_research_works(self):
        items = [{"id": "x", "name": "Shared", "type": "paper"}]
        self.report(items=items)
        self.report("second/paper/two/report.md", items=items)
        graph = self.build()
        self.assertEqual(graph["stats"]["objects"], 2)
        self.assertEqual(graph["stats"]["reports"], 2)
        obj = next(n for n in graph["nodes"] if n["kind"] == "object")
        self.assertEqual(len(obj["reportIds"]), 1)
        self.assertNotEqual(obj["label"], "Shared")

    def test_work_ids_are_scoped_to_their_theme(self):
        self.report(items=[{"name": "X", "type": "product"}, {"name": "X", "type": "open-source"}])
        self.plan("T001：[实际成果](paper/one/report.md)")
        self.write("second/plan.md", "---\ntheme_id: second\n---\n# 另一主题\n## 对象与任务\n| ID | 状态 |\n| --- | --- |\n| T001 | planned |\n")
        graph = self.build()
        self.assertEqual(graph["stats"]["objects"], 3)
        self.assertTrue({"work:agents:T001", "work:second:T001"}.issubset({n["id"] for n in graph["nodes"]}))

    def test_report_to_report_links_and_encoded_paths(self):
        self.report()
        target = self.report("agents/paper/报告 二/report.md")
        self.write("agents/paper/one/report.md", "# 一\n\n[引用](../%E6%8A%A5%E5%91%8A%20%E4%BA%8C/report.md#结论)\n")
        graph = self.build()
        self.assertEqual(graph["stats"]["objects"], 2)
        self.assertTrue(all(n["kind"] in {"theme", "object"} for n in graph["nodes"]))
        self.assertEqual(resolve_link(self.root, self.root / "agents/paper/one/report.md", "../%E6%8A%A5%E5%91%8A%20%E4%BA%8C/report.md"), target.relative_to(self.root).as_posix())

    def test_reference_links_resolve_but_external_or_escape_links_do_not(self):
        self.report()
        source = self.root / "agents/plan.md"
        self.assertIsNone(resolve_link(self.root, source, "https://example.com/report.md"))
        self.assertIsNone(resolve_link(self.root, source, "../../../../outside.md"))
        self.plan("T001 [成果][result]\n\n[result]: paper/one/report.md\n")
        self.assertTrue(any(n.get("taskId") == "T001" and n["reportIds"] for n in self.build()["nodes"] if n["kind"] == "object"))

    def test_deterministic_data_and_current_branch_urls(self):
        self.report()
        self.plan()
        one, two = self.build(), self.build()
        self.assertEqual(one, two)
        self.assertTrue(all("feature%2Fresearch/" in n["url"] for n in one["nodes"]))
        self.assertTrue(all(0 <= n["x"] <= 1 and 0 <= n["y"] <= 1 for n in one["nodes"]))
        self.assertEqual(one["updatedAt"], "2026-11-06")

    def test_changed_input_changes_fingerprint(self):
        path = self.report()
        one = self.build()
        path.write_text("# 新标题\n", encoding="utf-8")
        self.assertNotEqual(one["fingerprint"], self.build()["fingerprint"])

    def test_invalid_summary_fails_instead_of_silently_losing_data(self):
        self.write("agents/paper/one/report.md", "# 报告\n<!-- research-summary\n{invalid}\n-->")
        with self.assertRaisesRegex(ValueError, "research-summary"):
            self.build()

    def test_summary_examples_in_code_are_not_metadata(self):
        self.write("agents/paper/one/report.md", '# 报告\n\n```markdown\n<!-- research-summary\n{"completion":"complete","items":[{"name":"fake"}]}\n-->\n```\n')
        graph = self.build()
        self.assertEqual(graph["stats"]["objects"], 1)
        self.assertFalse(any(n["label"] == "fake" for n in graph["nodes"]))
        report = graph["reports"][0]
        self.assertEqual(report["status"], "unknown")

    def test_duplicate_summary_fails(self):
        path = self.report()
        path.write_text(path.read_text(encoding="utf-8") + '\n<!-- research-summary\n{"completion":"complete"}\n-->\n', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.build()

    def test_missing_plan_and_empty_repository_are_supported(self):
        self.assertEqual(self.build()["stats"]["reports"], 0)
        self.report()
        graph = self.build()
        theme = next(n for n in graph["nodes"] if n["kind"] == "theme")
        self.assertTrue(theme["inferredFromDirectory"])
        self.assertEqual(theme["status"], "unknown")

    def test_readme_is_idempotent_and_preserves_manual_sections(self):
        self.report()
        graph = self.build()
        self.write("README.md", "# 人工说明\n\n" + START + "\n旧内容\n" + END + "\n\n## 手工维护\n保留\n")
        update_readme(self.root, graph, "https://example.com/")
        one = (self.root / "README.md").read_bytes()
        update_readme(self.root, graph, "https://example.com/")
        self.assertEqual(one, (self.root / "README.md").read_bytes())
        self.assertIn("## 手工维护\n保留", one.decode())
        self.assertNotIn("旧内容", one.decode())

    def test_removing_readme_work_index_preserves_graph_work_nodes_and_dependencies(self):
        self.plan("T001：[成果](paper/one/report.md)")
        self.report()
        graph = self.build()
        before = deepcopy(graph)
        self.write("README.md", "# 人工说明\n\n" + START + "\n## 调研工作索引\n旧工作表\n" + END + "\n")
        update_readme(self.root, graph, "https://example.com/")
        content = (self.root / "README.md").read_text(encoding="utf8")
        self.assertNotIn("## 调研工作索引", content)
        self.assertNotIn("旧工作表", content)
        for heading in ("调研与分析计划总览", "调研报告总览", "分析洞察报告总览"):
            self.assertIn("## " + heading, content)
        self.assertEqual(graph, before)
        self.assertEqual(self.build(), before)
        works = {node["taskId"]: node for node in graph["nodes"] if node["kind"] == "object"}
        self.assertEqual(set(works), {"T001", "T002"})
        self.assertEqual(works["T001"]["reportIds"], ["report:agents/paper/one/report.md"])
        self.assertEqual(works["T002"]["reportIds"], [])
        self.assertTrue(any(edge["relation"] == "depends" and edge["source"] == "work:agents:T001"
                            and edge["target"] == "work:agents:T002" for edge in graph["edges"]))

    def test_readme_separates_analysis_overview_and_counts(self):
        self.report("research-reports/memory/paper/survey-memory/report.md")
        self.report("analysis-reports/memory/analysis/architecture/report.md", completion="complete")
        self.write("analysis-reports/memory/plan.md", """---
theme_id: memory
status: active
---
# 架构洞察
## 下一步
补充反例。
""")
        update_readme(self.root, self.build(), "https://example.com/")
        content = (self.root / "README.md").read_text(encoding="utf8")
        research = content.split("## 调研报告总览\n", 1)[1].split("## 分析洞察报告总览\n", 1)[0]
        analysis = content.split("## 分析洞察报告总览\n", 1)[1].split("\n当前纳入总览", 1)[0]
        self.assertIn("research-reports/memory/paper/survey-memory/report.md", research)
        self.assertNotIn("analysis-reports/", research)
        self.assertIn("analysis-reports/memory/analysis/architecture/report.md", analysis)
        self.assertNotIn("research-reports/", analysis)
        self.assertIn("[分析计划](analysis-reports/memory/plan.md)", analysis)
        self.assertIn("完整", analysis)
        self.assertIn("补充反例。", analysis)
        self.assertIn("调研报告 1 份，分析洞察报告 1 份", content)

    def test_readme_analysis_plan_without_reports_is_not_lost(self):
        self.write("analysis-reports/memory/plan.md", "# 分析计划\n")
        update_readme(self.root, self.build(), "https://example.com/")
        content = (self.root / "README.md").read_text(encoding="utf8")
        research = content.split("## 调研报告总览\n", 1)[1].split("## 分析洞察报告总览\n", 1)[0]
        analysis = content.split("## 分析洞察报告总览\n", 1)[1].split("\n当前纳入总览", 1)[0]
        self.assertIn("暂无调研主题", research)
        self.assertIn("[分析计划](analysis-reports/memory/plan.md)", analysis)
        self.assertIn("暂无报告", analysis)

    def test_readme_partitions_legacy_mixed_theme_reports(self):
        self.report("agents/paper/one/report.md")
        self.report("agents/analysis/insights/report.md")
        update_readme(self.root, self.build(), "https://example.com/")
        content = (self.root / "README.md").read_text(encoding="utf8")
        research = content.split("## 调研报告总览\n", 1)[1].split("## 分析洞察报告总览\n", 1)[0]
        analysis = content.split("## 分析洞察报告总览\n", 1)[1].split("\n当前纳入总览", 1)[0]
        self.assertIn("agents/paper/one/report.md", research)
        self.assertNotIn("agents/analysis/insights/report.md", research)
        self.assertIn("agents/analysis/insights/report.md", analysis)
        self.assertNotIn("agents/paper/one/report.md", analysis)

    def test_readme_lists_both_plan_roots_without_requiring_reports(self):
        for group, status, updated in (("research-reports", "draft", "2026-11-07"),
                                        ("analysis-reports", "paused", "2026-11-08")):
            self.write(f"{group}/memory/plan.md", f"""---
theme_id: memory
status: {status}
updated_at: {updated}
---
# 记忆计划
""")
        self.report("standalone/paper/one/report.md")
        graph = self.build()
        update_readme(self.root, graph, "https://example.com/")
        content = (self.root / "README.md").read_text(encoding="utf8")
        plans = content.split("## 调研与分析计划总览\n", 1)[1].split("## 调研报告总览\n", 1)[0]
        self.assertIn("[查看计划](research-reports/memory/plan.md)", plans)
        self.assertIn("[查看计划](analysis-reports/memory/plan.md)", plans)
        self.assertIn("草案", plans)
        self.assertIn("暂停", plans)
        self.assertIn("2026-11-07", plans)
        self.assertIn("2026-11-08", plans)
        self.assertNotIn("standalone", plans)
        update_readme(self.root, graph, "https://example.com/")
        self.assertEqual(content, (self.root / "README.md").read_text(encoding="utf8"))

    def test_readme_lists_a_shared_legacy_plan_once(self):
        self.plan()
        self.report("agents/paper/one/report.md")
        self.report("agents/analysis/insights/report.md")
        update_readme(self.root, self.build(), "https://example.com/")
        content = (self.root / "README.md").read_text(encoding="utf8")
        plans = content.split("## 调研与分析计划总览\n", 1)[1].split("## 调研报告总览\n", 1)[0]
        self.assertEqual(plans.count("](agents/plan.md)"), 1)
        self.assertIn("调研／分析洞察", plans)

    def test_invalid_readme_markers_fail(self):
        self.write("README.md", START)
        with self.assertRaisesRegex(ValueError, "markers"):
            update_readme(self.root, self.build(), "https://example.com/")

    def test_missing_prerequisite_is_reported_not_invented(self):
        path = self.plan()
        path.write_text(path.read_text(encoding="utf-8").replace("| T001 | blocked", "| T999 | blocked"), encoding="utf-8")
        graph = self.build()
        self.assertEqual(len(graph["warnings"]), 1)
        self.assertFalse(any(e["relation"] == "depends" for e in graph["edges"]))

    def test_untracked_files_are_not_default_inputs(self):
        self.report()
        self.plan()
        with patch("research_graph.tracked_inputs", return_value=set()):
            graph = build_graph(self.root, "owner/repo", "branch")
        self.assertEqual(graph["nodes"], [])
        self.assertEqual(graph["reports"], [])

    def test_explicit_skill_exclusions_apply_to_tracked_inputs(self):
        self.report()
        self.plan()
        self.write(".research-graph.json", json.dumps({"schema_version": 1, "exclude_paths": ["agents/plan.md", "agents/paper/one/**"]}))
        self.assertEqual(self.build()["nodes"], [])

    def test_no_forced_type_layer_and_no_report_or_task_nodes(self):
        self.plan("T001：[实际成果](paper/one/report.md)")
        self.report(items=[{"name": "Candidate", "type": "product"}])
        graph = self.build()
        self.assertEqual({n["kind"] for n in graph["nodes"]}, {"theme", "object"})
        works = [n for n in graph["nodes"] if n["kind"] == "object"]
        self.assertEqual({n["label"] for n in works}, {"分析方法", "对照分析"})
        self.assertTrue(all(n["type"] == "paper" for n in works))

    def test_multiple_reports_in_same_directory_are_one_work(self):
        self.report()
        self.report("agents/paper/one/details.md")
        graph = self.build()
        self.assertEqual(graph["stats"]["objects"], 1)
        self.assertEqual(graph["stats"]["reports"], 2)

    def test_empty_state_has_no_demo_nodes(self):
        graph = self.build()
        self.assertEqual(graph["nodes"], [])
        self.assertEqual(graph["edges"], [])
        update_readme(self.root, graph, "https://example.com/")
        content = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("暂无调研主题", content)
        self.assertIn("0 份", content)
        self.assertIn("## 分析洞察报告总览", content)
        self.assertIn("暂无分析洞察主题", content)
        self.assertIn("## 调研与分析计划总览", content)
        self.assertIn("暂无调研计划", content)
        self.assertIn("暂无分析洞察计划", content)

    def test_readme_summarizes_theme_status_plan_reports_and_next_steps(self):
        self.report(completion="partial")
        path = self.plan("- T001、T002：[共同报告](paper/one/report.md)。")
        path.write_text(path.read_text(encoding="utf-8") + """
## 缺口与下一步
| 问题／任务 | 缺口或阻碍 | 影响 | 下一步／恢复条件 |
| --- | --- | --- | --- |
| Q001／T001 | 缺少复现 | 尚不能定论 | 补查独立复现 |
""", encoding="utf-8")
        graph = self.build()
        update_readme(self.root, graph, "https://example.com/")
        content = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("| 主题 | 状态 | 计划 | 报告 | 下一步 |", content)
        self.assertIn("| 智能体 | 进行中 | [调研计划](agents/plan.md)", content)
        self.assertEqual(content.count("[报告一](agents/paper/one/report.md)（部分完成）"), 1)
        self.assertIn("Q001／T001：补查独立复现", content)
        self.assertEqual(graph["themeOverview"][0]["status"], "active")

    def test_readme_keeps_archived_theme_and_does_not_invent_next_actions(self):
        self.plan(status="archived")
        self.write("agents/archive/plan.md", "# 不应新增主题")
        graph = self.build()
        update_readme(self.root, graph, "https://example.com/")
        content = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertEqual(len(graph["themeOverview"]), 1)
        self.assertIn("| 智能体 | 已归档 |", content)
        self.assertIn("| 暂无报告 | 未记录 |", content)

    def test_next_steps_support_prose_and_escape_table_delimiters(self):
        path = self.plan()
        path.write_text(path.read_text(encoding="utf-8") + "\n## 下一步\n\n先核对 A | B，再继续研究。\n\n- 补查数据来源\n", encoding="utf-8")
        graph = self.build()
        self.assertEqual(graph["themeOverview"][0]["nextSteps"], ["先核对 A | B，再继续研究。", "补查数据来源"])
        update_readme(self.root, graph, "https://example.com/")
        self.assertIn("先核对 A &#124; B，再继续研究。<br>补查数据来源", (self.root / "README.md").read_text(encoding="utf-8"))

    def test_report_only_theme_has_no_fake_plan_link(self):
        self.report()
        graph = self.build()
        self.assertIsNone(graph["themeOverview"][0]["planPath"])
        update_readme(self.root, graph, "https://example.com/")
        content = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("| agents | 未标注 | 尚未建立 | [报告一]", content)
        self.assertNotIn("[调研计划]", content)

    def test_reference_in_next_steps_is_not_a_delivered_result(self):
        self.report()
        path = self.plan("T001：[实际成果](paper/one/report.md)")
        path.write_text(path.read_text(encoding="utf-8") + "\n## 缺口与下一步\n\nT002 后续需参考[已有报告](paper/one/report.md)，尚未产出成果。\n", encoding="utf-8")
        works = {n["taskId"]: n for n in self.build()["nodes"] if n.get("taskId")}
        self.assertEqual(len(works["T001"]["reportIds"]), 1)
        self.assertEqual(works["T002"]["reportIds"], [])

    def test_same_run_id_is_not_proof_of_delivery(self):
        self.report()
        self.plan()
        work = next(n for n in self.build()["nodes"] if n.get("taskId") == "T001")
        self.assertEqual(work["runId"], "run-1")
        self.assertEqual(work["reportIds"], [])

    def test_explicit_actual_report_field_and_reference_columns(self):
        self.report()
        path = self.plan()
        path.write_text(path.read_text(encoding="utf-8") + """
## 执行记录
| 工作 ID | 参考报告 | 预期报告 | 前置任务 | 实际报告 |
| --- | --- | --- | --- | --- |
| T002 | [参考](paper/one/report.md) | [计划](paper/one/report.md) | T001 | [交付](paper/one/report.md) |
""", encoding="utf-8")
        works = {n["taskId"]: n for n in self.build()["nodes"] if n.get("taskId")}
        self.assertEqual(works["T001"]["reportIds"], [])
        self.assertEqual(len(works["T002"]["reportIds"]), 1)

    def test_reference_subsection_within_results_is_not_a_result(self):
        self.report()
        self.plan("### 参考资料\n\nT002 参考[已有报告](paper/one/report.md)")
        self.assertTrue(all(not n["reportIds"] for n in self.build()["nodes"] if n.get("taskId")))

    def test_nested_result_sections_and_explicit_prose_field(self):
        self.report()
        self.plan("### 第一轮\n\nT001：[成果](paper/one/report.md)\n\n## 执行记录\n\n实际报告：T002 [成果](paper/one/report.md)")
        self.assertTrue(all(len(n["reportIds"]) == 1 for n in self.build()["nodes"] if n.get("taskId")))

    def test_nested_next_steps_keep_source_order_and_stop_at_peer_heading(self):
        parsed = parse_markdown("""# 计划
## 缺口与下一步
先整理证据。
### 本周
- 启动验证
#### 验证后
| 工作 | 下一步／恢复条件 |
| --- | --- |
| T001 | 核对结果 |
### 下周
- 更新报告
## 变更记录
- 不应出现在下一步
""")
        self.assertEqual(next_steps(parsed), ["先整理证据。", "启动验证", "T001：核对结果", "更新报告"])

    def test_separate_next_step_sections_do_not_absorb_unrelated_sections(self):
        parsed = parse_markdown("## 下一步\n\n### 本周\n\n- 阅读论文\n\n## 其他\n\n### 本周\n\n- 不属于下一步\n\n## 后续下一步\n\n- 验证方法\n")
        self.assertEqual(next_steps(parsed), ["阅读论文", "验证方法"])

    def published_files(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*")
                if p.is_file() and ".tmp" not in p.relative_to(self.root).parts}

    def seed_artifacts(self):
        for rel in ("graph.json", "graph-data.js", ".nojekyll", "preview.gif", "preview.png"):
            self.write("docs/research-graph/" + rel, "old-" + rel)
        self.write("README.md", "# 人工说明\n\n" + START + "\n旧总览\n" + END + "\n\n保留手工内容\n")

    def test_invalid_readme_preserves_all_published_artifacts(self):
        self.seed_artifacts()
        self.write("README.md", START + "\n未配对标记\n")
        graph, before = self.build(), self.published_files()
        with self.assertRaisesRegex(ValueError, "markers"):
            generate_artifacts(self.root, graph, "https://example.com/")
        self.assertEqual(self.published_files(), before)

    def test_render_failure_preserves_all_published_artifacts(self):
        self.seed_artifacts()
        graph, before = self.build(), self.published_files()
        with patch("research_graph_preview.render_preview", side_effect=RuntimeError("font unavailable")):
            with self.assertRaisesRegex(RuntimeError, "font unavailable"):
                generate_artifacts(self.root, graph, "https://example.com/")
        self.assertEqual(self.published_files(), before)

    def test_corrupt_preview_is_rejected_before_publication(self):
        self.seed_artifacts()
        graph, before = self.build(), self.published_files()
        def bad_preview(graph, output):
            (output / "preview.gif").write_bytes(b"not an image")
            (output / "preview.png").write_bytes(b"not an image")
        with patch("research_graph_preview.render_preview", side_effect=bad_preview):
            with self.assertRaises(OSError):
                generate_artifacts(self.root, graph, "https://example.com/")
        self.assertEqual(self.published_files(), before)

    def test_replace_failure_restores_old_files(self):
        self.seed_artifacts()
        graph, before = self.build(), self.published_files()
        original_replace = delivery.replace_file
        def fail_readme(source, target):
            if "new" in source.parts and target.name == "README.md":
                raise PermissionError("target locked")
            original_replace(source, target)
        with patch.object(delivery, "replace_file", side_effect=fail_readme):
            with self.assertRaisesRegex(PermissionError, "target locked"):
                generate_artifacts(self.root, graph, "https://example.com/", preview=False)
        self.assertEqual(self.published_files(), before)

    def test_replace_failure_removes_newly_created_files(self):
        graph, before = self.build(), self.published_files()
        original_replace = delivery.replace_file
        def fail_readme(source, target):
            if target.name == "README.md":
                raise PermissionError("target locked")
            original_replace(source, target)
        with patch.object(delivery, "replace_file", side_effect=fail_readme):
            with self.assertRaises(PermissionError):
                generate_artifacts(self.root, graph, "https://example.com/", preview=False)
        self.assertEqual(self.published_files(), before)

    def test_rollback_failure_keeps_recoverable_originals(self):
        self.seed_artifacts()
        graph = self.build()
        original = (self.root / "docs/research-graph/graph.json").read_bytes()
        original_replace = delivery.replace_file
        def fail_write_and_restore(source, target):
            if target.name == "README.md" or "backup" in source.parts:
                raise PermissionError("restore also locked")
            original_replace(source, target)
        with patch.object(delivery, "replace_file", side_effect=fail_write_and_restore):
            with self.assertRaisesRegex(delivery.ArtifactRollbackError, "originals retained"):
                generate_artifacts(self.root, graph, "https://example.com/", preview=False)
        stages = list((self.root / ".tmp/research-graph").glob("build-*"))
        self.assertEqual(len(stages), 1)
        self.assertEqual((stages[0] / "backup/docs/research-graph/graph.json").read_bytes(), original)
        self.assertTrue((stages[0] / "transaction.json").is_file())

    def test_bundle_success_preserves_manual_text_and_is_idempotent(self):
        self.seed_artifacts()
        graph = self.build()
        generate_artifacts(self.root, graph, "https://example.com/", preview=False)
        data = json.loads((self.root / "docs/research-graph/graph.json").read_text(encoding="utf-8"))
        self.assertEqual(data, graph)
        self.assertIn("保留手工内容", (self.root / "README.md").read_text(encoding="utf-8"))
        before = {p: (self.root / p).stat().st_mtime_ns for p in self.published_files()}
        generate_artifacts(self.root, graph, "https://example.com/", preview=False)
        self.assertEqual(before, {p: (self.root / p).stat().st_mtime_ns for p in self.published_files()})
        self.assertFalse(list((self.root / ".tmp/research-graph").glob("build-*")))

    def test_concurrent_manual_readme_edit_is_not_overwritten(self):
        self.seed_artifacts()
        graph = self.build()
        old_data = (self.root / "docs/research-graph/graph.json").read_bytes()
        original_update = update_readme
        def edit_during_prepare(stage, data, url):
            original_update(stage, data, url)
            (self.root / "README.md").write_text("并行编辑的人工内容\n", encoding="utf-8")
        with patch("research_graph.update_readme", side_effect=edit_during_prepare):
            with self.assertRaisesRegex(RuntimeError, "changed during generation"):
                generate_artifacts(self.root, graph, "https://example.com/", preview=False)
        self.assertEqual((self.root / "docs/research-graph/graph.json").read_bytes(), old_data)
        self.assertEqual((self.root / "README.md").read_text(encoding="utf-8"), "并行编辑的人工内容\n")

    def test_preview_label_prioritizes_work_name_with_optional_identifier(self):
        self.assertEqual(work_labels({"label": "分析工具的扩展机制", "taskId": "T001"}), ("分析工具的扩展机制", "T001"))
        self.assertEqual(work_labels({"label": "  ", "taskId": "T001"}), ("T001", ""))
        self.assertEqual(work_labels({"label": "独立调研工作"}), ("独立调研工作", ""))

    def test_publication_manifest_binds_version_and_all_asset_bytes(self):
        site = self.root / "docs/research-graph"
        for name in ASSETS:
            self.write("docs/research-graph/" + name, "asset: " + name)
        graph = self.build()
        self.write("docs/research-graph/graph.json", json.dumps(graph))
        manifest = publication_manifest(site, "a" * 40, "b" * 40)
        self.assertEqual(manifest["sourceCommit"], "a" * 40)
        self.assertEqual(manifest["artifactCommit"], "b" * 40)
        self.assertEqual(manifest["fingerprint"], graph["fingerprint"])
        self.assertEqual(set(manifest["assets"]), set(ASSETS))
        for name in ASSETS:
            self.assertEqual(manifest["assets"][name], hashlib.sha256((site / name).read_bytes()).hexdigest())
        with self.assertRaisesRegex(ValueError, "Full Git commit"):
            publication_manifest(site, "short", "b" * 40)

    def test_identity_column_aliases_exclude_dependency_and_reference_ids(self):
        for identity in ("ID", "工作 ID", "任务编号", "调研工作ID", "任务／对象 ID", "工作 ＩＤ"):
            for reference in ("前置任务 ID", "依赖工作ID", "参考任务ID", "后续工作 ID", "任务ID（前置）"):
                with self.subTest(identity=identity, reference=reference):
                    self.assertEqual(work_ids([reference, identity], ["T001", "T002"]), ["T002"])
        self.assertEqual(work_ids(["关联工作 ID"], ["T001、T002"]), ["T001", "T002"])

    def test_dependency_id_column_does_not_own_an_actual_report(self):
        self.report()
        self.plan("""| 前置任务 ID | 工作 ID | 参考工作 ID | 实际报告 |
| --- | --- | --- | --- |
| T001 | T002 | T001 | [成果](paper/one/report.md) |
""")
        works = {n["taskId"]: n for n in self.build()["nodes"] if n.get("taskId")}
        self.assertEqual(works["T001"]["reportIds"], [])
        self.assertEqual(works["T002"]["reportIds"], ["report:agents/paper/one/report.md"])

    def test_work_definitions_use_identity_column_even_when_dependency_comes_first(self):
        self.write("agents/plan.md", """---
theme_id: agents
---
# 计划
## 对象与任务
| 前置任务 ID | 工作 ID | 类型／对象 | 本次目标 |
| --- | --- | --- | --- |
| 无 | T001 | paper／甲 | 阅读甲 |
| T001 | T002 | paper／乙 | 阅读乙 |
""")
        graph = self.build()
        self.assertEqual({n["taskId"] for n in graph["nodes"] if n.get("taskId")}, {"T001", "T002"})
        self.assertEqual(graph["stats"]["objects"], 2)
        self.assertTrue(any(e["relation"] == "depends" and e["source"] == "work:agents:T001" and e["target"] == "work:agents:T002" for e in graph["edges"]))

    def test_dependency_ids_alone_do_not_create_work_definitions(self):
        self.write("agents/plan.md", "# 计划\n\n## 对象与任务\n| 前置工作 ID | 类型／对象 |\n| --- | --- |\n| T001 | paper／甲 |\n")
        graph = self.build()
        self.assertEqual(graph["stats"]["objects"], 0)
        self.assertTrue(any("工作定义行" in w for w in graph["warnings"]))

    def test_nested_work_and_dependency_tables_do_not_read_peer_sections(self):
        path = self.plan()
        content = path.read_text(encoding="utf-8").replace("## 对象与任务\n", "## 对象与任务\n\n### 论文\n")
        content = content.replace("| P1 | T001 |", "| P1 | 无 |")
        content += """
## 依赖与接受条件
### 本轮依赖
#### 论文核对
| 关系 | 下游 ← 前置 |
| --- | --- |
| D001 | T002 ← T001 |
## 其他记录
### 论文
| ID | 类型／对象 |
| --- | --- |
| T003 | paper／丙 |
### 本轮依赖
| 关系 | 下游 ← 前置 |
| --- | --- |
| D002 | T001 ← T002 |
"""
        path.write_text(content, encoding="utf-8")
        graph = self.build()
        self.assertEqual(graph["stats"]["objects"], 2)
        dependencies = [(e["source"], e["target"]) for e in graph["edges"] if e["relation"] == "depends"]
        self.assertEqual(dependencies, [("work:agents:T001", "work:agents:T002")])

    def test_supplemental_report_is_pending_without_creating_or_delivering_work(self):
        self.report()
        self.plan("T001：[主报告](paper/one/report.md)")
        before_ids = {n["id"] for n in self.build()["nodes"] if n["kind"] == "object"}
        self.report("agents/paper/one/details.md")
        graph = self.build()
        self.assertEqual({n["id"] for n in graph["nodes"] if n["kind"] == "object"}, before_ids)
        self.assertEqual(graph["stats"]["reports"], 2)
        work = next(n for n in graph["nodes"] if n.get("taskId") == "T001")
        pending_id = "report:agents/paper/one/details.md"
        self.assertEqual(work["reportIds"], ["report:agents/paper/one/report.md"])
        self.assertEqual(work["pendingReportIds"], [pending_id])
        pending = next(r for r in graph["reports"] if r["id"] == pending_id)
        self.assertEqual(pending["associationStatus"], "pending")
        self.assertEqual(pending["workIds"], [])
        self.assertEqual(pending["candidateWorkIds"], [work["id"]])
        self.assertTrue(any("补充报告待关联" in w for w in graph["warnings"]))
        update_readme(self.root, graph, "https://example.com/")
        self.assertIn("details.md)（部分完成；工作待关联）", (self.root / "README.md").read_text(encoding="utf-8"))

    def test_shared_report_directory_keeps_ambiguous_supplement_pending(self):
        self.report()
        self.report("agents/paper/one/details.md")
        self.plan("T001、T002：[共同报告](paper/one/report.md)")
        graph = self.build()
        self.assertEqual(graph["stats"]["objects"], 2)
        pending = next(r for r in graph["reports"] if r["path"].endswith("details.md"))
        self.assertEqual(pending["candidateWorkIds"], ["work:agents:T001", "work:agents:T002"])
        self.assertTrue(all(n["reportIds"] == ["report:agents/paper/one/report.md"] and n["pendingReportIds"] == [pending["id"]]
                            for n in graph["nodes"] if n["kind"] == "object"))

    def test_explicit_supplement_binding_clears_pending_state_without_new_work(self):
        self.report()
        self.report("agents/paper/one/details.md")
        path = self.plan("T001：[主报告](paper/one/report.md)")
        self.assertTrue(self.build()["warnings"])
        path.write_text(path.read_text(encoding="utf-8") + "\nT002：[补充报告](paper/one/details.md)\n", encoding="utf-8")
        graph = self.build()
        self.assertEqual(graph["stats"]["objects"], 2)
        self.assertEqual(graph["warnings"], [])
        self.assertTrue(all(r["associationStatus"] == "explicit" for r in graph["reports"]))
        self.assertTrue(all(not n["pendingReportIds"] for n in graph["nodes"] if n["kind"] == "object"))

    def test_standalone_directory_keeps_one_stable_work_and_canonical_title(self):
        self.report()
        before = next(n for n in self.build()["nodes"] if n["kind"] == "object")
        supplement = self.report("agents/paper/one/aaa-details.md", run="supplement-run")
        supplement.write_text(supplement.read_text(encoding="utf-8").replace("# 报告一", "# 补充分析"), encoding="utf-8")
        graph = self.build()
        after = next(n for n in graph["nodes"] if n["kind"] == "object")
        self.assertEqual(graph["stats"]["objects"], 1)
        self.assertEqual(after["id"], before["id"])
        self.assertEqual(after["label"], "报告一")
        self.assertTrue(after["path"].endswith("/report.md"))
        self.assertEqual(after["runId"], before["runId"])
        self.assertEqual(len(after["reportIds"]), 2)
        self.assertEqual(graph["warnings"], [])

    def test_independent_delivery_directory_still_creates_a_work(self):
        self.report()
        self.plan("T001：[主报告](paper/one/report.md)")
        self.report("agents/paper/another/report.md")
        graph = self.build()
        self.assertEqual(graph["stats"]["objects"], 3)
        standalone = [n for n in graph["nodes"] if n.get("sourceKind") == "report"]
        self.assertEqual(len(standalone), 1)
        self.assertEqual(standalone[0]["path"], "agents/paper/another/report.md")

    def test_old_type_first_report_and_plan_remain_readable_without_moving(self):
        self.report("paper/legacy/one/report.md")
        self.write("plans/legacy/plan.md", """---
theme_id: legacy
title: 既有主题
status: active
---
# 既有计划
## 对象与任务
| ID | 类型／对象 | 本次目标 |
| --- | --- | --- |
| T001 | paper／甲 | 核查甲 |
## 成果索引
T001：[既有报告](../../paper/legacy/one/report.md)
""")
        before = self.published_files()
        graph = self.build()
        self.assertEqual(graph["stats"]["objects"], 1)
        self.assertEqual(graph["themeOverview"][0]["planPath"], "plans/legacy/plan.md")
        work = next(n for n in graph["nodes"] if n.get("taskId"))
        self.assertEqual(work["reportIds"], ["report:paper/legacy/one/report.md"])
        self.assertEqual(self.published_files(), before)

    def test_theme_first_chinese_official_product_name_is_indexed(self):
        self.report("coding-agent/product/扣子/report.md")
        graph = self.build()
        work = next(n for n in graph["nodes"] if n["kind"] == "object")
        self.assertEqual((work["theme"], work["type"]), ("coding-agent", "product"))
        self.assertEqual(work["path"], "coding-agent/product/扣子/report.md")

    def test_support_directories_do_not_become_theme_roots(self):
        self.report("docs/paper/example/report.md")
        self.write("docs/plan.md", "---\ntheme_id: docs\n---\n# 文档计划\n")
        self.assertEqual(self.build()["nodes"], [])


if __name__ == "__main__":
    unittest.main()
