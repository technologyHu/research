#!/usr/bin/env node
import assert from 'node:assert/strict';
import { cp, mkdir, mkdtemp, readFile, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { inspectTarget, parseArgs } from './preflight.mjs';
import { skillRoot, skillsRoot } from './runtime-paths.mjs';
import { run } from './process.mjs';

assert.equal(parseArgs([]).backend, 'source');
assert.throws(() => parseArgs(['--backend', 'all', '--run', 'status']), /one concrete backend/);
assert.throws(() => parseArgs(['--target']), /needs a value/);
const temporary = await mkdtemp(path.join(tmpdir(), 'code understanding test '));
const project = path.join(temporary, 'sample project');
await mkdir(project);
await writeFile(path.join(project, 'a.txt'), 'baseline-a');
await writeFile(path.join(project, 'b.txt'), 'baseline-b');
await writeFile(path.join(project, 'auth.py'), 'def validate_token(token):\n    return token == "valid"\n\ndef login(token):\n    return validate_token(token)\n');
await run('git', ['init', '--quiet'], { cwd: project });
await run('git', ['add', '.'], { cwd: project });
await run('git', ['-c', 'user.name=Skill Test', '-c', 'user.email=skill-test@example.invalid', 'commit', '--quiet', '-m', 'Fixture'], { cwd: project });
assert.equal((await inspectTarget(project)).repository.dirty, false);
await writeFile(path.join(project, 'a.txt'), 'a');
await writeFile(path.join(project, 'b.txt'), 'bc');
const before = await inspectTarget(project);
await writeFile(path.join(project, 'a.txt'), 'ab');
await writeFile(path.join(project, 'b.txt'), 'c');
const after = await inspectTarget(project);
assert.equal(after.repository.head, before.repository.head);
assert.notEqual(after.repository.dirtyFingerprint, before.repository.dirtyFingerprint, 'Dirty code changes under the same HEAD must change the evidence token.');
assert.equal(after.repository.fingerprintComplete, true);
assert.equal((await inspectTarget(path.join(project, 'auth.py'))).scope, 'file');
const worktree = path.join(temporary, 'separate worktree');
await run('git', ['worktree', 'add', '--quiet', '-b', 'skill-fixture', worktree], { cwd: project });
const worktreeState = await inspectTarget(worktree);
assert.equal(worktreeState.selectedPath, worktreeState.repository.root);
assert.equal(worktreeState.repository.isWorktree, true);
await mkdir(path.join(project, '.ua'));
await writeFile(path.join(project, '.ua/knowledge-graph.json'), '{}');
const indexState = await inspectTarget(project);
assert.equal(indexState.indexes[0].understand, true);
assert.equal(indexState.indexes[0].freshness, 'backend-check-required');

// Create and actually clone a repository containing only distributable skill files.
const origin = path.join(temporary, 'origin');
const sourceSkills = path.join(origin, '.agents/skills');
await mkdir(sourceSkills, { recursive: true });
const names = ['code-understanding', 'graphify', 'gitnexus-cli', 'gitnexus-guide', 'gitnexus-exploring', 'understand', 'understand-chat', 'understand-dashboard', 'understand-diff', 'understand-domain', 'understand-explain', 'understand-onboard'];
for (const name of names) {
  await cp(path.join(skillsRoot, name), path.join(sourceSkills, name), {
    recursive: true,
    filter: (source) => !/(?:^|[\\/])(?:node_modules|\.runtime|pnpm-package-lock-work)(?:[\\/]|$)|[\\/]\.ready-|[\\/]\.bootstrap-lock|[\\/]\.npm-install\.log/.test(source),
  });
}
await run('git', ['init', '--quiet'], { cwd: origin });
await run('git', ['add', '.agents/skills'], { cwd: origin });
await run('git', ['-c', 'user.name=Skill Test', '-c', 'user.email=skill-test@example.invalid', 'commit', '--quiet', '-m', 'Distributable skill fixture'], { cwd: origin });
const clone = path.join(temporary, 'fresh clone with spaces');
await run('git', ['clone', '--quiet', '--no-hardlinks', origin, clone]);
const clonedSkill = path.join(clone, '.agents/skills/code-understanding');
const entry = path.join(clonedSkill, 'scripts/preflight.mjs');
const home = path.join(temporary, 'isolated home');
await mkdir(home);
const env = { ...process.env, HOME: home, USERPROFILE: home, GITNEXUS_HOME: path.join(home, '.gitnexus'), PLUGIN_ROOT: '' };
console.log('Fresh clone:', clone);
const command = async (args) => run(process.execPath, [entry, '--target', project, ...args], { cwd: temporary, env });
assert.equal(existsSync(path.join(clonedSkill, '.runtime')), false);
await command(['--backend', 'all']);
assert.equal(existsSync(path.join(clonedSkill, '.runtime')), false, 'A plain preflight must not create or install runtimes.');

const bundle = path.join(clonedSkill, 'vendor/understand-plugin.json.gz');
const original = await readFile(bundle), corrupted = Buffer.from(original);
corrupted[corrupted.length - 1] ^= 1;
await writeFile(bundle, corrupted);
await assert.rejects(command(['--backend', 'understand', '--prepare']), /checksum mismatch/);
await writeFile(bundle, original);
for (const backend of ['graphify', 'understand', 'gitnexus']) {
  console.log('Preparing cloned backend:', backend);
  const result = JSON.parse((await command(['--backend', backend, '--prepare'])).stdout);
  assert.equal(result.backends[0].status, 'ready');
  for (const p of Object.values(result.backends[0].paths)) {
    assert.ok(path.resolve(p).startsWith(path.resolve(clone)), `Runtime path escaped the fresh clone: ${p}`);
  }
}
const version = await command(['--backend', 'graphify', '--run', '--', '--version']);
assert.match(version.stdout, /graphify 0\.9\.103/);
const doctor = await command(['--backend', 'gitnexus', '--run', '--', 'doctor']);
assert.match(doctor.stdout, /Full-text search:\s+available/);
assert.match(doctor.stdout, /VECTOR extension:\s+available/);
const environment = await command(['--backend', 'understand', '--run', '--', '-e', 'console.log(JSON.stringify({root:process.env.PLUGIN_ROOT,worktree:process.env.UNDERSTAND_NO_WORKTREE_REDIRECT}))']);
const values = JSON.parse(environment.stdout);
assert.ok(values.root.startsWith(clone));
assert.equal(values.worktree, '1');

// Invoke the copied upstream helpers directly: their fallback must resolve this clone.
const uaSkill = path.join(clone, '.agents/skills/understand');
const scan = path.join(temporary, 'scan.json');
await run(process.execPath, [path.join(uaSkill, 'scan-project.mjs'), project, scan, '--exclude-analysis-data'], { env });
const scanned = JSON.parse(await readFile(scan, 'utf8'));
const input = path.join(temporary, 'extract-input.json'), output = path.join(temporary, 'extract-output.json');
await writeFile(input, JSON.stringify({ projectRoot: project, batchFiles: scanned.files.filter((file) => file.path === 'auth.py'), batchImportData: {} }));
await run(process.execPath, [path.join(uaSkill, 'extract-structure.mjs'), input, output], { env });
const extracted = JSON.parse(await readFile(output, 'utf8'));
assert.equal(extracted.scriptCompleted, true);
assert.deepEqual(new Set(extracted.results[0].functions.map((fn) => fn.name)), new Set(['validate_token', 'login']));
assert.ok(extracted.results[0].callGraph.some((edge) => edge.caller === 'login' && edge.callee === 'validate_token'));
assert.equal(existsSync(path.join(project, '.gitnexus')), false, 'Runtime preparation must not index the target.');
assert.equal(existsSync(path.join(project, 'graphify-out')), false, 'Runtime preparation must not build a graph.');
console.log(JSON.stringify({ readOnlyCheck: true, sameHeadDirtyChange: true, worktreeIdentity: true, freshClone: true, isolatedHome: true, allBackends: true, sourceBundleIntegrity: true, upstreamPythonCallExtraction: true, fixture: temporary }));
