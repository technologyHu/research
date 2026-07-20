# Research

个人研究调研仓库，用于记录和整理各类技术调研报告。每篇调研以 `report.md` 形式存放在独立子目录中，本文件为全仓索引。

## 目录结构

按调研对象性质分为四大类一级目录：`paper/`（学术论文）、`framework/`（框架/内核/方法论框架）、`product/`（产品级系统）、`open-source-project/`（开源工具/项目）。各类下保留原研究主题的二级分组与目录层级。

```
paper/                                    # 学术论文调研（含 arXiv 编号 / 会议发表）
├── recursive-self-improvement/           # 递归自我改进相关研究
│   ├── auto-harness/                     # Agent Harness 自动优化相关研究
│   │   ├── agentic-harness-engineering/  # Agentic Harness Engineering 综述调研
│   │   ├── auto-harness-deepmind/        # AutoHarness 代码约束框架自动合成调研
│   │   ├── autogenesis/                  # Autogenesis 自进化协议调研
│   │   ├── continual-harness/            # Continual Harness 在线适应调研
│   │   ├── harness_x/                    # HarnessX 可组合可进化 Harness 铸造厂调研
│   │   ├── life-harness/                 # Life-Harness 运行时适配调研
│   │   ├── memo-harness/                 # MemoHarness 经验学习 Harness 适配调研
│   │   ├── meta-evolution-harness/       # Meta-Evolution Harness 元演化调研
│   │   ├── meta-harness/                 # Meta-Harness Harness 端到端优化调研
│   │   ├── retro-harness/                # RHO 回顾式 Harness 优化调研
│   │   ├── reward-harness/               # RewardHarness 奖励建模调研
│   │   └── self-harness/                 # Self-Harness 自优化 Harness 调研
│   ├── auto-research/                    # Agent 自动研究相关
│   │   ├── arbor/                        # Arbor 论文+代码综合调研
│   │   └── ml-evolve/                    # MLEvolve ML 算法发现自演化调研
│   └── evolution-of-mas/                 # 多智能体系统演化生成相关研究
│       ├── evo-mas/                      # EvoMAS 配置空间演化生成调研
│       └── skill-mas/                    # Skill-MAS Meta-Skill 演化调研
├── context_engineering/                  # Agent 上下文工程相关研究
│   ├── self-gc/                          # Self-GC 自治理对象级上下文管理调研
│   └── token-pilot/                      # TokenPilot 缓存感知上下文管理调研
└── agent_rl/                             # Agent 强化学习相关研究
    └── teamtr/                           # TeamTR 多智能体协调信任域微调调研

framework/                                # 框架 / 内核 / 方法论框架调研
├── agent-framework/                      # Agent 框架相关研究
│   ├── auto-harness-aha/                 # AutoHarness (Aha) 开源框架调研
│   ├── langchain/                        # LangChain 相关框架调研
│   │   ├── loop-engineering/             # LangChain Loop Engineering (deepagents) 调研
│   │   └── better-harness/               # LangChain Better Harness 调研
│   └── pi/                               # Pi 终端 AI 编码代理调研
│       └── pi-agent-core/                # pi-agent-core 通用内核调研
└── multi-agent-framework/                # 多智能体协作框架相关研究
    └── agentspace/                       # AgentSpace 人机协作工作空间调研

product/                                  # 产品级系统调研
└── hermes/                               # Nous Research Hermes 自进化系统调研
    └── agent-self-evolution/             # Hermes Agent 自进化调研

open-source-project/                      # 开源工具 / 项目调研
├── recursive-self-improvement/           # 递归自我改进相关研究
│   └── auto-research/                    # Agent 自动研究相关
│       ├── auto-research/                # Karpathy autoresearch 项目调研
│       └── pi-auto-research/             # pi-autoresearch 项目调研
└── vibe-coding/                          # Spec-Driven Development 相关研究
    ├── openspec/                         # OpenSpec 调研
    ├── spec-kit/                         # GitHub spec-kit 调研
    ├── superpowers/                      # Superpowers 调研
    └── todo.md                           # AI 编程能力提升工具清单（来源索引）
```

## 调研报告

### Agent 框架（framework/）

#### 1. AutoHarness (Aha)

