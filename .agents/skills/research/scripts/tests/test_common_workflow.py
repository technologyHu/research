"""Retain the old unittest discovery command while keeping tests with the common tools."""

from pathlib import Path
import unittest


def load_tests(loader, _tests, _pattern):
    directory = Path(__file__).resolve().parents[3] / "research-common/scripts/tests"
    return loader.discover(str(directory), pattern="test_*.py", top_level_dir=str(directory))


if __name__ == "__main__":
    unittest.main()
