#!/usr/bin/env node
// Offline policy checks over facts collected by the researching agent. This
// module does not browse, authenticate repository owners, clone, or run code.
import { createHash } from 'node:crypto';
import { readFile, writeFile, mkdir, rename } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const nonempty = (value) => typeof value === 'string' && value.trim().length > 0;
const requireThat = (condition, message) => { if (!condition) throw new Error(message); };
const sha = (value) => createHash('sha256').update(value).digest('hex');
const canonical = (value) => JSON.stringify(value, (_, entry) => entry && !Array.isArray(entry) && typeof entry === 'object'
  ? Object.fromEntries(Object.entries(entry).sort(([left], [right]) => left < right ? -1 : left > right ? 1 : 0)) : entry);
const validUrl = (value) => {
  try { return ['http:', 'https:', 'file:'].includes(new URL(value).protocol); } catch { return false; }
};
const officialKinds = new Set(['paper', 'official_page', 'author_profile']);
const reproductionKinds = new Set(['reproduction_report', 'independent_evaluation', 'author_endorsement']);
const mappingKinds = new Set(['tag_mapping', 'paper', 'official_page', 'reproduction_report']);
const verifiedEvidence = (evidence, kinds) => evidence.some((entry) => entry.verified === true && kinds.has(entry.kind));

function checkEvidence(evidence, where) {
  requireThat(Array.isArray(evidence), `${where} must be an evidence array.`);
  for (const entry of evidence) {
    requireThat(entry && nonempty(entry.kind) && validUrl(entry.url) && nonempty(entry.locator) && nonempty(entry.note)
      && typeof entry.verified === 'boolean', `${where} needs kind, URL, locator, note and a verified boolean.`);
  }
}

export function validateRecord(input) {
  requireThat(input?.schema_version === 1, 'Repository record schema_version must be 1.');
  const { request, search, candidates } = input;
  requireThat(request && nonempty(request.object), 'request.object is required.');
  requireThat(request.version === null || nonempty(request.version), 'request.version must be a string or explicit null.');
  for (const flag of ['latest', 'refresh']) if (flag in request) requireThat(typeof request[flag] === 'boolean', `request.${flag} must be boolean.`);
  requireThat(Array.isArray(request.questions) && request.questions.length > 0, 'request.questions must not be empty.');
  const questionIds = new Set();
  for (const question of request.questions) {
    requireThat(nonempty(question.id) && !questionIds.has(question.id), 'Question IDs must be unique nonempty strings.');
    questionIds.add(question.id);
    requireThat(Array.isArray(question.roles) && question.roles.length > 0 && question.roles.every(nonempty)
      && new Set(question.roles).size === question.roles.length, `${question.id}: roles must be a nonempty list without duplicates.`);
  }
  requireThat(Array.isArray(request.specified_ids) && request.specified_ids.every(nonempty)
    && new Set(request.specified_ids).size === request.specified_ids.length, 'request.specified_ids must be a list of unique candidate IDs (empty for discovery).');
  requireThat(search && /^\d{4}-\d{2}-\d{2}$/.test(search.checked_at)
    && !Number.isNaN(Date.parse(search.checked_at)) && new Date(search.checked_at).toISOString().startsWith(search.checked_at), 'search.checked_at must be a real ISO date.');
  for (const flag of ['official_entry_checked', 'code_hosts_checked', 'complete']) requireThat(typeof search[flag] === 'boolean', `search.${flag} must be boolean.`);
  requireThat(Array.isArray(candidates), 'candidates must be an array.');
  const ids = new Set();
  for (const candidate of candidates) {
    requireThat(candidate && nonempty(candidate.id) && !ids.has(candidate.id) && validUrl(candidate.url), 'Candidates need a unique ID and a repository URL or local file URI.');
    ids.add(candidate.id);
    requireThat(['readable', 'blocked', 'missing', 'unverified'].includes(candidate.access), `${candidate.id}: invalid access state.`);
    requireThat(['official', 'reproduction', 'other', 'unverified'].includes(candidate.authority?.kind), `${candidate.id}: invalid authority kind.`);
    checkEvidence(candidate.authority.evidence, `${candidate.id}.authority.evidence`);
    requireThat(['matched', 'unrelated', 'unverified'].includes(candidate.relevance?.status), `${candidate.id}: invalid relevance state.`);
    checkEvidence(candidate.relevance.evidence, `${candidate.id}.relevance.evidence`);
    requireThat(['matched', 'mismatch', 'unverified'].includes(candidate.version?.status), `${candidate.id}: invalid version state.`);
    requireThat(candidate.version.requested === null || nonempty(candidate.version.requested), `${candidate.id}: record the research version in version.requested.`);
    checkEvidence(candidate.version.evidence, `${candidate.id}.version.evidence`);
    requireThat(Array.isArray(candidate.components), `${candidate.id}.components must be an array (empty for an empty repository).`);
    for (const component of candidate.components) {
      requireThat(nonempty(component.role) && Array.isArray(component.paths) && component.paths.every(nonempty), `${candidate.id}: component role and relative paths are required.`);
      requireThat(component.paths.every((p) => !p.startsWith('/') && !/[\\:\0]/.test(p) && !p.split('/').includes('..')), `${candidate.id}: component paths must stay within the repository.`);
      requireThat(Array.isArray(component.question_ids) && component.question_ids.every(nonempty), `${candidate.id}: component question_ids are required.`);
      checkEvidence(component.evidence, `${candidate.id}.components.evidence`);
    }
    if (candidate.runtime) {
      requireThat(['not_run', 'blocked', 'verified'].includes(candidate.runtime.status), `${candidate.id}: invalid runtime status.`);
      requireThat(!candidate.runtime.missing || (Array.isArray(candidate.runtime.missing) && candidate.runtime.missing.every(nonempty)), `${candidate.id}: runtime.missing must be a string list.`);
      if (candidate.runtime.status === 'verified') {
        checkEvidence(candidate.runtime.evidence, `${candidate.id}.runtime.evidence`);
        requireThat(verifiedEvidence(candidate.runtime.evidence, new Set(['execution'])), `${candidate.id}: a verified runtime needs recorded execution evidence.`);
      }
    }
  }
  requireThat(request.specified_ids.every((id) => ids.has(id)), 'Every specified repository must have a candidate record, including inaccessible ones.');
  return input;
}