**文件**: [framework/agent-framework/auto-harness-aha/report.md](framework/agent-framework/auto-harness-aha/report.md)

**简介**: 调研 aiming-lab 开源的 AutoHarness (代号 Aha) 框架。轻量级 AI Agent 行为治理框架，核心理念是 "Agent = Model + Harness"。提供三层治理模式 (Core/Standard/Enhanced)，6-14步治理流水线，风险模式匹配，多层上下文管理，多 Agent 协作支持。2行代码零侵入集成，958 测试用例生产级质量。

**关键词**: Harness Engineering、治理流水线、风险分级、上下文管理、多Agent协作、零侵入集成

---

#### 2. Pi agent-core

**文件**: [framework/agent-framework/pi/pi-agent-core/report.md](framework/agent-framework/pi/pi-agent-core/report.md)

**简介**: 调研 earendil-works/pi monorepo 中的 `@earendil-works/pi-agent-core` 通用 agent 内核包。拆解 Pi 的三层架构（内核层 / 产品会话层 / CLI·TUI·RPC 接入层），内核层提供状态机、事件流、LLM turn loop、工具调用、队列与通用 harness/session 抽象；上层 `pi-coding-agent`（Pi CLI/TUI/SDK 产品层）通过 npm 依赖与 import 实例化内核 `Agent`，叠加 session JSONL 持久化、extension hooks、内置工具注册、自动压缩与重试。源码快照 `ec6311b`，覆盖 `packages/agent` 与 `packages/coding-agent` 的集成关系。

**关键词**: Pi、pi-agent-core、agent 内核、turn loop、工具调用、session 持久化、monorepo 集成

---

#### 3. LangChain Loop Engineering (deepagents)

**文件**: [framework/agent-framework/langchain/loop-engineering/report.md](framework/agent-framework/langchain/loop-engineering/report.md)

**简介**: 调研 LangChain 官方博客《The Art of Loop Engineering》（2026-06-16）的代码落地——开源仓库 `langchain-ai/deepagents`（26.3k★，"the batteries-included agent harness"，README 自述"Inspired by Claude Code"）。报告核心是 blog 提出的 **4 层循环栈（loop stack）**：Loop 1 Agent（模型在循环中调用工具直到完成，`create_agent`/`create_deep_agent`）、Loop 2 Verification（grader 按 rubric 打分、`needs_revision` 则带反馈回流，开源 `RubricMiddleware` 靠 `after_agent` + `jump_to='model'` 实现）、Loop 3 Event-driven（cron/webhook/Fleet channel 触发后台运行，LangSmith 平台能力）、Loop 4 Hill-climbing（生产 trace 喂给分析 agent 重写 harness 配置自改进，LangSmith Engine 平台能力）。**如实标注**：4 层中仅 Loop 1/2 的核心实现在开源仓库，Loop 3/4 是 LangSmith 平台能力、仓库 CLI `deepagents deploy` 仅提供对接点。含两层架构视角（框架层 `AgentMiddleware` 契约 vs 实现层具体 middleware）、`RubricState`/`GraderResponse` 数据结构、middleware 装配三段式（base/user/tail，受保护脚手架不可删）、`recursion_limit=9_999` 与 `DeltaChannel` 降 checkpoint 复杂度 $O(N^2)\to O(N)$、防 prompt 注入 nonce、安全模型"trust the LLM"落地（`FilesystemPermission` allow/deny/interrupt）。报告含 8 张 blog 原图（4 层 loop 通用图 + docs-writer 贯穿示例图，已校验为真 PNG）、5 幅 Mermaid 设计图、7 张表格。

**关键词**: Loop Engineering、deepagents、loop stack、RubricMiddleware、jump_to回流、AgentMiddleware、两层架构、LangSmith Engine/Fleet、trust the LLM

---

### Agent Harness 自动优化（paper/，第 7 条 Hermes 例外位于 product/、第 8 条 Better Harness 例外位于 framework/）

#### 4. Agentic Harness Engineering

**文件**: [paper/recursive-self-improvement/auto-harness/agentic-harness-engineering/report.md](paper/recursive-self-improvement/auto-harness/agentic-harness-engineering/report.md)

