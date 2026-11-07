"""Exercise the skill's Git procedures in disposable repositories, never the project."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
SKILLS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILLS / "research" / "scripts"))
from validate_report import validate  # noqa: E402


@dataclass(frozen=True)
class Attempt:
    start: str
    tree: str
    parents: tuple[str, ...]


class GitWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="research-commit-test-")
        self.base = Path(self.temporary.name).resolve()
        self.base.relative_to(Path(tempfile.gettempdir()).resolve())
        self.addCleanup(self.temporary.cleanup)
        self.repo = self.base / "repository with spaces"
        self.repo.mkdir()
        self.hooks = self.base / "hooks"
        self.hooks.mkdir()
        self.serial = 0
        self.environment = os.environ.copy()
        for key in tuple(self.environment):
            if key.startswith("GIT_"):
                self.environment.pop(key)
        self.environment.update({
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
        })
        self.git("init", "-q")
        self.write("baseline.txt", "base\n")
        self.git("add", "--", "baseline.txt")
        self.git("commit", "-q", "-m", "baseline")
        self.baseline = self.text("rev-parse", "HEAD")

    def git(self, *args, index=None, data=None, check=True):
        # All mutations are bound to this test's resolved temporary repository.
        self.repo.resolve().relative_to(self.base)
        env = self.environment.copy()
        if index is not None:
            env["GIT_INDEX_FILE"] = str(index)
        command = [
            "git", "--literal-pathspecs", "-c", "user.name=Skill Test",
            "-c", "user.email=skill-test@example.invalid",
            "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false",
            "-c", "core.fsmonitor=false", "-c", "core.splitIndex=false",
            "-c", f"core.hooksPath={self.hooks}", *args,
        ]
        result = subprocess.run(command, cwd=self.repo, env=env, input=data,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if check and result.returncode:
            self.fail(f"git {args}: {result.stderr.decode('utf-8', errors='replace')}")
        return result

    def text(self, *args, **kwargs):
        return self.git(*args, **kwargs).stdout.decode("utf-8").strip()

    def paths(self, *args, **kwargs):
        return {p.decode("utf-8") for p in self.git(*args, **kwargs).stdout.split(b"\0") if p}

    def write(self, relative, text):
        target = self.repo / relative
        target.resolve().relative_to(self.repo.resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")

    def original_index(self):
        path = Path(self.text("rev-parse", "--git-path", "index"))
        return (self.repo / path).read_bytes()

    def temporary_index(self):
        self.serial += 1
        return self.base / f"candidate-{self.serial}.index"

    def candidate(self, files, *, staged):
        """Follow the reference's temporary-index recipe, preserving index blob IDs."""
        index = self.temporary_index()
        self.git("read-tree", "HEAD", index=index)
        if staged:
            entries = self.git("ls-files", "--stage", "-z", "--", *files).stdout
            for entry in entries.split(b"\0"):
                if entry and entry.split(b"\t", 1)[0].split()[2] != b"0":
                    raise ValueError("Selected paths contain unresolved index stages")
            self.git("update-index", "--force-remove", "--", *files, index=index)
            if entries:
                self.git("update-index", "-z", "--index-info", index=index, data=entries)
        else:
            self.git("add", "--", *files, index=index)
        return index, self.text("write-tree", index=index)

    def attempt(self, tree, *, amend=False):
        start = self.text("rev-parse", "HEAD")
        parents = tuple(self.text("show", "-s", "--format=%P", start).split()) if amend else (start,)
        return Attempt(start, tree, parents)

    def recovery(self, attempt):
        current = self.text("rev-parse", "HEAD")
        if current == attempt.start:
            return "not-committed"
        actual_tree = self.text("rev-parse", "HEAD^{tree}")
        parents = tuple(self.text("show", "-s", "--format=%P", "HEAD").split())
        return "committed" if actual_tree == attempt.tree and parents == attempt.parents else "diverged"

    def snapshot(self, tree):
        """Read committed blobs, not worktree files, without executing snapshot code."""
        self.serial += 1
        target = self.base / f"snapshot-{self.serial}"
        target.mkdir()
        entries = self.git("ls-tree", "-r", "-z", tree).stdout.split(b"\0")
        for entry in entries:
            if not entry:
                continue
            meta, raw_path = entry.split(b"\t", 1)
            mode, kind, oid = meta.split()
            if mode not in {b"100644", b"100755"} or kind != b"blob":
                raise ValueError("Snapshot extraction requires regular blobs")
            path = target / raw_path.decode("utf-8")
            path.resolve().relative_to(target.resolve())
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(self.git("cat-file", "blob", oid.decode("ascii")).stdout)
        return target

    def full_commit(self, files, message):
        self.git("add", "--", *files)
        _, tree = self.candidate(files, staged=False)
        attempt = self.attempt(tree)
        self.git("commit", "-q", "--only", "-m", message, "--", *files)
        self.assertEqual(self.recovery(attempt), "committed")
        return self.text("rev-parse", "HEAD")

    def changed_in_head(self):
        return self.paths("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "HEAD")

    def test_literal_filenames_do_not_select_similar_files(self):
        chosen = "theme/paper/a/references/资料 [ab].md"
        others = ["theme/paper/a/references/资料 a.md", "theme/paper/a/references/资料 b.md"]
        for path in [chosen, *others]:
            self.write(path, "# Source\n")
        self.git("add", "--", chosen)
        self.assertEqual(self.paths("diff", "--cached", "--name-only", "-z"), {chosen})
        self.full_commit([chosen], "literal filename")
        self.assertEqual(self.changed_in_head(), {chosen})
        for path in others:
            self.assertTrue((self.repo / path).is_file())

    def test_two_reports_have_separate_commits_and_keep_unrelated_staging(self):
        reports = ["theme/paper/a/report.md", "theme/product/b/report.md"]
        for path in reports:
            self.write(path, "# Report\n")
        self.write("unrelated.txt", "user staged change\n")
        self.git("add", "--", *reports, "unrelated.txt")
        for path in reports:
            self.full_commit([path], path)
            self.assertEqual(self.changed_in_head(), {path})
        self.assertEqual(self.paths("diff", "--cached", "--name-only", "-z"), {"unrelated.txt"})
        self.assertEqual(self.text("rev-list", "--count", f"{self.baseline}..HEAD"), "2")

    def test_staged_only_preserves_unstaged_content_and_original_index(self):
        report = "theme/paper/a/report.md"
        self.write(report, "# Original\n")
        self.full_commit([report], "original")
        self.write(report, "# Staged version\n")
        self.write("other.txt", "other staged file\n")
        self.git("add", "--", report, "other.txt")
        self.write(report, "# Unstaged version\n")
        original = self.original_index()
        index, tree = self.candidate([report], staged=True)
        attempt = self.attempt(tree)
        self.git("commit", "-q", "-m", "staged report", index=index)
        self.assertEqual(self.recovery(attempt), "committed")
        self.assertEqual(self.text("show", f"HEAD:{report}"), "# Staged version")
        self.assertEqual((self.repo / report).read_text(encoding="utf-8"), "# Unstaged version\n")
        self.assertEqual(self.original_index(), original)
        self.assertEqual(self.paths("diff", "--cached", "--name-only", "-z"), {"other.txt"})
        self.assertEqual(self.paths("diff", "--name-only", "-z"), {report})

    def test_staged_new_report_excludes_other_staged_reports(self):
        chosen, other = "theme/paper/a/report.md", "theme/paper/b/report.md"
        self.write(chosen, "# Selected\n")
        self.write(other, "# Other\n")
        self.git("add", "--", chosen, other)
        index, tree = self.candidate([chosen], staged=True)
        self.assertTrue(validate(self.snapshot(tree) / "theme/paper/a")["valid"])
        self.git("commit", "-q", "-m", "selected only", index=index)
        self.assertEqual(self.changed_in_head(), {chosen})
        self.assertEqual(self.paths("diff", "--cached", "--name-only", "-z"), {other})

    def test_staged_delete_and_rename_keep_exact_versions(self):
        report = "theme/paper/a/report.md"
        old, new = "theme/paper/a/references/old.md", "theme/paper/a/references/new.md"
        self.write(report, "# Report\n[Source](references/old.md)\n")
        self.write(old, "# Source\n")
        self.full_commit([report, old], "old reference")
        (self.repo / old).unlink()
        self.write(new, "# Source\n")
        self.write(report, "# Report\n[Source](references/new.md)\n")
        self.git("add", "--", report, old, new)
        index, tree = self.candidate([report, old, new], staged=True)
        snapshot = self.snapshot(tree)
        self.assertFalse((snapshot / old).exists())
        self.assertTrue(validate(snapshot / "theme/paper/a")["valid"])
        self.git("commit", "-q", "-m", "renamed source", index=index)
        self.assertEqual(self.text("show", f"HEAD:{report}"), "# Report\n[Source](references/new.md)")

    def test_staged_amend_merges_revision_and_preserves_other_staging(self):
        report = "theme/paper/a/report.md"
        self.write(report, "# First\n")
        old_commit = self.full_commit([report], "report A")
        self.write(report, "# Staged revision\n")
        self.write("foreign.txt", "preserve\n")
        self.git("add", "--", report, "foreign.txt")
        self.write(report, "# Later unstaged revision\n")
        original = self.original_index()
        index, tree = self.candidate([report], staged=True)
        attempt = self.attempt(tree, amend=True)
        self.git("commit", "-q", "--amend", "--no-edit", index=index)
        self.assertEqual(self.recovery(attempt), "committed")
        self.assertNotEqual(self.text("rev-parse", "HEAD"), old_commit)
        self.assertEqual(self.text("rev-parse", "HEAD^"), self.baseline)
        self.assertEqual(self.text("rev-list", "--count", f"{self.baseline}..HEAD"), "1")
        self.assertEqual(self.text("show", f"HEAD:{report}"), "# Staged revision")
        self.assertEqual(self.original_index(), original)
        self.assertEqual((self.repo / report).read_text(encoding="utf-8"), "# Later unstaged revision\n")

    def test_candidate_validation_detects_worktree_only_reference(self):
        report, source = "theme/paper/a/report.md", "theme/paper/a/references/source.md"
        self.write(report, "# Report\n[Source](references/source.md)\n")
        self.write(source, "# Actual source\n")
        self.git("add", "--", report)
        self.assertTrue(validate(self.repo / "theme/paper/a")["valid"])
        _, tree = self.candidate([report], staged=True)
        result = validate(self.snapshot(tree) / "theme/paper/a")
        self.assertFalse(result["valid"])
        self.assertTrue(any("missing file" in error for error in result["errors"]))
        self.assertEqual(self.paths("diff", "--cached", "--name-only", "-z"), {report})
        self.git("add", "--", source)
        _, complete_tree = self.candidate([report, source], staged=True)
        self.assertTrue(validate(self.snapshot(complete_tree) / "theme/paper/a")["valid"])

    def test_shared_plan_is_committed_after_separate_reports(self):
        a, b, plan = "theme/paper/a/report.md", "theme/product/b/report.md", "theme/plan.md"
        for path in (a, b):
            self.write(path, "# Report\n")
        self.write(plan, "# Plan\n[A](paper/a/report.md)\n[B](product/b/report.md)\n")
        self.git("add", "--", a, b, plan)
        for path in (a, b):
            self.full_commit([path], path)
            self.assertEqual(self.changed_in_head(), {path})
        self.assertEqual(self.paths("diff", "--cached", "--name-only", "-z"), {plan})
        self.full_commit([plan], "shared plan")
        self.assertEqual(self.changed_in_head(), {plan})
        snapshot = self.snapshot(self.text("rev-parse", "HEAD^{tree}"))
        for path in (a, b):
            self.assertTrue((snapshot / path).is_file())

    def test_precommit_failure_does_not_create_commit_and_can_be_rechecked(self):
        report = "theme/paper/a/report.md"
        self.write(report, "# Report\n")
        self.git("add", "--", report)
        index, tree = self.candidate([report], staged=True)
        attempt = self.attempt(tree)
        hook = self.hooks / "pre-commit"
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8", newline="\n")
        hook.chmod(0o755)
        result = self.git("commit", "-q", "-m", "blocked", index=index, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.recovery(attempt), "not-committed")
        hook.unlink()  # Remove only the synthetic test hook after checking the refusal.
        self.assertEqual(self.text("write-tree", index=index), tree)
        self.git("commit", "-q", "-m", "after recheck", index=index)
        self.assertEqual(self.recovery(attempt), "committed")

    def test_postcommit_check_failure_is_recovered_without_duplicate_commit(self):
        report = "theme/paper/a/report.md"
        self.write(report, "# Report\n")
        self.git("add", "--", report)
        index, tree = self.candidate([report], staged=True)
        attempt = self.attempt(tree)
        with self.assertRaisesRegex(RuntimeError, "after commit"):
            self.git("commit", "-q", "-m", "report saved", index=index)
            raise RuntimeError("validation interrupted after commit")
        self.assertEqual(self.recovery(attempt), "committed")
        self.assertEqual(self.text("rev-list", "--count", f"{self.baseline}..HEAD"), "1")

    def test_concurrent_commit_is_not_treated_as_success_or_retried(self):
        report = "theme/paper/a/report.md"
        self.write(report, "# Report\n")
        self.git("add", "--", report)
        _, tree = self.candidate([report], staged=True)
        attempt = self.attempt(tree)
        self.write("foreign.txt", "concurrent\n")
        self.full_commit(["foreign.txt"], "concurrent commit")
        self.assertEqual(self.recovery(attempt), "diverged")
        self.assertEqual(self.paths("diff", "--cached", "--name-only", "-z"), {report})

    def test_hook_modified_tree_is_detected_after_commit(self):
        report = "theme/paper/a/report.md"
        self.write(report, "# Report\n")
        self.write("injected.txt", "hook addition\n")
        self.git("add", "--", report)
        index, tree = self.candidate([report], staged=True)
        attempt = self.attempt(tree)
        hook = self.hooks / "pre-commit"
        hook.write_text("#!/bin/sh\ngit --literal-pathspecs add -- injected.txt\n", encoding="utf-8", newline="\n")
        hook.chmod(0o755)
        self.git("commit", "-q", "-m", "hook changed candidate", index=index)
        self.assertEqual(self.recovery(attempt), "diverged")
        self.assertIn("injected.txt", self.changed_in_head())


if __name__ == "__main__":
    unittest.main(verbosity=2)
