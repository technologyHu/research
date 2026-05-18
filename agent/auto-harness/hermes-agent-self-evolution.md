# Hermes Agent Self-Evolution 调研报告

## 基本信息

| 字段 | 内容 |
|------|------|
| **项目名称** | Hermes Agent Self-Evolution |
| **作者/机构** | Nous Research |
| **论文** | ICLR 2026 Oral (Paper ID: 10009494) |
| **OpenReview** | https://openreview.net/forum?id=RQm2KQTM5r |
| **GitHub** | https://github.com/NousResearch/hermes-agent-self-evolution |
| **许可证** | MIT (© 2026 Nous Research) |
| **发布日期** | 2026年 |

## 项目概述

Hermes Agent Self-Evolution 是一个独立的优化流水线项目，旨在通过自动优化循环系统性地提升 Hermes Agent 的性能。它能够进化（evolve）Agent 的 skills、prompts、tool descriptions 和 agent configurations。该项目独立于 hermes-agent 仓库存在，作为外部优化器作用于 hermes-agent，输出 PR 供人工审核合并。

**核心理念**：无需 GPU 训练，仅通过 API 调用实现对 prompt/instruction/few-shot 文本的变异和评估，每次优化运行成本约 $2-10。

## 核心方法

### 三大优化引擎

| 引擎 | 优化对象 | 许可证 | 集成方式 |
|------|---------|--------|---------|
| **DSPy + GEPA** | Skills、prompts、instructions、tool descriptions | MIT | 原生 Python，主引擎 |
| **Darwinian Evolver** | 代码文件、算法、工具实现 | AGPL v3 | 外部 CLI |
| **DSPy MIPROv2** | Few-shot examples、instruction text | MIT | 原生 Python，备用优化器 |

### GEPA（Genetic-Pareto Prompt Evolution）

GEPA 是该项目的核心优化器，主要特点：

- **集成于 DSPy**：作为 DSPy 的优化器之一
- **反射式进化**：读取执行轨迹（execution traces）来理解**为什么**失败，而非仅仅知道失败
- **小样本友好**：仅需 3 个示例即可开始优化
- **性能优势**：优于 RL 和之前的 DSPy 优化器
- **无需 GPU**：通过标准 LLM API 调用运行

### 优化循环流程

```
1. 选择目标 → 选取 skill/prompt section/tool，加载当前版本作为基线
2. 构建评估数据集 → 从 SessionDB 挖掘真实用例或使用手工测试集
3. 封装为 DSPy 模块 → Skill 文本 → DSPy Signature，Agent 工作流 → DSPy ReAct
4. 运行优化器 → 主：dspy.GEPA（反射式进化）；备用：dspy.MIPROv2（贝叶斯优化）
5. 评估与比较 → 在保留测试集上运行，比较准确率、成本、延迟
6. 部署（需审批） → Git commit 改进版本，A/B 测试（可选），通过 PR 提交
```

## 分层优化目标

### Tier 1: Skill 文件（最高价值，最低风险）
- **目标**：SKILL.md 文件 — 程序化指令
- **方法**：将 skill 文本封装为 DSPy 模块，通过 batch_runner 在测试任务上评估，用 GEPA 进化
- **原理**：Skills 是纯文本，易于变异，且可直接测量（Agent 是否正确地完成了任务？）

### Tier 2: Tool Descriptions（中等价值，低风险）
- **目标**：工具 schema 中的 description 字段
- **方法**：GEPA 进化描述，评估 Agent 是否为给定任务选择了正确的工具
- **约束**：每个工具 description ≤ 500 字符，参数 description ≤ 200 字符

### Tier 3: System Prompt 组件（高价值，较高风险）
- **目标**：系统 prompt 的各个部分（persona、policies、formatting instructions）
- **风险**：需确保不破坏 prompt caching，仅离线优化，部署为新版本

### Tier 4: Code Evolution（高价值，最高风险）
- **目标**：工具实现代码、辅助函数
- **方法**：Darwinian Evolver + GitBasedOrganism，通过 pytest + batch_runner 测试
- **约束**：全部 2550+ 测试必须通过，函数签名不可变更

### Tier 5: Continuous Improvement Loop（自动化）
- **目标**：Agent 自动识别薄弱环节并持续改进
- **方法**：性能监控 + 自动分类 + 定时优化触发

## 数据流架构

```
SessionDB (真实对话)
    │
    ▼
Evaluation Dataset Builder
    │
    ├──► DSPy Module Wrapper（封装 skill/prompt/tool 为可优化模块）
    │        │
    │        ▼
    │    GEPA Optimizer ◄── Execution Traces（来自 batch_runner）
    │        │                    ▲
    │        ▼                    │
    │    Candidate Variants ──► batch_runner（并行评估）
    │        │
    │        ├──► Constraint Validation（测试、字符限制、缓存兼容性）
    │        │
    │        ▼
    │    Best Valid Variant
    │        │
    ▼        ▼
Git Branch + PR（含 diff、指标、前后对比）
    │
    ▼
Human Review & Merge
```

## 评估数据集来源

| 来源 | 描述 | 质量 |
|------|------|------|
| **A. 合成生成（主要）** | 强模型（如 Claude Opus）读取 skill → 生成 15-30 个测试用例 | 高 |
| **B. SessionDB 挖掘** | 查询真实使用历史，LLM-as-judge 评分 | 随时间增长 |
| **C. 手工黄金集** | 手动编写的高质量测试用例 | 最高 |
| **D. Skill 自动评估** | 特定 skill 的自然验证方式（如种 bug 测 debugging） | 特定场景 |