**简介**: 调研复旦大学、北京大学、上海奇绩智峰联合提出的 AHE（Agentic Harness Engineering）框架。通过三层可观测性支柱（组件可观测性、经验可观测性、决策可观测性）将 Harness 演化转变为闭环自动化过程。核心创新是分层轨迹蒸馏流水线，将千万级 token 压缩为 10K 级可消费证据。在 Terminal-Bench 2 上将 pass@1 从 69.7% 提升至 77.0%，超越人工设计和自动化基线。

**关键词**: 可观测性驱动、轨迹蒸馏、闭环演化、组件解耦、arXiv 2604.25850

---

#### 5. Autogenesis

**文件**: [paper/recursive-self-improvement/auto-harness/autogenesis/report.md](paper/recursive-self-improvement/auto-harness/autogenesis/report.md)

**简介**: 调研 Autogenesis 自进化协议，提出了一套面向 LLM 智能体自进化的协议标准。核心创新是定义了自进化单元（AEU）作为最小可进化组件，支持生命周期管理和版本追溯。

**关键词**: 自进化协议、AEU、生命周期管理、组件解耦

---

#### 6. Continual Harness

**文件**: [paper/recursive-self-improvement/auto-harness/continual-harness/report.md](paper/recursive-self-improvement/auto-harness/continual-harness/report.md)

**简介**: 调研 Princeton + DeepMind 的 Continual Harness 论文，解决具身智能体在长时序环境中脚手架自动构建和持续改进的问题。提出了在线适应的 Harness 优化方法。

**关键词**: 具身智能、在线适应、脚手架工程、长时序任务

---

#### 7. Hermes Agent Self-Evolution

**文件**: [product/hermes/agent-self-evolution/report.md](product/hermes/agent-self-evolution/report.md)

**简介**: 调研 Nous Research 的 Hermes Agent 自进化系统。作为一个独立的优化流水线，通过 API 调用实现对 prompt/instruction/few-shot 的变异和评估，无需 GPU 训练。

**关键词**: Hermes、自进化流水线、Prompt优化、ICLR 2026 Oral

---

#### 8. LangChain Better Harness

**文件**: [framework/agent-framework/langchain/better-harness/report.md](framework/agent-framework/langchain/better-harness/report.md)

**简介**: 调研 LangChain 发布的 Better Harness 工作，这是一套 eval 驱动的 agent harness 自动优化系统。核心思想是让一个"外部 Deep Agent"通过阅读评估反馈来自动改进另一个"目标Agent"的 harness 配置。

**关键词**: LangChain、评估驱动、Harness Hill Climbing、Deep Agents

---

#### 9. RewardHarness

**文件**: [paper/recursive-self-improvement/auto-harness/reward-harness/report.md](paper/recursive-self-improvement/auto-harness/reward-harness/report.md)

**简介**: 调研 RewardHarness 论文，提出自演进的奖励建模框架。仅用 0.05% 数据即可超越 GPT-5，实现了高效、可解释的奖励模型构建。

**关键词**: 奖励建模、自演进、数据效率、可解释性

---

#### 10. Self-Harness

**文件**: [paper/recursive-self-improvement/auto-harness/self-harness/report.md](paper/recursive-self-improvement/auto-harness/self-harness/report.md)

**简介**: 调研上海AI Lab提出的Self-Harness论文，首次提出让LLM Agent自己改进运行框架的闭环范式。三阶段循环（Weakness Mining → Harness Proposal → Proposal Validation）实现无需人类专家或更强外部模型的自优化。在Terminal-Bench-2.0上，三个模型均获得显著提升，最高相对提升138%。

**关键词**: 自优化Harness、弱点挖掘、回归测试、模型特异性、NeurIPS 2026

---

#### 11. AutoHarness (DeepMind)

**文件**: [paper/recursive-self-improvement/auto-harness/auto-harness-deepmind/report.md](paper/recursive-self-improvement/auto-harness/auto-harness-deepmind/report.md)

**简介**: 调研 Google DeepMind 提出的 AutoHarness 方法，让 LLM 自动合成代码约束框架（Harness）。核心思想是将规则判断从 LLM 的概率性推理转移到确定性执行的代码，通过树搜索和 Thompson 采样管理多个代码假设。在 145 个 TextArena 游戏上实现 100% 合法动作率，使较小的 Gemini-2.5-Flash 能够战胜更大的 Gemini-2.5-Pro（56.3% 胜率）。代码即策略模式下，推理成本几乎为零，在 16 个单人游戏上平均奖励 0.870，超越 GPT-5.2-High。

