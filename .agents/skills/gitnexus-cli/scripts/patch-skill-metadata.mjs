import { readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

/** Keep the pinned upstream plan skill discoverable by Codex's skill validator. */
export async function patchPlanDescription(packageRoot) {
  const file = path.join(packageRoot, 'skills/gitnexus-plan/SKILL.md');
  const source = await readFile(file, 'utf8');
  const frontmatter = source.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
  const description = frontmatter?.[1].match(/^description:[^\r\n]+/m);
  if (!description) throw new Error('gitnexus-plan description is missing; check the pinned skill package.');

  // Change only the known example in metadata, leaving YAML quoting and the body intact.
  const updated = description[0].replaceAll('docs/plans/<plan>.md', 'docs/plans/plan-file.md');
  if (/[<>]/.test(updated)) {
    throw new Error('gitnexus-plan description contains unsupported angle brackets; review the upstream metadata before updating the patch.');
  }
  if (updated === description[0]) return false;
  const header = frontmatter[0].replace(description[0], () => updated);
  await writeFile(file, header + source.slice(frontmatter[0].length), 'utf8');
  return true;
}