## 安全约束与护栏

每个候选变体必须通过以下全部约束：

1. **全量测试套件**：`pytest tests/ -q` 必须 100% 通过
2. **字符/Token 限制**：Skills ≤ 15KB，tool descriptions ≤ 500 chars，system prompt sections 不超过当前大小 20%
3. **Prompt Caching 兼容性**：进化内容仅在**新会话**生效，绝不热替换活跃对话
4. **语义保持**：优化不能偏离原始目的，包含语义相似度检查
5. **PR 部署（非直接 commit）**：所有变更通过 PR 提交，需人工审核合并

## 基准测试作为门控

| 基准测试 | 测试内容 | 速度 | 角色 |
|---------|---------|------|------|
| **TBLite** | 编程/系统管理（100 任务） | ~1-2 小时 | **主要回归门控** — 每个候选都运行 |
| **TerminalBench2** | 编程/系统管理（89 更难任务） | ~2-4 小时 | **深度验证** — PR 前最终候选运行 |
| **YC-Bench** | 长程战略连贯性（100-500 轮） | ~3-6 小时 | **连贯性检查** — 确保进化不破坏多轮行为 |

**关键原则**：基准测试是**门控（gates）**，不是适应度函数。适应度函数是任务特定的（skill/tool/prompt 是否更好地完成了工作）。基准测试确保改进没有破坏其他能力。

## 分阶段实施计划

| 阶段 | 内容 | 周期 | 依赖 | 通过门控 |
|------|------|------|------|---------|
| **Phase 1** | Skill 进化 | 3-4 周 | 无 | ≥1 skill 可测量改进 |
| **Phase 2** | Tool descriptions | 2-3 周 | Phase 1 基础设施 | 工具选择准确率提升 |
| **Phase 3** | System prompt | 2-3 周 | Phase 1-2 基础设施 | 行为测试通过，基准不退化 |
| **Phase 4** | Code 进化 | 3-4 周 | Phase 1-3 | Bug 修复，测试全通过 |
| **Phase 5** | 持续循环 | 2 周 | 以上全部 | 自动化流水线无人值守运行 |

**总计：13-17 周（如所有阶段都产生价值）**

## 成本估算

- GEPA 优化：每次运行约 $2-10（取决于评估数据集大小）
- Darwinian Evolver：每个任务约 $2-9
- 批量评估：取决于测试用例数量和模型成本

## 项目架构

```
hermes-agent-self-evolution/
├── PLAN.md                          # 完整架构设计
├── README.md                        # 安装、使用、示例
├── pyproject.toml                   # 包配置 + 依赖（dspy, gepa）
├── evolution/                       # 主包
│   ├── core/                        # 共享基础设施
│   │   ├── dataset_builder.py       # 评估数据集生成
│   │   ├── fitness.py              # 适应度函数（LLM-as-judge）
│   │   ├── constraints.py          # 约束验证器
│   │   ├── benchmark_gate.py       # 基准门控
│   │   └── pr_builder.py          # 自动生成 PR
│   ├── skills/                      # Phase 1: Skill 进化
│   ├── tools/                       # Phase 2: Tool description 进化
│   ├── prompts/                     # Phase 3: System prompt 进化
│   ├── code/                        # Phase 4: Code 进化
│   └── monitor/                     # Phase 5: 持续循环
├── datasets/                        # 生成的评估数据集
└── tests/                           # 测试套件
```

## CLI 使用示例

```bash
# 进化 skill（合成评估数据）
python -m evolution.skills.evolve_skill \
    --skill github-code-review \
    --iterations 10 \
    --eval-source synthetic

# 使用真实会话历史
python -m evolution.skills.evolve_skill \
    --skill github-code-review \
    --iterations 10 \
    --eval-source sessiondb

# 进化 tool descriptions
python -m evolution.tools.evolve_tool_descriptions \
    --iterations 5 \
    --benchmark-gate tblite-fast
```

## 核心发现与洞察

1. **反射式优化是关键差异点**：GEPA 不仅知道"什么失败了"，还通过分析执行轨迹理解"为什么失败"，这使得它能够提出有针对性的改进方案，而非盲目变异。

2. **无需训练，纯 API 调用**：与传统 fine-tuning 不同，Self-Evolution 优化的是文本（prompts、descriptions、instructions），而非模型权重，大幅降低了计算门槛。

3. **严格的安全约束设计**：多层门控（pytest → TBLite → YC-Bench）+ 语义保持 + 人工审核，确保进化不会引入回归。

4. **渐进式演进策略**：从最低风险的 Skill 文件开始，逐步扩展到 tool descriptions、system prompt、代码实现，最后实现自动化持续改进。

5. **成本可控**：每次优化运行仅需 $2-10，使得小团队甚至个人开发者也能使用 Agent 自我进化。

## 参考资料

1. [GitHub 仓库](https://github.com/NousResearch/hermes-agent-self-evolution)
2. [ICLR 2026 Oral](https://iclr.cc/virtual/2026/oral/10009494)
3. [OpenReview 论文](https://openreview.net/forum?id=RQm2KQTM5r)
4. [PLAN.md 完整架构设计](https://github.com/NousResearch/hermes-agent-self-evolution/blob/main/PLAN.md)
5. [DSPy 框架](https://github.com/stanfordnlp/dspy)
6. [GEPA 项目](https://github.com/gepa-ai/gepa)
7. [Darwinian Evolver](https://github.com/imbue-ai/darwinian_evolver)