**关键词**: 代码约束框架、自动合成、树搜索、Thompson采样、代码即策略、ICLR 2026、arXiv 2603.03329

---

#### 12. LIFE-HARNESS

**文件**: [paper/recursive-self-improvement/auto-harness/life-harness/report.md](paper/recursive-self-improvement/auto-harness/life-harness/report.md)

**简介**: 调研北京大学提出的 LIFE-HARNESS，一个面向确定性 LLM Agent 的生命周期感知运行时外壳。核心思想是"适配接口而非模型"，通过四层架构（环境契约层、技能层、动作层、轨迹层）实现不改模型权重的 Agent 能力提升。在 126 个 model-environment 设置中平均相对改进 88.5%，且用小模型生成的 Harness 可直接迁移到大模型。

**关键词**: 运行时适配、四层架构、跨模型迁移、确定性Agent、arXiv 2605.22166

---

#### 13. Meta-Evolution Harness

**文件**: [paper/recursive-self-improvement/auto-harness/meta-evolution-harness/report.md](paper/recursive-self-improvement/auto-harness/meta-evolution-harness/report.md)

**简介**: 调研 Sylph.AI 提出的两层 Harness 演化框架。核心创新是 Meta-Evolution Loop：内层 Harness Evolution Loop 优化单个任务的 Worker Harness，外层 Meta-Evolution Loop 跨多样化任务优化演化蓝图本身。建立了与元学习的精确对应关系，实现"自动化设计自动化本身"。理论框架论文，暂无开源代码和实验验证。

**关键词**: 元演化、两层优化、Harness Evolution Loop、元学习、ICLR 2026、arXiv 2604.21003

---

#### 14. Meta-Harness

**文件**: [paper/recursive-self-improvement/auto-harness/meta-harness/report.md](paper/recursive-self-improvement/auto-harness/meta-harness/report.md)

**简介**: 调研 Stanford IRIS Lab 提出的 Harness 端到端优化框架。核心思想是将 Harness 视为可搜索的代码空间，以 Coding Agent（Claude Code）为 Proposer，将完整经验（源码、分数、执行轨迹）作为可查询文件系统，实现非马尔可夫式进化搜索。报告包含论文全部10张原图（从arXiv源文件提取）、17个精确表格数据（从LaTeX源文件提取）、4个自动发现的策略分析（Draft-Verification、Label-Primed Query、四路BM25、环境快照注入）、消融实验、因果推理轨迹分析。在文本分类上比 ACE 提升 7.7pt 且仅用 1/4 上下文，4次评估即达到 OpenEvolve 40次评估精度（10倍搜索效率）；在 Terminal-Bench-2 上 Opus 4.6 达到 76.4%超越人工基线；消融实验证明原始轨迹访问比压缩摘要更关键。

**关键词**: 代码空间搜索、Coding Agent、可查询文件系统、非马尔可夫搜索、反参数调优、Pareto优化、arXiv 2603.28052、CoLM 2026

---

#### 15. Retrospective Harness Optimization (RHO)

**文件**: [paper/recursive-self-improvement/auto-harness/retro-harness/report.md](paper/recursive-self-improvement/auto-harness/retro-harness/report.md)

**简介**: 调研香港城市大学与微软亚洲研究院联合提出的 RHO（Retrospective Harness Optimization）框架（arXiv:2606.05922，目标 EMNLP 2026）。将 harness 形式化为"工具、prompts 与技能的持久集合"，把 Agent 执行多任务积累的轨迹数据集（含失败案例与有用洞察）作为离线优化信号，寻找最大化未来任务期望效用的最优 harness $h^\star$。核心创新是"自偏好（Self-Preference）"机制——Agent 自身作为评判者对历史轨迹做 pairwise ranking，提取改进信号，无需外部更强模型或人工标注。提供可替换的 Protocol 接口、Web UI 结果浏览与 Claude Code 动态工作流集成。

**关键词**: 回顾式优化、自偏好、轨迹数据集、pairwise ranking、Harness 形式化、EMNLP 2026、arXiv 2606.05922

---

#### 16. HarnessX

