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

### 算法细节

核心优化循环（来自core.py）：

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

接受条件：仅当 `combined_passed` 提升时保留变更。

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
   @wrap_tool_call
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
