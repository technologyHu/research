# Repository-local GitNexus runtime

Resolve the sibling `gitnexus-cli` skill directory from the location of this file. Its `scripts/gitnexus.mjs` is the only CLI/MCP entry point for this installation. Do not use a previous install under a maintainer-specific drive or home directory.

From the repository root:

```sh
node .agents/skills/gitnexus-cli/scripts/gitnexus.mjs doctor
```

When the working directory is a different project, derive the entry point's absolute path from this skill location, then run it with the target project as cwd or the explicit analyze path. Use it instead of `npx gitnexus`, a global binary, or a nonexistent `.gitnexus/run.cjs`.

The entry point automatically installs the locked npm dependencies on first use and installs/checksums bundled FTS and VECTOR extensions. `--verify-runtime` executes real FTS and vector nearest-neighbor queries. See [the shared README](../gitnexus-cli/README.md) for prerequisites, platform limits and fresh-clone verification.

For a new index requiring semantic search, run `analyze <target-path> --embeddings --skip-agents-md --skip-skills`. FTS is built by default. Existing indexes may need `embeddings`; inspect that command's help before running it. A loaded VECTOR extension alone does not create code embeddings. A first local embedding run downloads the default model; no personal API key is required on supported local platforms.

MCP is optional: launch the same entry point with `mcp`. Register it in the user's chosen client only when asked; do not assume MCP tools are already exposed. Without MCP, use the CLI query/context/trace/impact/cypher commands and their help. Bootstrap uses stderr, preserving MCP stdout.
