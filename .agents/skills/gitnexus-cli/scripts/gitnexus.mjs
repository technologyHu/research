#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { existsSync, realpathSync } from 'node:fs';
import { mkdir, readFile, writeFile, rename, unlink, rmdir } from 'node:fs/promises';
import { homedir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import { gunzipSync } from 'node:zlib';

export const skillRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const runtimeRoot = path.join(skillRoot, 'runtime');
const hash = (data) => createHash('sha256').update(data).digest('hex');
const log = (message) => process.stderr.write(`[gitnexus bootstrap] ${message}\n`);

export function checkNode(version = process.versions.node) {
  const [major, minor] = version.split('.').map(Number);
  if (!((major === 22 && minor >= 18) || (major === 24 && minor >= 11) || major > 24)) {
    throw new Error('GitNexus requires Node.js 22.18+ (22.x), or 24.11+. Install a supported Node.js LTS release.');
  }
}

export function npmCommand() {
  const candidates = [
    process.env.npm_execpath,
    path.join(path.dirname(process.execPath), 'node_modules/npm/bin/npm-cli.js'),
    path.resolve(path.dirname(process.execPath), '../lib/node_modules/npm/bin/npm-cli.js'),
    '/usr/share/nodejs/npm/bin/npm-cli.js',
  ];
  for (const dir of (process.env.PATH || '').split(path.delimiter)) {
    for (const name of ['npm', 'npm.cmd']) {
      const executable = path.join(dir, name);
      if (!existsSync(executable)) continue;
      const resolved = realpathSync(executable);
      candidates.push(resolved.endsWith('npm-cli.js') ? resolved : null);
      candidates.push(path.join(path.dirname(resolved), 'node_modules/npm/bin/npm-cli.js'));
    }
  }
  const cli = candidates.find((candidate) => candidate && candidate.endsWith('npm-cli.js') && existsSync(candidate));
  if (!cli) throw new Error('npm-cli.js was not found. Install Node.js with npm, then retry the same skill command.');
  return [process.execPath, cli];
}

export async function run(command, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: options.cwd || process.cwd(),
      env: options.env || process.env,
      stdio: options.capture ? ['ignore', 'pipe', 'pipe'] : 'inherit',
      windowsHide: true,
    });
    let stdout = '', stderr = '';
    if (options.capture) {
      child.stdout.on('data', (chunk) => { stdout += chunk; });
      child.stderr.on('data', (chunk) => { stderr += chunk; });
    }
    const timer = options.timeout ? setTimeout(() => child.kill(), options.timeout) : null;
    child.on('error', reject);
    child.on('close', (code, signal) => {
      if (timer) clearTimeout(timer);
      if (code !== 0 && !options.allowFailure) {
        reject(new Error(`${path.basename(command)} failed (${signal || code}).${stderr ? `\n${stderr}` : ''}`));
      } else resolve({ code, stdout, stderr });
    });
  });
}