**文件**: [paper/recursive-self-improvement/auto-harness/harness_x/report.md](paper/recursive-self-improvement/auto-harness/harness_x/report.md)

**简介**: 调研小米 Darwin Agent Team 提出的 HarnessX（arXiv:2606.14249），把 Agent 运行时 Harness（prompt/工具/记忆/控制流）当作可组合、可进化的第一类对象。三大支柱：Compose（harness 拆成带类型 processor 挂 8 生命周期 hook + 九维分类 + 替换代数）、Adapt（AEGIS 进化引擎用"操作镜像"把 harness 适应映射为符号空间 MDP，把奖励作弊/灾难性遗忘/探索不足三 RL 病理转可预测设计风险，由四阶段流水线 Digester/Planner/Evolver/Critic + 确定性门控 seesaw 应对）、Evolve（共享 replay buffer 上的跨 harness GRPO 让模型内化历代 harness 策略，破"脚手架天花板"与"训练信号天花板"）。在 5 基准 × 3 模型族平均 +14.5%（最高 +44.0%），基线越弱收益越大（逆缩放），协同进化再增收 +4.7%。报告含论文全部 11 张原图、4 幅公式、2 幅 Mermaid 设计图，并诚实记录仓库与论文的脱节：基座层与论文完全一致（`agentic()` 字面相同），但变体隔离/Ensemble routing 与协同进化在仓库属 ROADMAP planned 未实现。

**关键词**: 可组合 Harness、AEGIS、操作镜像、符号空间 MDP、跨 harness GRPO、变体隔离、逆缩放、arXiv 2606.14249

---

#### 17. MemoHarness

**文件**: [paper/recursive-self-improvement/auto-harness/memo-harness/report.md](paper/recursive-self-improvement/auto-harness/memo-harness/report.md)

**简介**: 调研 Notre Dame/USC 等机构提出的 MemoHarness（arXiv:2607.14159，2026-07 预印本）。把 agent harness（模型外围控制层：上下文/工具/编排/memory/解码/输出）作为优化对象，提出"训练时搜索 + 测试时案例适配"两阶段框架。三大设计：(1) 六维 harness 空间 D1–D6（Context/Tool/Generation/Orchestration/Memory/Output）按推理时间流分解，使搜索可做诊断式编辑；(2) 双层经验库 $B_t=(E_t,G_t)$ 用 typed pair 存 per-case 执行条目 + 蒸馏全局模式，诊断算子把弱分数监督升级为维度级失败归因 $z=(s,d_{prim},D_{sec},a)$；(3) 测试时逐案例适配 $W(x)=\Pi_{test}(W^*,x,S_{test}(x))$，无需标签/反馈/额外搜索轮次，从冻结经验库检索相似成功/失败案例与全局模式生成案例专属 harness。正确性优先字典序选择 $W^*=\arg\max_{lex}(\bar{r},-\bar{c})$ 防漂向"便宜但错"配置。Terminal-Bench 18 题评估分片上 0.806 vs 最强 baseline Codex 0.722（+0.084），跨 6 个未见模型平均 +0.098，成本 \$6.89 < Codex \$10.28（94% 输入 token 可缓存）。报告含论文全部 4 张原图、5 幅 Mermaid 设计图、11 个合规 LaTeX 公式块、20 个连续编号表格，并对照开源仓库 HowieHwong/MemoHarness 建立 17 行论文概念→代码实现映射（distill_every=5/min_consecutive_failures=3/train_split=0.8/seed=42 等超参与论文 Appendix C 严格对应）。诚实标注局限：18 题点估计无显著性检验、组件未分别 ablate、成本竞争力依赖缓存假设。

**关键词**: 经验学习 Harness、六维分解、双层经验库、测试时案例适配、正确性优先字典序、operation-level 诊断、跨模型迁移、arXiv 2607.14159

---

### Agent 自动研究（paper/ 学术论文 + open-source-project/ 开源项目）

#### 18. Arbor

**文件**: [paper/recursive-self-improvement/auto-research/arbor/report.md](paper/recursive-self-improvement/auto-research/arbor/report.md)

