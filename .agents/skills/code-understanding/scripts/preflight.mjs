#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { readFile, readlink, realpath, stat, lstat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { backendPaths } from './runtime-paths.mjs';
import { backendState, prepareBackend } from './prepare-backends.mjs';
import { run } from './process.mjs';

export function parseArgs(args) {
  const result = { target: process.cwd(), backend: 'source', prepare: false, run: null, help: false };
  for (let index = 0; index < args.length; index++) {
    const argument = args[index];
    if (argument === '--help' || argument === '-h') result.help = true;
    else if (argument === '--prepare') result.prepare = true;
    else if (argument === '--run') {
      result.run = args.slice(index + 1);
      if (result.run[0] === '--') result.run.shift();
      if (!result.run.length) throw new Error('--run needs a backend command after it.');
      break;
    } else if (argument === '--target' || argument === '--backend') {
      const value = args[++index];
      if (!value || value.startsWith('--')) throw new Error(`${argument} needs a value.`);
      result[argument.slice(2)] = value;
    } else throw new Error(`Unknown option: ${argument}`);
  }
  if (!['source', 'gitnexus', 'understand', 'graphify', 'all'].includes(result.backend)) throw new Error(`Unknown backend: ${result.backend}`);
  if (result.run && ['source', 'all'].includes(result.backend)) throw new Error('--run needs one concrete backend.');
  return result;
}
function git(cwd, args) {
  const result = spawnSync('git', ['-C', cwd, ...args], { encoding: 'utf8', windowsHide: true, timeout: 15_000, maxBuffer: 8 * 1024 * 1024, env: { ...process.env, GIT_OPTIONAL_LOCKS: '0' } });
  return result.status === 0 ? result.stdout : null;
}
export async function inspectTarget(requested) {
  const selectedPath = await realpath(path.resolve(requested));
  const info = await stat(selectedPath);
  const projectPath = info.isDirectory() ? selectedPath : path.dirname(selectedPath);
  const gitRootRaw = git(projectPath, ['rev-parse', '--show-toplevel']);
  let repository = null;
  if (gitRootRaw) {
    const root = await realpath(gitRootRaw.trim());
    const head = git(root, ['rev-parse', '--verify', 'HEAD'])?.trim() || null;
    const branch = git(root, ['symbolic-ref', '--short', '-q', 'HEAD'])?.trim() || null;
    const gitDir = git(root, ['rev-parse', '--absolute-git-dir'])?.trim();
    const commonDir = git(root, ['rev-parse', '--path-format=absolute', '--git-common-dir'])?.trim();
    const status = git(root, ['status', '--porcelain=v1', '-z', '--untracked-files=all']);
    const changes = [], warnings = [];
    const digest = createHash('sha256').update(head || 'unborn').update(status ?? 'status-unavailable');
    let complete = status !== null, budget = 32 * 1024 * 1024;
    if (status !== null) {
      const records = status.split('\0');
      for (let index = 0; index < records.length; index++) {
        const record = records[index];
        if (!record) continue;
        const code = record.slice(0, 2), file = record.slice(3);
        changes.push({ status: code, path: file });
        if (/[RC]/.test(code)) index++;
        try {
          const candidate = path.resolve(root, file);
          const relative = path.relative(root, candidate);
          if (relative === '..' || relative.startsWith('..' + path.sep) || path.isAbsolute(relative)) { complete = false; continue; }
          const metadata = await lstat(candidate);
          if (metadata.isSymbolicLink()) { digest.update(await readlink(candidate)); continue; }
          if (metadata.isFile() && metadata.size <= 4 * 1024 * 1024 && metadata.size <= budget) {
            digest.update(createHash('sha256').update(await readFile(candidate)).digest()); budget -= metadata.size;
          } else if (metadata.isFile()) { complete = false; digest.update(`${metadata.size}/${metadata.mtimeMs}`); }
        } catch (error) { if (error.code !== 'ENOENT') complete = false; }
      }
    } else warnings.push('Git status could not be read; version freshness is unknown.');
    if (!complete) warnings.push('Dirty-content digest is incomplete; inspect changes before reusing cached conclusions.');
    repository = { root, head, branch, isWorktree: Boolean(gitDir && commonDir && path.resolve(gitDir) !== path.resolve(commonDir)), dirty: changes.length > 0, changeCount: changes.length, changes: changes.slice(0, 25), dirtyFingerprint: digest.digest('hex'), fingerprintComplete: complete, warnings };
  }
  const roots = [...new Set([projectPath, repository?.root].filter(Boolean))];
  const indexes = roots.map((root) => {
    const ua = existsSync(path.join(root, '.understand-anything')) ? '.understand-anything' : '.ua';
    return { root, gitnexus: existsSync(path.join(root, '.gitnexus/meta.json')), understand: existsSync(path.join(root, ua, 'knowledge-graph.json')), graphify: existsSync(path.join(root, 'graphify-out/graph.json')), freshness: 'backend-check-required' };
  });
  return { selectedPath, projectPath, scope: info.isDirectory() ? 'directory' : 'file', repository, indexes, note: 'Index presence does not prove freshness or complete coverage. External GitNexus storage/registry must be checked through GitNexus.' };
}
async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    console.log('Usage: node preflight.mjs [--target <directory-or-file>] [--backend source|gitnexus|understand|graphify|all] [--prepare] [--run -- <backend arguments>]\nChecks are read-only. --prepare initializes only the selected runtime. --run prepares and launches one backend, without indexing unless its arguments request it.');
    return;
  }
  const target = await inspectTarget(options.target);
  const selected = options.backend === 'all' ? ['gitnexus', 'understand', 'graphify'] : [options.backend];
  const backends = [];
  for (const backend of selected) backends.push(await ((options.prepare || options.run) ? prepareBackend(backend) : backendState(backend)));
  if (options.run) {
    const paths = backendPaths(options.backend);
    if (options.backend === 'graphify') await run(paths.entry, options.run, { cwd: target.projectPath, env: { ...process.env, PYTHONUTF8: '1' }, capture: false });
    else if (options.backend === 'gitnexus') await run(process.execPath, [paths.entry, ...options.run], { cwd: target.projectPath, capture: false });
    else await run(process.execPath, options.run, { cwd: target.projectPath, env: { ...process.env, PLUGIN_ROOT: paths.pluginRoot, UNDERSTAND_NO_WORKTREE_REDIRECT: '1' }, capture: false });
  } else console.log(JSON.stringify({ target, backends }, null, 2));
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => { console.error(`[code-understanding] ${error.message}`); process.exitCode = 1; });
}