async function acquireLock() {
  const lockDir = path.join(runtimeRoot, '.bootstrap-lock');
  const ownerFile = path.join(lockDir, 'owner.json');
  const deadline = Date.now() + 10 * 60_000;
  while (true) {
    try {
      await mkdir(lockDir);
      await writeFile(ownerFile, JSON.stringify({ pid: process.pid, created: Date.now() }));
      return async () => {
        await unlink(ownerFile).catch(() => {});
        await rmdir(lockDir).catch(() => {});
      };
    } catch (error) {
      if (error.code !== 'EEXIST') throw error;
      try {
        const owner = JSON.parse(await readFile(ownerFile, 'utf8'));
        if (Number.isInteger(owner.pid) && owner.pid > 0) {
          try { process.kill(owner.pid, 0); }
          catch (probeError) {
            if (probeError.code === 'ESRCH') {
              await unlink(ownerFile).catch(() => {});
              await rmdir(lockDir).catch(() => {});
              continue;
            }
          }
        }
      } catch { /* Another process may still be writing its owner file. */ }
      if (Date.now() > deadline) throw new Error(`Timed out waiting for ${lockDir}. Check the bootstrap process before removing that lock.`);
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
  }
}

export async function installExtensions(manifest, { platform = `${process.platform}-${process.arch}`, home = homedir() } = {}) {
  const artifacts = manifest.artifacts.filter((item) => item.platform === platform);
  if (artifacts.length !== 2 || !artifacts.some((item) => item.extension === 'fts') || !artifacts.some((item) => item.extension === 'vector')) {
    throw new Error(`No verified FTS + VECTOR bundle for ${platform}. Supported: Windows x64, Linux x64/arm64, macOS x64/arm64.`);
  }
  let changed = false;
  for (const artifact of artifacts) {
    const packed = await readFile(path.join(skillRoot, artifact.file));
    if (hash(packed) !== artifact.gzipSha256) throw new Error(`Extension archive checksum mismatch: ${artifact.file}. Restore it from Git.`);
    const bytes = gunzipSync(packed);
    if (bytes.length !== artifact.size || hash(bytes) !== artifact.sha256) throw new Error(`Extension binary checksum mismatch: ${artifact.file}. Restore it from Git.`);
    const target = path.join(home, '.lbdb', 'extension', manifest.extensionVersion, artifact.upstreamPlatform, artifact.extension, `lib${artifact.extension}.lbug_extension`);
    let installed;
    try { installed = await readFile(target); } catch (error) { if (error.code !== 'ENOENT') throw error; }
    if (installed && hash(installed) === artifact.sha256) continue;
    await mkdir(path.dirname(target), { recursive: true });
    const temporary = `${target}.${process.pid}.tmp`;
    await writeFile(temporary, bytes);
    await rename(temporary, target);
    changed = true;
    log(`Installed verified ${artifact.extension} extension for ${platform}.`);
  }
  return changed;
}

export async function bootstrap({ forceProbe = false } = {}) {
  checkNode();
  const manifestBytes = await readFile(path.join(skillRoot, 'extensions.lock.json'));
  const manifest = JSON.parse(manifestBytes);
  const platform = `${process.platform}-${process.arch}`;
  if (!manifest.artifacts.some((artifact) => artifact.platform === platform)) throw new Error(`Unsupported extension platform: ${platform}`);
  await mkdir(runtimeRoot, { recursive: true });
  const release = await acquireLock();
  try {
    const installedPackage = path.join(runtimeRoot, 'node_modules/gitnexus/package.json');
    const lockBytes = await readFile(path.join(runtimeRoot, 'package-lock.json'));
    const packageBytes = await readFile(path.join(runtimeRoot, 'package.json'));
    const fingerprint = hash(Buffer.concat([manifestBytes, packageBytes, lockBytes, Buffer.from(`${platform}|${process.versions.modules}|${homedir()}`)]));
    const marker = path.join(runtimeRoot, `.ready-${hash(homedir()).slice(0, 12)}.json`);
    let ready = {};
    try { ready = JSON.parse(await readFile(marker, 'utf8')); } catch { /* First use. */ }
    let version;
    try { version = JSON.parse(await readFile(installedPackage, 'utf8')).version; } catch { /* Not installed. */ }
    if (version !== manifest.gitnexusVersion || ready.fingerprint !== fingerprint) {
      log(`Preparing pinned GitNexus ${manifest.gitnexusVersion}; first use downloads npm dependencies.`);
      const [node, npm] = npmCommand();
      const result = await run(node, [npm, 'ci', '--prefer-offline', '--no-audit', '--no-fund'], {
        cwd: runtimeRoot, capture: true,
        env: { ...process.env, ONNXRUNTIME_NODE_INSTALL: process.env.ONNXRUNTIME_NODE_INSTALL || 'skip' },
      });
      await writeFile(path.join(runtimeRoot, '.npm-install.log'), result.stdout + result.stderr);
    }
    const changed = await installExtensions(manifest);
    if (changed || forceProbe || ready.fingerprint !== fingerprint) {
      const probe = await run(process.execPath, [path.join(skillRoot, 'scripts/probe.mjs')], { capture: true, timeout: 60_000 });
      const report = JSON.parse(probe.stdout);
      await writeFile(marker, JSON.stringify({ fingerprint, report }, null, 2) + '\n');
      log(`FTS keyword query and VECTOR nearest-neighbor query passed (${report.platform}).`);
    }
    return path.join(runtimeRoot, 'node_modules/gitnexus/dist/cli/index.js');
  } finally { await release(); }
}

async function main() {
  const args = process.argv.slice(2);
  const verify = args[0] === '--verify-runtime';
  const cli = await bootstrap({ forceProbe: verify });
  if (verify) return;
  const env = { ...process.env, GITNEXUS_LBUG_EXTENSION_INSTALL: process.env.GITNEXUS_LBUG_EXTENSION_INSTALL || 'load-only' };
  const result = await run(process.execPath, [cli, ...args], { env, allowFailure: true });
  process.exitCode = result.code ?? 1;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => { console.error(`[gitnexus bootstrap] ${error.message}`); process.exitCode = 1; });
}