export function recordFingerprint(input) {
  // Popularity is auxiliary: a new star count must not invalidate a frozen
  // source/version decision. All actual identity, code and mapping facts do.
  const candidates = input.candidates.map(({ stars, forks, downloads, ...candidate }) => candidate);
  return sha(canonical({ schema_version: input.schema_version, request: input.request, search: input.search, candidates }));
}

function assess(candidate, request) {
  const specified = request.specified_ids.includes(candidate.id);
  const excluded = request.specified_ids.length > 0 && !specified;
  const reasons = [];
  if (excluded) reasons.push('not_user_specified');
  if (candidate.access !== 'readable') reasons.push(`access_${candidate.access}`);
  if (candidate.relevance.status !== 'matched' || !candidate.relevance.evidence.some((entry) => entry.verified)) {
    reasons.push(candidate.relevance.status === 'unrelated' ? 'unrelated' : 'relevance_unverified');
  }
  if (!specified) {
    const { kind, evidence } = candidate.authority;
    if (kind === 'official') {
      if (!verifiedEvidence(evidence, officialKinds)) reasons.push('official_identity_unverified');
    } else if (kind === 'reproduction') {
      if (!nonempty(candidate.authority.maintainer) || !verifiedEvidence(evidence, reproductionKinds)) reasons.push('reproduction_basis_unverified');
    } else reasons.push('authority_unverified');
  }
  const version = candidate.version;
  if (version.requested !== request.version) reasons.push('version_scope_changed');
  if (version.status !== 'matched') reasons.push(version.status === 'mismatch' ? 'version_mismatch' : 'version_unverified');
  if (!/^(?:[0-9a-f]{40}|[0-9a-f]{64})$/i.test(version.commit || '') && !/^[0-9a-f]{64}$/i.test(version.snapshot_sha256 || '')) reasons.push('source_not_pinned');
  if (request.version !== null && !verifiedEvidence(version.evidence, mappingKinds)) reasons.push('version_mapping_unverified');
  const components = candidate.components.filter((component) => component.paths.length > 0
    && verifiedEvidence(component.evidence, new Set(['source_code'])));
  if (components.length === 0) reasons.push(candidate.components.length === 0 ? 'no_implementation' : 'code_unverified');
  const slots = [];
  for (const question of request.questions) for (const role of question.roles) {
    if (components.some((component) => component.question_ids.includes(question.id) && (role === 'any' || role === component.role))) slots.push({ question_id: question.id, role });
  }
  if (slots.length === 0 && components.length > 0) reasons.push('outside_question_scope');
  return { candidate_id: candidate.id, via: specified ? 'user' : 'discovery', eligible: reasons.length === 0, reasons,
    usable_slots: reasons.length === 0 ? slots : [], runtime: candidate.runtime || { status: 'not_run' } };
}

function reuseDecision(input, decision, previous) {
  if (input.request.latest || input.request.refresh) return { allowed: false, reason: 'latest_or_refresh_requires_recheck' };
  if (!['selected', 'partial'].includes(decision.status)) return { allowed: false, reason: 'negative_results_are_not_durable_cache' };
  if (!previous?.decision) return { allowed: false, reason: 'no_previous_decision' };
  try { validateRecord(previous); } catch { return { allowed: false, reason: 'invalid_previous_record' }; }
  if (previous.decision.fingerprint !== recordFingerprint(previous) || previous.decision.fingerprint !== decision.fingerprint) return { allowed: false, reason: 'request_or_repository_facts_changed' };
  if (!['selected', 'partial'].includes(previous.decision.status)) return { allowed: false, reason: 'previous_result_not_reusable' };
  return { allowed: true, reason: 'same_recorded_scope_versions_and_evidence' };
}

