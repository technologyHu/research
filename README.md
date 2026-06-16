# Research

个人研究调研仓库，用于记录和整理各类技术调研报告。

## 目录结构

```
agent/
├── agent-framework/                 # Agent 框架相关研究
│   └── auto-harness-aha/            # AutoHarness (Aha) 开源框架调研
├── auto-harness/                    # Agent Harness 自动优化相关研究
│   ├── agentic-harness-engineering/ # Agentic Harness Engineering 综述调研
│   ├── auto-harness-deepmind/       # AutoHarness 代码约束框架自动合成调研
│   ├── autogenesis/                 # Autogenesis 自进化协议调研
│   ├── continual-harness/           # Continual Harness 在线适应调研
│   ├── hermes-agent-self-evolution/ # Hermes Agent 自进化调研
│   ├── langchain-better-harness/    # LangChain Better Harness 调研
│   ├── life-harness/                # Life-Harness 运行时适配调研
│   ├── reward-harness/              # RewardHarness 奖励建模调研
│   └── self-harness/                # Self-Harness 自优化 Harness 调研
└── auto-research/                   # Agent 自动研究相关
    ├── arbor/                       # Arbor 论文+代码综合调研
    ├── auto-research/               # Karpathy autoresearch 项目调研
    ├── ml-evolve/                   # ML-Evolve 机器学习进化调研
    └── pi-auto-research/            # pi-autoresearch 项目调研

vibe-coding/                         # Spec-Driven Development 相关研究
├── openspec/                        # OpenSpec 调研
├── spec-kit/                        # GitHub spec-kit 调研
└── superpowers/                     # Superpowers 调研
```

## 调研报告

### Agent 框架

#### 1. AutoHarness (Aha)

**文件**: [agent/agent-framework/auto-harness-aha/report.md](agent/agent-framework/auto-harness-aha/report.md)

**简介**: 调研 aiming-lab 开源的 AutoHarness (代号 Aha) 框架。轻量级 AI Agent 行为治理框架，核心理念是 "Agent = Model + Harness"。提供三层治理模式 (Core/Standard/Enhanced)，6-14步治理流水线，风险模式匹配，多层上下文管理，多 Agent 协作支持。2行代码零侵入集成，958 测试用例生产级质量。

**关键词**: Harness Engineering、治理流水线、风险分级、上下文管理、多Agent协作、零侵入集成

---

### Agent Harness 自动优化

#### 2. Agentic Harness Engineering

**文件**: [agent/auto-harness/agentic-harness-engineering/report.md](agent/auto-harness/agentic-harness-engineering/report.md)

**简介**: 调研复旦大学、北京大学、上海奇绩智峰联合提出的 AHE（Agentic Harness Engineering）框架。通过三层可观测性支柱（组件可观测性、经验可观测性、决策可观测性）将 Harness 演化转变为闭环自动化过程。核心创新是分层轨迹蒸馏流水线，将千万级 token 压缩为 10K 级可消费证据。在 Terminal-Bench 2 上将 pass@1 从 69.7% 提升至 77.0%，超越人工设计和自动化基线。

**关键词**: 可观测性驱动、轨迹蒸馏、闭环演化、组件解耦、arXiv 2604.25850

---

#### 3. Autogenesis

**文件**: [agent/auto-harness/autogenesis/report.md](agent/auto-harness/autogenesis/report.md)

**简介**: 调研 Autogenesis 自进化协议，提出了一套面向 LLM 智能体自进化的协议标准。核心创新是定义了自进化单元（AEU）作为最小可进化组件，支持生命周期管理和版本追溯。

**关键词**: 自进化协议、AEU、生命周期管理、组件解耦

---

#### 4. Continual Harness

**文件**: [agent/auto-harness/continual-harness/report.md](agent/auto-harness/continual-harness/report.md)

**简介**: 调研 Princeton + DeepMind 的 Continual Harness 论文，解决具身智能体在长时序环境中脚手架自动构建和持续改进的问题。提出了在线适应的 Harness 优化方法。

**关键词**: 具身智能、在线适应、脚手架工程、长时序任务

---

#### 5. Hermes Agent Self-Evolution

**文件**: [agent/auto-harness/hermes-agent-self-evolution/report.md](agent/auto-harness/hermes-agent-self-evolution/report.md)

**简介**: 调研 Nous Research 的 Hermes Agent 自进化系统。作为一个独立的优化流水线，通过 API 调用实现对 prompt/instruction/few-shot 的变异和评估，无需 GPU 训练。

**关键词**: Hermes、自进化流水线、Prompt优化、ICLR 2026 Oral

---

#### 6. LangChain Better Harness

**文件**: [agent/auto-harness/langchain-better-harness/report.md](agent/auto-harness/langchain-better-harness/report.md)

**简介**: 调研 LangChain 发布的 Better Harness 工作，这是一套 eval 驱动的 agent harness 自动优化系统。核心思想是让一个"外部 Deep Agent"通过阅读评估反馈来自动改进另一个"目标Agent"的 harness 配置。

**关键词**: LangChain、评估驱动、Harness Hill Climbing、Deep Agents

---

#### 7. RewardHarness

**文件**: [agent/auto-harness/reward-harness/report.md](agent/auto-harness/reward-harness/report.md)