**简介**: 调研中国人民大学和微软研究院联合提出的 Arbor 框架。通过假设树细化（HTR）将自主研究转变为累积的证据驱动过程。核心创新是持久协调器+短期执行器的双Agent架构，以及假设树作为研究状态的组织方式。在六项真实研究任务上超过 Codex 和 Claude Code 平均增益的 2.5 倍，MLE-Bench Lite 达到 86.36% Any Medal。

**关键词**: 假设树、自主优化、协调器-执行器、证据驱动、arXiv 2606.11926

---

#### 19. autoresearch (Karpathy)

**文件**: [open-source-project/recursive-self-improvement/auto-research/auto-research/report.md](open-source-project/recursive-self-improvement/auto-research/auto-research/report.md)

**简介**: 调研 Andrej Karpathy 的 autoresearch 项目。核心理念是让 AI Agent 在无人值守情况下自主迭代优化模型，人类编写指令约束，Agent 自主修改训练代码并运行实验循环。

**关键词**: Karpathy、自主研究、LLM训练、实验循环

---

#### 20. MLEvolve

**文件**: [paper/recursive-self-improvement/auto-research/ml-evolve/report.md](paper/recursive-self-improvement/auto-research/ml-evolve/report.md)

**简介**: 调研上海AI Lab与华东师大联合提出的 MLEvolve 自演化框架（arXiv:2606.06473）。针对机器学习工程（MLE）长周期自主任务中"分支信息孤立、无记忆搜索、缺乏层次化生成控制"三大瓶颈，提出三大创新：Progressive MCGS（渐进式蒙特卡洛图搜索）实现跨分支灵感共享、Retrospective Memory（回顾式记忆）主动总结复用历史成败、Hierarchical Planning（层次化规划）分离算法规划与代码实现。在 MLE-Bench 上以 12 小时预算达到 65.3% 奖牌率，并在数学算法发现任务上超越 AlphaEvolve。

**关键词**: 自演化、MLE、图搜索、回顾式记忆、层次化代码生成、AlphaEvolve、arXiv 2606.06473

---

#### 21. pi-autoresearch

**文件**: [open-source-project/recursive-self-improvement/auto-research/pi-auto-research/report.md](open-source-project/recursive-self-improvement/auto-research/pi-auto-research/report.md)

**简介**: 调研 pi-autoresearch 开源项目。作为 pi 终端 AI 编码代理的扩展，让 pi 能够自主优化用户的代码项目，包括测试速度、打包体积、训练损失等指标。

**关键词**: pi、终端代理、代码优化、自主迭代

---

### 上下文工程 (Context Engineering)（paper/）

#### 22. TokenPilot

**文件**: [paper/context_engineering/token-pilot/report.md](paper/context_engineering/token-pilot/report.md)

**简介**: 调研浙江大学（zjunlp / Ningyu Zhang）等机构提出的 TokenPilot 框架（arXiv:2606.17016，疑似投稿 EMNLP 2026）。面向 Claude Code、Codex 等有状态执行控制器的长程会话上下文膨胀问题，首个显式协调"文本稀疏性"与"prompt cache 连续性"的双粒度上下文管理框架。全局层 Ingestion-Aware Compaction 通过 Prefix Stabilization（静态占位符替换易失字段 + 工具定义下沉）从首轮起锁定 byte-identical prefix 把冷启动转暖启动，并净化摄入消息；局部层 Lifecycle-Aware Eviction 提出"残余效用（residual utility）"概念——段完成后不立即驱逐而转入保守的 `completed` 中间态，三态状态机 active → completed → evictable 仅在任务级效用彻底失效时清除。在 PinchBench 与 Claw-Eval 上相对 9 个基线实现 isolated 61%/56%、continuous 61%/87% 成本下降，continuous 模式 Claw-Eval 成本从 \$81.52 砍至 \$10.58，保持竞争性精度。代码集成于 `zjunlp/LightMem2`。

**关键词**: 上下文管理、KV prompt cache、Prefix Stabilization、残余效用、双粒度、三态状态机、arXiv 2606.17016

---

#### 23. Self-GC

**文件**: [paper/context_engineering/self-gc/report.md](paper/context_engineering/self-gc/report.md)