export function selectRepositories(record, previous = null) {
  validateRecord(record);
  const { request, candidates, search } = record;
  const assessments = candidates.map((candidate) => assess(candidate, request));
  const lookup = new Map(candidates.map((candidate) => [candidate.id, candidate]));
  const rank = (assessment) => request.specified_ids.length ? request.specified_ids.indexOf(assessment.candidate_id)
    : lookup.get(assessment.candidate_id).authority.kind === 'official' ? 0 : 1;
  const eligible = assessments.filter((entry) => entry.eligible).sort((a, b) => rank(a) - rank(b)
    || b.usable_slots.length - a.usable_slots.length || candidates.findIndex((c) => c.id === a.candidate_id) - candidates.findIndex((c) => c.id === b.candidate_id));
  const assignments = request.questions.flatMap((question) => question.roles.map((role) => ({ question_id: question.id, role,
    candidate_id: eligible.find((entry) => entry.usable_slots.some((slot) => slot.question_id === question.id && slot.role === role))?.candidate_id || null })));
  const used = new Set(assignments.map((assignment) => assignment.candidate_id).filter(Boolean));
  const selected = [...used].map((id) => {
    const candidate = lookup.get(id);
    return { candidate_id: id, url: candidate.url, authority: candidate.authority.kind,
      version: candidate.version, assignments: assignments.filter((assignment) => assignment.candidate_id === id),
      components: candidate.components.filter((component) => component.paths.length > 0 && verifiedEvidence(component.evidence, new Set(['source_code']))
        && assignments.some((assignment) => assignment.candidate_id === id && component.question_ids.includes(assignment.question_id)
          && (assignment.role === 'any' || assignment.role === component.role))),
      runtime: candidate.runtime || { status: 'not_run' } };
  });
  const gaps = assignments.filter((assignment) => assignment.candidate_id === null);
  let status, message;
  if (gaps.length === 0) { status = 'selected'; message = '已为本次问题选择版本和实现范围匹配的仓库。'; }
  else if (selected.length > 0) { status = 'partial'; message = '仅找到覆盖部分问题的相关实现，其余范围保留缺口。'; }
  else {
    const considered = assessments.filter((entry) => {
      if (entry.reasons.includes('not_user_specified') || entry.reasons.includes('unrelated')) return false;
      // Once readable code is known to be absent or outside the question, an
      // unavailable pin/mapping cannot make it a still-promising implementation.
      const readable = lookup.get(entry.candidate_id).access === 'readable';
      return !(readable && (entry.reasons.includes('no_implementation') || entry.reasons.includes('outside_question_scope')));
    });
    if (considered.some((entry) => entry.reasons.some((reason) => ['access_blocked', 'access_missing'].includes(reason)))) {
      status = 'unavailable'; message = '相关候选仓库当前无法访问或指定地址无法取得，不能据此判定没有实现。';
    } else if (considered.some((entry) => entry.reasons.some((reason) => /unverified|not_pinned|scope_changed/.test(reason)))) {
      status = 'unverified'; message = '候选仓库的身份、版本或实际代码尚未核实，暂不采用。';
    } else if (request.specified_ids.length > 0) {
      status = 'specified_uncovered'; message = '指定仓库在要求版本或实现范围内未提供可采用的相关代码，未替换为其他仓库。';
    } else if (!(search.complete && search.official_entry_checked && search.code_hosts_checked)) {
      status = 'search_incomplete'; message = '尚未完成相关官方入口和代码平台检索，不能认定未找到实现。';
    } else { status = 'not_found'; message = '未找到符合要求的相关代码实现。'; }
  }
  const decision = { status, message, selected, assignments, gaps, assessments, fingerprint: recordFingerprint(record) };
  decision.reuse = reuseDecision(record, decision, previous);
  return { ...record, decision };
}

async function main() {
  const options = {}, args = process.argv.slice(2);
  for (let i = 0; i < args.length; i++) {
    const key = args[i];
    if (key === '--help') { console.log('Usage: node repository-selection.mjs --input <record.json> [--previous <previous-record.json>] [--output <decision-record.json>]\nOffline consistency/selection checks only; supplied evidence still requires actual source verification.'); return; }
    requireThat(['--input', '--previous', '--output'].includes(key) && args[i + 1] && !args[i + 1].startsWith('--'), `Invalid argument: ${key}`);
    options[key.slice(2)] = args[++i];
  }
  requireThat(options.input, '--input is required.');
  const input = JSON.parse(await readFile(options.input, 'utf8'));
  const previous = options.previous ? JSON.parse(await readFile(options.previous, 'utf8')) : null;
  const result = selectRepositories(input, previous), serialized = JSON.stringify(result, null, 2) + '\n';
  if (options.output) {
    const output = path.resolve(options.output), temporary = `${output}.${process.pid}.tmp`;
    await mkdir(path.dirname(output), { recursive: true });
    await writeFile(temporary, serialized);
    await rename(temporary, output);
  }
  process.stdout.write(serialized);
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => { console.error(JSON.stringify({ valid: false, error: error.message })); process.exitCode = 1; });
}
