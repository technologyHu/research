"""Forward old command and import paths to this skill without copying implementations."""

from pathlib import Path


def forward(namespace):
    target = Path(__file__).resolve().parent / Path(namespace["__file__"]).name
    # Keep the caller's module dictionary, including for file-based imports and
    # mocks, while resolving runtime resources beside the canonical source.
    namespace["__file__"] = str(target)
    exec(compile(target.read_bytes(), str(target), "exec"), namespace)
