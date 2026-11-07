#!/usr/bin/env node
import assert from 'node:assert/strict';
import { cp, mkdir, mkdtemp, readFile, readdir, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { checkNode, installExtensions, run, skillRoot } from './gitnexus.mjs';

checkNode('22.18.0');
checkNode('24.11.0');
assert.throws(() => checkNode('22.17.0'), /requires Node/);
assert.throws(() => checkNode('23.1.0'), /requires Node/);
const manifest = JSON.parse(await readFile(path.join(skillRoot, 'extensions.lock.json'), 'utf8'));
await assert.rejects(installExtensions(manifest, { platform: 'win32-arm64' }), /No verified/);

const temporary = await mkdtemp(path.join(tmpdir(), 'gitnexus clone test '));
const origin = path.join(temporary, 'origin');
const clone = path.join(temporary, 'fresh clone with spaces');
const skills = path.join(origin, '.agents/skills');
await mkdir(skills, { recursive: true });
for (const name of ['gitnexus-cli', 'gitnexus-guide', 'gitnexus-exploring']) {
  await cp(path.join(skillRoot, '..', name), path.join(skills, name), {
    recursive: true,
    filter: (source) => !/(?:^|[\\/])node_modules(?:[\\/]|$)|[\\/]\.ready-|[\\/]\.bootstrap-lock|[\\/]\.npm-install\.log/.test(source),
  });
}
await run('git', ['init', '--quiet'], { cwd: origin, capture: true });
await run('git', ['add', '.agents/skills'], { cwd: origin, capture: true });
await run('git', ['-c', 'user.name=Bootstrap Test', '-c', 'user.email=bootstrap-test@example.invalid', 'commit', '--quiet', '-m', 'Portable skill fixture'], { cwd: origin, capture: true });
await run('git', ['clone', '--quiet', '--no-hardlinks', origin, clone], { capture: true });
const clonedSkill = path.join(clone, '.agents/skills/gitnexus-cli');
const clonedEntry = path.join(clonedSkill, 'scripts/gitnexus.mjs');
const emptyHome = path.join(temporary, 'new user');
await mkdir(emptyHome);
const environment = { ...process.env, USERPROFILE: emptyHome, HOME: emptyHome, GITNEXUS_HOME: path.join(emptyHome, '.gitnexus') };
console.log('Fresh clone:', clone);
await run(process.execPath, [clonedEntry, '--verify-runtime'], { cwd: temporary, env: environment });
const doctor = await run(process.execPath, [clonedEntry, 'doctor'], { cwd: temporary, env: environment, capture: true });
assert.match(doctor.stdout, /Full-text search:\s+available/);
assert.match(doctor.stdout, /VECTOR extension:\s+available/);
assert.match(doctor.stdout, /Semantic support:.*VECTOR.*available|Semantic support:.*vector-index/i);
const markers = (await readdir(path.join(clonedSkill, 'runtime'))).filter((name) => name.startsWith('.ready-'));
assert.equal(markers.length, 1);
const marker = JSON.parse(await readFile(path.join(clonedSkill, 'runtime', markers[0]), 'utf8'));
assert.equal(marker.report.fullText, true);
assert.equal(marker.report.vector, true);

// Prove corrupted tracked assets fail closed rather than loading arbitrary bytes.
const artifact = manifest.artifacts.find((item) => item.platform === `${process.platform}-${process.arch}`);
const packed = path.join(clonedSkill, artifact.file);
const bytes = await readFile(packed);
bytes[bytes.length - 1] ^= 1;
await writeFile(packed, bytes);
const corrupt = await run(process.execPath, [clonedEntry, '--verify-runtime'], { cwd: temporary, env: environment, capture: true, allowFailure: true });
assert.notEqual(corrupt.code, 0);
assert.match(corrupt.stderr, /checksum mismatch/);
await writeFile(packed, await readFile(path.join(skillRoot, artifact.file)));

console.log(JSON.stringify({ freshClone: true, emptyUserHome: true, pathWithSpaces: true, ftsQuery: true, vectorQuery: true, corruptedAssetRejected: true, fixture: temporary }));
