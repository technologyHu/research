# LLM Ensemble 方向调研计划

> **调研计划文档** — 基于 `D:\code\work\moa\moa_evolution_roadmap.md` 整理的 LLM Ensemble（MoA 与多模型路由）方向调研计划。以**具体工作为粒度**列出覆盖清单与调研顺序，覆盖 before / during / after inference / cascade / benchmark 五条主线以及对应的产品与工程实现。
>
> 生成日期：2026-08-05
> 范围：系统层面多 LLM 的组合、选择、路由、聚合、级联、评测；不含模型内部 MoE 专家路由。

---

## 0. 调研原则与总体顺序

### 0.1 调研原则

1. **先综述建坐标系，再按主线深挖**：所有工作先挂到 before / during / after / cascade / benchmark 五分类下，避免重复造轮子。
2. **以"具体工作"为粒度**：本计划每个条目都是一篇论文 / 一个产品 / 一个 benchmark，不停留在概念层。
3. **主线内顺序**：奠基工作（被反复引用）→ 关键对照/质疑工作 → 工程实现/产品对照 → 评测配套。
4. **2026 年新工作降级处理**：MTRouter、Conformal LLM Routing、ICL-Router、ZeroRouter、CP-Router、R2-Route、RouteMoA、Attention-MoA、BiCSRouter、ACRouter、RouteJudge、CodeRouterBench 等目前仅 arXiv / 会议接收，**主线吃透前不前置精读**，仅在确定切入点后针对性补强。
5. **评测贯穿全程**：MoA 一开始就要用 AlpacaEval / MT-Bench；路由一开始就要用 RouterBench。评测不放到最后。

### 0.2 阶段速查

| 顺序 | 阶段 | 投入 | 必读核心工作 | 产出 |
|---|---|---|---|---|
| 1 | 阶段 0 坐标系 | 0.5 天 | LLM Ensemble 综述（2502.18036） | taxonomy 速查表 |
| 2 | 阶段 1 MoA 主线 | 1–2 天 | MoA 原始 + Self-MoA + Together MoA + SMoA/RMoA | MoA 变体对比与信息流退化全景 |
| 3 | 阶段 2 路由主线 | 1.5–2 天 | RouteLLM + GraphRouter + MixLLM + BEST-Route | 路由三路线（偏好/图/bandit）与产品形态对照 |
| 4 | 阶段 3 级联主线 | 0.5–1 天 | FrugalGPT + AutoMix + Unified Routing&Cascading | routing 与 cascade 统一框架 |
| 5 | 阶段 4 评测体系 | 贯穿全程 | RouterBench + RouterEval + RouterArena + AlpacaEval/MT-Bench | 选定主评测 |
| 6 | 阶段 5 during-inference | 按需 | Collab | 多半跳过 |
| 7 | 前沿补强 | 按需 | 2026 年细分方向 | 针对性补强 |

> **最小可行阅读集**：若只读 5 篇，选 LLM Ensemble 综述（2502.18036）、MoA 原始（2406.04692）、Self-MoA（2502.00674）、RouteLLM（2406.18665）、A Unified Approach to Routing and Cascading（ICML 2025）。覆盖"分类 + after 主线 + 质疑 + before 主线 + before/after 统一"。

---

## 1. 阶段 0｜建立坐标系（必读）

**目标**：用一个统一 taxonomy 把后续所有工作挂上去。