**简介**: 调研小红书（Xiaohongshu）提出的 Self-GC 自治理上下文框架（arXiv:2607.00692，源文件用 `aaai2027.sty`，疑似投稿 AAAI 2027）。针对长程 LLM agent（浏览/工具/文件编辑/多步工作流）活动上下文膨胀问题，核心论点是上下文不应被理解为被动 token buffer，而应被理解为带不同生命周期需求的运行时对象集合——把上下文管理重定义为「对可索引、可恢复对象的生命周期控制」而非「事后文本清理」。Self-GC 把 user turn、tool span、skill state 映射为带稳定标识符的可索引对象，由 side-channel planner 在 fork prefix 上产出 fold/mask/prune 动作计划，harness 本地排练通过 object-valid 校验后存为 pending，仅在安全 turn 边界且 cache-aware commit 公式净收益为正时才提交新活动视图；fold 把精确 payload 移入 sidecar 并留恢复指针，实现压缩活动视图同时保留对象身份与逐字节可恢复性。Hard Set 上 43.95% 剪枝下达到 84.85% 无影响率（最强启发式基线仅 69.70%），332-session Production Suite 上三个 planner backbone 达到 91.27%–94.58% 无影响率，在线账户级分流下白天平均 input token 降低 10%–15%、峰值近 20%。报告含论文全部 7 张原图、planner/judge prompt 契约、输出 schema、规划-排练-提交伪代码与失败分类法。无开源代码（作者承诺发表后发布 sanitized artifact）。

**关键词**: 自治理上下文、对象级生命周期、fold/mask/prune、side-channel planner、cache-aware commit、sidecar 恢复指针、无影响率、arXiv 2607.00692

---

### 多智能体系统演化 (MAS Evolution)（paper/）

#### 24. EvoMAS

**文件**: [paper/recursive-self-improvement/evolution-of-mas/evo-mas/report.md](paper/recursive-self-improvement/evolution-of-mas/evo-mas/report.md)

**简介**: 调研 Amazon AWS 提出的 EvoMAS 框架（ICML 2026，arXiv:2602.06511）。针对自动生成多智能体系统（Automatic-MAS）中"代码生成路线表达力强但可执行性灾难、模板约束路线可靠但僵化"的根本张力，提出配置空间演化范式：用一个可进化的 meta-model 编码 MAS 配置，配置经 workflow 执行图解释为可运行的多智能体工作流，演化操作作用于配置而非代码，从源头规避语法/运行时错误。兼具代码生成的表达力与模板方法的执行可靠性。

**关键词**: MAS演化、配置空间演化、meta-model、workflow执行图、Automatic-MAS、ICML 2026、arXiv 2602.06511

---

#### 25. Skill-MAS

**文件**: [paper/recursive-self-improvement/evolution-of-mas/skill-mas/report.md](paper/recursive-self-improvement/evolution-of-mas/skill-mas/report.md)

**简介**: 调研香港科技大学（广州）与蚂蚁集团联合提出的 Skill-MAS（arXiv:2606.18837）。定位为 Automatic-MAS 的"第三条路"——把 Meta-agent 的编排能力建模为可进化的 Meta-Skill，冻结前沿 LLM、不做参数更新，既摆脱推理时编排的经验无关性（同类任务反复踩坑、per-query 搜索账单高昂），又回避训练时编排的能力上限受限（绑定小模型、难扩展到 100B+ 闭源模型）。报告含同名辨析：与 arXiv:2605.09341（上海交大/中南大学/OPPO）的 SkillMAS 层次不同，切勿混淆。

**关键词**: Meta-Skill、编排能力进化、冻结LLM、Automatic-MAS第三条路、同名辨析、arXiv 2606.18837

---

### 多智能体协作 (Multi-Agent Collaboration)（framework/）

#### 26. AgentSpace

**文件**: [framework/multi-agent-framework/agentspace/report.md](framework/multi-agent-framework/agentspace/report.md)

