import { createHash } from 'node:crypto';
import { existsSync } from 'node:fs';
import { mkdir, readFile, writeFile, unlink, rmdir, chmod } from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { gunzipSync } from 'node:zlib';
import { backendLock, backendPaths, runtimeRoot, skillRoot } from './runtime-paths.mjs';
import { executable, npmCli, run } from './process.mjs';

const hash = (data) => createHash('sha256').update(data).digest('hex');
const log = (message) => process.stderr.write(`[code-understanding] ${message}\n`);
const marker = (backend) => path.join(runtimeRoot, `${backend}.ready.json`);
async function fingerprint(backend) {
  const lock = backendLock()[backend];
  const files = backend === 'graphify' ? [lock.requirements] : ['references/pnpm.package.json', 'references/pnpm.package-lock.json'];
  return hash(Buffer.concat([Buffer.from(JSON.stringify(lock)), ...await Promise.all(files.map((f) => readFile(path.join(skillRoot, f)))), Buffer.from(`${process.platform}/${process.arch}/${process.versions.modules}`)]));
}
export async function backendState(backend) {
  const paths = backendPaths(backend);
  if (backend === 'source') return { backend, status: 'ready', paths };
  if (backend === 'gitnexus') return { backend, status: existsSync(paths.entry) ? 'entry-available' : 'missing-skill', paths, note: 'The GitNexus entry checks/prepares its own native runtime when invoked.' };
  let saved;
  try { saved = JSON.parse(await readFile(marker(backend), 'utf8')); } catch { /* Not prepared. */ }
  const artifact = backend === 'graphify' ? paths.entry : paths.core;
  const ready = existsSync(artifact) && saved?.fingerprint === await fingerprint(backend);
  return { backend, status: ready ? 'ready' : 'setup-required', paths,
    ...(backend === 'understand' ? { environment: { PLUGIN_ROOT: paths.pluginRoot, UNDERSTAND_NO_WORKTREE_REDIRECT: '1' } } : {}) };
}
async function withLock(backend, action) {
  await mkdir(runtimeRoot, { recursive: true });
  const dir = path.join(runtimeRoot, `${backend}.lock`), owner = path.join(dir, 'owner.json');
  const deadline = Date.now() + 10 * 60_000;
  while (true) {
    try {
      await mkdir(dir);
      await writeFile(owner, JSON.stringify({ pid: process.pid }));
      break;
    } catch (error) {
      if (error.code !== 'EEXIST') throw error;
      try {
        const { pid } = JSON.parse(await readFile(owner, 'utf8'));
        if (Number.isInteger(pid) && pid > 0) {
          try { process.kill(pid, 0); }
          catch (probe) {
            if (probe.code === 'ESRCH') { await unlink(owner); await rmdir(dir); continue; }
          }
        }
      } catch { /* Lock owner may be writing. */ }
      if (Date.now() > deadline) throw new Error(`Timed out waiting for ${dir}. Inspect its owner before removing the lock.`);
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
  }
  try { return await action(); }
  finally { await unlink(owner).catch(() => {}); await rmdir(dir).catch(() => {}); }
}
async function prepareGraphify() {
  const paths = backendPaths('graphify'), uv = executable('uv');
  if (!existsSync(paths.python)) {
    log('Creating the isolated Graphify Python environment.');
    if (uv) await run(uv, ['venv', paths.root, '--python', '>=3.10']);
    else {
      const candidates = process.platform === 'win32' ? ['python', 'python3'] : ['python3', 'python'];
      let python;
      for (const candidate of candidates) {
        const command = executable(candidate);
        if (!command) continue;
        try {
          const result = await run(command, ['-c', 'import sys; assert sys.version_info >= (3,10); print(sys.executable)'], { timeout: 10_000 });
          if (result.stdout.trim()) { python = command; break; }
        } catch { /* Try another interpreter. */ }
      }
      if (!python) throw new Error('Graphify needs Python 3.10+ (venv/pip) or uv. Install one, then repeat the same command.');
      await run(python, ['-m', 'venv', paths.root]);
    }
  }
  log('Installing Graphify from the hashed cross-platform dependency lock.');
  const requirements = path.join(skillRoot, backendLock().graphify.requirements);
  if (uv) await run(uv, ['pip', 'sync', '--python', paths.python, '--require-hashes', requirements]);
  else await run(paths.python, ['-m', 'pip', 'install', '--require-hashes', '-r', requirements]);
  const result = await run(paths.entry, ['--version'], { env: { ...process.env, PYTHONUTF8: '1' } });
  if (!result.stdout.includes(backendLock().graphify.version)) throw new Error(`Unexpected Graphify version: ${result.stdout}`);
}
async function preparePnpm() {
  const root = path.join(runtimeRoot, 'pnpm');
  const expected = backendLock().understand.pnpmVersion;
  const packageFile = path.join(root, 'node_modules/pnpm/package.json');
  let pkg;
  try { pkg = JSON.parse(await readFile(packageFile, 'utf8')); } catch { /* First use. */ }
  if (pkg?.version !== expected) {
    await mkdir(root, { recursive: true });
    await writeFile(path.join(root, 'package.json'), await readFile(path.join(skillRoot, 'references/pnpm.package.json')));
    await writeFile(path.join(root, 'package-lock.json'), await readFile(path.join(skillRoot, 'references/pnpm.package-lock.json')));
    log(`Installing the pinned pnpm ${expected} runtime.`);
    await run(process.execPath, [npmCli(), 'ci', '--prefer-offline', '--no-audit', '--no-fund'], { cwd: root });
    pkg = JSON.parse(await readFile(packageFile, 'utf8'));
  }
  const entry = path.resolve(root, 'node_modules/pnpm', typeof pkg.bin === 'string' ? pkg.bin : pkg.bin.pnpm);
  if (!existsSync(entry)) throw new Error('The pinned pnpm package has no runnable entry point.');
  return entry;
}
async function extractUnderstand() {
  const config = backendLock().understand, { pluginRoot } = backendPaths('understand');
  const stamp = path.join(pluginRoot, '.source-ready.json');
  const packed = await readFile(path.join(skillRoot, config.bundle));
  if (hash(packed) !== config.archiveSha256) throw new Error('Understand Anything source bundle checksum mismatch; restore the tracked bundle from Git.');
  const raw = gunzipSync(packed);
  if (hash(raw) !== config.contentSha256) throw new Error('Understand Anything source content checksum mismatch.');
  try { if (JSON.parse(await readFile(stamp, 'utf8')).sha256 === config.contentSha256) return; } catch { /* Extract below. */ }
  const source = JSON.parse(raw);
  if (source.format !== 1 || source.files.length !== config.fileCount) throw new Error('Invalid Understand Anything source bundle format.');
  log(`Extracting pinned Understand Anything ${config.commit.slice(0, 12)} sources.`);
  for (const file of source.files) {
    const parts = file.path.split('/');
    if (path.isAbsolute(file.path) || /[\\:\0]/.test(file.path) || parts.some((part) => !part || part === '.' || part === '..')) throw new Error(`Unsafe bundle path: ${file.path}`);
    const destination = path.join(pluginRoot, ...parts);
    await mkdir(path.dirname(destination), { recursive: true });
    await writeFile(destination, Buffer.from(file.data, 'base64'));
    if (process.platform !== 'win32') await chmod(destination, file.mode & 0o777);
  }
  await writeFile(stamp, JSON.stringify({ sha256: config.contentSha256 }));
}
async function prepareUnderstand() {
  if (Number(process.versions.node.split('.')[0]) < 22) throw new Error('Understand Anything requires Node.js 22+; use a supported Node.js LTS release.');
  await extractUnderstand();
  const pnpm = await preparePnpm(), { pluginRoot, core } = backendPaths('understand');
  log('Installing the locked Understand Anything workspace dependencies and building core.');
  const env = { ...process.env, CI: '1' };
  // The plugin loads web-tree-sitter and packaged WASM grammars. Native
  // node-gyp lifecycle builds are unnecessary for that analysis path, and pnpm's
  // Windows lifecycle shell is unreliable under long, space-containing paths.
  const install = await run(process.execPath, [pnpm, 'install', '--frozen-lockfile', '--ignore-scripts'], { cwd: pluginRoot, env });
  const coreRoot = path.join(pluginRoot, 'packages/core');
  const tsc = path.join(coreRoot, 'node_modules/typescript/bin/tsc');
  const build = await run(process.execPath, [tsc, '--project', path.join(coreRoot, 'tsconfig.json')], { cwd: coreRoot, env });
  await writeFile(path.join(runtimeRoot, 'understand-install.log'), install.stdout + install.stderr + build.stdout + build.stderr);
  await run(process.execPath, ['--input-type=module', '-e', "const core = await import(process.argv[1]); if(typeof core.TreeSitterPlugin !== 'function') process.exit(1)", pathToFileURL(core).href]);
}
export async function prepareBackend(backend) {
  if (backend === 'source') return backendState(backend);
  if (backend === 'gitnexus') {
    const paths = backendPaths(backend);
    if (!existsSync(paths.entry)) throw new Error('The sibling gitnexus-cli skill is missing; install its portable runtime entry.');
    await run(process.execPath, [paths.entry, '--verify-runtime']);
    return { backend, status: 'ready', paths };
  }
  return withLock(backend, async () => {
    if ((await backendState(backend)).status !== 'ready') {
      if (backend === 'graphify') await prepareGraphify();
      else if (backend === 'understand') await prepareUnderstand();
      else throw new Error(`Unknown backend: ${backend}`);
      await writeFile(marker(backend), JSON.stringify({ fingerprint: await fingerprint(backend) }));
    }
    return backendState(backend);
  });
}
