# Research

个人研究调研仓库，用于记录和整理各类技术调研报告。

## 目录结构

```
agent/
├── auto-harness/                    # Agent Harness 自动优化相关研究
│   ├── autogenesis_research/        # Autogenesis 自进化协议调研
│   ├── continual_harness/           # Continual Harness 在线适应调研
│   ├── hermes-agent-self-evolution/ # Hermes Agent 自进化调研
│   ├── langchain_better_harness_research/  # LangChain Better Harness 调研
│   └── RewardHarness_research/      # RewardHarness 奖励建模调研
└── auto-research/                   # Agent 自动研究相关
    ├── auto-research/               # Karpathy autoresearch 项目调研
    └── pi-auto-research/            # pi-autoresearch 项目调研

vibe-coding/                         # Spec-Driven Development 相关研究
├── openspec/                        # OpenSpec 调研
├── spec-kit/                        # GitHub spec-kit 调研
└── superpowers_research/            # Superpowers 调研
```

## 调研报告

### Agent Harness 自动优化

#### 1. Autogenesis

**文件**: [agent/auto-harness/autogenesis_research/report.md](agent/auto-harness/autogenesis_research/report.md)

**简介**: 调研 Autogenesis 自进化协议，提出了一套面向 LLM 智能体自进化的协议标准。核心创新是定义了自进化单元（AEU）作为最小可进化组件，支持生命周期管理和版本追溯。

**关键词**: 自进化协议、AEU、生命周期管理、组件解耦

---

#### 2. Continual Harness

**文件**: [agent/auto-harness/continual_harness/report.md](agent/auto-harness/continual_harness/report.md)

**简介**: 调研 Princeton + DeepMind 的 Continual Harness 论文，解决具身智能体在长时序环境中脚手架自动构建和持续改进的问题。提出了在线适应的 Harness 优化方法。

**关键词**: 具身智能、在线适应、脚手架工程、长时序任务

---

#### 3. Hermes Agent Self-Evolution

**文件**: [agent/auto-harness/hermes-agent-self-evolution/report.md](agent/auto-harness/hermes-agent-self-evolution/report.md)

**简介**: 调研 Nous Research 的 Hermes Agent 自进化系统。作为一个独立的优化流水线，通过 API 调用实现对 prompt/instruction/few-shot 的变异和评估，无需 GPU 训练。

**关键词**: Hermes、自进化流水线、Prompt优化、ICLR 2026 Oral

---

#### 4. LangChain Better Harness

**文件**: [agent/auto-harness/langchain_better_harness_research/report.md](agent/auto-harness/langchain_better_harness_research/report.md)

**简介**: 调研 LangChain 发布的 Better Harness 工作，这是一套 eval 驱动的 agent harness 自动优化系统。核心思想是让一个"外部 Deep Agent"通过阅读评估反馈来自动改进另一个"目标Agent"的 harness 配置。

**关键词**: LangChain、评估驱动、Harness Hill Climbing、Deep Agents

---

#### 5. RewardHarness

**文件**: [agent/auto-harness/RewardHarness_research/report.md](agent/auto-harness/RewardHarness_research/report.md)

**简介**: 调研 RewardHarness 论文，提出自演进的奖励建模框架。仅用 0.05% 数据即可超越 GPT-5，实现了高效、可解释的奖励模型构建。

**关键词**: 奖励建模、自演进、数据效率、可解释性

---

### Agent 自动研究

#### 6. autoresearch (Karpathy)

**文件**: [agent/auto-research/auto-research/report.md](agent/auto-research/auto-research/report.md)

**简介**: 调研 Andrej Karpathy 的 autoresearch 项目。核心理念是让 AI Agent 在无人值守情况下自主迭代优化模型，人类编写指令约束，Agent 自主修改训练代码并运行实验循环。

**关键词**: Karpathy、自主研究、LLM训练、实验循环

---

#### 7. pi-autoresearch

**文件**: [agent/auto-research/pi-auto-research/report.md](agent/auto-research/pi-auto-research/report.md)

**简介**: 调研 pi-autoresearch 开源项目。作为 pi 终端 AI 编码代理的扩展，让 pi 能够自主优化用户的代码项目，包括测试速度、打包体积、训练损失等指标。

**关键词**: pi、终端代理、代码优化、自主迭代

---

### Spec-Driven Development (vibe-coding)

#### 8. OpenSpec

**文件**: [vibe-coding/openspec/report.md](vibe-coding/openspec/report.md)

**简介**: 调研 OpenSpec 项目，为 AI 编码助手提供规范驱动开发(SDD)方法论和工具支持。通过结构化规范文件和增量规范(Delta Specs)机制管理需求变更，实现迭代式开发。

**关键词**: OpenSpec、规范驱动开发、Delta Specs、AI编码助手

---

#### 9. spec-kit (GitHub)

**文件**: [vibe-coding/spec-kit/report.md](vibe-coding/spec-kit/report.md)

**简介**: 调研 GitHub 开源的 spec-kit 工具集，实现 Spec-Driven Development。让开发者专注于产品场景和可预测结果，而非"vibe coding"每一行代码。

**关键词**: GitHub、spec-kit、规范驱动开发、可执行规范

---

#### 10. Superpowers

**文件**: [vibe-coding/superpowers_research/report.md](vibe-coding/superpowers_research/report.md)

**简介**: 调研 Superpowers 项目，一个面向 coding agent 的 agentic skills 框架和软件开发方法论。让 AI 编程助手具备"先设计、再规划、后实现"的结构化开发能力。

**关键词**: agentic skills、结构化开发、TDD、软件工程方法论