| 序号 | 工作 | 类型 | 优先级 | 链接 |
|---|---|---|---|---|
| 0.1 | Harnessing Multiple Large Language Models: A Survey on LLM Ensemble | 综述 | ⭐⭐⭐ 必读 | [arXiv](https://arxiv.org/abs/2502.18036) / [HTML](https://arxiv.org/html/2502.18036) / [project](https://junchenzhi.github.io/LLM-Ensemble/) |
| 0.2 | Ensemble Large Language Models: A Survey | 综述 | ⭐ 对照 | [MDPI Information](https://www.mdpi.com/2078-2489/16/8/688) |
| 0.3 | Awesome-LLM-Ensemble | 索引 | ⭐ 当索引用 | [GitHub](https://github.com/junchenzhi/Awesome-LLM-Ensemble) |

**重点抓取**：
- 0.1 抓 before / during / after 三段定义，以及 routing / cascade / selection / aggregation 的边界划分。
- 0.2 从传统 ensemble learning 视角的补充对照，篇幅短，快速过。
- 0.3 遇到新工作先来这里查分类，不深读。

**产出**：taxonomy 速查表（哪个工作落在哪一格）。

---

## 2. 阶段 1｜MoA 主线（After-Inference，核心）

**目标**：吃透 MoA 及其变体演化，建立"信息流退化 / 异构是否总有益"等关键问题的全景。

### 2.1 奠基与主线工作

| 序号 | 工作 | 年份/场景 | 优先级 | 链接 |
|---|---|---|---|---|
| 1.1 | Mixture-of-Agents Enhances Large Language Model Capabilities（**原始 MoA**） | 2024 / ICLR 2025 | ⭐⭐⭐ 必读 | [arXiv](https://arxiv.org/abs/2406.04692) / [ICLR](https://proceedings.iclr.cc/paper_files/paper/2025/hash/5434be94e82c54327bb9dcaf7fca52b6-Abstract-Conference.html) |
| 1.2 | Together MoA（工程参考实现） | 2024 / 工程实现 | ⭐⭐⭐ 必看 | [blog](https://www.together.ai/blog/together-moa) / [docs](https://docs.together.ai/docs/mixture-of-agents) / [GitHub](https://github.com/togethercomputer/moa) |
| 1.3 | Rethinking Mixture-of-Agents / **Self-MoA** | 2025 / arXiv | ⭐⭐⭐ 关键质疑，必读 | [arXiv](https://arxiv.org/abs/2502.00674) / [HF](https://huggingface.co/papers/2502.00674) |

**重点抓取**：
- 1.1 layered 结构、aggregator 职责、reference model 异构假设——所有后续变体的 baseline。
- 1.2 真实部署里 MoA 长什么样、aggregator 怎么落地、用什么 benchmark（AlpacaEval）。
- 1.3 质疑"异构 MoA 是否总有益"，给出 Self-MoA baseline。决定后续评估任何 MoA 变体时对照组怎么设。

### 2.2 信息流退化子问题（并列读）

| 序号 | 工作 | 年份/场景 | 优先级 | 链接 |
|---|---|---|---|---|
| 1.4 | SMoA: Sparse Mixture-of-Agents | 2025 / PAKDD | ⭐⭐ 必读 | [arXiv](https://arxiv.org/abs/2411.03284) / [KAUST](https://repository.kaust.edu.sa/items/e02a890c-2744-4493-9a10-68afe363c969) |
| 1.5 | RMoA: Residual Mixture-of-Agents | 2025 / Findings of ACL | ⭐⭐ 必读 | [arXiv](https://arxiv.org/abs/2505.24442) |

**重点抓取**：两者都解决 MoA 成本 / 信息退化问题，但机制不同（SMoA：response selection + early stopping；RMoA：diversity selection + residual extraction/aggregation）。读完形成"MoA 信息流退化"子问题全景。

### 2.3 应用延伸与近亲

| 序号 | 工作 | 年份/场景 | 优先级 | 链接 |
|---|---|---|---|---|
| 1.6 | Improving Model Alignment Through Collective Intelligence of Open-Source Models / **MoAA** | 2025 / ICML | ⭐ 略读 | [PMLR](https://proceedings.mlr.press/v267/wang25dr.html) |
| 1.7 | Dipper（同模型多样 prompt 并行 ensemble） | 2025 / EMNLP | ⭐ 略读作背景 | [ACL Anthology](https://aclanthology.org/2025.emnlp-main.1801/) |

**重点抓取**：
- 1.6 视角不同——用 MoA 生成对齐数据而非直接推理聚合，知道有这条岔路即可。
- 1.7 Self-MoA 近亲，同模型多路径。

### 2.4 产品化形态对照

| 序号 | 工作 | 类型 | 优先级 | 链接 |
|---|---|---|---|---|
| 1.8 | Hermes Agent MoA（`moa` provider 虚拟模型） | 产品实现 | ⭐⭐ 必看 | [docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/mixture-of-agents) / [source mirror](https://fossies.org/linux/hermes-agent/website/docs/user-guide/features/mixture-of-agents.md) |

### 2.5 前沿（主线吃透后再看，不前置）

| 序号 | 工作 | 年份/场景 | 优先级 | 链接 |
|---|---|---|---|---|
| 1.9 | RouteMoA（routing 引入 MoA + judge posterior correction） | 2026 / arXiv | ⭐ 按需 | [arXiv](https://arxiv.org/abs/2601.18130) |
| 1.10 | Attention-MoA（inter-agent semantic attention + residual synthesis） | 2026 / arXiv | ⭐ 按需 | [arXiv](https://arxiv.org/abs/2601.16596) |
| 1.11 | BiCSRouter（单 agent 强推理 vs 多 agent 协作 bi-level routing） | 2026 / Findings of ACL | ⭐ 按需 | [ACL Anthology](https://aclanthology.org/2026.findings-acl.947/) |

### 2.6 MoA 评测配套（本阶段就要熟悉）

| 序号 | Benchmark | 优先级 | 链接 |
|---|---|---|---|
| 1.12 | AlpacaEval / AlpacaEval 2.0 | ⭐⭐⭐ 必用 | [AlpacaEval](https://tatsu-lab.github.io/alpaca_eval/) |
| 1.13 | MT-Bench | ⭐⭐ 必用 | [FastChat/llm_judge](https://github.com/lm-sys/FastChat/tree/main/fastchat/llm_judge) |
| 1.14 | FLASK（多维度质量评价） | ⭐⭐ 必用 | [FLASK](https://github.com/kaistAI/FLASK) |

**重点抓取**：MoA 所有收益都靠这三个衡量；FLASK 能告诉你聚合在哪个能力维度真正涨点。

---

## 3. 阶段 2｜路由主线（Before-Inference，核心）

**目标**：吃透路由三路线（偏好数据 / 图建模 / bandit），并对照产品形态。

### 3.1 三条主线

| 序号 | 工作 | 年份/场景 | 优先级 | 链接 |
|---|---|---|---|---|
| 2.1 | RouteLLM: Learning to Route LLMs from Preference Data | 2024 / ICLR 2025 | ⭐⭐⭐ 必读 | [arXiv](https://arxiv.org/abs/2406.18665) / [ICLR](https://proceedings.iclr.cc/paper_files/paper/2025/hash/5503a7c69d48a2f86fc00b3dc09de686-Abstract-Conference.html) / [GitHub](https://github.com/lm-sys/RouteLLM) |
| 2.2 | GraphRouter: A Graph-based Router for LLM Selections | 2024 / ICLR 2025 | ⭐⭐⭐ 必读 | [arXiv](https://arxiv.org/abs/2410.03834) / [ICLR](https://proceedings.iclr.cc/paper_files/paper/2025/hash/41b6674c28a9b93ec8d22a53ca25bc3b-Abstract-Conference.html) |
| 2.3 | MixLLM: Dynamic Routing in Mixed Large Language Models | 2025 / NAACL | ⭐⭐⭐ 必读 | [ACL Anthology](https://aclanthology.org/2025.naacl-long.545/) |

**重点抓取**：
- 2.1 偏好数据训练 router、强弱模型二选一、OpenAI-compatible server——**先看 repo 和 server 形态**，决定后续所有路由工作的工程接口预期。
- 2.2 异构图建模 task/query/LLM，泛化到新任务新模型，RouteLLM 之外的另一条 router 设计主线。
- 2.3 routing 建成动态上下文 bandit，质量/成本/延迟多目标——**工程化最关心的视角**，与 RouteLLM 偏好路线形成对照。

### 3.2 NeurIPS 2025 三篇（选 1–2 篇精读）

| 序号 | 工作 | 年份/场景 | 优先级 | 链接 |
|---|---|---|---|---|
| 2.4 | Lookahead Routing for Large Language Models | 2025 / NeurIPS | ⭐⭐ 选读 | [NeurIPS](https://papers.neurips.cc/paper_files/paper/2025/hash/552456ddb6f4b2956b2933ab83f56df0-Abstract-Conference.html) |
| 2.5 | Causal LLM Routing | 2025 / NeurIPS | ⭐⭐ 建议精读 | [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2025/hash/357774d53e5ee21c5f08ba779e3b5dd9-Abstract-Conference.html) |
| 2.6 | Efficient Training-Free Online Routing | 2025 / NeurIPS | ⭐⭐ 选读 | [NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2025/hash/c878e34a1b2095ae8177961ba24d642d-Abstract-Conference.html) |

**重点抓取**：三种新信号源（潜在输出表征 / 因果去偏 / 在线 training-free）。建议精读 2.5，因为"部署日志里只有实际调用结果"这个约束最贴近真实工程场景。

### 3.3 路由与 test-time compute 桥梁

| 序号 | 工作 | 年份/场景 | 优先级 | 链接 |
|---|---|---|---|---|
| 2.7 | BEST-Route（模型 + best-of-n 采样次数联合决策） | 2025 / ICML | ⭐⭐⭐ 必读 | [MSR](https://www.microsoft.com/en-us/research/publication/best-route-adaptive-llm-routing-with-test-time-optimal-compute/) / [GitHub](https://github.com/microsoft/best-route-llm) |

**重点抓取**：把 routing 扩展为"模型 + 采样预算"联合决策，是路由和 test-time compute 的桥梁，也横跨到级联部分。

### 3.4 产品与工程实现对照（挑 2 个代表）

| 序号 | 产品/工程 | 优先级 | 链接 |
|---|---|---|---|
| 2.8 | OpenRouter Auto Router | ⭐⭐ | [docs](https://openrouter.ai/docs/guides/routing/routers/auto-router) / [model](https://openrouter.ai/openrouter/auto) / [announcement](https://openrouter.ai/blog/announcements/happy-new-year-introducing-a-new-auto-router/) / [guide](https://openrouter.ai/blog/insights/model-routing/) |
| 2.9 | Not Diamond（预训练/自定义 router + modelSelect API） | ⭐⭐ 建议看 | [overview](https://docs.notdiamond.ai/docs/what-is-not-diamond) / [model routing](https://docs.notdiamond.ai/docs/what-is-model-routing) / [modelSelect API](https://docs.notdiamond.ai/reference/token_model_select_v2_modelrouter_modelselect_post) |
| 2.10 | Martian Model Router / Gateway | ⭐⭐ 建议看 | [docs](https://docs.withmartian.com/) / [SDK](https://withmartian.github.io/martian-sdk-python/api/router.html) / [SDK overview](https://withmartian.github.io/martian-sdk-python/index.html) |
| 2.11 | LiteLLM Router / Auto Routing（开源 gateway） | ⭐⭐⭐ 必看 | [docs](https://docs.litellm.ai/) / [routing](https://docs.litellm.com.cn/docs/routing) / [auto routing](https://docs.litellm.com.cn/docs/proxy/auto_routing) / [GitHub](https://github.com/BerriAI/litellm) |
| 2.12 | Portkey AI Gateway | ⭐⭐ | [AI Gateway](https://portkey.ai/docs/product/ai-gateway) / [fallbacks](https://portkey.ai/docs/product/ai-gateway/fallbacks) / [GitHub](https://github.com/portkey-ai/gateway) |
| 2.13 | UnifyRoute | ⭐ | [website](https://www.unifyroute.com/) |

**建议组合**：2.11 LiteLLM（开源 gateway，看生产路由落地）+ 2.9 Not Diamond 或 2.10 Martian（商业 router-as-a-service 形态）。

### 3.5 前沿细分方向（确定切入点后再针对性精读，不前置）

| 序号 | 工作 | 年份/场景 | 细分点 | 链接 |
|---|---|---|---|---|
| 2.14 | Universal Model Routing / UniRoute | 2025 / ICLR Workshop | 动态模型池 + 未见模型接入 | [arXiv](https://arxiv.org/abs/2502.08773) / [ML Anthology](https://mlanthology.org/iclrw/2025/jitkrittum2025iclrw-universal/) |
| 2.15 | MTRouter | 2026 / ACL | 多轮任务，历史-模型联合 embedding | [ACL Anthology](https://aclanthology.org/2026.acl-long.2045/) |
| 2.16 | Conformal LLM Routing | 2026 / ACL SRW | conformal calibration + distribution-free 风险控制 | [ACL Anthology](https://aclanthology.org/2026.acl-srw.70/) |
| 2.17 | ICL-Router | 2026 / AAAI | in-context vectors 表示模型能力 | [AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/40628) |
| 2.18 | ZeroRouter | 2026 / AAAI | 潜在空间解耦 difficulty 与 model profiling | [AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/40970) |
| 2.19 | CP-Router | 2026 / AAAI | 普通 LLM 与 large reasoning model 不确定性感知路由 | [AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/40589) |
| 2.20 | R2-Route | 2026 / ICML | 模型 + 输出长度预算联合决策 | [OpenReview](https://openreview.net/forum?id=S3m1tSp8F4&noteId=PPahOFqvJa) |
| 2.21 | Agent-as-a-Router / ACRouter | 2026 / arXiv | agentic C-A-F 循环 router | [arXiv](https://arxiv.org/abs/2606.22902) |

---

## 4. 阶段 3｜级联主线（Cascade，最短）

**目标**：把 before（routing）和 cascade 在脑子里打通成统一框架。

| 序号 | 工作 | 年份/场景 | 优先级 | 链接 |
|---|---|---|---|---|
| 3.1 | FrugalGPT | 2023 / 成本优化 | ⭐⭐⭐ 必读 | [arXiv](https://arxiv.org/abs/2305.05176) |
| 3.2 | AutoMix: Automatically Mixing Language Models | 2024 / NeurIPS | ⭐⭐⭐ 必读 | [project](https://automix-llm.github.io/automix/) / [NeurIPS](https://papers.nips.cc/paper_files/paper/2024/hash/ecda225cb187b40ea8edc1f46b03ffda-Abstract-Conference.html) / [HF](https://huggingface.co/papers/2310.12963) |
| 3.3 | A Unified Approach to Routing and Cascading for LLMs | 2025 / ICML | ⭐⭐⭐ 必读 | [PMLR](https://proceedings.mlr.press/v267/dekoninck25a.html) |
| 3.4 | BEST-Route（级联视角） | 2025 / ICML | ⭐⭐ 已在 2.7 | [MSR](https://www.microsoft.com/en-us/research/publication/best-route-adaptive-llm-routing-with-test-time-optimal-compute/) / [GitHub](https://github.com/microsoft/best-route-llm) |
| 3.5 | LiteLLM fallback / routing（工程级联） | 工程级联 | ⭐⭐ 已在 2.11 | [routing](https://docs.litellm.com.cn/docs/routing) / [auto routing](https://docs.litellm.com.cn/docs/proxy/auto_routing) / [GitHub](https://github.com/BerriAI/litellm) |
| 3.6 | Portkey fallbacks（工程级联） | 工程级联 | ⭐⭐ 已在 2.12 | [fallbacks](https://portkey.ai/docs/product/ai-gateway/fallbacks) / [AI Gateway](https://portkey.ai/docs/product/ai-gateway) / [GitHub](https://github.com/portkey-ai/gateway) |

**重点抓取**：
- 3.1 级联奠基，prompt adaptation / approximation / cascade 三件套。
- 3.2 小模型自验证 + POMDP router 决定升级——"基于置信度/可靠性信号升级"代表。
- 3.3 把一次性 routing 和逐步 cascading 统一进一个框架，**读完打通阶段 2 和阶段 3**。
- 3.4 / 3.5 / 3.6 不额外投入，阶段 2 已覆盖 gateway 产品，这里只补 fallback 链这一面。

---

## 5. 阶段 4｜评测体系（Benchmark，贯穿全程）

**目标**：把每个 benchmark 对"自己要做的系统"的意义对齐，选定主评测。

### 5.1 路由与系统评测

| 序号 | 工作 | 年份/场景 | 优先级 | 链接 |
|---|---|---|---|---|
| 4.1 | RouterBench | 2024 / routing benchmark | ⭐⭐⭐ 必用 | [HF](https://huggingface.co/papers/2403.12031) / [Martian blog](https://withmartian.com/post/introducing-routerbench) |
| 4.2 | RouterEval | 2025 / EMNLP Findings | ⭐⭐⭐ 必用 | [ACL Anthology](https://aclanthology.org/2025.findings-emnlp.208/) |
| 4.3 | RouterArena | 2025 / open platform | ⭐⭐⭐ 建议作主评测 | [arXiv](https://arxiv.org/abs/2510.00202) / [leaderboard](https://routeworks.github.io/) / [HF dataset](https://huggingface.co/datasets/RouteWorks/RouterArena) / [GitHub](https://github.com/RouteWorks/RouterArena) |
| 4.4 | RouteJudge | 2026 / arXiv / ICML workshop | ⭐⭐ 理念必看 | [arXiv DOI](https://doi.org/10.48550/arXiv.2606.18774) |
| 4.5 | CodeRouterBench | 2026 / coding routing | ⭐ coding 场景才看 | [arXiv](https://arxiv.org/abs/2606.22902) |

**重点抓取**：
- 4.1 路由评测基础，提供候选模型输出/成本/任务记录。
- 4.2 大规模，研究候选模型数增加时 routing 的 scaling 行为。
- 4.3 最全面（9 领域 44 类、Bloom 难度、accuracy/cost/optimality/robustness/latency、Arena Score），**建议作为主评测参照**。
- 4.4 重点在"评价 router 决策质量"而非"模型回答质量"，理念最贴近工程，但 2026 年才出，先了解理念暂不深究数据。
- 4.5 仅当关注 coding agent 场景路由时才看（与 ACRouter 配套）。

### 5.2 MoA / 聚合评测常用基准（与阶段 1 配套）

已在 2.6 列出（AlpacaEval / MT-Bench / FLASK），此处不重复。

---

## 6. 阶段 5｜推理中处理（During-Inference，按需）

| 序号 | 工作 | 年份/场景 | 优先级 | 链接 |
|---|---|---|---|---|
| 5.1 | Collab: Controlled Decoding using Mixture of Agents for LLM Alignment | 2025 / ICLR | ⭐ 按需 | [ICLR](https://proceedings.iclr.cc/paper_files/paper/2025/hash/2e79dce47c5bbe738dff9c05ace8a037-Abstract-Conference.html) |

**处理建议**：roadmap 这一类只有一篇，且与你产品/系统形态关系较远。除非明确要做 token-level controlled decoding，否则**整个阶段 5 可跳过或只读摘要**。

---

## 7. 调研覆盖统计

### 7.1 按类型

| 类型 | 数量 | 说明 |
|---|---:|---|
| 学术/算法论文 | ~33 | 含必读核心与前沿细分 |
| 综述 | 2 | 阶段 0 坐标系 |
| 索引仓库 | 1 | Awesome-LLM-Ensemble |
| 产品/工程实现 | ~8 | 路由产品 + MoA 产品 |
| Benchmark | ~8 | 路由评测 + MoA 评测 |

### 7.2 按优先级

| 优先级 | 含义 | 大致数量 |
|---|---|---:|
| ⭐⭐⭐ | 必读/必用，主线核心 | ~15 |
| ⭐⭐ | 必看/选读，重要对照 | ~12 |
| ⭐ | 略读/按需，前沿或近亲 | ~17 |

### 7.3 按阶段

| 阶段 | 覆盖工作数 | 必读核心 |
|---|---:|---|
| 阶段 0 坐标系 | 3 | LLM Ensemble 综述 |
| 阶段 1 MoA | 14 | MoA + Self-MoA + Together MoA + SMoA/RMoA |
| 阶段 2 路由 | 21 | RouteLLM + GraphRouter + MixLLM + BEST-Route |
| 阶段 3 级联 | 6（含与阶段 2 共享） | FrugalGPT + AutoMix + Unified |
| 阶段 4 评测 | 5 + 3 共享 | RouterBench + RouterEval + RouterArena |
| 阶段 5 during | 1 | — |

---

## 8. 调研执行建议

1. **先建 taxonomy 速查表**（阶段 0），后续每读一篇就往表里填一行分类。
2. **MoA 主线先于路由主线**：roadmap 标题即 MoA，且 after-inference 概念更直观，作为热身。
3. **评测贯穿全程**：阶段 1 开始用 AlpacaEval/MT-Bench，阶段 2 开始用 RouterBench，阶段 4 集中梳理时再选 RouterArena 作主评测。
4. **2026 年前沿统一放到主线吃透后**：先不碰，避免被未沉淀工作带偏主线判断。
5. **产品与工程对照和学术工作同步进行**：每个主线读完学术奠基后，立刻看 1–2 个对应产品，互相印证落地形态。
6. **阶段 5 默认跳过**，除非产品形态明确涉及 token-level controlled decoding。

---

## 9. 调研进度跟踪

以**具体工作为粒度**记录每项调研的进度、状态与产出。所有工作初始为 ⬜ 未开始，调研推进时更新状态并在"笔记/产出"列填写对应 `report.md` 路径或要点链接。

**状态图例**：⬜ 未开始 ｜ 🟦 进行中 ｜ ✅ 已完成 ｜ ⏭️ 跳过/暂缓

### 9.1 阶段 0｜坐标系

| 序号 | 工作 | 优先级 | 状态 | 笔记/产出 | 备注 |
|---|---|---|---|---|---|
| 0.1 | Harnessing Multiple LLMs 综述（2502.18036） | ⭐⭐⭐ | ✅ | [report.md](./paper/survey/report.md) | taxonomy 速查表来源，IJCAI Survey 2026，已建坐标系 |
| 0.2 | Ensemble LLMs: A Survey（MDPI） | ⭐ | ⬜ |  | 对照视角 |
| 0.3 | Awesome-LLM-Ensemble | ⭐ | ✅ | [Awesome-LLM-Ensemble](https://github.com/junchenzhi/Awesome-LLM-Ensemble) | 当索引用，综述配套清单，254 star，已作引用源 |

### 9.2 阶段 1｜MoA 主线

| 序号 | 工作 | 优先级 | 状态 | 笔记/产出 | 备注 |
|---|---|---|---|---|---|
| 1.1 | Mixture-of-Agents 原始（2406.04692） | ⭐⭐⭐ | ✅ | [report.md](./paper/moa/report.md) | 所有变体 baseline，已建 proposer/aggregator 框架 |
| 1.2 | Together MoA 工程实现 | ⭐⭐⭐ | ✅ | [report.md](./paper/moa/report.md) §4 | 部署形态，代码分析章节已覆盖 moa.py/advanced-moa.py |
| 1.3 | Rethinking MoA / Self-MoA（2502.00674） | ⭐⭐⭐ | ⬜ |  | 关键质疑，决定对照组 |
| 1.4 | SMoA：Sparse Mixture-of-Agents | ⭐⭐ | ⬜ |  | selection + early stopping |
| 1.5 | RMoA：Residual Mixture-of-Agents | ⭐⭐ | ⬜ |  | residual extraction |
| 1.6 | MoAA（ICML 2025） | ⭐ | ⬜ |  | 应用延伸，对齐数据 |
| 1.7 | Dipper（EMNLP 2025） | ⭐ | ⬜ |  | Self-MoA 近亲 |
| 1.8 | Hermes Agent MoA 产品 | ⭐⭐ | ⬜ |  | 产品化形态 |
| 1.9 | RouteMoA | ⭐ | ⬜ |  | 前沿，主线后看 |
| 1.10 | Attention-MoA | ⭐ | ⬜ |  | 前沿，主线后看 |
| 1.11 | BiCSRouter | ⭐ | ⬜ |  | 前沿，主线后看 |
| 1.12 | AlpacaEval / AlpacaEval 2.0 | ⭐⭐⭐ | ⬜ |  | 评测配套 |
| 1.13 | MT-Bench | ⭐⭐ | ⬜ |  | 评测配套 |
| 1.14 | FLASK | ⭐⭐ | ⬜ |  | 评测配套 |

### 9.3 阶段 2｜路由主线

| 序号 | 工作 | 优先级 | 状态 | 笔记/产出 | 备注 |
|---|---|---|---|---|---|
| 2.1 | RouteLLM（2406.18665） | ⭐⭐⭐ | ⬜ |  | 偏好数据线，先看 repo/server |
| 2.2 | GraphRouter（2410.03834） | ⭐⭐⭐ | ⬜ |  | 图建模线 |
| 2.3 | MixLLM（NAACL 2025） | ⭐⭐⭐ | ⬜ |  | bandit 线，工程化视角 |
| 2.4 | Lookahead Routing（NeurIPS 2025） | ⭐⭐ | ⬜ |  | 选读 |
| 2.5 | Causal LLM Routing（NeurIPS 2025） | ⭐⭐ | ⬜ |  | 建议精读 |
| 2.6 | Efficient Training-Free Online Routing（NeurIPS 2025） | ⭐⭐ | ⬜ |  | 选读 |
| 2.7 | BEST-Route（ICML 2025） | ⭐⭐⭐ | ⬜ |  | 路由+test-time compute 桥梁 |
| 2.8 | OpenRouter Auto Router | ⭐⭐ | ⬜ |  | 产品 |
| 2.9 | Not Diamond | ⭐⭐ | ⬜ |  | 产品，router-as-a-service |
| 2.10 | Martian Model Router / Gateway | ⭐⭐ | ⬜ |  | 产品 |
| 2.11 | LiteLLM Router / Auto Routing | ⭐⭐⭐ | ⬜ |  | 开源 gateway，必看 |
| 2.12 | Portkey AI Gateway | ⭐⭐ | ⬜ |  | 产品 |
| 2.13 | UnifyRoute | ⭐ | ⬜ |  | 产品 |
| 2.14 | UniRoute（ICLR Workshop 2025） | ⭐ | ⬜ |  | 前沿，动态模型池 |
| 2.15 | MTRouter（ACL 2026） | ⭐ | ⬜ |  | 前沿，多轮 |
| 2.16 | Conformal LLM Routing（ACL SRW 2026） | ⭐ | ⬜ |  | 前沿，conformal |
| 2.17 | ICL-Router（AAAI 2026） | ⭐ | ⬜ |  | 前沿 |
| 2.18 | ZeroRouter（AAAI 2026） | ⭐ | ⬜ |  | 前沿 |
| 2.19 | CP-Router（AAAI 2026） | ⭐ | ⬜ |  | 前沿 |
| 2.20 | R2-Route（ICML 2026） | ⭐ | ⬜ |  | 前沿 |
| 2.21 | ACRouter / Agent-as-a-Router | ⭐ | ⬜ |  | 前沿，agentic |

### 9.4 阶段 3｜级联主线

| 序号 | 工作 | 优先级 | 状态 | 笔记/产出 | 备注 |
|---|---|---|---|---|---|
| 3.1 | FrugalGPT（2305.05176） | ⭐⭐⭐ | ⬜ |  | 级联奠基 |
| 3.2 | AutoMix（NeurIPS 2024） | ⭐⭐⭐ | ⬜ |  | 自验证+POMDP |
| 3.3 | A Unified Approach to Routing and Cascading（ICML 2025） | ⭐⭐⭐ | ⬜ |  | 统一框架 |
| 3.4 | BEST-Route（级联视角） | ⭐⭐ | ⬜ |  | 已在 2.7 |
| 3.5 | LiteLLM fallback（工程级联） | ⭐⭐ | ⬜ |  | 已在 2.11 |
| 3.6 | Portkey fallbacks（工程级联） | ⭐⭐ | ⬜ |  | 已在 2.12 |

### 9.5 阶段 4｜评测体系

| 序号 | 工作 | 优先级 | 状态 | 笔记/产出 | 备注 |
|---|---|---|---|---|---|
| 4.1 | RouterBench | ⭐⭐⭐ | ⬜ |  | 路由评测基础 |
| 4.2 | RouterEval（EMNLP Findings 2025） | ⭐⭐⭐ | ⬜ |  | scaling 行为 |
| 4.3 | RouterArena | ⭐⭐⭐ | ⬜ |  | 建议作主评测 |
| 4.4 | RouteJudge | ⭐⭐ | ⬜ |  | 理念先看，数据后究 |
| 4.5 | CodeRouterBench | ⭐ | ⬜ |  | coding 场景才看 |

### 9.6 阶段 5｜During-Inference

| 序号 | 工作 | 优先级 | 状态 | 笔记/产出 | 备注 |
|---|---|---|---|---|---|
| 5.1 | Collab（ICLR 2025） | ⭐ | ⬜ |  | 默认跳过 |

### 9.7 进度汇总

| 阶段 | 总数 | ✅ 已完成 | 🟦 进行中 | ⬜ 未开始 | ⏭️ 跳过 |
|---|---:|---:|---:|---:|---:|
| 阶段 0 坐标系 | 3 | 2 | 0 | 1 | 0 |
| 阶段 1 MoA | 14 | 2 | 0 | 12 | 0 |
| 阶段 2 路由 | 21 | 0 | 0 | 21 | 0 |
| 阶段 3 级联 | 6 | 0 | 0 | 6 | 0 |
| 阶段 4 评测 | 5 | 0 | 0 | 5 | 0 |
| 阶段 5 during | 1 | 0 | 0 | 1 | 0 |
| **合计** | **50** | **4** | **0** | **46** | **0** |

> 调研推进时，请同步更新对应行状态与"笔记/产出"列，并刷新 9.7 汇总数字。

---

## 附：原始 roadmap 引用

本计划基于 `D:\code\work\moa\moa_evolution_roadmap.md`（生成于 2026-08-04）整理。原始 roadmap 采用 [Harnessing Multiple Large Language Models: A Survey on LLM Ensemble](https://arxiv.org/abs/2502.18036) 的 before / during / after inference taxonomy，并结合工程形态单独展开 cascade 与 benchmark 两类。所有工作的链接、年份、场景信息均来自该 roadmap，本计划仅做调研顺序与优先级重组，未引入新工作。
