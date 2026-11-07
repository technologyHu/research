import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { selectRepositories, validateRecord, recordFingerprint } from '../repository-selection.mjs';

// Fictional, offline evidence fixtures. verified means accepted fixture facts;
// these tests do not claim to verify real repositories or remote authorities.
const evidence = (kind, note = 'Accepted fixture fact') => ({
  kind, url: 'https://example.org/source', locator: 'section or file:1-12', note, verified: true,
});
const component = (role = 'core', question = 'method') => ({
  role, paths: [`src/${role}.py`], question_ids: [question], evidence: [evidence('source_code')],
});
function candidate(id = 'official', kind = 'official') {
  return {
    id, url: `https://example.org/${id}`, access: 'readable',
    authority: { kind, maintainer: 'Fixture team', evidence: [evidence(kind === 'official' ? 'paper' : 'reproduction_report')] },
    relevance: { status: 'matched', evidence: [evidence('paper')] },
    version: { requested: 'paper-v1', status: 'matched', ref: 'v1', commit: 'a'.repeat(40), evidence: [evidence('tag_mapping')] },
    components: [component()], runtime: { status: 'not_run' }, stars: 0,
  };
}
function record(candidates = [candidate()]) {
  return {
    schema_version: 1,
    request: { object: 'Fictional Method', version: 'paper-v1', questions: [{ id: 'method', roles: ['core'] }], specified_ids: [] },
    search: { checked_at: '2026-11-06', official_entry_checked: true, code_hosts_checked: true, complete: true },
    candidates,
  };
}
const ids = (result) => result.decision.selected.map((entry) => entry.candidate_id);
const reasons = (result, id) => result.decision.assessments.find((entry) => entry.candidate_id === id).reasons;

test('user-specified third-party code wins over an unrequested official repository', () => {
  const input = record([candidate(), candidate('provided', 'other')]);
  input.request.specified_ids = ['provided'];
  const result = selectRepositories(input);
  assert.deepEqual(ids(result), ['provided']);
  assert.equal(result.decision.status, 'selected');
  assert.equal(result.decision.selected[0].authority, 'other');
  assert.ok(reasons(result, 'official').includes('not_user_specified'));
});

test('an inaccessible specified repository is not silently replaced', () => {
  const provided = candidate('provided', 'other');
  provided.access = 'blocked';
  const input = record([candidate(), provided]);
  input.request.specified_ids = ['provided'];
  const result = selectRepositories(input);
  assert.deepEqual(ids(result), []);
  assert.equal(result.decision.status, 'unavailable');
});

test('specified wrong-version code leaves a gap instead of substituting another repo', () => {
  const provided = candidate('provided');
  provided.version.status = 'mismatch';
  const input = record([provided, candidate('alternative')]);
  input.request.specified_ids = ['provided'];
  assert.equal(selectRepositories(input).decision.status, 'specified_uncovered');
});

test('matching reproduction is selected over a wrong-version official main branch', () => {
  const official = candidate();
  official.version.status = 'mismatch';
  official.version.ref = 'main';
  const result = selectRepositories(record([official, candidate('repro', 'reproduction')]));
  assert.deepEqual(ids(result), ['repro']);
  assert.equal(result.decision.selected[0].version.ref, 'v1');
  assert.ok(reasons(result, 'official').includes('version_mismatch'));
});

test('version mapping evidence and a frozen commit are required', () => {
  for (const missing of ['mapping', 'pin', 'scope']) {
    const input = record();
    if (missing === 'mapping') input.candidates[0].version.evidence = [];
    if (missing === 'pin') delete input.candidates[0].version.commit;
    if (missing === 'scope') input.candidates[0].version.requested = 'paper-v2';
    const result = selectRepositories(input);
    assert.equal(result.decision.status, 'unverified', missing);
    assert.deepEqual(ids(result), []);
  }
});

test('matching official code has priority over a more popular reproduction', () => {
  const reproduction = candidate('repro', 'reproduction');
  reproduction.stars = 100000;
  assert.deepEqual(ids(selectRepositories(record([reproduction, candidate()]))), ['official']);
});

test('a trusted zero-star reproduction is eligible', () => {
  const result = selectRepositories(record([candidate('repro', 'reproduction')]));
  assert.equal(result.decision.status, 'selected');
  assert.deepEqual(ids(result), ['repro']);
});

test('a high-star unrelated project is rejected', () => {
  const unrelated = candidate('same-name');
  unrelated.relevance.status = 'unrelated';
  unrelated.stars = 1000000;
  const result = selectRepositories(record([unrelated]));
  assert.equal(result.decision.status, 'not_found');
  assert.deepEqual(ids(result), []);
  assert.ok(reasons(result, 'same-name').includes('unrelated'));
});

