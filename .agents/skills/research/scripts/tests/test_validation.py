"""Run with python -B -m unittest discover -s <this directory> -v."""

import base64
import copy
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))


def module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


results = module("validate_results")
reports = module("validate_report")
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jB7sAAAAASUVORK5CYII=")


class ResultChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="research-results-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.work = self.root / "temporary-run"
        (self.work / "results").mkdir(parents=True)
        self.outline = {
            "schema_version": 2, "revision": 1, "run_id": "sample", "topic": "示例调研",
            "workspace": str(self.workspace), "work_dir": str(self.work),
            "output_dir": str(self.workspace / "reports/sample"),
            "object_type": "paper", "mode": "single", "depth": "standard",
            "items": [{"id": "sample", "name": "示例", "type": "paper", "version": "v1"}],
        }
        self.fields = {"schema_version": 2, "fields": [{"id": "method", "description": "方法是什么？"}]}
        self.result = {
            "schema_version": 2, "item_id": "sample", "type": "paper", "version": "v1",
            "sources": [{"id": "s1", "title": "示例原文", "url": "https://example.org/paper", "kind": "primary", "accessed_at": "2026-11-05"}],
            "fields": {"method": {"status": "confirmed", "value": "方法说明", "evidence": [{"source_id": "s1", "locator": "第 3 节"}]}},
        }

    def bind_inputs(self, data):
        item = next((item for item in self.outline["items"] if item["id"] == data["item_id"]), None)
        if item:
            for field in self.fields["fields"]:
                record = data.get("fields", {}).get(field["id"])
                if isinstance(record, dict):
                    record["input_fingerprint"] = results.input_fingerprint(self.outline, item, field)

    def run_check(self, save_result=True, selected=None, refresh_fingerprints=True):
        for name, data in (("outline.json", self.outline), ("fields.json", self.fields)):
            (self.work / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        if save_result:
            if refresh_fingerprints:
                self.bind_inputs(self.result)
            (self.work / "results/sample.json").write_text(json.dumps(self.result, ensure_ascii=False), encoding="utf-8")
        return results.validate(self.work / "outline.json", self.work / "fields.json", item_ids=selected)

    def test_valid_and_zero_value(self):
        self.result["fields"]["method"]["value"] = 0
        self.assertTrue(self.run_check()["valid"])

    def test_unknown_is_retained_with_reason(self):
        self.result["sources"] = []
        self.result["fields"]["method"] = {"status": "unknown", "value": None, "reason": "附录未公开", "evidence": []}
        checked = self.run_check()
        self.assertTrue(checked["valid"])
        self.assertTrue(checked["warnings"])
        self.assertEqual(checked["completion"], "blocked")
        self.assertFalse(checked["report_ready"])

    def test_unknown_without_reason_fails(self):
        self.result["fields"]["method"] = {"status": "unknown", "value": None}
        self.assertFalse(self.run_check()["valid"])

    def test_missing_file_never_counts_as_success(self):
        checked = self.run_check(save_result=False)
        self.assertFalse(checked["valid"])
        self.assertEqual(checked["checked_items"], 0)

    def test_missing_selected_field(self):
        self.fields["fields"].append({"id": "limitations", "description": "局限"})
        self.assertFalse(self.run_check()["valid"])

    def test_version_and_type_mismatch(self):
        for key, value in (("version", "v2"), ("type", "product")):
            with self.subTest(key=key):
                original = self.result[key]
                self.result[key] = value
                self.assertFalse(self.run_check()["valid"])
                self.result[key] = original

    def test_unknown_source_and_missing_locator(self):
        self.result["fields"]["method"]["evidence"] = [{"source_id": "missing"}]
        checked = self.run_check()
        self.assertFalse(checked["valid"])
        self.assertGreaterEqual(len(checked["errors"]), 2)

    def test_inference_requires_reason(self):
        self.result["fields"]["method"]["status"] = "inferred"
        self.assertFalse(self.run_check()["valid"])

    def test_field_type_and_item_scope(self):
        self.outline["mode"] = "comparison"
        self.outline["items"].append({"id": "other", "name": "另一篇论文", "type": "paper"})
        self.fields["fields"].append({"id": "workflow", "description": "流程", "applies_to": ["paper"], "item_ids": ["other"]})
        self.assertTrue(self.run_check(selected=["sample"])["valid"])
        self.assertFalse(self.run_check()["valid"])

    def test_duplicate_fields_and_unsafe_ids(self):
        self.fields["fields"].append(copy.deepcopy(self.fields["fields"][0]))
        self.assertFalse(self.run_check()["valid"])
        self.fields["fields"].pop()
        self.outline["items"][0]["id"] = "../outside"
        self.assertFalse(self.run_check()["valid"])

    def test_work_inside_workspace_and_protected_output(self):
        original = self.outline["work_dir"]
        self.outline["work_dir"] = str(self.workspace / "cache")
        self.assertFalse(self.run_check()["valid"])
        self.outline["work_dir"] = original
        self.outline["output_dir"] = str(self.workspace / ".agents/reports")
        self.assertFalse(self.run_check()["valid"])

    def test_malformed_plan_is_reported(self):
        self.run_check()
        (self.work / "outline.json").write_text("{", encoding="utf-8")
        self.assertFalse(results.validate(self.work / "outline.json", self.work / "fields.json")["valid"])

    def test_cli_failure_exit_code(self):
        self.run_check(save_result=False)
        run = subprocess.run([sys.executable, "-B", str(SCRIPTS / "validate_results.py"), "--outline", str(self.work / "outline.json"), "--fields", str(self.work / "fields.json")], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(run.returncode, 1)
        self.assertFalse(json.loads(run.stdout)["valid"])

    def test_all_object_profiles_are_supported(self):
        for kind in ("paper", "open-source", "product", "benchmark", "analysis"):
            with self.subTest(kind=kind):
                self.outline["object_type"] = kind
                self.outline["items"][0]["type"] = kind
                self.result["type"] = kind
                self.assertTrue(self.run_check()["valid"])

    def test_comparison_keeps_item_specific_dimensions(self):
        self.outline["object_type"] = "paper"
        self.outline["mode"] = "comparison"
        self.outline["items"].append({"id": "product", "name": "另一篇论文", "type": "paper"})
        self.fields["fields"][0]["applies_to"] = ["paper"]
        self.fields["fields"][0]["item_ids"] = ["sample"]
        self.fields["fields"].append({"id": "capabilities", "description": "另一篇论文的覆盖", "applies_to": ["paper"], "item_ids": ["product"]})
        product = {"schema_version": 2, "item_id": "product", "type": "paper", "version": None, "sources": [], "fields": {"capabilities": {"status": "unknown", "value": None, "reason": "未公开", "evidence": []}}}
        self.bind_inputs(product)
        (self.work / "results/product.json").write_text(json.dumps(product), encoding="utf-8")
        checked = self.run_check()
        self.assertTrue(checked["valid"], checked)
        self.assertEqual(checked["checked_items"], 2)
        self.assertEqual(checked["completion"], "partial")
        self.assertEqual(checked["item_completion"]["product"]["status"], "blocked")

    def test_yaml_plans_and_invalid_yaml(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("YAML support is optional")
        self.run_check()
        outline_path, fields_path = self.work / "outline.yaml", self.work / "fields.yaml"
        outline_path.write_text(yaml.safe_dump(self.outline), encoding="utf-8")
        fields_path.write_text(yaml.safe_dump(self.fields), encoding="utf-8")
        self.assertTrue(results.validate(outline_path, fields_path)["valid"])
        outline_path.write_text("items: [", encoding="utf-8")
        self.assertFalse(results.validate(outline_path, fields_path)["valid"])

    def test_changed_question_rejects_existing_result(self):
        self.assertTrue(self.run_check()["valid"])
        self.fields["fields"][0]["description"] = "改为核实完全不同的研究问题"
        self.outline["revision"] += 1
        checked = self.run_check(refresh_fingerprints=False)
        self.assertFalse(checked["valid"])
        self.assertEqual(checked["completion"], "blocked")
        self.assertTrue(any("stale input_fingerprint" in message for message in checked["errors"]))

    def test_missing_fingerprint_requires_review(self):
        checked = self.run_check(refresh_fingerprints=False)
        self.assertFalse(checked["valid"])
        self.assertTrue(any("input_fingerprint" in message for message in checked["errors"]))

    def test_progress_stale_and_pending_block_reporting(self):
        self.run_check()
        for state in ("stale", "pending"):
            with self.subTest(state=state):
                (self.work / "progress.json").write_text(json.dumps({"sample": {"method": {"status": state, "reason": "需要补查"}}}), encoding="utf-8")
                checked = self.run_check(refresh_fingerprints=False)
                self.assertFalse(checked["valid"])
                self.assertFalse(checked["report_ready"])
                self.assertTrue(any(f"progress is {state}" in message for message in checked["errors"]))
        (self.work / "progress.json").write_text(json.dumps({"sample": {"method": {"status": "done"}}}), encoding="utf-8")
        self.assertTrue(self.run_check(refresh_fingerprints=False)["valid"])

    def test_malformed_progress_is_not_ignored(self):
        self.run_check()
        (self.work / "progress.json").write_text("{", encoding="utf-8")
        self.assertFalse(self.run_check(refresh_fingerprints=False)["valid"])

    def test_revision_change_does_not_invalidate_unchanged_field(self):
        self.run_check()
        self.outline["revision"] += 1
        self.outline["mode"] = "comparison"
        self.outline["items"].append({"id": "other", "name": "其他论文", "type": "paper"})
        checked = self.run_check(selected=["sample"], refresh_fingerprints=False)
        self.assertTrue(checked["valid"], checked)
        self.assertEqual(checked["scope"], "selected")
        self.assertEqual(checked["planned_items"], 2)

    def test_new_field_does_not_invalidate_old_field(self):
        self.run_check()
        old = self.result["fields"]["method"]["input_fingerprint"]
        self.fields["fields"].append({"id": "limitations", "description": "局限是什么？"})
        self.result["fields"]["limitations"] = {"status": "unknown", "value": None, "reason": "附录未公开", "evidence": [], "input_fingerprint": results.input_fingerprint(self.outline, self.outline["items"][0], self.fields["fields"][1])}
        checked = self.run_check(refresh_fingerprints=False)
        self.assertTrue(checked["valid"], checked)
        self.assertEqual(self.result["fields"]["method"]["input_fingerprint"], old)
        self.assertEqual(checked["completion"], "partial")

    def test_changed_scope_rejects_existing_result(self):
        self.run_check()
        self.outline["time_range"] = "仅考察新的时间范围"
        self.assertFalse(self.run_check(refresh_fingerprints=False)["valid"])

    def test_changed_version_cannot_be_hidden_by_changing_label(self):
        self.run_check()
        self.outline["items"][0]["version"] = "v2"
        self.result["version"] = "v2"
        self.assertFalse(self.run_check(refresh_fingerprints=False)["valid"])

    def test_core_gap_is_partial_with_other_findings(self):
        self.fields["fields"].append({"id": "limitations", "description": "主要局限", "core": True})
        self.result["fields"]["limitations"] = {"status": "unknown", "value": None, "reason": "缺少附录", "evidence": []}
        checked = self.run_check()
        self.assertTrue(checked["valid"], checked)
        self.assertEqual(checked["completion"], "partial")
        self.assertTrue(checked["report_ready"])
        self.assertEqual(checked["item_completion"]["sample"]["core_unknown_fields"], ["limitations"])

    def test_noncore_gap_keeps_limitations_but_can_complete(self):
        self.fields["fields"].append({"id": "optional-cost", "description": "附加成本信息", "core": False})
        self.result["fields"]["optional-cost"] = {"status": "unknown", "value": None, "reason": "未公开", "evidence": []}
        checked = self.run_check()
        self.assertTrue(checked["valid"], checked)
        self.assertEqual(checked["completion"], "complete")
        self.assertEqual(checked["item_completion"]["sample"]["unknown_fields"], ["optional-cost"])
        self.assertTrue(checked["warnings"])

    def test_all_not_applicable_is_not_completed_research(self):
        self.result["fields"]["method"] = {"status": "not_applicable", "value": None, "reason": "对象不适用该维度", "evidence": []}
        checked = self.run_check()
        self.assertTrue(checked["valid"])
        self.assertEqual(checked["completion"], "blocked")

    def test_fingerprints_command_does_not_need_result_files(self):
        self.run_check(save_result=False)
        command = [sys.executable, "-B", str(SCRIPTS / "validate_results.py"), "--outline", str(self.work / "outline.json"), "--fields", str(self.work / "fields.json"), "--fingerprints"]
        run = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(run.returncode, 0, run.stdout)
        data = json.loads(run.stdout)
        self.assertEqual(data["mode"], "fingerprints")
        self.assertEqual(data["input_fingerprints"]["sample"]["method"], results.input_fingerprint(self.outline, self.outline["items"][0], self.fields["fields"][0]))
        self.assertFalse((self.work / "results/sample.json").exists())

    def test_cli_distinguishes_complete_partial_and_blocked(self):
        command = [sys.executable, "-B", str(SCRIPTS / "validate_results.py"), "--outline", str(self.work / "outline.json"), "--fields", str(self.work / "fields.json")]
        self.run_check()
        run = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(run.returncode, 0)
        self.assertEqual(json.loads(run.stdout)["completion"], "complete")
        self.fields["fields"].append({"id": "limitations", "description": "局限"})
        self.result["fields"]["limitations"] = {"status": "unknown", "value": None, "reason": "未取得资料", "evidence": []}
        self.run_check()
        run = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(run.returncode, 2)
        self.assertEqual(json.loads(run.stdout)["completion"], "partial")
        self.result["fields"]["method"] = {"status": "unknown", "value": None, "reason": "未取得资料", "evidence": []}
        self.run_check()
        run = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(run.returncode, 3)
        self.assertEqual(json.loads(run.stdout)["completion"], "blocked")

    def test_validation_does_not_modify_result_or_progress(self):
        self.run_check()
        (self.work / "progress.json").write_text(json.dumps({"sample": {"method": {"status": "done"}}}), encoding="utf-8")
        before = {str(p): p.read_bytes() for p in self.work.rglob("*") if p.is_file()}
        results.validate(self.work / "outline.json", self.work / "fields.json")
        after = {str(p): p.read_bytes() for p in self.work.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_core_classification_changes_completion_without_invalidating_evidence(self):
        self.fields["fields"].append({"id": "limitations", "description": "局限", "core": True})
        self.result["fields"]["limitations"] = {"status": "unknown", "value": None, "reason": "未公开", "evidence": []}
        self.assertEqual(self.run_check()["completion"], "partial")
        self.fields["fields"][1]["core"] = False
        checked = self.run_check(refresh_fingerprints=False)
        self.assertTrue(checked["valid"], checked)
        self.assertEqual(checked["completion"], "complete")

    def test_documented_schema_example_runs_as_partial(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("YAML support is optional")
        text = (SCRIPTS.parent / "references/research-config.md").read_text(encoding="utf-8")
        yaml_blocks = re.findall(r"```yaml\n(.*?)```", text, re.S)
        json_blocks = re.findall(r"```json\n(.*?)```", text, re.S)
        outline, fields = (yaml.safe_load(block) for block in yaml_blocks[:2])
        data = json.loads(json_blocks[0])
        work = self.workspace / outline["work_dir"]
        (work / "results").mkdir(parents=True)
        (self.workspace / "themes.yaml").write_bytes((SCRIPTS.parents[3] / "themes.yaml").read_bytes())
        outline_path, fields_path = work / "example-outline.json", work / "example-fields.json"
        outline_path.write_text(json.dumps(outline, ensure_ascii=False), encoding="utf-8")
        fields_path.write_text(json.dumps(fields, ensure_ascii=False), encoding="utf-8")
        (work / "results" / f"{data['item_id']}.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        checked = results.validate(outline_path, fields_path)
        self.assertTrue(checked["valid"], checked)
        self.assertEqual(checked["completion"], "partial")


class ReportChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="research-report-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "output"
        (self.root / "assets").mkdir(parents=True)
        (self.root / "references").mkdir()
        (self.root / "assets/figure.png").write_bytes(PNG)
        (self.root / "references/sources.md").write_text("# 来源\n\n[原文](https://example.org/paper)\n", encoding="utf-8")
        self.write("# 示例报告\n\n## 核心方法\n\n![方法图](assets/figure.png)\n\n[来源](references/sources.md)\n")

    def write(self, text):
        (self.root / "report.md").write_text(text, encoding="utf-8")

    def check(self):
        return reports.validate(self.root)

    def test_valid_delivery(self):
        result = self.check()
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["images"], 1)

    def test_missing_image_and_anchor(self):
        self.write("# 报告\n![图](assets/missing.png)\n[章节](#不存在)\n[来源](references/sources.md)")
        self.assertFalse(self.check()["valid"])

    def test_extra_files_rejected(self):
        for name in ("outline.yaml", "result.json", "example.py", "paper.pdf", "README.md"):
            with self.subTest(name=name):
                p = self.root / name
                p.write_text("extra", encoding="utf-8")
                self.assertFalse(self.check()["valid"])
                p.unlink()

    def test_unlinked_article_rejected(self):
        (self.root / "references/orphan.md").write_text("# 未使用文章", encoding="utf-8")
        self.assertFalse(self.check()["valid"])

    def test_download_link_does_not_count_as_embedded_image(self):
        self.write("# 报告\n[下载](assets/figure.png)\n[来源](references/sources.md)")
        self.assertFalse(self.check()["valid"])

    def test_images_in_reference_article_alone_do_not_count(self):
        self.write("# 报告\n[来源](references/sources.md)")
        (self.root / "references/sources.md").write_text("# 文章\n![图](../assets/figure.png)", encoding="utf-8")
        self.assertFalse(self.check()["valid"])

    def test_linked_supplement_can_embed_image(self):
        self.write("# 报告\n[补充](details.md)\n[来源](references/sources.md)")
        (self.root / "details.md").write_text("# 补充\n![图](assets/figure.png)", encoding="utf-8")
        self.assertTrue(self.check()["valid"])

    def test_angle_path_parentheses_and_reference_image(self):
        (self.root / "assets/figure.png").rename(self.root / "assets/中文 图(1).png")
        self.write('# 报告\n![图][pic]\n[pic]: <assets/中文 图(1).png>\n[来源](references/sources.md)\n')
        self.assertTrue(self.check()["valid"], self.check())
        self.write('# 报告\n![图](assets/中文%20图(1).png)\n[来源](references/sources.md)\n')
        self.assertTrue(self.check()["valid"], self.check())

    def test_html_and_code_examples(self):
        self.write('# 报告\n<img src="assets/figure.png" alt="图">\n[来源](references/sources.md)\n```md\n![例](missing.png)\n```\n`![例](also-missing.png)`\n')
        self.assertTrue(self.check()["valid"], self.check())

    def test_duplicate_heading_anchor(self):
        original = (self.root / "report.md").read_text(encoding="utf-8")
        self.write(original + "\n## 重复\n## 重复\n[第二处](#重复-1)\n")
        self.assertTrue(self.check()["valid"], self.check())

    def test_traversal_and_empty_directories_rejected(self):
        (self.root.parent / "outside.md").write_text("outside", encoding="utf-8")
        original = (self.root / "report.md").read_text(encoding="utf-8")
        self.write(original + "\n[越界](../outside.md)\n")
        (self.root / "unused").mkdir()
        result = self.check()
        self.assertFalse(result["valid"])
        self.assertTrue(any("outside" in error for error in result["errors"]))
        self.assertTrue(any("Empty directory" in error for error in result["errors"]))

    def test_missing_root_report(self):
        (self.root / "report.md").unlink()
        self.assertFalse(self.check()["valid"])

    def test_validator_does_not_change_deliverables(self):
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.check()
        after = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_unclosed_link_is_not_silently_accepted(self):
        for broken in ("![图](<assets/figure.png>", '![图](assets/figure.png "title"'):
            with self.subTest(link=broken):
                self.write("# 报告\n" + broken + "\n[来源](references/sources.md)")
                self.assertFalse(self.check()["valid"])

    def test_image_with_optional_title(self):
        self.write('# 报告\n![图](assets/figure.png "说明")\n[来源](references/sources.md)')
        self.assertTrue(self.check()["valid"], self.check())

    def test_svg_image_and_missing_external_host(self):
        (self.root / "assets/figure.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>', encoding="utf-8")
        (self.root / "assets/figure.png").unlink()
        self.write("# 报告\n![图](assets/figure.svg)\n[来源](references/sources.md)")
        self.assertTrue(self.check()["valid"], self.check())
        self.write("# 报告\n![图](assets/figure.svg)\n[错误链接](https://)\n[来源](references/sources.md)")
        self.assertFalse(self.check()["valid"])

    def test_explanatory_footnote_is_not_a_file_link(self):
        original = (self.root / "report.md").read_text(encoding="utf-8")
        self.write(original + "\n说明[^1]，再次说明[^1]。\n\n[^1]: 这是解释性脚注。\n")
        self.assertTrue(self.check()["valid"], self.check())

    def test_footnote_body_links_are_still_checked(self):
        self.write("# 报告\n![图](assets/figure.png)\n资料见[^来源]。\n\n[^来源]: [原始资料](references/sources.md)\n    这段脚注还有 [原文](https://example.org/paper)。\n")
        self.assertTrue(self.check()["valid"], self.check())
        self.write("# 报告\n![图](assets/figure.png)\n[来源](references/sources.md)\n资料见[^1]。\n\n[^1]: [丢失资料](references/missing.md)\n")
        checked = self.check()
        self.assertFalse(checked["valid"])
        self.assertTrue(any("missing.md" in message for message in checked["errors"]))

    def test_undefined_footnote_is_reported(self):
        original = (self.root / "report.md").read_text(encoding="utf-8")
        self.write(original + "\n说明[^missing]。\n")
        checked = self.check()
        self.assertFalse(checked["valid"])
        self.assertTrue(any("Undefined footnote" in message for message in checked["errors"]))

    def test_footnotes_inside_code_and_escaped_text_are_ignored(self):
        original = (self.root / "report.md").read_text(encoding="utf-8")
        self.write(original + "\n`[^inline]`\n\n```md\n[^fake]: missing.md\n示例[^code]\n```\n\n\\[^escaped]\n")
        self.assertTrue(self.check()["valid"], self.check())

    def test_numeric_reference_link_still_resolves_as_a_file(self):
        self.write("# 报告\n![图](assets/figure.png)\n[来源][1]\n\n[1]: references/sources.md\n")
        self.assertTrue(self.check()["valid"], self.check())


if __name__ == "__main__":
    unittest.main()
