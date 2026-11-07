# Portable Graphify runtime

Prepare Graphify through the sibling `code-understanding` skill. Resolve that skill directory from this file, then run:

If the caller already supplied a successful preparation result, reuse its runtime paths and skip this preparation step.

```sh
node <code-understanding-skill-dir>/scripts/preflight.mjs --target <project> --backend graphify --prepare
```

Use the returned `backends[0].paths.python` as `PYTHON` in the upstream numbered pipeline and `backends[0].paths.entry` for CLI commands. This replaces the upstream global-install/upgrade step; do not run a second installer after the pinned runtime has been prepared.
Alternatively run a CLI command through the portable launcher:

```sh
node <code-understanding-skill-dir>/scripts/preflight.mjs --target <project> --backend graphify --run -- query "<question>"
```

The runtime version and all core dependencies are hash-locked. Extra PDF/media/cloud capabilities are not automatically installed. See [runtime details](../code-understanding/references/runtime.md).

When called by code-understanding, keep its bound target, snapshot, scope and output location. Resolve the existing-graph fast path against the supplied absolute `GRAPHIFY_OUT` (otherwise the target's default output), after checking source freshness and coverage. In a research task, generated graph/report/HTML files are task scratch artifacts; the caller returns source evidence to the current research task instead of treating them as a separate research deliverable. Adapt literal `graphify-out` paths in upstream commands to that same output directory.