test('README self-declaration alone does not establish official identity', () => {
  const input = record();
  input.candidates[0].authority.evidence = [evidence('readme')];
  assert.equal(selectRepositories(input).decision.status, 'unverified');
});

test('an empty official repo does not block a credible reproduction', () => {
  const official = candidate();
  official.components = [];
  const result = selectRepositories(record([official, candidate('repro', 'reproduction')]));
  assert.deepEqual(ids(result), ['repro']);
  assert.ok(reasons(result, 'official').includes('no_implementation'));
});

test('a confirmed empty repository without any commit is not an unresolved version candidate', () => {
  const empty = candidate();
  empty.components = [];
  empty.version.status = 'unverified';
  empty.version.evidence = [];
  delete empty.version.commit;
  const input = record([empty]);
  assert.equal(selectRepositories(input).decision.status, 'not_found');
  input.request.specified_ids = ['official'];
  assert.equal(selectRepositories(input).decision.status, 'specified_uncovered');
  empty.access = 'blocked';
  assert.equal(selectRepositories(input).decision.status, 'unavailable');
});

test('a reproduction needs identifiable maintenance and credible reproduction evidence', () => {
  for (const missing of ['maintainer', 'report']) {
    const repro = candidate('repro', 'reproduction');
    if (missing === 'maintainer') delete repro.authority.maintainer;
    if (missing === 'report') repro.authority.evidence = [evidence('readme')];
    assert.equal(selectRepositories(record([repro])).decision.status, 'unverified', missing);
  }
});

test('SDK wrappers do not satisfy a core implementation question', () => {
  const sdk = candidate('sdk');
  sdk.components = [component('sdk')];
  const result = selectRepositories(record([sdk]));
  assert.equal(result.decision.status, 'not_found');
  assert.ok(reasons(result, 'sdk').includes('outside_question_scope'));
  assert.deepEqual(result.decision.gaps.map(({ question_id, role }) => ({ question_id, role })), [{ question_id: 'method', role: 'core' }]);
});

test('multiple official repositories can cover distinct research questions', () => {
  const evaluation = candidate('evaluation');
  evaluation.components = [component('evaluation', 'quality')];
  const input = record([candidate(), evaluation]);
  input.request.questions.push({ id: 'quality', roles: ['evaluation'] });
  const result = selectRepositories(input);
  assert.deepEqual(ids(result), ['official', 'evaluation']);
  assert.equal(result.decision.status, 'selected');
  assert.deepEqual(result.decision.selected[1].assignments, [{ question_id: 'quality', role: 'evaluation', candidate_id: 'evaluation' }]);
});

test('one question may require training and inference from different repositories', () => {
  const training = candidate('training'), inference = candidate('inference');
  training.components = [component('training')];
  inference.components = [component('inference')];
  const input = record([training, inference]);
  input.request.questions[0].roles = ['training', 'inference'];
  const result = selectRepositories(input);
  assert.equal(result.decision.status, 'selected');
  assert.deepEqual(ids(result), ['training', 'inference']);
  assert.equal(result.decision.gaps.length, 0);
});

test('partial coverage preserves the missing roles and can still be analyzed', () => {
  const input = record();
  input.request.questions.push({ id: 'quality', roles: ['evaluation'] });
  const result = selectRepositories(input);
  assert.equal(result.decision.status, 'partial');
  assert.deepEqual(ids(result), ['official']);
  assert.deepEqual(result.decision.gaps, [{ question_id: 'quality', role: 'evaluation', candidate_id: null }]);
});

test('missing weights/data/environment do not disqualify readable implementation', () => {
  const input = record();
  input.candidates[0].runtime = { status: 'blocked', missing: ['weights', 'dataset', 'GPU environment'] };
  const result = selectRepositories(input);
  assert.equal(result.decision.status, 'selected');
  assert.deepEqual(result.decision.selected[0].runtime, input.candidates[0].runtime);
});

test('selection does not turn an unexecuted project into a verified runtime', () => {
  const result = selectRepositories(record());
  assert.equal(result.decision.selected[0].runtime.status, 'not_run');
  const input = record();
  input.candidates[0].runtime = { status: 'verified', evidence: [evidence('readme')] };
  assert.throws(() => selectRepositories(input), /execution evidence/);
  input.candidates[0].runtime.evidence = [evidence('execution')];
  assert.equal(selectRepositories(input).decision.selected[0].runtime.status, 'verified');
});

test('incomplete discovery cannot claim that no implementation was found', () => {
  for (const flag of ['complete', 'official_entry_checked', 'code_hosts_checked']) {
    const input = record([]);
    input.search[flag] = false;
    assert.equal(selectRepositories(input).decision.status, 'search_incomplete', flag);
  }
  assert.equal(selectRepositories(record([])).decision.status, 'not_found');
});