**简介**: 调研港大 HKUDS 开源的 AgentSpace（Apache-2.0，697★/95 fork，v1.0@2026-06-21）。把 AI Agent 从「个人终端里的工具」升级为「可调度、可共享、可审计、可转移的数字员工」，定位为「人类 + Agent」的 agent-native 协作工作空间（"飞书为人类协作而生，AgentSpace 为人类和 Agent 共同协作而生"）。针对现有 Agent 框架围绕个人使用设计导致的五大痛点——Agent 私有化、上下文散落、runtime 割裂、治理缺失、工作不持久——提供四大核心能力：① 调度（AgentRouter 把 Claude Code/Codex/OpenClaw/OpenCode/Antigravity/Hermes 多 runtime 归一化为统一执行契约，身份/指令/技能稳定、只换 harness）；② 能力共享（数字员工展板把私有 Agent 变成组织级资产，可借用/转移）；③ 协作（多 Agent war room 围绕任务分工，人类在关键节点审批）；④ 治理（权限控制面 + runtime_tool 审批桥 + 三级预算熔断 + 全量审计）。两层架构视角（平台/治理层 vs 承载的治理实现），monorepo 全栈 TypeScript（12.26 万行，apps/web + apps/cli + packages/domain/db/services/daemon/sandbox）。亮点实现：`HarnessAdapter` 四方法契约（detect/buildLaunch/run/normalizeError）归一化事件/诊断/会话、`employeeToPersona()` 把数字员工映射成可 ed25519 签名的 OpenAgent persona-card（默认脱敏 + did:key）、`BudgetCheckResult` 三 scope 短路检查、远程 daemon 物化技能/知识上下文。报告含 5 幅 Mermaid 设计图（整体架构/AgentRouter 流程/daemon 时序/数据结构 classDiagram/实体 ER 图）、4 张官方 showcase 截图、5 张表格，并配 7 人研发团队 RBAC 重构实例闭环。如实标注局限：项目极早期、部署门槛高（Node 24 + PG16 + daemon）、沙箱隔离/存储隔离在路线图、非 CrewAI/LangGraph 替代（偏治理层非推理编排层）。6 篇微信解读交叉验证。

**关键词**: 数字员工、AgentRouter、harness 归一化、身份与运行时解耦、权限控制面、runtime_tool 审批、OpenAgent persona-card、三级预算熔断、远程 daemon、HKUDS、Apache-2.0

---

### Agent 强化学习 (Agent RL)（paper/）

#### 27. TeamTR

**文件**: [paper/agent_rl/teamtr/report.md](paper/agent_rl/teamtr/report.md)

**简介**: 调研 University of Arizona 等机构提出的 TeamTR（Trust-Region Fine-Tuning for Multi-Agent LLM Coordination，ICML 2026，arXiv:2605.15207）。针对"多智能体 LLM 系统往往不如单强模型 + best-of-N 采样"的协调失败问题，深入指出训练过程本身才是偏差根源——共享上下文团队的朴素序列微调中存在被忽视的复合占据度偏移（compounding occupancy shift）：每次更新改变团队状态分布，后续更新在缓存 rollout 上评估时分布不匹配会复合累积。借鉴 TRPO 信任域思想，在每次更新后重新采样以稳定多智能体微调。基于 VERL 框架实现。

**关键词**: 多智能体协调、信任域微调、复合占据度偏移、共享上下文团队、VERL、ICML 2026、arXiv 2605.15207

---

### Spec-Driven Development (vibe-coding)（open-source-project/）

#### 28. OpenSpec

**文件**: [open-source-project/vibe-coding/openspec/report.md](open-source-project/vibe-coding/openspec/report.md)

**简介**: 调研 OpenSpec 项目，为 AI 编码助手提供规范驱动开发(SDD)方法论和工具支持。通过结构化规范文件和增量规范(Delta Specs)机制管理需求变更，实现迭代式开发。

**关键词**: OpenSpec、规范驱动开发、Delta Specs、AI编码助手

---

#### 29. spec-kit (GitHub)

**文件**: [open-source-project/vibe-coding/spec-kit/report.md](open-source-project/vibe-coding/spec-kit/report.md)

**简介**: 调研 GitHub 开源的 spec-kit 工具集，实现 Spec-Driven Development。让开发者专注于产品场景和可预测结果，而非"vibe coding"每一行代码。

**关键词**: GitHub、spec-kit、规范驱动开发、可执行规范

---

#### 30. Superpowers

**文件**: [open-source-project/vibe-coding/superpowers/report.md](open-source-project/vibe-coding/superpowers/report.md)

**简介**: 调研 Superpowers 项目，一个面向 coding agent 的 agentic skills 框架和软件开发方法论。让 AI 编程助手具备"先设计、再规划、后实现"的结构化开发能力。

**关键词**: agentic skills、结构化开发、TDD、软件工程方法论
