import { existsSync, realpathSync } from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';

export function executable(name) {
  for (const dir of (process.env.PATH || '').split(path.delimiter)) {
    for (const suffix of process.platform === 'win32' ? ['.exe', ''] : ['']) {
      const candidate = path.join(dir, name + suffix);
      if (existsSync(candidate)) return candidate;
    }
  }
  return null;
}
export function npmCli() {
  const candidates = [process.env.npm_execpath,
    path.join(path.dirname(process.execPath), 'node_modules/npm/bin/npm-cli.js'),
    path.resolve(path.dirname(process.execPath), '../lib/node_modules/npm/bin/npm-cli.js'),
    '/usr/share/nodejs/npm/bin/npm-cli.js'];
  for (const dir of (process.env.PATH || '').split(path.delimiter)) {
    for (const name of ['npm', 'npm.cmd']) {
      const candidate = path.join(dir, name);
      if (!existsSync(candidate)) continue;
      const real = realpathSync(candidate);
      if (real.endsWith('npm-cli.js')) candidates.push(real);
      candidates.push(path.join(path.dirname(real), 'node_modules/npm/bin/npm-cli.js'));
    }
  }
  const result = candidates.find((p) => p && p.endsWith('npm-cli.js') && existsSync(p));
  if (!result) throw new Error('npm was not found; install Node.js with npm before preparing this backend.');
  return result;
}
export async function run(command, args, { cwd = process.cwd(), env = process.env, capture = true, timeout = 0 } = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { cwd, env, windowsHide: true, stdio: capture ? ['ignore', 'pipe', 'pipe'] : 'inherit' });
    let stdout = '', stderr = '';
    if (capture) {
      child.stdout.on('data', (data) => { stdout += data; });
      child.stderr.on('data', (data) => { stderr += data; });
    }
    const timer = timeout ? setTimeout(() => child.kill(), timeout) : null;
    child.on('error', reject);
    child.on('close', (code, signal) => {
      if (timer) clearTimeout(timer);
      if (code !== 0) reject(new Error(`${path.basename(command)} failed (${signal || code}).\n${stderr || stdout}`));
      else resolve({ stdout, stderr });
    });
  });
}
