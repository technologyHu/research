#!/usr/bin/env node
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, realpath } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { skillRoot } from './runtime-paths.mjs';
import { run } from './process.mjs';

const fixture = await mkdtemp(path.join(tmpdir(), 'code-understanding external '));
const caller = path.join(fixture, 'caller repo');
const target = path.join(fixture, 'outside project');
for (const [directory, body] of [[caller, 'caller-only'], [target, 'target-only']]) {
  await mkdir(directory);
  await writeFile(path.join(directory, 'sample.py'), `VALUE = '${body}'\n`);
  await run('git', ['init', '--quiet'], { cwd: directory });
  await run('git', ['add', '.'], { cwd: directory });
  await run('git', ['-c', 'user.name=Target Test', '-c', 'user.email=target-test@example.invalid', 'commit', '--quiet', '-m', body], { cwd: directory });
}
const entry = path.join(skillRoot, 'scripts/preflight.mjs');
const inspect = async (cwd, args = []) => JSON.parse((await run(process.execPath, [entry, ...args, '--backend', 'source'], { cwd })).stdout).target;
const callerState = await inspect(caller);
const expected = await realpath(target);
for (const value of [target, path.relative(caller, target)]) {
  const state = await inspect(caller, ['--target', value]);
  assert.equal(state.selectedPath, expected);
  assert.equal(state.projectPath, expected);
  assert.equal(state.repository.root, expected);
  assert.notEqual(state.repository.head, callerState.repository.head);
  assert.ok(state.indexes.every((index) => index.root === expected));
}
assert.equal((await inspect(target)).selectedPath, expected);
assert.equal((await inspect(caller, ['--target', path.join(target, 'sample.py')])).scope, 'file');
await assert.rejects(inspect(caller, ['--target', path.join(fixture, 'missing project')]), /ENOENT/);
assert.equal(existsSync(path.join(target, '.agents')), false);
assert.equal(existsSync(path.join(target, '.gitnexus')), false);
assert.equal(existsSync(path.join(target, '.ua')), false);
assert.equal(existsSync(path.join(target, 'graphify-out')), false);
console.log(JSON.stringify({ absoluteTarget: true, relativeTarget: true, cwdDefault: true, distinctGitRepository: true, missingTargetRejected: true, targetNotModified: true }));
