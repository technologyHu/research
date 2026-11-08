"""Language-edit snapshots retain technical content and respect update scope."""

import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_task_workflow as fixtures
from test_task_workflow import task
import research_polish as polish


BODY = """\n## 方法
<a id="method"></a>
这个方案具有非常重要的作用，采用8个单元。
参见[原始资料](https://example.org/original)。
概念为 `run(8)`，公式为 $n = 8$。

```python
print(8)
```

    run(original)

| 项目 | 数值 |
| --- | --- |
| 单元 | 8 |

原文说：“仅适用于当前版本”。
"""


class PolishChecks(unittest.TestCase):
    setUp = fixtures.TaskWorkflow.setUp
    create = fixtures.TaskWorkflow.create
    populate = fixtures.TaskWorkflow.populate
    write_report = fixtures.TaskWorkflow.write_report

    def draft(self):
        path, outline, report = self.write_report(self.create())
        report.write_text(report.read_text(encoding="utf-8") + BODY, encoding="utf-8")
        return path, outline, report

    def test_prose_edit_passes_and_snapshot_preserves_exact_original(self):
        path, _, report = self.draft()
        before = report.read_bytes()
        saved = polish.snapshot(path, report)
        folder = Path(saved["snapshot"])
        self.assertTrue(folder.is_relative_to(path / "scratch/polish"))
        self.assertEqual((folder / "before.md").read_bytes(), before)
        report.write_text(report.read_text(encoding="utf-8").replace("这个方案具有非常重要的作用，采用", "该方案采用"), encoding="utf-8")
        checked = polish.check(path, folder)
        self.assertTrue(checked["valid"], checked)
        self.assertTrue(checked["diff"])
        self.assertTrue(task.verify_task(path)["verified"])

    def test_technical_changes_are_reported_without_modifying_files(self):
        path, _, report = self.draft()
        before = report.read_text(encoding="utf-8")
        folder = Path(polish.snapshot(path, report)["snapshot"])
        cases = [
            ("## 方法", "## 新方法", "headings"),
            ('id="method"', 'id="other"', "anchors"),
            ("print(8)", "print(16)", "code_blocks"),
            ("`run(8)`", "`run(16)`", "inline_code"),
            ("run(original)", "run(changed)", "indented_code"),
            ("$n = 8$", "$n = 16$", "math"),
            ("| 单元 | 8 |", "| 单元 | 16 |", "tables"),
            ("采用8个", "采用16个", "numbers"),
            ("https://example.org/original", "https://example.org/other", "links"),
            ("[原始资料]", "[其他资料]", "link_markers"),
            ("仅适用于当前版本", "适用于所有版本", "quotes"),
            ("> 调研状态：", "> 状态：", "state_notes"),
        ]
        for old, new, category in cases:
            with self.subTest(category=category):
                report.write_text(before.replace(old, new), encoding="utf-8")
                current = report.read_bytes()
                checked = polish.check(path, folder)
                self.assertFalse(checked["valid"])
                self.assertIn(category, checked["changed_protected_content"]["document"])
                self.assertEqual(report.read_bytes(), current)
                self.assertEqual((folder / "before.md").read_text(encoding="utf-8"), before)

    def test_local_update_is_polished_and_checked_before_apply(self):
        path, _, report = self.draft()
        task.begin_update(path, ["## 方法"])
        baseline = report.read_bytes()
        section = path / "scratch/sections.json"
        section.parent.mkdir(exist_ok=True)
        task.write_json(section, {"## 方法": BODY.lstrip()})
        folder = Path(polish.snapshot(path, section)["snapshot"])
        task.write_json(section, {"## 方法": BODY.lstrip().replace("重要的作用", "关键的作用").replace("8个", "16个")})
        self.assertFalse(polish.check(path, folder)["valid"])
        self.assertEqual(report.read_bytes(), baseline)
        task.write_json(section, {"## 方法": BODY.lstrip().replace("这个方案具有非常重要的作用，采用", "该方案采用")})
        self.assertTrue(polish.check(path, folder)["valid"])
        task.apply_update(path, json.loads(section.read_text(encoding="utf-8")))
        self.assertTrue(task.verify_task(path)["verified"])
        self.assertIn("该方案采用8个单元", report.read_text(encoding="utf-8"))

    def test_source_articles_and_unregistered_drafts_cannot_be_snapshotted(self):
        path, outline, report = self.draft()
        article = report.parent / "references/article.md"
        article.parent.mkdir()
        article.write_text("# 原文", encoding="utf-8")
        with self.assertRaises(ValueError):
            polish.snapshot(path, article)
        with self.assertRaises(ValueError):
            polish.snapshot(path, path / "outline.json")
        task.begin_update(path, ["## 方法"])
        with self.assertRaises(ValueError):
            polish.snapshot(path, report)
        section = path / "scratch/sections.json"
        section.parent.mkdir(exist_ok=True)
        task.write_json(section, {"## 无关章节": "## 无关章节\n新的说明"})
        with self.assertRaises(ValueError):
            polish.snapshot(path, section)

    def test_section_keys_and_inner_headings_cannot_change(self):
        path, _, _ = self.draft()
        task.begin_update(path, ["## 方法"])
        section = path / "scratch/sections.json"
        section.parent.mkdir(exist_ok=True)
        task.write_json(section, {"## 方法": "## 方法\n### 实现\n简要说明"})
        folder = Path(polish.snapshot(path, section)["snapshot"])
        task.write_json(section, {"## 方法": "## 方法\n### 实现细节\n简要说明"})
        self.assertFalse(polish.check(path, folder)["valid"])
        task.write_json(section, {"## 无关": "## 无关\n简要说明"})
        with self.assertRaises(ValueError):
            polish.check(path, folder)

    def test_snapshot_tampering_and_wrong_task_are_rejected(self):
        path, _, report = self.draft()
        folder = Path(polish.snapshot(path, report)["snapshot"])
        (folder / "before.md").write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "snapshot body changed"):
            polish.check(path, folder)
        other = Path(self.create()["work_dir"])
        with self.assertRaises(ValueError):
            polish.check(other, folder)

    def test_each_snapshot_is_independent_and_records_relative_target(self):
        path, _, report = self.draft()
        first = Path(polish.snapshot(path, report)["snapshot"])
        second = Path(polish.snapshot(path, report)["snapshot"])
        self.assertNotEqual(first, second)
        self.assertTrue(polish.check(path, first)["valid"])
        metadata = json.loads((first / "snapshot.json").read_text(encoding="utf-8"))
        self.assertFalse(Path(metadata["target"]).is_absolute())

    def test_cli_returns_relative_paths_and_failure_exit_code(self):
        path, _, report = self.draft()
        script = str(Path(polish.__file__).resolve())
        common = [sys.executable, "-X", "utf8", "-B", script]
        work = path.relative_to(self.workspace).as_posix()
        run = subprocess.run(common + ["snapshot", "--work-dir", work, "--file", report.relative_to(self.workspace).as_posix()], cwd=self.workspace, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        saved = json.loads(run.stdout)
        self.assertFalse(Path(saved["snapshot"]).is_absolute())
        report.write_text(report.read_text(encoding="utf-8").replace("8个", "16个"), encoding="utf-8")
        checked = subprocess.run(common + ["check", "--work-dir", work, "--snapshot", saved["snapshot"]], cwd=self.workspace, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(checked.returncode, 1, checked.stdout + checked.stderr)
        self.assertFalse(json.loads(checked.stdout)["valid"])

    def test_math_frontmatter_and_reference_definitions_are_preserved(self):
        before = "---\ntitle: 示例\n---\n# 标题\n文字[^说明]，见[来源][src]。\n\\[n = 8\\]\n$$x = 4$$\n[src]: https://example.org/source\n[^说明]: 边界未知。\n"
        protected = polish.protected(before)
        after = polish.protected(before.replace("文字", "论述"))
        self.assertEqual(protected, after)
        for old, new, key in (("title: 示例", "title: 新名", "frontmatter"), ("n = 8", "n = 9", "math"), ("[src]: https://example.org/source", "[src]: https://example.org/other", "definitions")):
            self.assertNotEqual(protected[key], polish.protected(before.replace(old, new))[key])


if __name__ == "__main__":
    unittest.main()
