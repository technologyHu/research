# LangChain Better Harness 调研报告

> 调研日期: 2026-05-12

## 参考资料来源

### 官方博客文章
1. [Better Harness: A Recipe for Harness Hill Climbing with Evals](https://www.langchain.com/blog/better-harness-a-recipe-for-harness-hill-climbing-with-evals) - LangChain官方博客，介绍Better Harness的核心概念和hill climbing方法论
2. [Improving Deep Agents with Harness Engineering](https://www.langchain.com/blog/improving-deep-agents-with-harness-engineering) - LangChain官方博客，介绍Deep Agents和Harness Engineering实践

> **注**：以上两篇博客是配套关系，代码参考相同，均指向下方代码仓库中的 `examples/better-harness/` 目录。

### 代码仓库
3. [langchain-ai/deepagents](https://github.com/langchain-ai/deepagents) - Deep Agents主仓库，包含SDK、CLI、evals和Better Harness示例

### 具体代码路径
4. [examples/better-harness/](https://github.com/langchain-ai/deepagents/tree/main/examples/better-harness) - Better Harness研究项目目录
5. [better_harness/core.py](https://github.com/langchain-ai/deepagents/blob/main/examples/better-harness/better_harness/core.py) - 核心数据模型、配置加载、运行循环
6. [better_harness/agent.py](https://github.com/langchain-ai/deepagents/blob/main/examples/better-harness/better_harness/agent.py) - Outer-loop Deep Agent实现
7. [better_harness/runners.py](https://github.com/langchain-ai/deepagents/blob/main/examples/better-harness/better_harness/runners.py) - pytest/harbor运行器
8. [better_harness/patching.py](https://github.com/langchain-ai/deepagents/blob/main/examples/better-harness/better_harness/patching.py) - Surface补丁机制
9. [examples/deepagents_example.toml](https://github.com/langchain-ai/deepagents/blob/main/examples/better-harness/examples/deepagents_example.toml) - 配置示例文件
10. [libs/evals/EVAL_CATALOG.md](https://github.com/langchain-ai/deepagents/blob/main/libs/evals/EVAL_CATALOG.md) - 105个评估用例目录
11. [libs/deepagents/graph.py](https://github.com/langchain-ai/deepagents/blob/main/libs/deepagents/deepagents/graph.py) - Deep Agent核心图定义，包含BASE_AGENT_PROMPT

---

## Executive Summary

Better Harness是LangChain发布的Deep Agents项目中的一个研究性成果，提供了一套**eval驱动的agent harness自动优化系统**。其核心思想是让一个"外部Deep Agent"（Outer Agent）通过阅读评估反馈来自动改进另一个"目标Agent"（Inner Agent）的harness配置。这种方法受到"hill climbing with evals"方法论启发，通过迭代编辑prompt、tools、skills、middleware等"可编辑表面"来持续优化agent性能。

---

## Better Harness 核心概念

### 定义

**Better Harness** 是一个用于自主harness优化的系统（System for autonomous harness optimization）。它允许一个Deep Agent改进另一个agent harness，通过evals评估反馈来驱动优化循环。

核心定义：
- **Harness**: Agent的配置框架，包含prompt、tools、skills、middleware等组件
- **Deep Agent**: LangChain推出的"batteries-included agent"，一个开箱即用、预配置好的agent框架
- **Better Harness**: 让outer agent自动优化inner agent harness的研究工具

### 核心思想

Better Harness的核心思想来源于三个方面：
1. LangChain之前的harness engineering工作实践
2. Andrej Karpathy的autoresearch项目
3. Meta-Harness论文（arXiv:2603.28052）

**工作原理**：
```
用户提供 → 目标workspace + 可编辑surface + train/holdout evals + outer agent模型

系统执行：
1. 运行baseline评估
2. 构建proposer workspace供outer agent使用
3. Outer agent编辑允许的surface
4. 测试编辑后的inner agent（train + holdout）
5. 仅当综合pass count提升时保留变更
6. 可选：对baseline和final运行scorecard
```

### 与传统方法对比

| 维度 | 传统方法 | Better Harness |
|------|----------|----------------|
| 优化方式 | 手动调参、启发式规则 | Eval驱动的自动优化 |
| 反馈来源 | 人工review | 自动化评估case |
| 迭代速度 | 慢（人工参与） | 快（自动化循环） |
| 适用场景 | 简单agent | 复杂deep agent系统 |
| 可扩展性 | 有限 | 高度可配置 |

---

## Harness Hill Climbing 方法论

### 具体步骤

Better Harness实现了"hill climbing with evals"方法论，具体步骤如下：

#### 1. 配置阶段
```toml
[experiment]
name = "my-deepagents-harness"
runner = "pytest"
workspace_root = "${DEEPAGENTS_ROOT}"
model = "claude-sonnet-4-6"
max_iterations = 3

[better_agent]
model = "claude-sonnet-4-6"
max_turns = 11000
```

#### 2. 定义可编辑表面（Editable Surfaces）
```toml
[surfaces.prompt]
kind = "module_attr"
target = "deepagents.graph:BASE_AGENT_PROMPT"
filename = "prompt.txt"
base_value = """You are a helpful agent..."""

[surfaces.tools]
kind = "workspace_file"
target = "libs/deepagents/deepagents/custom_tools.py"
filename = "custom_tools.py"

[surfaces.middleware_impl]
kind = "workspace_file"
target = "libs/deepagents/deepagents/custom_middleware.py"
filename = "custom_middleware.py"
```

#### 3. 定义评估用例
```toml
[[cases]]
case_id = "tests/evals/test_tool_selection.py::test_indirect_email_report[{model}]"
split = "train"
stratum = "tool_use"

[[cases]]
case_id = "tests/evals/test_tool_selection.py::test_direct_request_slack_dm[{model}]"
split = "holdout"
stratum = "tool_use"
```

#### 4. 迭代优化循环
```bash
# 验证配置
uv run better-harness validate my_experiment.toml

# 运行优化
uv run better-harness run my_experiment.toml \
  --output-dir runs/my-harness \
  --max-iterations 3
```

### 关键技术

#### Train/Holdout Split
- **train**: 对outer agent可见的评估用例，用于指导优化
- **holdout**: 对outer agent不可见，用于验证泛化能力
- **scorecard**: 可选的最终评估集

#### Surface Types
1. **module_attr**: 修改Python模块属性
   ```toml
   [surfaces.prompt]
   kind = "module_attr"
   target = "deepagents.graph:BASE_AGENT_PROMPT"
   ```

2. **workspace_file**: 临时替换目标workspace中的文件
   ```toml
   [surfaces.middleware]
   kind = "workspace_file"
   target = "my_agent/middleware.py"
   ```

#### Runner Support
- **pytest**: 标准pytest测试运行器
- **harbor**: LangChain Harbor沙箱环境

### 优化算法详解

Better Harness 的核心是一个 **LLM 驱动的贪心爬山算法（Greedy Hill Climbing with LLM Proposer）**。它用一个 Deep Agent 作为"提案者"（Proposer），通过读取评估反馈来编辑目标 Agent 的 harness 表面，然后用严格的定量指标决定是否接受变更。

#### 完整优化循环流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    run_experiment() 入口                          │
│                                                                 │
│  1. 构建 baseline variant（所有 surface 取 base_value）            │
│  2. 运行 baseline eval（train + holdout）                         │
│  3. current = baseline                                          │
│                                                                 │
│  ┌─ for iteration in 1..max_iterations: ──────────────────────┐ │
│  │                                                             │ │
│  │  a. 检查早停条件：train 和 holdout 是否全部通过？→ 提前退出      │ │
│  │                                                             │ │
│  │  b. 构建 Proposer Workspace：                                 │ │
│  │     - 复制当前 surface 文件到 /current                        │ │
│  │     - 写入 surface_manifest.json（映射关系）                   │ │
│  │     - 写入 train 失败详情到 train_failures.json               │ │
│  │     - 复制 train 测试用例源码到 /train_cases                  │ │
│  │     - 写入可见历史到 /history/visible_history.md              │ │
│  │     - 复制前几轮的 proposer 产物到 /history/prior_visible     │ │
│  │     - 写入 task.md（任务指令 + 失败清单）                      │ │
│  │     - 预填 /proposal.md 模板                                 │ │
│  │                                                             │ │
│  │  c. Outer Agent 提案（调用 Deep Agent）：                      │ │
│  │     - 读取 /task.md 和 train_failures.json                   │ │
│  │     - 分析 /current 下的 surface 文件                        │ │
│  │     - 编辑 /current 下的文件（prompt/tools/skills/middleware） │ │
│  │     - 写入 /proposal.md（变更说明）                           │ │
│  │     - 系统读取编辑后的文件值 → candidate variant              │ │
│  │                                                             │ │
│  │  d. 如果 outer agent 未做任何编辑 → 退出循环                   │ │
│  │                                                             │ │
│  │  e. 运行 candidate eval（train + holdout）                    │ │
│  │     - 通过 patching 机制临时替换 target 文件                  │ │
│  │     - 逐 case 运行 pytest，收集 JUnit XML + summary           │ │
│  │     - 计算 candidate_combined = train.passed + holdout.passed │ │
│  │                                                             │ │
│  │  f. 贪心接受/拒绝判定：                                        │ │
│  │     if candidate_combined > current_combined:                 │ │
│  │         → accepted，current = candidate                      │ │
│  │     else:                                                    │ │
│  │         → rejected，保留上一轮最优 variant                    │ │
│  │                                                             │ │
│  │  g. 写入 iteration 决策记录（decision.json + decision.md）    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  4. 可选：运行 scorecard（baseline vs final 对比）                 │
│  5. 生成报告（report.json + report.md）                           │
└─────────────────────────────────────────────────────────────────┘
```

#### 核心数据模型

```python
@dataclass(frozen=True)
class IterationRecord:
    """One optimization iteration."""
    iteration: int
    starting_variant: str
    candidate: CandidateEvaluation | None

@dataclass(frozen=True)
class CandidateEvaluation:
    """One candidate evaluation."""
    variant: str
    proposal: Proposal
    train: SplitResult
    holdout: SplitResult
    accepted: bool
    reason: str

    def combined_passed(self) -> int:
        """Return the combined pass count."""
        return self.train.passed + self.holdout.passed
```

#### 搜索策略：贪心爬山

Better Harness 采用**单候选贪心爬山**策略，而非束搜索、模拟退火或遗传算法。具体特点：

| 维度 | 策略 |
|------|------|
| 搜索空间 | 所有 surface 的文件内容空间（文本 × N 个 surface） |
| 每轮候选数 | **1 个**（outer agent 只提一个方案） |
| 接受准则 | **严格大于**：`candidate_combined > current_combined` |
| 回溯机制 | **无**：一旦接受就永久写入，不可回退 |
| 终止条件 | 达到 `max_iterations` 或 train+holdout 全部通过 |
| 探索方向 | 由 LLM 提案者的语义理解能力引导，而非随机扰动 |

**关键设计决策**：

1. **平局视为拒绝**（`>` 而非 `>=`）。这防止系统在等价解之间无限震荡，确保优化只在有实质改进时继续。
2. **不接受即丢弃**。被拒绝的 candidate 不会保留其部分编辑，下一轮从上一个最优 variant 重新开始。
3. **单轮单候选**。不做多候选对比，因为 LLM 提案的生成成本高（每次调用一个完整的 Deep Agent），且 LLM 的语义推理能力使其倾向于"一次给出好方案"而非"随机扰动"。

#### 信息可见性控制：防过拟合机制

Outer Agent 对评估数据的可见性受到严格控制：

```
┌──────────────────────────────────────────────┐
│            Outer Agent 的视角                  │
│                                              │
│  ✅ 可见（VISIBLE_SPLITS = {"train"}）          │
│     - train 用例的通过/失败状态                 │
│     - train 失败的 failure_message             │
│     - train 用例的源码（测试文件）              │
│     - 前几轮的 proposal 和决策                  │
│     - 当前 surface 文件内容                    │
│                                              │
│  ❌ 不可见（PRIVATE_SPLITS = {"holdout",        │
│                               "scorecard"}）    │
│     - holdout 用例的存在和 ID                  │
│     - holdout 的评估结果                       │
│     - scorecard 的任何信息                    │
└──────────────────────────────────────────────┘
```

但**接受判定**使用的是 `combined_passed = train.passed + holdout.passed`。这意味着：
- Outer Agent 可能针对 train 用例做过拟合（写死 case 特定逻辑）
- 但 holdout 作为"盲测集"会自动拦截这类过拟合
- 如果某个变更在 train 上提升但在 holdout 上退化，综合分数不升则被拒绝

**三层评估体系**：

| 层级 | 对 Outer Agent | 影响优化循环 | 最终报告 |
|------|---------------|-------------|---------|
| **train** | ✅ 可见 | ✅ 是（combined 的一部分） | 基线 + 最终对比 |
| **holdout** | ❌ 不可见 | ✅ 是（combined 的一部分） | 基线 + 最终对比 |
| **scorecard** | ❌ 不可见 | ❌ 否（只跑在 baseline 和 final 上） | 独立验证报告 |

Scorecard 是一个可选的第三层评估集，**不参与优化循环**，仅在最终阶段对 baseline 和 final variant 各跑一次，用于验证优化后的 harness 在未见过的用例上的泛化能力。

#### 提案生成：Outer Agent 的工作机制

Outer Agent 本身是一个 Deep Agent，通过 `invoke_deepagents_proposer()` 调用。它的输入和输出流程：

**输入构造（Proposer Workspace）**：

1. **`/current/`** — 当前 surface 文件的副本，outer agent 只能编辑这里
2. **`surface_manifest.json`** — 每个 surface 的元数据（kind, target, 文件路径映射）
3. **`train_failures.json`** — 训练集失败案例的结构化清单：
   ```json
   [
     {
       "case_id": "tests/evals/test_tool_selection.py::test_email[{model}]",
       "stratum": "tool_use",
       "status": "failed",
       "failure_message": "AssertionError: expected send_email, got send_slack"
     }
   ]
   ```
4. **`train_summary.json`** — 当前轮次的完整评估结果
5. **`/train_cases/`** — 训练集测试用例的 Python 源码（让 outer agent 理解测试逻辑）
6. **`/history/visible_history.md`** — 前几轮的决策摘要：
   ```
   - Iteration 1: accepted (train 3/5)
   - Iteration 2: rejected (train 3/5)
   ```
7. **`/history/prior_visible/`** — 前几轮的完整 proposer 产物（proposal.md, result.json 等）
8. **`/task.md`** — 任务指令，包含 surface 列表、当前分数、失败清单

**Outer Agent 的 System Prompt**：

```
You are Better Agent, an outer-loop Deep Agent that improves another agent harness.

Your job is to read eval feedback and edit the provided harness surface files
so the next eval run passes more cases.

Rules:
- Edit only files under /current.
- Do not edit train_cases, history, or bookkeeping files except /proposal.md.
- Prefer general harness fixes over case-specific hacks.
- Do not overfit to the visible examples.
  Infer the broader policy or behavior they expose,
  then encode that as general instructions, tools, skills, or middleware changes.
- The files under /current are the actual harness surfaces.
  Edit them as final prompt text, code, or config that the target agent should load during eval.
- If a surface is a code file such as a tool or middleware file,
  write the real code or registration needed there, not notes or pseudocode.
- If you change tool or middleware behavior,
  update both the implementation and any registration or wiring surfaces you were given.
- Use surface_manifest.json and task.md to understand how each editable file maps back to the target harness.
- Use the visible failures and the train case files to decide what to change.
- Keep changes concise and coherent.
- Make the smallest set of edits needed for the visible train failures in this iteration.
- Stop as soon as /current and /proposal.md are updated.
- When done, write a short explanation to /proposal.md.
```

**输出提取**：

Outer Agent 完成后，系统从 proposer workspace 读取：
- 扫描 `/current/` 下所有 surface 文件 → 提取新的 surface 值
- 对比当前的值 → 计算 `changed_surfaces`（哪些 surface 实际变了）
- 读取 `/proposal.md` → 作为 `proposal.summary`
- 提取最后一个 AI 消息 → 作为 `proposal.final_message`
- 如果 `changed_surfaces` 为空 → 本轮无提案，退出循环

**容错与重试**：

Outer Agent 调用支持最多 **3 次重试**，仅对瞬时错误（transient errors）重试：
- `overloaded` / `overloaded_error`
- `error code: 529`
- `rate limit`
- `timeout`

重试间隔采用指数退避：`2 * (attempt + 1)` 秒（2s, 4s, 6s）。

#### 评估执行策略

评估由 `runners.py` 中的 `PytestRunner` 或 `HarborRunner` 执行。以 PytestRunner 为例：

**逐 Case 顺序执行**：

```python
for case in experiment.cases_for_split(split):
    rendered = case.render(model=experiment.model)
    case_slug = safe_slug(rendered)
    case_dir = split_dir / "cases" / case_slug
    # 运行单个 case，收集 stdout/stderr/JUnit/summary
    completed = subprocess.run(command + [rendered], ...)
    case_outcome = parse_pytest_outcomes(junit_path=..., cases=[case], ...)
    outcomes.append(case_outcome)
```

每个 case 独立运行，产物包括：
- `stdout.log` / `stderr.log` — 完整输出
- `junit.xml` — JUnit 格式的测试结果
- `summary.json` — LangSmith eval summary（含 correctness score）
- `command.json` — 执行的命令和环境变量
- `trace_refs.json` — LangSmith trace URL（如果配置了 API key）

**文件 Patching 机制**：

对于 `workspace_file` 类型的 surface，使用 `workspace_override_context()` 上下文管理器：

```python
@contextlib.contextmanager
def workspace_override_context(workspace_root, overrides):
    backups = {}
    try:
        for relative_path, value in overrides.items():
            target = workspace_root / relative_path
            backups[target] = target.read_text() if target.exists() else None
            target.write_text(value)  # 写入 candidate 的值
        yield  # 在此上下文中运行 eval
    finally:
        for target, original in backups.items():
            if original is None:
                target.unlink()  # 删除新增文件
            else:
                target.write_text(original)  # 恢复原内容
```

对于 `module_attr` 类型的 surface，使用 `sitecustomize.py` 在 Python 启动时注入：

```python
# .runtime/sitecustomize.py
from better_harness.patching import patch_from_env
patch_from_env()

# patch_from_env() 读取环境变量中的 variant 文件
# 然后调用 importlib.import_module + setattr 修改模块属性
def patch_module_attrs(overrides):
    for target, value in overrides.items():
        module_name, _, attribute = target.partition(":")
        module = importlib.import_module(module_name)
        setattr(module, attribute, value)
```

这种方式确保每次 eval 子进程启动时自动加载当前 variant 的 module_attr 覆盖。

#### 状态持久化与文件系统布局

每次运行在 `output_dir` 下生成完整的产物树：

```
runs/my-experiment-20260512T100000Z/
├── manifest.json                    # 实验元信息
├── split.json / split.md            # 评估用例清单
├── variants/
│   ├── baseline.json                # baseline variant 定义
│   └── iter-001.json                # candidate variant 定义
├── history/
│   ├── visible/                     # Outer Agent 可见的内容
│   │   ├── train/                   # 每轮的 train 评估结果
│   │   │   ├── iter-001/
│   │   │   │   ├── result.json
│   │   │   │   └── cases/...
│   │   │   └── baseline/
│   │   └── iterations/
│   │       └── 001/
│   │           ├── decision.json    # 决策摘要（visible）
│   │           ├── decision.md
│   │           └── proposer_workspace/
│   │               ├── current/     # 编辑后的 surface
│   │               ├── proposal.md  # Outer Agent 的变更说明
│   │               └── result.json  # 完整提案 + 候选
│   └── private/                     # Outer Agent 不可见的内容
│       └── holdout/
│           ├── iter-001/
│           │   └── result.json
│           └── baseline/
│               └── result.json
├── _runtime/                        # Python 运行时注入
│   └── sitecustomize.py
├── report.json                      # 完整 JSON 报告
└── report.md                        # Markdown 摘要报告
```

这种布局的关键设计：**visible / private 物理隔离**。Outer Agent 只能访问 `history/visible/` 下的产物，`history/private/`（holdout/scorecard 结果）对其完全不可见。

#### 接受/拒绝判定逻辑

判定逻辑位于 `run_experiment()` 核心循环中：

```python
current_combined = current_train.passed + current_holdout.passed
candidate_combined = train.passed + holdout.passed
accepted = candidate_combined > current_combined
reason = (
    "improved combined train + holdout pass count"
    if accepted
    else "did not improve combined train + holdout pass count"
)
```

**决策语义分析**：

1. **度量单位是"通过用例数"而非"通过率"**。使用绝对计数（pass count）而非比例（pass rate），避免了因 case 数量变化导致的度量不稳定。

2. **Train + Holdout 联合判定**。单独的 train 提升不足以被接受——如果 holdout 退化抵消了 train 的提升，综合分数不会增加，变更被拒绝。

3. **不接受部分改进**。不像某些优化算法会保留"局部更优"的编辑（如仅保留在 train 上改善的 surface），Better Harness 做全有/全无的判定。

#### 早停机制

```python
if current_train.passed == current_train.total and current_holdout.passed == current_holdout.total:
    break
```

当当前最优 variant 在 train 和 holdout 上都达到 **100% 通过率** 时，提前终止优化。这避免了在已经完美解上继续无意义的迭代。

#### 可选 Scorecard 最终验证

```python
def _run_optional_scorecard(experiment, runner, variant, layout, reuse_existing):
    if not experiment.has_split("scorecard"):
        return None
    return runner.run_split(experiment=experiment, variant=variant,
                            split="scorecard", layout=layout, ...)
```

Scorecard 在两个时间点各运行一次：
- **baseline scorecard**：优化前的原始 harness
- **final scorecard**：优化后的最终 harness

这两个结果不参与优化循环，仅出现在最终报告中用于对比。如果 scorecard 也提升了，说明优化具有良好的泛化性；如果 scorecard 下降但 train+holdout 提升，可能提示 harness 在训练分布外存在退化。

#### 算法局限性

当前实现的搜索策略有几个已知局限：

1. **单候选爬山**：每轮只有一个提案，无法对比多个方向的编辑。如果 LLM 给出的编辑方向错误，本轮机会就浪费了。

2. **无编辑粒度控制**：LLM 可以同时编辑多个 surface，但接受/拒绝是全有全无的。无法识别"某个 surface 的编辑是有益的，另一个有害"这种细粒度情况。

3. **无历史编辑记忆**：被拒绝的编辑不会被记录或分析。Outer Agent 可能在后续轮次重复相同的无效编辑。

4. **无多目标优化**：只用 pass count 作为单一目标函数，不考虑编辑复杂度、代码简洁度、推理延迟等维度。

5. **对 LLM 提案质量的强依赖**：整个算法的收敛速度和最终质量高度依赖 Outer Agent 模型的能力。如果 LLM 无法从失败案例中推断出正确的修复方向，爬山会陷入平台。

---

## Harness Engineering for Deep Agents

### Deep Agents 概念

**Deep Agents** 是LangChain推出的"batteries-included agent harness"，特点：

- **开箱即用**: 无需手动配置prompts、tools、context管理
- **核心功能内置**:
  - Planning: `write_todos` 任务分解和进度追踪
  - Filesystem: `read_file`, `write_file`, `edit_file`, `ls`, `glob`, `grep`
  - Shell access: `execute` 命令执行（带沙箱）
  - Sub-agents: `task` 委托工作，隔离上下文窗口
  - Context management: 自动summarization

### Harness Engineering 方法

Harness Engineering是指通过编辑agent的"可编辑表面"来改进agent性能的工程实践。

#### 可编辑表面类型

1. **Prompt Surface**
   ```python
   BASE_AGENT_PROMPT = """You are a deep agent...
   - Be concise and direct
   - NEVER add unnecessary preamble
   - If the request is underspecified, ask only the minimum followup
   ..."""
   ```

2. **Tools File**
   ```python
   @tool
   def send_report(recipient: str, subject: str, body: str) -> str:
       """Send a report to a user."""
       return f"sent report to {recipient}"
   ```

3. **Skills File**
   ```markdown
   # Reporting skill
   - Ask domain-defining questions before implementation questions
   - Prefer acting when the destination and core intent are already clear
   ```

4. **Middleware Implementation**
   ```python
   @wrap_toolcall
   def log_tool_calls(request, handler):
       """Simple example middleware that logs tool calls."""
       result = handler(request)
       return result
   ```

5. **Middleware Registration**
   ```python
   def build_agent(model: str):
       return create_deep_agent(
           model=model,
           tools=[send_report],
           middleware=[log_tool_calls],
       )
   ```

### 实践案例

Deep Agents evals库包含**105个评估用例**，覆盖**7个类别**：

| 类别 | 用例数量 | 描述 |
|------|----------|------|
| tool_use | 53 | 工具选择和使用 |
| file_operations | 13 | 文件操作 |
| memory | 17 | 记忆功能 |
| retrieval | 6 | 检索能力 |
| conversation | 2 | 对话质量 |
| summarization | 5 | 总结能力 |
| unit_test | 9 | 单元测试 |

---

## 技术实现

### 项目结构

```
langchain-ai/deepagents/
├── libs/
│   ├── deepagents/     # SDK核心
│   ├── cli/            # CLI工具
│   ├── acp/            # Agent Context Protocol
│   ├── evals/          # 评估套件和Harbor集成
│   └── partners/       # 集成包
├── examples/
│   └── better-harness/ # Better Harness研究项目
│       ├── better_harness/
│       │   ├── core.py       # 核心数据模型、配置加载、运行循环
│       │   ├── agent.py      # Outer-loop Deep Agent实现
│       │   ├── runners.py    # pytest/harbor运行器
│       │   └── patching.py   # Surface补丁机制
│       └── examples/
│           └── deepagents_example.toml
└── README.md
```

### 核心数据模型

```python
# Surface: 一个可编辑的harness表面
@dataclass(frozen=True)
class Surface:
    name: str
    kind: str           # "module_attr" | "workspace_file"
    target: str         # 目标路径或属性
    base_value: str     # 初始值
    filename: str       # 文件名

# EvalCase: 一个评估用例
@dataclass(frozen=True)
class EvalCase:
    case_id: str
    split: str          # "train" | "holdout" | "scorecard"
    stratum: str        # 评估类别

# Variant: 实际化的surface值集合
@dataclass(frozen=True)
class Variant:
    label: str
    model: str
    changed_surfaces: tuple[str, ...]
    surfaces: dict[str, Surface]
    values: dict[str, str]
```

### Outer Agent 系统提示

```python
DEFAULT_SYSTEM_PROMPT = """You are Better Agent, an outer-loop Deep Agent that improves another agent harness.

Your job is to read eval feedback and edit the provided harness surface files so the next eval run passes more cases.

Rules:
- Edit only files under /current.
- Do not edit train_cases, history, or bookkeeping files except /proposal.md.
- Prefer general harness fixes over case-specific hacks.
- Do not overfit to the visible examples. Infer the broader policy or behavior they expose.
- Use surface_manifest.json and task.md to understand how each editable file maps back to the target harness.
- Make the smallest set of edits needed for the visible train failures in this iteration.
- When done, write a short explanation to /proposal.md."""
```

### 代码示例

#### 创建Deep Agent
```python
from deepagents import create_deep_agent

agent = create_deep_agent()
result = agent.invoke({"messages": [{"role": "user", "content": "Research LangGraph and write a summary"}]})
```

#### 自定义Deep Agent
```python
from langchain.chat_models import init_chat_model

agent = create_deep_agent(
    model=init_chat_model("openai:gpt-4o"),
    tools=[my_custom_tool],
    system_prompt="You are a research assistant.",
)
```

#### 运行Better Harness优化
```bash
# 安装
uv sync --extra dev

# 复制示例配置
cp examples/deepagents_example.toml my_experiment.toml

# 验证配置
uv run better-harness validate my_experiment.toml

# 运行优化
uv run better-harness run my_experiment.toml \
  --output-dir runs/my-harness \
  --max-iterations 3
```

---

## 最佳实践

### 1. Surface设计原则
- Middleware通常需要两个surface：实现文件 + 注册文件
- 使用`base_value`创建自包含配置文件
- 使用`base_file`指向现有源文件

### 2. Evals设计原则
- Train/Holdout分离，防止过拟合
- 使用stratum分类评估类别
- 保持评估用例覆盖多种场景

### 3. Outer Agent配置
- 选择足够强大的模型（如claude-sonnet-4-6）
- 设置合理的max_turns（如11000）
- 提供清晰的system prompt指导

### 4. 安全考虑
- Deep Agents采用"trust the LLM"模型
- 在tool/sandbox层面强制边界
- 不要期望模型自我约束

---

## 信息来源

### 官方仓库和文档
1. [Deep Agents GitHub Repository](https://github.com/langchain-ai/deepagents) - 主仓库，包含SDK、CLI、evals
2. [Deep Agents Documentation](https://docs.langchain.com/deepagents) - 官方文档
3. [Better Harness Example](https://github.com/langchain-ai/deepagents/tree/main/examples/better-harness) - 研究项目

### 关键文件
4. [Better Harness README](https://github.com/langchain-ai/deepagents/blob/main/examples/better-harness/README.md)
5. [Better Harness Core Implementation](https://github.com/langchain-ai/deepagents/blob/main/examples/better-harness/better_harness/core.py)
6. [Better Harness Agent Implementation](https://github.com/langchain-ai/deepagents/blob/main/examples/better-harness/better_harness/agent.py)
7. [Deep Agents Example Config](https://github.com/langchain-ai/deepagents/blob/main/examples/better-harness/examples/deepagents_example.toml)

### 评估相关
8. [Eval Catalog](https://github.com/langchain-ai/deepagents/blob/main/libs/evals/EVAL_CATALOG.md) - 105个评估用例目录
9. [Evals README](https://github.com/langchain-ai/deepagents/blob/main/libs/evals/README.md)

### 灵感来源
10. [karpathy/autoresearch](https://github.com/karpathy/autoresearch) - Andrej Karpathy的研究项目
11. [Meta-Harness Paper](https://arxiv.org/abs/2603.28052) - 学术论文

### 项目统计（截至2026-05-12）
- Deep Agents: 22,685 stars, 3,191 forks
- deepagentsjs: 1,218 stars, 193 forks
- License: MIT

---

## 总结

Better Harness代表了LangChain在agent优化领域的前沿探索，将传统的手动调参转变为eval驱动的自动化优化。其核心贡献包括：

1. **方法论创新**: 将hill climbing优化算法应用于agent harness调优
2. **工程实践**: 提供完整的研究工具链，支持prompt、tools、skills、middleware的自动优化
3. **Train/Holdout分离**: 防止过拟合，确保泛化能力
4. **开源生态**: 作为Deep Agents项目的一部分，与LangChain/LangGraph深度集成

该工作为构建可自我改进的agent系统提供了重要参考，适合用于研究和实验性项目。
