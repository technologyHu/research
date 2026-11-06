import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from research_graph import build_graph, parse_markdown, next_steps, resolve_link, update_readme, generate_artifacts, START, END
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

    def report(self, path="paper/agents/one/report.md", completion="partial", run="run-1", items=None):
        summary = {"completion": completion, "run_id": run, "items": items or []}
        return self.write(path, "# 报告一\n\n<!-- research-summary\n" + json.dumps(summary) + "\n-->\n")

    def plan(self, extra="", status="active"):
        return self.write("plans/agents/plan.md", f"""---
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
        self.plan("- T001、T002：[共同报告](../../paper/agents/one/report.md)。")
        graph = self.build()
        self.assertEqual(graph["stats"], {"themes": 1, "reports": 1, "types": 1, "objects": 2})
        self.assertEqual(graph["reports"][0]["status"], "partial")
        self.assertTrue(all(len(n["reportIds"]) == 1 for n in graph["nodes"] if n["kind"] == "object"))
        dependency = next(e for e in graph["edges"] if e["relation"] == "depends")
        self.assertEqual(dependency["source"], "work:agents:T001")
        self.assertEqual(dependency["target"], "work:agents:T002")

    def test_does_not_scan_archives_references_or_temp(self):
        self.report()
        self.report("paper/agents/.tmp/report.md")
        self.report("paper/agents/references/report.md")
        self.write("paper/agents/one/references/copied.md", "# 原始文章")
        self.write("plans/agents/archive/plan.md", "invalid: [")
        self.plan()
        graph = self.build()
        self.assertEqual(graph["stats"]["reports"], 1)
        self.assertEqual(graph["stats"]["themes"], 1)

    def test_only_explicit_report_links_and_not_code_links(self):
        self.report()
        self.report("product/agents/two/report.md", run="different")
        self.plan("""- T001：[一](../../paper/agents/one/report.md)。
- T002：[二](../../product/agents/two/report.md)。

```markdown
T002 [不算引用](../../paper/agents/one/report.md)
```
""")
        graph = self.build()
        links = {(n["id"], r) for n in graph["nodes"] if n["kind"] == "object" for r in n["reportIds"]}
        self.assertEqual(links, {("work:agents:T001", "report:paper/agents/one/report.md"),
                                 ("work:agents:T002", "report:product/agents/two/report.md")})

    def test_table_result_links_keep_their_own_task_row(self):
        self.report()
        self.report("paper/agents/two/report.md", run="run-2")
        self.plan("""| 任务 | 报告 |
| --- | --- |
| T001 | [一](../../paper/agents/one/report.md) |
| T002 | [二](../../paper/agents/two/report.md) |
""")
        graph = self.build()
        produced = {(n["id"], r) for n in graph["nodes"] if n["kind"] == "object" for r in n["reportIds"]}
        self.assertEqual(len(produced), 2)
        self.assertNotIn(("work:agents:T002", "report:paper/agents/one/report.md"), produced)

    def test_candidate_names_do_not_merge_distinct_research_works(self):
        items = [{"id": "x", "name": "Shared", "type": "paper"}]
        self.report(items=items)
        self.report("paper/second/two/report.md", items=items)
        graph = self.build()
        self.assertEqual(graph["stats"]["objects"], 2)
        self.assertEqual(graph["stats"]["reports"], 2)
        obj = next(n for n in graph["nodes"] if n["kind"] == "object")
        self.assertEqual(len(obj["reportIds"]), 1)
        self.assertNotEqual(obj["label"], "Shared")

    def test_work_ids_are_scoped_to_their_theme(self):
        self.report(items=[{"name": "X", "type": "product"}, {"name": "X", "type": "open-source"}])
        self.plan("T001：[实际成果](../../paper/agents/one/report.md)")
        self.write("plans/second/plan.md", "---\ntheme_id: second\n---\n# 另一主题\n## 对象与任务\n| ID | 状态 |\n| --- | --- |\n| T001 | planned |\n")
        graph = self.build()
        self.assertEqual(graph["stats"]["objects"], 3)
        self.assertTrue({"work:agents:T001", "work:second:T001"}.issubset({n["id"] for n in graph["nodes"]}))

    def test_report_to_report_links_and_encoded_paths(self):
        self.report()
        target = self.report("paper/agents/报告 二/report.md")
        self.write("paper/agents/one/report.md", "# 一\n\n[引用](../%E6%8A%A5%E5%91%8A%20%E4%BA%8C/report.md#结论)\n")
        graph = self.build()
        self.assertEqual(graph["stats"]["objects"], 2)
        self.assertTrue(all(n["kind"] in {"theme", "object"} for n in graph["nodes"]))
        self.assertEqual(resolve_link(self.root, self.root / "paper/agents/one/report.md", "../%E6%8A%A5%E5%91%8A%20%E4%BA%8C/report.md"), target.relative_to(self.root).as_posix())

    def test_reference_links_resolve_but_external_or_escape_links_do_not(self):
        self.report()
        source = self.root / "plans/agents/plan.md"
        self.assertIsNone(resolve_link(self.root, source, "https://example.com/report.md"))
        self.assertIsNone(resolve_link(self.root, source, "../../../../outside.md"))
        self.plan("T001 [成果][result]\n\n[result]: ../../paper/agents/one/report.md\n")
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
        self.write("paper/agents/one/report.md", "# 报告\n<!-- research-summary\n{invalid}\n-->")
        with self.assertRaisesRegex(ValueError, "research-summary"):
            self.build()

    def test_summary_examples_in_code_are_not_metadata(self):
        self.write("paper/agents/one/report.md", '# 报告\n\n```markdown\n<!-- research-summary\n{"completion":"complete","items":[{"name":"fake"}]}\n-->\n```\n')
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
        self.write(".research-graph.json", json.dumps({"schema_version": 1, "exclude_paths": ["plans/agents/plan.md", "paper/agents/one/**"]}))
        self.assertEqual(self.build()["nodes"], [])

    def test_no_forced_type_layer_and_no_report_or_task_nodes(self):
        self.plan("T001：[实际成果](../../paper/agents/one/report.md)")
        self.report(items=[{"name": "Candidate", "type": "product"}])
        graph = self.build()
        self.assertEqual({n["kind"] for n in graph["nodes"]}, {"theme", "object"})
        works = [n for n in graph["nodes"] if n["kind"] == "object"]
        self.assertEqual({n["label"] for n in works}, {"分析方法", "对照分析"})
        self.assertTrue(all(n["type"] == "paper" for n in works))

    def test_multiple_reports_in_same_directory_are_one_work(self):
        self.report()
        self.report("paper/agents/one/details.md")
        graph = self.build()
        self.assertEqual(graph["stats"]["objects"], 1)
        self.assertEqual(graph["stats"]["reports"], 2)

    def test_empty_state_has_no_demo_nodes(self):
        graph = self.build()
        self.assertEqual(graph["nodes"], [])
        self.assertEqual(graph["edges"], [])
        update_readme(self.root, graph, "https://example.com/")
        content = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("暂无调研工作", content)
        self.assertIn("0 份", content)

    def test_readme_summarizes_theme_status_plan_reports_and_next_steps(self):
        self.report(completion="partial")
        path = self.plan("- T001、T002：[共同报告](../../paper/agents/one/report.md)。")
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
        self.assertIn("| 智能体 | 进行中 | [调研计划](plans/agents/plan.md)", content)
        self.assertEqual(content.count("[报告一](paper/agents/one/report.md)（部分完成）"), 1)
        self.assertIn("Q001／T001：补查独立复现", content)
        self.assertEqual(graph["themeOverview"][0]["status"], "active")

    def test_readme_keeps_archived_theme_and_does_not_invent_next_actions(self):
        self.plan(status="archived")
        self.write("plans/agents/archive/plan.md", "# 不应新增主题")
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
        path = self.plan("T001：[实际成果](../../paper/agents/one/report.md)")
        path.write_text(path.read_text(encoding="utf-8") + "\n## 缺口与下一步\n\nT002 后续需参考[已有报告](../../paper/agents/one/report.md)，尚未产出成果。\n", encoding="utf-8")
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
| T002 | [参考](../../paper/agents/one/report.md) | [计划](../../paper/agents/one/report.md) | T001 | [交付](../../paper/agents/one/report.md) |
""", encoding="utf-8")
        works = {n["taskId"]: n for n in self.build()["nodes"] if n.get("taskId")}
        self.assertEqual(works["T001"]["reportIds"], [])
        self.assertEqual(len(works["T002"]["reportIds"]), 1)

    def test_reference_subsection_within_results_is_not_a_result(self):
        self.report()
        self.plan("### 参考资料\n\nT002 参考[已有报告](../../paper/agents/one/report.md)")
        self.assertTrue(all(not n["reportIds"] for n in self.build()["nodes"] if n.get("taskId")))

    def test_nested_result_sections_and_explicit_prose_field(self):
        self.report()
        self.plan("### 第一轮\n\nT001：[成果](../../paper/agents/one/report.md)\n\n## 执行记录\n\n实际报告：T002 [成果](../../paper/agents/one/report.md)")
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


if __name__ == "__main__":
    unittest.main()
