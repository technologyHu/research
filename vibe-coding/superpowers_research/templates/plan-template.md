# Plan: [Feature Name]

> Based on `skills/writing-plans/SKILL.md` from obra/superpowers

## Header

- **Feature**: [feature name]
- **Goal**: [one sentence, clear, measurable outcome]
- **Architecture**: [brief description of the approach]
- **Tech stack**: [languages, frameworks, tools]

## Tasks

### Task 1: [Task Title]

**Files**:
- `src/path/to/file.ts` - new/modified for X purpose
- `src/path/to/file.test.ts` - test for X

**Steps**:
- [ ] Step 1: description of what to do
  ```typescript
  // actual code or skeleton
  ```
- [ ] Step 2: run test, verify it fails first (TDD)
  ```bash
  npm test -- path/to/file.test.ts
  ```
- [ ] Step 3: implement minimal code to pass
- [ ] Step 4: verify all tests pass
  ```bash
  npm test
  ```
- [ ] Step 5: commit
  ```bash
  git add -A && git commit -m "feat: brief description"
  ```

### Task 2: [Task Title]

...

## Self-Review Checklist

- [ ] Every requirement from the spec is covered by at least one task
- [ ] No placeholders (TBD, TODO, "add appropriate error handling", etc.)
- [ ] Each task is bite-sized (2-5 minutes of work)
- [ ] Type consistency across all code examples
- [ ] Tests are written before implementation in every task
- [ ] Commit messages are specific and conventional
