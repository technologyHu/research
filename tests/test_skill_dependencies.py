"""Check entry independence through prose, metadata, resource paths and local imports."""

import ast
from pathlib import Path
import re
import tempfile
import unittest
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
import yaml

ENTRIES = ("research", "research-analysis", "research-commit")
ROOT = Path(__file__).resolve().parents[1] / ".agents/skills"


def links(text):
    def walk(tokens):
        for token in tokens:
            if token.type == "link_open":
                yield token.attrGet("href")
            yield from walk(token.children or [])
    return walk(MarkdownIt("commonmark").parse(text))


def dependency_violations(root):
    root = root.resolve()
    failures, reported = [], set()
    entry_names = "|".join(re.escape(value) for value in sorted(ENTRIES, key=len, reverse=True))
    names = re.compile(r"(?<![\w/-])(" + entry_names + r")(?![\w/-])")
    private_paths = re.compile(r"(?<![\w-])(" + entry_names + r")[/\\]+(?:scripts|references|agents)(?:[/\\]|\b)")
    joined_paths = re.compile(r"[\"'](" + entry_names + r")[\"']\s*(?:/|,)\s*[\"'](?:scripts|references|agents)[\"']")
    for entry in ENTRIES:
        start = root / entry / "SKILL.md"
        visited, pending = set(), [(start, [start])]

        def report(path, chain, peer, reason):
            key = (entry, path, peer)
            if key not in reported:
                failures.append(" -> ".join(p.relative_to(root).as_posix() for p in chain) + ": " + reason)
                reported.add(key)

        while pending:
            path, chain = pending.pop()
            if path in visited:
                continue
            visited.add(path)
            text = path.read_text(encoding="utf-8-sig")
            owner = path.relative_to(root).parts[0]
            if path.suffix in {".md", ".yaml", ".yml"}:
                for match in names.finditer(text):
                    if match[1] != owner:
                        context = text[text.rfind("\n", 0, match.start()) + 1:text.find("\n", match.end()) if "\n" in text[match.end():] else len(text)]
                        # "research" is also an English noun; keep ordinary prose
                        # such as "User research showed..." out of the call graph.
                        explicit = re.search(r"[\u3400-\u9fff]|\$research\b|`research`|\b(?:call|invoke|use|run|route|delegate|reuse|start)\s+(?:the\s+)?research\b|\bresearch\s+(?:skill|entrypoint|entry|handles|manages|must|should)\b", context, re.I)
                        if match[1] == "research" and not explicit:
                            continue
                        line = text.count("\n", 0, match.start()) + 1
                        report(path, chain, match[1], f"line {line}: textual entry reference {match[1]}")
            for pattern in (private_paths, joined_paths):
                for match in pattern.finditer(text):
                    if match[1] != owner:
                        line = text.count("\n", 0, match.start()) + 1
                        report(path, chain, match[1], f"line {line}: private entry resource {match[0]}")
            if path.suffix in {".yaml", ".yml"}:
                try:
                    yaml.safe_load(text)
                except yaml.YAMLError as error:
                    report(path, chain, "metadata", "Invalid metadata: " + str(error))
                continue
            if path.suffix == ".py":
                for node in ast.walk(ast.parse(text, filename=str(path))):
                    modules = [alias.name for alias in node.names] if isinstance(node, ast.Import) else [node.module] if isinstance(node, ast.ImportFrom) and node.module else []
                    for module in modules:
                        package = module.split(".")[0]
                        if package in ENTRIES and package != owner:
                            report(path, chain, package, f"line {node.lineno}: private entry import {module}")
                        sibling = path.parent / (module.split(".")[0] + ".py")
                        if sibling.is_file():
                            pending.append((sibling, [*chain, sibling]))
                continue
            if path.name == "SKILL.md":
                for metadata in sorted((path.parent / "agents").glob("*.y*ml")):
                    pending.append((metadata, [*chain, metadata]))
            for href in links(text):
                parsed = urlsplit(href)
                if parsed.scheme or parsed.netloc:
                    continue
                target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
                if not target.is_relative_to(root):
                    continue
                parts = target.relative_to(root).parts
                if "runtime" in parts or "node_modules" in parts:
                    continue  # Installed third-party documentation is outside this contract.
                if parts[0] in ENTRIES and parts[0] != owner:
                    report(path, [*chain, target], parts[0], "Cross-entry resource reference")
                elif target.is_file() and target.suffix.lower() in {".md", ".py", ".yaml", ".yml"}:
                    pending.append((target, [*chain, target]))
    return failures


