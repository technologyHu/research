import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const skillRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const skillsRoot = path.dirname(skillRoot);
export const runtimeRoot = path.join(skillRoot, '.runtime');
export function backendLock() {
  return JSON.parse(readFileSync(path.join(skillRoot, 'backends.lock.json'), 'utf8'));
}
export function understandPluginRoot() {
  const lock = backendLock().understand;
  return path.join(runtimeRoot, `understand-${lock.commit.slice(0, 12)}`, 'plugin');
}
export function backendPaths(backend) {
  if (backend === 'source') return {};
  if (backend === 'gitnexus') return { entry: path.join(skillsRoot, 'gitnexus-cli/scripts/gitnexus.mjs') };
  if (backend === 'understand') return {
    pluginRoot: understandPluginRoot(),
    core: path.join(understandPluginRoot(), 'packages/core/dist/index.js'),
    scripts: path.join(skillsRoot, 'understand'),
  };
  if (backend === 'graphify') {
    const root = path.join(runtimeRoot, `graphify-${backendLock().graphify.version}`);
    return {
      root,
      python: path.join(root, process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python'),
      entry: path.join(root, process.platform === 'win32' ? 'Scripts/graphify.exe' : 'bin/graphify'),
    };
  }
  throw new Error(`Unknown backend: ${backend}`);
}
