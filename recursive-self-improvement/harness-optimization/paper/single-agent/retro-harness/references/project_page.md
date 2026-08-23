# Evolving Agents in the Dark — Retrospective Harness Optimization (RHO)

> arXiv 2026 · Preprint
> Source: [https://paper-rho.wenbo.io/](https://paper-rho.wenbo.io/)

---

**Title:** Evolving Agents in the Dark: Retrospective Harness Optimization via Self-Preference

**Authors:** Wenbo Pan<sup>1</sup>, Shujie Liu<sup>2</sup>, Chin-Yew Lin<sup>2</sup>, Jingying Zeng<sup>2</sup>, Xianfeng Tang<sup>2</sup>, Xiangyang Zhou<sup>2</sup>, Yan Lu<sup>2</sup>, Xiaohua Jia<sup>1</sup>

**Affiliations:** <sup>1</sup>City University of Hong Kong · <sup>2</sup>Microsoft Research Asia

**Links:** [Paper](https://arxiv.org/abs/2606.05922) | [Code](https://github.com/wbopan/retro-harness) | [Try it](#try-it-on-your-own-projects) | [BibTeX](#citation) | [Blog post](https://www.wenbo.io/blog/rho-dynamic-workflow/)

---

## Pipeline Overview

![The RHO pipeline: coreset selection, group rollout, harness proposal](https://paper-rho.wenbo.io/static/fig2-pipeline.png)

The **RHO** pipeline. A diverse coreset of past tasks is re-solved in parallel; within- and cross-trajectory signals drive candidate harness edits; the agent's own pairwise self-preference selects the winner. No ground-truth labels are used.

---

## Abstract

AI agents rely on a *harness* of skills, tools, and workflows to solve complex problems, and continually improving this harness is essential for adapting to new tasks. Existing optimization methods typically require ground-truth validation sets, yet such labeled data is difficult to acquire in practical deployment settings.

We introduce **Retrospective Harness Optimization (RHO)**, a self-supervised method that optimizes the agent harness using only past trajectories. RHO selects a diverse coreset of challenging tasks from past trajectories and re-solves them in parallel. The agent analyzes these rollouts using self-validation and self-consistency, then generates candidate harness updates and selects the most effective one by its own pairwise self-preference.

We evaluate RHO across three diverse domains spanning software engineering, technical work, and knowledge work. Notably, a single optimization round improves the pass rate on SWE-Bench Pro from 59% to 78% without any external grading. Our analysis shows that RHO effectively targets prior failure modes: the optimized harness alters the agent's behavior patterns and sustains higher accuracy during long-horizon sessions.

**TL;DR** — RHO improves an agent's harness purely from its own **unlabeled past trajectories**, with no validation set and no external grading. One retrospective pass: **SWE-Bench Pro 59% → 78%**.

---

## How it works

Most harness optimizers iterate against a *labeled validation set* — but real deployments rarely have one. A deployed agent does, however, produce a continuous stream of **unlabeled trajectories**. RHO turns those into harness improvements in three label-free stages:

### Step 1: Coreset Selection

A determinantal point process (DPP) picks a small, difficulty-diverse subset of past tasks to re-solve.

### Step 2: Group Rollout

Each coreset task is re-solved *G* times in parallel, yielding two diagnostic signals: self-validation within a trajectory and self-consistency across trajectories.

### Step 3: Harness Proposal

The agent samples *N* candidate harness edits and keeps the one its own *pairwise self-preference* ranks highest over the baseline.

### No validation set, no feedback loop

Validation-feedback methods repeatedly score harness edits against labeled data. RHO instead reflects on past trajectories in a single retrospective pass — replacing the external grader with the agent's own self-validation, self-consistency, and self-preference.

![Validation-based vs retrospective optimization](https://paper-rho.wenbo.io/static/fig1-rho-comparison.png)

---

## Results

Held-out pass rate after a single optimization round (Codex + GPT-5.5), against feedback-free baselines under a matched agent-call budget:

| Method | Harness surface | SWE-Bench Pro | Terminal-Bench 2 | GAIA-2 |
|---|---|---|---|---|
| Vanilla Codex | — | 0.59 | 0.71 | 0.29 |
| Dynamic Cheatsheet | Skills | 0.62 (+0.03) | 0.73 (+0.02) | 0.30 (+0.01) |
| ReasoningBank | Memory | 0.61 (+0.02) | 0.73 (+0.02) | 0.28 (−0.01) |
| Sleep-time Compute | Memory | 0.64 (+0.05) | 0.73 (+0.02) | 0.32 (+0.03) |
| **RHO (ours)** | **Skills + Tools** | **0.78 (+0.19)** | **0.76 (+0.05)** | **0.37 (+0.08)** |

RHO also beats **Meta-Harness**, a validation-feedback optimizer, at a matched single-round budget (0.78 vs 0.62 on SWE-Bench Pro) — without ever touching ground-truth labels.

![What the optimized harness contains](https://paper-rho.wenbo.io/static/fig-harness-artifacts.png)

What RHO writes into the harness: task-agnostic instructions, skills that record environment idiosyncrasies behind past failures, and executable tools — each targeting a failure mode observed in the original trajectories.

---

## Try it on your own projects

RHO learns from the sessions your agent has already produced. One line runs a full retrospection cycle — digest past sessions, diagnose recurring failures, evolve the persistent harness, and accept an update only when the agent's own pairwise self-preference favors it (with a backup first).

### Claude Code (Recommended)

Paste as a prompt — a [dynamic workflow](https://code.claude.com/docs/en/workflows) runs the cycle on the project you're in, evolving `CLAUDE.md`, auto-memory, and helper scripts. Plug and play.

```
Run the workflow at https://raw.githubusercontent.com/wbopan/retro-harness/main/.claude/workflows/retrospection.js on this project
```

### Codex CLI

A stdlib-only Python orchestrator over `codex exec` — the same cycle on your `AGENTS.md` and skills.

```
curl -fsSLO https://raw.githubusercontent.com/wbopan/retro-harness/main/codex/retrospection.py && python3 retrospection.py
```

### This repo

Used to reproduce our results, for research purposes.

```
git clone https://github.com/wbopan/retro-harness && cd retro-harness && uv sync && uv run rho evolve --dataset locomo:data/locomo10.json --rounds 1
```

---

## Citation

If you find RHO useful, please cite:

```bibtex
@article{pan2026rho,
  title   = {Evolving Agents in the Dark: Retrospective Harness
             Optimization via Self-Preference},
  author  = {Pan, Wenbo and Liu, Shujie and Lin, Chin-Yew and Zeng, Jingying
             and Tang, Xianfeng and Zhou, Xiangyang and Lu, Yan and Jia, Xiaohua},
  journal = {arXiv preprint arXiv:2606.05922},
  year    = {2026}
}
```

---

> Source: [https://paper-rho.wenbo.io/](https://paper-rho.wenbo.io/)