**简介**: 调研 RewardHarness 论文，提出自演进的奖励建模框架。仅用 0.05% 数据即可超越 GPT-5，实现了高效、可解释的奖励模型构建。

**关键词**: 奖励建模、自演进、数据效率、可解释性

---

#### 8. Self-Harness

**文件**: [agent/auto-harness/self-harness/report.md](agent/auto-harness/self-harness/report.md)

**简介**: 调研上海AI Lab提出的Self-Harness论文，首次提出让LLM Agent自己改进运行框架的闭环范式。三阶段循环（Weakness Mining → Harness Proposal → Proposal Validation）实现无需人类专家或更强外部模型的自优化。在Terminal-Bench-2.0上，三个模型均获得显著提升，最高相对提升138%。

**关键词**: 自优化Harness、弱点挖掘、回归测试、模型特异性、NeurIPS 2026

---

#### 9. AutoHarness (DeepMind)

**文件**: [agent/auto-harness/auto-harness-deepmind/report.md](agent/auto-harness/auto-harness-deepmind/report.md)

**简介**: 调研 Google DeepMind 提出的 AutoHarness 方法，让 LLM 自动合成代码约束框架（Harness）。核心思想是将规则判断从 LLM 的概率性推理转移到确定性执行的代码，通过树搜索和 Thompson 采样管理多个代码假设。在 145 个 TextArena 游戏上实现 100% 合法动作率，使较小的 Gemini-2.5-Flash 能够战胜更大的 Gemini-2.5-Pro（56.3% 胜率）。代码即策略模式下，推理成本几乎为零，在 16 个单人游戏上平均奖励 0.870，超越 GPT-5.2-High。

**关键词**: 代码约束框架、自动合成、树搜索、Thompson采样、代码即策略、ICLR 2026、arXiv 2603.03329

---

#### 10. LIFE-HARNESS

**文件**: [agent/auto-harness/life-harness/report.md](agent/auto-harness/life-harness/report.md)

**简介**: 调研北京大学提出的 LIFE-HARNESS，一个面向确定性 LLM Agent 的生命周期感知运行时外壳。核心思想是"适配接口而非模型"，通过四层架构（环境契约层、技能层、动作层、轨迹层）实现不改模型权重的 Agent 能力提升。在 126 个 model-environment 设置中平均相对改进 88.5%，且用小模型生成的 Harness 可直接迁移到大模型。

**关键词**: 运行时适配、四层架构、跨模型迁移、确定性Agent、arXiv 2605.22166

---

### Agent 自动研究

#### 11. Arbor

**文件**: [agent/auto-research/arbor/report.md](agent/auto-research/arbor/report.md)

**简介**: 调研中国人民大学和微软研究院联合提出的 Arbor 框架。通过假设树细化（HTR）将自主研究转变为累积的证据驱动过程。核心创新是持久协调器+短期执行器的双Agent架构，以及假设树作为研究状态的组织方式。在六项真实研究任务上超过 Codex 和 Claude Code 平均增益的 2.5 倍，MLE-Bench Lite 达到 86.36% Any Medal。

**关键词**: 假设树、自主优化、协调器-执行器、证据驱动、arXiv 2606.11926

---

#### 12. autoresearch (Karpathy)

**文件**: [agent/auto-research/auto-research/report.md](agent/auto-research/auto-research/report.md)

**简介**: 调研 Andrej Karpathy 的 autoresearch 项目。核心理念是让 AI Agent 在无人值守情况下自主迭代优化模型，人类编写指令约束，Agent 自主修改训练代码并运行实验循环。

**关键词**: Karpathy、自主研究、LLM训练、实验循环

---

#### 13. pi-autoresearch

**文件**: [agent/auto-research/pi-auto-research/report.md](agent/auto-research/pi-auto-research/report.md)

**简介**: 调研 pi-autoresearch 开源项目。作为 pi 终端 AI 编码代理的扩展，让 pi 能够自主优化用户的代码项目，包括测试速度、打包体积、训练损失等指标。

**关键词**: pi、终端代理、代码优化、自主迭代

---

### Spec-Driven Development (vibe-coding)

#### 14. OpenSpec

**文件**: [vibe-coding/openspec/report.md](vibe-coding/openspec/report.md)

**简介**: 调研 OpenSpec 项目，为 AI 编码助手提供规范驱动开发(SDD)方法论和工具支持。通过结构化规范文件和增量规范(Delta Specs)机制管理需求变更，实现迭代式开发。

**关键词**: OpenSpec、规范驱动开发、Delta Specs、AI编码助手

---

#### 15. spec-kit (GitHub)

**文件**: [vibe-coding/spec-kit/report.md](vibe-coding/spec-kit/report.md)

**简介**: 调研 GitHub 开源的 spec-kit 工具集，实现 Spec-Driven Development。让开发者专注于产品场景和可预测结果，而非"vibe coding"每一行代码。

**关键词**: GitHub、spec-kit、规范驱动开发、可执行规范

---

#### 16. Superpowers

**文件**: [vibe-coding/superpowers/report.md](vibe-coding/superpowers/report.md)

**简介**: 调研 Superpowers 项目，一个面向 coding agent 的 agentic skills 框架和软件开发方法论。让 AI 编程助手具备"先设计、再规划、后实现"的结构化开发能力。

**关键词**: agentic skills、结构化开发、TDD、软件工程方法论
