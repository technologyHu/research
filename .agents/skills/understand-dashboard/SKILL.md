---
name: understand-dashboard
description: 打开已有 Understand Anything 知识图谱的交互式浏览界面。
metadata:
  argument-hint: "[project-path]"
---

## Workspace installation

Read [LOCAL_INSTALL.md](LOCAL_INSTALL.md) for this workspace runtime location before resolving plugin paths.


# /understand-dashboard

Start the Understand Anything dashboard to visualize the knowledge graph for the current project.

## Instructions

1. Determine the project directory and data directory:
   - If `$ARGUMENTS` contains a path, use that as the project directory
   - Otherwise, use the current working directory
   - Prefer the legacy `.understand-anything/` data directory when it exists, otherwise use `.ua/`

   Use the Bash tool to resolve:
   ```bash
   PROJECT_ARG="$ARGUMENTS"
   if [ -n "$PROJECT_ARG" ]; then
     PROJECT_DIR=$(cd "$PROJECT_ARG" 2>/dev/null && pwd -P)
   else
     PROJECT_DIR=$(pwd -P)
   fi

   if [ -z "$PROJECT_DIR" ] || [ ! -d "$PROJECT_DIR" ]; then
     echo "Error: Project directory not found: ${PROJECT_ARG:-$PWD}"
     exit 1
   fi

   if [ -d "$PROJECT_DIR/.understand-anything" ]; then
     UA_DIR="$PROJECT_DIR/.understand-anything"
   else
     UA_DIR="$PROJECT_DIR/.ua"
   fi
   ```

2. Check that `$UA_DIR/knowledge-graph.json` exists in the project directory. If not, tell the user:
   ```
   No knowledge graph found. Run /understand first to analyze this project.
   ```

   Use the Bash tool to check:
   ```bash
   if [ ! -f "$UA_DIR/knowledge-graph.json" ]; then
     echo "No knowledge graph found. Run /understand first to analyze this project."
     exit 1
   fi
   ```

3. Use the portable plugin prepared through [LOCAL_INSTALL.md](LOCAL_INSTALL.md), or reuse the caller's successful preparation result. Carry `backends[0].paths.pluginRoot` as `PLUGIN_ROOT`. The dashboard code is beneath that root; do not clear `PLUGIN_ROOT` or search global and home-directory installations.

   ```bash
   : "${PLUGIN_ROOT:?Use the pluginRoot returned by LOCAL_INSTALL.md preparation}"
   DASHBOARD_DIR="$PLUGIN_ROOT/packages/dashboard"
   if [ ! -d "$DASHBOARD_DIR" ]; then
     echo "Error: Prepared dashboard source is missing; check backend preparation."
     exit 1
   fi
   ```

4. **Fast path — try the prebuilt viewer first (no install, no build).** Each release ships a self-contained viewer tarball; run it pinned to the installed plugin version:
   ```bash
   : "${PLUGIN_ROOT:?Run step 3 first so PLUGIN_ROOT is set}"
   : "${PROJECT_DIR:?Run step 1 first so PROJECT_DIR is set}"
   PLUGIN_VERSION=$(node -p "require('$PLUGIN_ROOT/package.json').version")
   VIEWER_URL="https://github.com/Egonex-AI/Understand-Anything/releases/download/v${PLUGIN_VERSION}/understand-anything-viewer.tgz"
   npx --yes "$VIEWER_URL" "$PROJECT_DIR"
   ```
   Run this in the background. It prints the same `🔑  Dashboard URL` line as the dev server:
   - If the line appears, **skip steps 5-6** and continue at step 7.
   - If the process exits without printing it (no release asset for this version, or no network), fall back to steps 5-6.

5. Fallback: install dependencies and build if needed:
   ```bash
   : "${PLUGIN_ROOT:?Run step 3 first so PLUGIN_ROOT is set}"
   DASHBOARD_DIR="${DASHBOARD_DIR:-$PLUGIN_ROOT/packages/dashboard}"
   cd "$DASHBOARD_DIR" && (pnpm install --frozen-lockfile 2>/dev/null || pnpm install)
   ```
   Then ensure the core package is built (the dashboard depends on it):
   ```bash
   : "${PLUGIN_ROOT:?Run step 3 first so PLUGIN_ROOT is set}"
   cd "$PLUGIN_ROOT" && pnpm --filter @understand-anything/core build
   ```

6. Fallback: start the Vite dev server pointing at the project's knowledge graph:
   ```bash
   : "${PROJECT_DIR:?Run step 1 first so PROJECT_DIR is set}"
   : "${DASHBOARD_DIR:?Run step 5 first so DASHBOARD_DIR is set}"
   cd "$DASHBOARD_DIR" && GRAPH_DIR="$PROJECT_DIR" npx vite --host 127.0.0.1
   ```
   Run this in the background so the user can continue working.

7. **Capture the access token URL from the server output.** The server (viewer or Vite) prints a line like:
   ```
   🔑  Dashboard URL: http://127.0.0.1:<PORT>?token=<TOKEN>
   ```
   Extract the full URL including the `?token=` parameter. The token is required to access the knowledge graph data — without it the dashboard will show an "Access Token Required" gate.

8. Report to the user, including the full tokenized URL:
   ```
   Dashboard started at http://127.0.0.1:<PORT>?token=<TOKEN>
   Viewing: $UA_DIR/knowledge-graph.json

   The dashboard is running in the background. Press Ctrl+C in the terminal to stop it.
   ```
   **Important:** Always include the `?token=` parameter in the URL you share. If you omit it, the user will be blocked by the token gate and have to manually find the token in the terminal output.

## Notes

- The fast path (step 4) downloads a version-pinned, self-contained viewer from the GitHub release — nothing is installed into the plugin directory and no build runs
- The dashboard auto-opens in the default browser (both the viewer and Vite's `--open`)
- If port 5173 is already in use, the next available port is picked (both paths)
- In the fallback, the `GRAPH_DIR` environment variable tells the dev server where to find the knowledge graph
