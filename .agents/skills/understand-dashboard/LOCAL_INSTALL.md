# Portable Understand Anything runtime

Before resolving plugin files, prepare the backend through the sibling `code-understanding` skill:

```sh
node <code-understanding-skill-dir>/scripts/preflight.mjs --target <project> --backend understand --prepare
```

Resolve `<code-understanding-skill-dir>` relative to this skill directory, not the current working directory or a maintainer home. Use the returned `backends[0].paths.pluginRoot` as `PLUGIN_ROOT`. The bundled Node scripts resolve that same portable location by default.
For running a Node helper with the plugin environment already set, use:

```sh
node <code-understanding-skill-dir>/scripts/preflight.mjs --target <project> --backend understand --run -- <script.mjs> <arguments>
```

Keep `UNDERSTAND_NO_WORKTREE_REDIRECT=1` when analyzing the user's current worktree, including when translating upstream Bash examples to PowerShell. Avoid redirecting the output to the main checkout.
The fixed source bundle, dependency preparation and supported runtimes are documented in [the shared runtime reference](../code-understanding/references/runtime.md). Do not rebuild a project graph merely to prepare the tool.

For the dashboard, use the direct Node/Vite entry described in the shared runtime reference instead of `pnpm dev`, especially on Windows paths containing spaces.
