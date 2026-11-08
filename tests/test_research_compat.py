"""Canonical tools run without a research entry installation; old paths still forward."""

from datetime import date
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / ".agents/skills"
COMMON = SKILLS / "research-common/scripts"
LEGACY = SKILLS / "research/scripts"


class ResearchCompatibilityTests(unittest.TestCase):
    def run_python(self, args, *, cwd=ROOT):
        result = subprocess.run([sys.executable, "-X", "utf8", "-B", *map(str, args)],
                                cwd=cwd, capture_output=True, text=True, encoding="utf8")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_old_cli_entrypoints_have_the_same_help_as_canonical_tools(self):
        for name in ("research_task.py", "research_polish.py", "validate_report.py", "validate_results.py"):
            with self.subTest(name=name):
                self.assertEqual(self.run_python([LEGACY / name, "--help"]),
                                 self.run_python([COMMON / name, "--help"]))

    def test_old_module_imports_resolve_to_common_implementations(self):
        for path in sorted(LEGACY.glob("*.py")):
            with self.subTest(module=path.stem):
                code = ("import importlib, sys; from pathlib import Path; "
                        "sys.path.insert(0, sys.argv[1]); "
                        "module = importlib.import_module(sys.argv[2]); "
                        "assert Path(module.__file__).resolve().parent == Path(sys.argv[3]).resolve()")
                self.run_python(["-c", code, LEGACY, path.stem, COMMON])

    def test_old_test_discovery_loads_the_canonical_test_suite(self):
        bridge = LEGACY / "tests/test_common_workflow.py"
        code = """import importlib.util, inspect, sys, unittest
from pathlib import Path
spec = importlib.util.spec_from_file_location('legacy_tests', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
suite = module.load_tests(unittest.TestLoader(), None, None)
def cases(entries):
    for entry in entries:
        if isinstance(entry, unittest.TestSuite):
            yield from cases(entry)
        else:
            yield entry
tests = list(cases(suite))
assert tests
assert all(Path(inspect.getfile(type(test))).resolve().is_relative_to(Path(sys.argv[2]).resolve()) for test in tests)
"""
        self.run_python(["-c", code, bridge, COMMON / "tests"])

    def test_file_based_legacy_import_keeps_function_globals_on_the_loaded_module(self):
        code = """import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('legacy_loaded_task', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert module.create_task.__globals__ is module.__dict__
assert Path(module.__file__).resolve().parent == Path(sys.argv[2]).resolve()
"""
        self.run_python(["-c", code, LEGACY / "research_task.py", COMMON])

    def test_common_only_installation_can_create_stamp_and_verify_analysis(self):
        with tempfile.TemporaryDirectory(prefix="common-tools-") as folder:
            workspace = Path(folder).resolve()
            installed = workspace / ".agents/skills/research-common"
            shutil.copytree(COMMON.parent, installed, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            self.assertFalse((workspace / ".agents/skills/research").exists())
            entry = installed / "scripts/research_task.py"

            def command(*args, raw=False):
                output = self.run_python([entry, *args], cwd=workspace)
                return output if raw else json.loads(output)

            command("init-themes", "--workspace", ".")
            job = command("create", "--workspace", ".", "--topic", "隔离环境分析", "--type", "analysis", "--depth", "brief")
            work = workspace / job["work_dir"]
            outline = json.loads((work / "outline.json").read_text(encoding="utf8"))
            outline["items"][0]["version"] = "fixture-v1"
            outline["assessment"] = {"input_fingerprint": job["input_fingerprint"], "status": "complete", "version": "fixture-v1", "core_gaps": [],
                                     "sources": [{"title": "测试依据", "url": "https://example.org/evidence", "kind": "primary", "accessed_at": date.today().isoformat(), "locator": "测试章节"}]}
            # Version is part of the evidence scope; ask show for its current fingerprint.
            (work / "outline.json").write_text(json.dumps(outline, ensure_ascii=False), encoding="utf8")
            outline["assessment"]["input_fingerprint"] = command("show", "--work-dir", job["work_dir"])["input_fingerprint"]
            (work / "outline.json").write_text(json.dumps(outline, ensure_ascii=False), encoding="utf8")
            (work / "notes.md").write_text("# 证据笔记\n\n[测试依据](https://example.org/evidence)支持当前问题的有界解释。\n", encoding="utf8")
            note = command("report-note", "--work-dir", job["work_dir"], raw=True)
            report = workspace / job["output_dir"] / "report.md"
            report.write_text("# 隔离环境分析\n\n" + note + "\n## 分析\n\n[测试依据](https://example.org/evidence)说明当前样本的机制与适用边界。\n", encoding="utf8")
            stamped = command("stamp-report", "--work-dir", job["work_dir"])
            self.assertTrue(command("verify", "--work-dir", stamped["work_dir"])["verified"])
            self.assertEqual(len(command("list", "--workspace", ".")["tasks"]), 1)
            self.assertFalse((workspace / ".agents/skills/research").exists())


if __name__ == "__main__":
    unittest.main()