test('access failures and uncertainty remain distinct from completed negative searches', () => {
  for (const access of ['blocked', 'missing', 'unverified']) {
    const input = record();
    input.candidates[0].access = access;
    assert.equal(selectRepositories(input).decision.status, access === 'unverified' ? 'unverified' : 'unavailable');
  }
});

test('user-specified local non-Git snapshots can be frozen without a commit', () => {
  const local = candidate('local', 'other');
  local.url = 'file:///D:/external/project';
  delete local.version.commit;
  local.version.snapshot_sha256 = 'b'.repeat(64);
  const input = record([local]);
  input.request.specified_ids = ['local'];
  assert.equal(selectRepositories(input).decision.status, 'selected');
});

test('identical recorded scope and evidence can be reused, independently of JSON key order', () => {
  const input = record(), previous = selectRepositories(input);
  const reordered = Object.fromEntries(Object.entries(input).reverse());
  assert.equal(recordFingerprint(reordered), recordFingerprint(input));
  assert.equal(selectRepositories(reordered, previous).decision.reuse.allowed, true);
});

test('changed commit, research version, question scope or identity evidence invalidates reuse', () => {
  const previous = selectRepositories(record());
  for (const change of ['commit', 'version', 'question', 'evidence']) {
    const input = record();
    if (change === 'commit') input.candidates[0].version.commit = 'b'.repeat(40);
    if (change === 'version') input.request.version = input.candidates[0].version.requested = 'paper-v2';
    if (change === 'question') input.request.questions.push({ id: 'extra', roles: ['evaluation'] });
    if (change === 'evidence') input.candidates[0].authority.evidence[0].note = 'Updated provenance';
    assert.equal(selectRepositories(input, previous).decision.reuse.allowed, false, change);
  }
});

test('latest/refresh requests always recheck and negative results are not durable cache', () => {
  const previous = selectRepositories(record());
  for (const flag of ['latest', 'refresh']) {
    const input = record();
    input.request[flag] = true;
    assert.equal(selectRepositories(input, previous).decision.reuse.allowed, false);
  }
  const negative = selectRepositories(record([]));
  assert.equal(selectRepositories(negative, negative).decision.reuse.allowed, false);
});

test('popularity changes alone do not change selection or invalidate reuse', () => {
  const input = record(), previous = selectRepositories(input);
  input.candidates[0].stars = 100000;
  assert.equal(selectRepositories(input, previous).decision.reuse.allowed, true);
  assert.deepEqual(ids(selectRepositories(input, previous)), ['official']);
});

test('a stale or tampered previous fingerprint cannot authorize reuse', () => {
  const previous = selectRepositories(record());
  previous.candidates[0].version.commit = 'b'.repeat(40);
  assert.equal(selectRepositories(record(), previous).decision.reuse.allowed, false);
});

test('malformed records fail explicitly rather than returning a negative search result', () => {
  const mutations = [
    (input) => { input.candidates.push(structuredClone(input.candidates[0])); },
    (input) => { input.request.questions[0].roles.push('core'); },
    (input) => { input.search.checked_at = '2026-02-30'; },
    (input) => { input.request.specified_ids = ['unrecorded']; },
    (input) => { input.candidates[0].components[0].paths = ['../outside.py']; },
    (input) => { input.candidates[0].authority.evidence[0].verified = 'yes'; },
  ];
  for (const mutate of mutations) {
    const input = record();
    mutate(input);
    assert.throws(() => validateRecord(input));
  }
});

test('CLI persists a decision record, reloads it, and rejects invalid input', async () => {
  const directory = await mkdtemp(path.join(tmpdir(), 'repository selection '));
  const cli = fileURLToPath(new URL('../repository-selection.mjs', import.meta.url));
  const input = path.join(directory, 'input.json'), output = path.join(directory, 'nested', 'decision.json');
  const invoke = (args) => spawnSync(process.execPath, [cli, ...args], { encoding: 'utf8', windowsHide: true });
  try {
    await writeFile(input, JSON.stringify(record()));
    const first = invoke(['--input', input, '--output', output]);
    assert.equal(first.status, 0, first.stderr);
    const saved = JSON.parse(await readFile(output, 'utf8'));
    assert.deepEqual(ids(saved), ['official']);
    const repeated = invoke(['--input', input, '--previous', output, '--output', output]);
    assert.equal(repeated.status, 0, repeated.stderr);
    assert.equal(JSON.parse(repeated.stdout).decision.reuse.allowed, true);
    await writeFile(input, JSON.stringify(record([])));
    const negative = invoke(['--input', input]);
    assert.equal(negative.status, 0, negative.stderr);
    assert.equal(JSON.parse(negative.stdout).decision.status, 'not_found');
    await writeFile(input, '{"schema_version":1}');
    const invalid = invoke(['--input', input]);
    assert.equal(invalid.status, 1);
    assert.equal(JSON.parse(invalid.stderr).valid, false);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
