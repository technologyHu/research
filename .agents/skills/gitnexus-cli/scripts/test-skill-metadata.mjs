import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, writeFile, unlink, rmdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { patchPlanDescription } from './patch-skill-metadata.mjs';

async function fixture(t, source) {
  const root = await mkdtemp(path.join(tmpdir(), 'gitnexus metadata '));
  const skills = path.join(root, 'skills');
  const skill = path.join(skills, 'gitnexus-plan');
  const file = path.join(skill, 'SKILL.md');
  await mkdir(skill, { recursive: true });
  await writeFile(file, source, 'utf8');
  t.after(async () => {
    await unlink(file);
    await rmdir(skill);
    await rmdir(skills);
    await rmdir(root);
  });
  return { root, file };
}

test('repairs metadata without changing body examples or newline style', async (t) => {
  for (const newline of ['\n', '\r\n']) {
    const original = ['---', 'name: gitnexus-plan',
      'description: \'Plan with "docs/plans/<plan>.md".\'', '---', '',
      '# Plan', 'Keep the body example docs/plans/<plan>.md.', ''].join(newline);
    const { root, file } = await fixture(t, original);
    assert.equal(await patchPlanDescription(root), true);
    assert.equal(await readFile(file, 'utf8'), original.replace('docs/plans/<plan>.md', 'docs/plans/plan-file.md'));
    assert.equal(await patchPlanDescription(root), false);
  }
});

test('repeated initialization and valid upstream metadata are unchanged', async (t) => {
  const original = '---\nname: gitnexus-plan\ndescription: Plan a code change.\n---\nBody <plan>.\n';
  const { root, file } = await fixture(t, original);
  assert.equal(await patchPlanDescription(root), false);
  assert.equal(await patchPlanDescription(root), false);
  assert.equal(await readFile(file, 'utf8'), original);
});

test('rejects unknown metadata placeholders without modifying the file', async (t) => {
  const original = '---\nname: gitnexus-plan\ndescription: Plan <unknown> with docs/plans/<plan>.md.\n---\n';
  const { root, file } = await fixture(t, original);
  await assert.rejects(patchPlanDescription(root), /unsupported angle brackets/);
  assert.equal(await readFile(file, 'utf8'), original);
});

test('does not patch a description-like line in the body', async (t) => {
  const original = '---\nname: gitnexus-plan\n---\ndescription: docs/plans/<plan>.md\n';
  const { root, file } = await fixture(t, original);
  await assert.rejects(patchPlanDescription(root), /description is missing/);
  assert.equal(await readFile(file, 'utf8'), original);
});