class SkillDependencyTests(unittest.TestCase):
    def test_repository_entries_have_no_direct_or_indirect_peer_dependencies(self):
        self.assertEqual(dependency_violations(ROOT), [])

    def test_entry_instructions_do_not_route_peers_by_name(self):
        for entry in ENTRIES:
            text = (ROOT / entry / "SKILL.md").read_text(encoding="utf8")
            for peer in set(ENTRIES) - {entry}:
                with self.subTest(entry=entry, peer=peer):
                    self.assertNotRegex(text, r"(?<![\w/-])" + re.escape(peer) + r"(?![\w/-])")

    def fixture(self):
        temporary = tempfile.TemporaryDirectory(prefix="skill-dependencies-")
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name).resolve()
        for entry in ENTRIES:
            self.write(root, entry + "/SKILL.md", "# Entry\n[common](../common/SKILL.md)\n")
        self.write(root, "common/SKILL.md", "# Support\n[draw](../draw/SKILL.md)\n")
        self.write(root, "draw/SKILL.md", "# Draw\n[common](../common/SKILL.md)\n")
        return root

    def write(self, root, relative, text):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf8")

    def test_shared_children_and_child_cycles_are_allowed(self):
        self.assertEqual(dependency_violations(self.fixture()), [])

    def test_reference_file_callback_to_peer_is_detected(self):
        root = self.fixture()
        self.write(root, "common/SKILL.md", "# Support\n[rules](references/rules.md)\n")
        self.write(root, "common/references/rules.md", "# Rules\n[commit](../../research-commit/SKILL.md)\n")
        failures = dependency_violations(root)
        self.assertEqual(len(failures), 3)
        self.assertTrue(all("common/references/rules.md -> research-commit/SKILL.md" in chain for chain in failures))

    def test_private_peer_resource_dependency_is_detected(self):
        root = self.fixture()
        self.write(root, "research/SKILL.md", "# Entry\n[analysis rules](../research-analysis/references/rules.md)\n")
        self.write(root, "research-analysis/references/rules.md", "# Private rules\n")
        self.assertEqual(len(dependency_violations(root)), 1)

    def test_plain_text_parent_reference_in_shared_child_is_detected(self):
        root = self.fixture()
        self.write(root, "common/SKILL.md", "# Support\n用户直接调用时复用 research 的计划建立步骤。\n")
        failures = dependency_violations(root)
        self.assertEqual(len(failures), 3)
        self.assertTrue(all("textual entry reference research" in value for value in failures))

    def test_peer_invocation_in_entry_metadata_is_detected(self):
        root = self.fixture()
        self.write(root, "research-analysis/agents/openai.yaml", 'interface:\n  default_prompt: "使用 $research-commit 提交结果。"\n')
        failures = dependency_violations(root)
        self.assertEqual(len(failures), 1)
        self.assertIn("agents/openai.yaml", failures[0])

    def test_parent_invocation_in_shared_child_metadata_is_detected(self):
        root = self.fixture()
        self.write(root, "common/agents/openai.yaml", 'interface:\n  default_prompt: "使用 $research 继续执行。"\n')
        self.assertEqual(len(dependency_violations(root)), 3)

    def test_private_script_paths_in_links_and_commands_are_detected(self):
        for text in ("[tool](../research/scripts/tool.py)", "python <skills_root>/research/scripts/tool.py"):
            with self.subTest(text=text):
                root = self.fixture()
                self.write(root, "common/SKILL.md", "# Support\n" + text + "\n")
                self.assertEqual(len(dependency_violations(root)), 3)

    def test_imported_helper_cannot_depend_on_private_entry_scripts(self):
        root = self.fixture()
        self.write(root, "common/SKILL.md", "# Support\n[tool](scripts/tool.py)\n")
        self.write(root, "common/scripts/tool.py", "import helper\n")
        self.write(root, "common/scripts/helper.py", 'from pathlib import Path\nSCRIPTS = Path(__file__).parents[2] / "research" / "scripts"\n')
        failures = dependency_violations(root)
        self.assertEqual(len(failures), 3)
        self.assertTrue(all("helper.py" in value for value in failures))

    def test_common_script_paths_and_own_entry_metadata_are_allowed(self):
        root = self.fixture()
        self.write(root, "common/SKILL.md", "# Support\n[tool](scripts/tool.py)\npython <skills_root>/research-common/scripts/tool.py\n")
        self.write(root, "common/scripts/tool.py", "import helper\n")
        self.write(root, "common/scripts/helper.py", "VALUE = 1\n")
        self.write(root, "research-analysis/agents/openai.yaml", 'interface:\n  default_prompt: "使用 $research-analysis 分析已有成果。"\n')
        self.assertEqual(dependency_violations(root), [])

    def test_python_package_import_from_a_peer_entry_is_detected(self):
        root = self.fixture()
        self.write(root, "common/SKILL.md", "# Support\n[tool](scripts/tool.py)\n")
        self.write(root, "common/scripts/tool.py", "from research.scripts import research_task\n")
        failures = dependency_violations(root)
        self.assertEqual(len(failures), 3)
        self.assertTrue(all("private entry import research.scripts" in value for value in failures))

    def test_ordinary_english_research_prose_is_not_an_entry_invocation(self):
        root = self.fixture()
        self.write(root, "common/SKILL.md", "# Support\nUser research showed a preference for simplicity.\nClean styles suit AI research notes.\n")
        self.assertEqual(dependency_violations(root), [])

    def test_english_parent_invocation_in_shared_child_is_detected(self):
        root = self.fixture()
        self.write(root, "common/SKILL.md", "# Support\nCall research to plan the report.\n")
        self.assertEqual(len(dependency_violations(root)), 3)


if __name__ == "__main__":
    unittest.main()
