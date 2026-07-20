# HarnessX：可组合、自适应、可进化的 Agent Harness 铸造厂调研报告

> 论文：*HarnessX: A Composable, Adaptive, and Evolvable Agent Harness Foundry*（arXiv:2606.14249，2026 年 6 月，小米 Darwin Agent Team）

---

## 📋 基本信息

<p align="center"><b>表1：论文基本信息</b></p>

| 项目 | 内容 |
|-----|------|
| 论文标题 | HarnessX: A Composable, Adaptive, and Evolvable Agent Harness Foundry |
| 作者 | Tingyang Chen*, Shuo Lu*, Kang Zhao*（共同一作）, Weicheng Meng, Kun Shao†, Jian Luan†（通讯）, Hanlin Teng, Tianhao Li, Chao Li, Xule Liu, Jian Liang, Zhizhong Zhang, Yuan Xie, Heng Qu |
| 机构 | 小米 Darwin Agent Team |
| 发表时间 | 2026 年 6 月（v1: 2026-06-12；v2: 2026-07-02） |
| arXiv | cs.AI；[arxiv.org/abs/2606.14249](https://arxiv.org/abs/2606.14249) |
| 代码仓库 | [github.com/Darwin-Agent/HarnessX](https://github.com/Darwin-Agent/HarnessX)（MIT，Beta v0.1.0） |
| 代码状态 | 已开源；论文 v1 称"未来发布"，仓库现为 Beta。注：论文中的 AEGIS 四阶段、变体隔离、协同进化三项在仓库中属 planned/未完全实现（详见第 4 章） |
| 核心结论 | 5 基准 × 3 模型族，平均 +14.5%（最高 +44.0%），协同进化再增收 +4.7% |

---

## 1. 研究背景与动机

### 1.1 问题定义

现代 Agent 的能力不只取决于底层模型，还取决于包裹模型的 **harness**（运行时中介层）——它由 prompt、工具、记忆、控制流组成，决定任务如何被表示、外部服务如何被调用、中间决策如何传递。论文要解决的核心问题是：**harness 长期被当作"手工维护的工程品"而非"可被程序化进化的对象"**，导致其工程化程度远未成熟。

### 1.2 研究动机：现有 Harness 的三重困境

论文从 intro 与 related work 中归纳出现有 harness 体系的三个结构性缺陷（参考文献佐证：LangChain/LlamaIndex/Smolagents 为原语层；LangGraph/AutoGen/CrewAI/Letta 为编排层；Claude Code/Cursor/Manus/DeerFlow 为产品层）：

1. **手工工程化、静态固化**——任何模型版本、工具、问题域的变更都需要定制修改，无经验驱动的改进机制。换一个模型或任务域，就要重新手写一整套脚手架；执行跑出来的几百条轨迹大多被丢弃。
2. **架构纠缠**——prompt 模板、工具封装、重试策略、记忆管理写在同一条代码路径里，改一处静默破坏另一处，跨域复用退化为"复制粘贴"而非真正的组合。
3. **Harness 工程与模型训练割裂**——改进 harness 时收集的轨迹数据被丢弃而非用于模型训练；模型改进也无法反哺 harness。两者各自迭代，永远差半步。

### 1.3 研究目标

把 harness 提升为**第一类对象（first-class object）**，使其可**组合（Compose）**、可**适应（Adapt）**、可与模型**协同进化（Evolve）**，从而在模型缩放之外开辟一条提升 Agent 能力的互补路径。论文核心判断：**Agent 的进步不必只靠堆模型参数**——从执行反馈中组合与进化运行时接口，是一条互补且可落地的杠杆。

---

## 2. 核心贡献

### 2.1 主要贡献

<p align="center"><b>表2：论文主要贡献</b></p>

| 编号 | 贡献 | 对应章节 | 核心要点 |
|-----|------|---------|---------|
| C1 | Harness Composition | §3.1 | harness 形式化为带类型、可替换的一类对象；processor 挂在生命周期 hook 上；九维分类法 + 替换代数（substitution algebra）实现按任务类型安全插拔；每条改动的作用域显式化——变体隔离能稳定进化的前提 |
| C2 | Harness Adaptation（AEGIS） | §3.2 | 提出 AEGIS，trace 驱动的多 agent 进化引擎；**操作镜像（operational mirror）**把 harness 适应映射为符号空间的 RL（MDP），把奖励作弊/灾难性遗忘/探索不足三大 RL 病理转化为具体设计风险，由四阶段流水线（Digester/Planner/Evolver/Critic）+ 确定性门控应对；可选的变体隔离策略防止异构任务集上的跨任务干扰 |
| C3 | Harness-Model Co-Evolution | §3.3 | 闭合优化回路：在共享 replay buffer 上交错 harness 进化与模型 RL；**跨 harness GRPO**让模型内化历代 harness 版本的策略，打破"脚手架天花板"与"训练信号天花板" |
| C4 | Empirical Validation | §4 | 5 基准、3 task-agent 族、最多 15 轮进化，平均 +14.5%（最高 +44.0%），基线越弱收益越大；变体隔离消融解决异构任务集停滞；协同进化在两基准上比 harness-only 再增收 +4.7% |

### 2.2 创新点

1. **方法创新**：首次把 harness 适应严格形式化为符号空间上的 MDP（操作镜像），从而把成熟的 RL 病理学（奖励作弊、灾难性遗忘、探索不足）作为可预测的设计风险，并为每种病理配一个防御机制——而非事后补救。
2. **技术创新**：processor + 8 hook + 替换代数的类型化组合基座，使 harness 的"可编辑面"显式化；确定性门控把"是否上线"的决定权从 LLM 判断中剥离，保证安全属性不依赖 LLM 的可靠性。
3. **实验创新**：对三种病理各给出一个真实运行中观测到的失败案例（含自愈过程），并坦承 per-edit 门控的结构局限（次阈值耦合累积）；同时给出跨模型族的逆缩放规律——基线越弱、harness 收益越大。

---

## 3. 方法详解

### 3.1 方法概述

HarnessX 由三个递进的能力层构成，形成闭环：**智能体运行 → 轨迹采集 → harness 重组/自适应 → 模型微调 → 新一轮运行**。

- **Compose（组合）**：把 harness 拆成带类型的原子零件（processor）挂在生命周期 hook 上，使任意行为改动都成为可插拔、可替换、作用域明确的操作。
- **Adapt（适应）**：AEGIS 引擎盯着运行轨迹，自动诊断失败、生成候选改动、并经确定性门控把关后上线——把"改 harness"从手工编辑变成 trace 驱动的学习问题。
- **Evolve（进化）**：每次运行产生的奖励标注轨迹同时喂给 harness 进化与模型 RL 训练，让外壳与认知核心互相反哺。

![Figure 1: HarnessX 系统总览](assets/fig1_overview.png)

*Figure 1: HarnessX 系统总览。展示 Compose（组合式 harness 基座）+ Adapt（AEGIS 进化引擎）+ Evolve（harness-model 协同进化闭环）三大支柱如何首尾相连。基座把 harness 拆成可替换零件；AEGIS 在其上从执行轨迹中自动改写 harness；协同进化把同一批轨迹数据再喂给模型 RL，闭合"模型变强→能撑起更复杂 harness 重组→harness 变好→暴露更多模型可学策略"的双向回路。读者核心洞察：Agent 能力由"模型核心"与"harness 执行装置"共同决定，任何单边优化都会撞天花板。*

### 3.2 整体架构：Harness 组合（Foundry）

#### 3.2.1 Harness 作为第一类对象

HarnessX 的统一设计原则：**harness 是第一类值，processor 是带类型的原子组件，组合通过在带类型的 hook 点插入 processor 完成**。

形式化地，一个 harness 是一个 pair $\mathcal{H} = (\mathcal{M}, \mathcal{C})$：

- $\mathcal{M}$（模型配置）：记录 *哪个* 模型服务哪个角色（`main` / `judge` / `evaluator`）及各角色的 fallback 策略。
- $\mathcal{C}$（harness 配置）：记录 *如何* 行为，与模型身份无关。

两者经 `agent = model_config.agentic(harness_config)` 组合成可执行 agent——一个绑定到模型的 processor 流水线，二者各自可独立替换。这是论文与代码完全一致的核心 API。

Harness 配置进一步分解为 $\mathcal{C} = (\mathbf{P}, \mathbf{S})$：

- $\mathbf{P} : \text{Hook} \to \text{List}[\text{Processor}]$：按 hook 索引的 processor 列表（Hook 是 8 元生命周期事件集合）。
- $\mathbf{S}$：固定的一组正交**槽位资源**——工具注册表、tracer、工作区、沙箱提供者、插件列表。槽位是单例、跨 processor 共享；processor 状态则是实例私有。

$\mathcal{C}$ 之所以是第一类对象，因为它**可独立序列化、可比较、可哈希、可替换**：两个共享 $\mathcal{C}$ 但 $\mathcal{M}$ 不同的 agent 执行相同流水线、行为差异仅来自模型响应；两个共享 $\mathcal{M}$ 但 $\mathcal{C}$ 不同的 agent 在行为上根本不同。这种"具象化"是程序化进化的前提。

#### 3.2.2 Processor 抽象

每条逐步行为都实现为一个 processor，满足协议：

```python
async def process(self, event: Event) -> AsyncIterator[Event]
```

processor 消费一个事件、产出零个或多个，结果恰为五种之一：**透传**（原样 yield）、**变换**（yield 修改版）、**分裂**（yield 多个同类型事件，下游独立处理——多 agent fork 的基础）、**拦截**（不 yield、阻断传播）、**中断**（抛异常、停止循环）。这种受限接口保证了组合性：同一 hook 上的 processor 输入输出同类型，于是 processor 按顺序应用即可组合，插入或移除不会破坏类型正确性。

每个 processor 携带三个类级元数据约束组合行为：

<p align="center"><b>表3：Processor 元数据字段</b></p>

| 字段 | 作用 |
|------|------|
| `_singleton_group` | 命名一个互斥组，同组最多一个 processor |
| `_order` | hook 内排序提示（常量 `PRE=0` / `NORMAL=50` / `POST=100`） |
| `_after` | 对其他互斥组的软依赖列表 |

这使 harness 进化成为第一类操作：AEGIS 可以"在某个 hook 插入新 processor""按 singleton group 匹配替换现有 processor""整体移除一个 processor"，而不触碰同一或不同 hook 上的其他 processor。类型契约（输入事件类型 = 输出事件类型）逐 hook 强制，任意替换都保持整体流水线的类型良构。

#### 3.2.3 八个生命周期 Hook 点

<p align="center"><b>表4：Hook 点及允许的修改</b></p>

| Hook | 事件类型 | 允许的修改 |
|------|---------|-----------|
| `task_start` | `TaskStartEvent` | system prompt |
| `step_start` | `StepStartEvent` | 结构化历史编辑 |
| `before_model` | `BeforeModelEvent` | 最后一条用户内容；追加一条 user message |
| `after_model` | `ModelResponseEvent` | 响应内容、工具调用 |
| `before_tool` | `ToolCallEvent` | 工具输入、审批标志 |
| `after_tool` | `ToolResultEvent` | 工具结果 |
| `step_end` | `StepEndEvent` | 只读 |
| `task_end` | `TaskEndEvent` | 只读 |

run loop 在每次调用后校验 hook 契约：违规（如修改只读字段）立即抛异常，而非静默传播已损坏的状态。**受限的修改面是关键设计**——它让每个 hook 上"能改什么"白纸黑字，是变体隔离能界定作用域的基础。

#### 3.2.4 九维行为分类法

论文把行为空间组织为九个正交维度：

<p align="center"><b>表5：九维行为分类法</b></p>

| 维度 | 名称 | 职责 | Compose/Adapt/Evolve 归属 |
|------|------|------|--------------------------|
| D1 | Model Selection | 各角色用哪个模型 | Compose |
| D2 | Context Assembly | 每步呈现给模型什么 | Compose |
| D3 | Memory Management | 跨步/跨会话保留什么 | Compose |
| D4 | Tool Ecosystem | agent 可调用哪些工具 | Compose |
| D5 | Execution Environment | 工具副作用在哪里发生（沙箱） | Compose |
| D6 | Evaluation & Reward | 结果如何被判定 | Adapt |
| D7 | Control & Safety | 防止循环/超支/偏离意图的规则 | Adapt |
| D8 | Observability | 记录每个事件、模型调用、工具调用 | Evolve |
| D9 | Training Bridge | 把执行轨迹转为 RL 记录 | Evolve |

实践中，AEGIS 的编辑横跨九维：**D2（上下文）与 D4（工具）是最频繁的编辑目标**（见 §5.2）；D8 提供了 AEGIS 自身赖以推理的 trace 基底；D9 为协同进化供给轨迹记录，闭合优化回路。

### 3.3 方法：AEGIS 适应引擎

![Figure 2: AEGIS 进化回路](assets/fig2_aegis_loop.png)

*Figure 2: AEGIS 进化回路。单个 meta-agent $\mathcal{M}$ 驱动全部四阶段（Digester/Planner/Evolver/Critic），根据是否存在足够信号**选择性调用**各阶段；确定性门控决定是否上线候选编辑。关键洞察：四阶段并非外部路由分派，而是同一 meta-agent 自主判断"是否有足够信号继续"——Digester/Planner/Evolver 各自评估继续条件并可短路该轮（行动性不足/landscape 为空/无可行候选），唯 Critic 与门控对每个抵达的候选都是强制的。这让系统在信号稀疏时干净地以 no-op 退出，而非硬凑改动。*

#### 3.3.1 核心洞察：操作镜像（Operational Mirror）

AEGIS 的关键洞察是**harness 进化在结构上映射为符号空间的强化学习**：harness 配置是状态、带类型编辑是动作、执行轨迹加验证器分数构成反馈。这映射是**预测性的**：它识别出三种类比于已知 RL 病理的失败模式（奖励作弊、灾难性遗忘、探索不足），这些病理在符号设置中被放大，因为 (1) LLM evolver 能构造数值扰动无法表达的**结构化漏洞**，(2) 对共享组件的编辑会**非局部传播**。

<p align="center"><b>表6：操作镜像——RL 概念与符号空间对偶</b></p>

| RL 概念 | 符号空间对偶 | AEGIS 实现 |
|--------|------------|-----------|
| Policy $\pi$ | harness 更新过程 $\pi_{\text{evo}}$ | 四阶段流水线 |
| State $s_t$ | $(\mathcal{H}_t, \mathcal{T}_t)$（harness 配置 + trace 存储） | 状态空间 |
| Action $a_t$ | 带类型 harness 编辑 | builder 操作 + change manifest |
| Feedback | trace $\tau$ + 验证器分数 $r$ | 可观测性层 |
| Update | $\mathcal{H}_{t+1} \leftarrow U(\widetilde{\mathcal{H}}_t, \mathcal{T}_t, r_t)$ | 确定性接受门控 |

#### 3.3.2 形式化定义

**定义 1（Harness 配置）**：$\mathcal{H} = (c_1, c_2, \ldots, c_9)$，每个 $c_i \in \mathcal{C}_i$ 实例化九维之一，受 hook 类型契约与 singleton-group 排他约束。

**定义 2（Harness 编辑）**：$e: \mathcal{H} \to \mathcal{H}$，修改一或多维但保类型契约。动作空间 $\mathcal{E}$ 是**离散但开放式**的——每个编辑是 meta-agent LLM 生成的代码级制品（新 processor 源码、改 prompt 模板、重配工具注册表、改写控制流），而非从预枚举集合中选取。组合爆炸不由穷举搜索管理，而由 LLM 的生成能力（Planner 从 trace 锚定的假设提编辑）与生成期类型约束剪枝无效组合来管理。

**定义 3（操作镜像）**：四元组 $(\mathcal{H}, \mathcal{E}, \mathcal{R}, \mathcal{T})$，构成 harness 层的 MDP。$\mathcal{R}: \mathcal{H} \times \mathcal{E} \to \mathbb{R}$ 把配置-编辑对映为标量奖励（一批适应任务上聚合的验证器分数），$\mathcal{T}$ 是 trace 存储，提供超越标量的结构化反馈。

**MDP 实例化**：令 $\mathcal{H}_t$ 为第 $t$ 轮 harness（模型 $\mathcal{M}$ 在进化期固定），$\mathcal{T}_t$ 为此前执行累积的 trace 存储。符号状态 $s_t = (\mathcal{H}_t, \mathcal{T}_t)$。harness 更新策略 $\pi_{\text{evo}}$ 选动作 $a_t \sim \pi_{\text{evo}}(\cdot \mid s_t)$，$a_t \in \mathcal{E}$ 为代码级编辑。应用得候选 harness $\widetilde{\mathcal{H}}_t = a_t(\mathcal{H}_t)$。在适应批上跑候选（模型 $\mathcal{M}$ 固定）产生新 trace $\Delta\mathcal{T}_t$ 与逐任务验证器分数 $r_t$。确定性接受算子 $U(\widetilde{\mathcal{H}}_t, \mathcal{T}_t, r_t)$ 或提交（$\mathcal{H}_{t+1} = \widetilde{\mathcal{H}}_t$）或拒绝（$\mathcal{H}_{t+1} = \mathcal{H}_t$），强制**跷跷板约束（seesaw constraint）**：候选不得让 $\mathcal{T}_t$ 中任何此前已解任务回归。两种情况下 trace 存储都增长：$\mathcal{T}_{t+1} = \mathcal{T}_t \cup \Delta\mathcal{T}_t$。

#### 3.3.3 符号空间的三种病理与对应防御

<p align="center"><b>表7：三种 RL 病理在符号空间的重现与防御</b></p>

| 病理 | 在符号 harness 进化中的放大形式 | AEGIS 防御机制 |
|------|------------------------------|---------------|
| 奖励作弊（reward hacking） | evolver 可直接攻击验证协议：把 benchmark 答案塞进 prompt、利用验证器格式规律、引入重写输出以匹配验证器期望的 processor | **Critic**——评估候选的 manifest 是否与 trace 证据一致，是否经共享状态/控制流产生非局部效应 |
| 灾难性遗忘（catastrophic forgetting） | 修失败模式 A 的编辑经共享上下文/工具/记忆/控制规则静默回归 B | **确定性门控层**——seesaw 约束拒绝任何回归此前已解任务的编辑 |
| 探索不足（under-exploration） | 偏好低风险局部编辑（改措辞、调工具描述），结构性大改（拆 agent、换控制策略、换记忆架构）难自发涌现 | **Planner**——生成编辑前先构 adaptation landscape，把结构性与增量编辑并置考虑 |

核心设计原则：**LLM 子 agent 负责探索、假设、提议；带类型结构与确定性门控决定什么上线。**这一剥离保证安全属性（无回归、无未审计编辑）不依赖 LLM 子 agent 的可靠性。

#### 3.3.4 AEGIS 四阶段流水线

所有阶段共享单一信息基底——trace 存储（执行事件、验证器评分结果、回归信号、已上线/被拒编辑的结构化记录）。无任何阶段消费超出 trace 存储 + 当前 harness $\mathcal{H}_t$ 的输入。数据前向流过流水线并带选择性门控。

**Digester（消化器）**：GAIA 一轮（103 任务，pass@2）产生约 10M token 原始 trace。直接传给下游超上下文限制，朴素截断丢诊断信号。Digester 把每任务 trace 压缩为结构化摘要：二值结果、失败类别、牵连组件 ID、证据片段；并跨轮连续（每任务摘要链到其历史结果与已上线编辑），让 Planner 区分顽固失败与瞬态噪声。

**Planner（规划器）**：接收 Digester 输出，构造 **adaptation landscape**——哪些任务失败、试过哪些编辑、牵连哪些组件、哪些编辑类型（prompt/tool/processor/config）尚未尝试。这是**对抗探索不足的主防线**：生成编辑前先画地图，避免流水线收敛到 trace 条件式的局部修复，确保结构变更与增量 prompt 编辑并置。

**Evolver（进化器）**：基于 landscape 产出一个或多个候选 $\{\widetilde{\mathcal{H}}_t^{\,k}\}_{k=1}^{K_t}$，每个指定为对当前 $\mathcal{H}_t$ 的带类型 builder 操作，并附带 **change manifest**（编辑的组件、预期行为效应、预期改进/回归的任务）。引入新 processor 代码时须提供 smoke test 证明其能实例化并在合成输入上运行不抛异常。builder 代数保证类型安全但不保证行为安全——类型通过的编辑仍可能产生非局部效应，只能由 Critic 与门控检出。

**Critic 与门控**：Critic 防奖励作弊；确定性门控层防灾难性遗忘。Critic 把候选 manifest 与 trace 证据比对，评估是否经共享状态/控制流冒非局部风险；发现缺口时向 Evolver 发一次修订请求，至多一轮修订后返回 `no_op` 或有序 `ship_ranking`。门控随后按序执行接受检查：manifest 完整性、配置规范化、构建/smoke 测试（适用时）、seesaw 约束（此前通过任务的回归检查）。首个失败的检查中止序列；通过的候选提交，失败的归档附拒绝理由。这把 LLM 判断与接受剥离：**无论 Critic 推荐，只有确定性检查掌管上线。**

#### 3.3.5 AEGIS 适应回路（Algorithm 1）

```
Algorithm 1: AEGIS Harness Evolution Loop（选择性调用）
Input: 初始 harness H0，meta-agent M，预算 T，patience P，阈值 α
Output: 进化后 harness H_{t+1}，trace 存储 T_{t+1}
1  T0 <- ∅ ; idle <- 0
2  for t = 0 .. T-1:
3    采批 B_t；跑 H_t 得 traces ΔT_t；T_{t+1} <- T_t ∪ ΔT_t
4    # Digester（可选）
5    (evidence_t, a_t) <- M.Digester(ΔT_t, T_t)
6    if a_t < α: H_{t+1} <- H_t ; idle++ ; continue
7    # Planner（可选）
8    landscape_t <- M.Planner(evidence_t)
9    if landscape_t = ∅: H_{t+1} <- H_t ; idle++ ; continue
10   # Evolver（可选）
11   {(H̃_t^k, manifest_k)} <- M.Evolver(H_t, landscape_t)
12   if K_t = 0: H_{t+1} <- H_t ; idle++ ; continue
13   # Critic 与门控（强制）
14   ranking <- M.Critic({(H̃_t^k, manifest_k)}, evidence_t)
15   k* <- ⊥
16   for k in ranking:
17     if DeterministicGate(H̃_t^k, H_t, T_t) passes: k* <- k ; break
18   if k* != ⊥: H_{t+1} <- H̃_t^k* ; idle <- 0
19   else: H_{t+1} <- H_t ; idle++
20   if idle >= P: break
21  return H_{t+1}, T_{t+1}
```

<p align="center"><b>表8：算法步骤解读</b></p>

| 步骤 | 操作 | 输入 | 输出 | 设计意图 |
|------|------|------|------|---------|
| 3 | 跑当前 harness | $\mathcal{H}_t$, 批 $B_t$ | traces $\Delta\mathcal{T}_t$ | 收集这一轮的失败证据 |
| 5-6 | Digester 压缩 + 行动性判定 | $\Delta\mathcal{T}_t, \mathcal{T}_t$ | evidence + 行动性分 $a_t$ | 信号太稀就短路该轮，不硬凑改动 |
| 8-9 | Planner 构 landscape | evidence | landscape 或空 | 防局部修复，逼结构性改动上桌 |
| 11-12 | Evolver 产候选 | $\mathcal{H}_t$, landscape | 带类型候选集 | 离散但开放式的代码级编辑 |
| 14-17 | Critic 排序 + 门控判定 | 候选集 + 证据 | $k^\star$ 或 ⊥ | LLM 提议、确定性门控拍板 |
| 18-20 | 接受/拒绝 + early stop | 门控结果 | $\mathcal{H}_{t+1}$ | 连续 P 轮无上线即停，省预算 |

#### 3.3.6 变体隔离（Variant Isolation / Ensemble Routing）

单 harness 维护的回路在任务需冲突行为时受限：改善某子集可能回归另一子集，seesaw 拒绝它、保稳定但丢弃了局部有益改动。**变体隔离**通过维护至多 $K$ 个 harness 变体 $\{\mathcal{H}_t^{(1)}, \ldots, \mathcal{H}_t^{(V_t)}\}$（$V_t \leq K$）并把每个任务路由到该任务簇上历史成功率最高的变体来解除限制。此机制称 **Ensemble routing**。

门控层对每候选区分两种结果：(1) 改善某些任务且不回归任何——应用到其目标变体；(2) 改善子集但回归其他——**fork 新变体而非直接拒绝**（池满则退役最弱变体）。多变体后 seesaw 按**变体**作用域：针对变体 $k$ 的候选只对路由到 $k$ 的任务测试，一个簇的改进不能回归另一簇。该设计预测三个性质（§5.3 验证）：非退化聚合轨迹（peak=final）、跨更多轮持续探索、更低总 token 消耗。

### 3.4 方法：Harness-Model 协同进化

![Figure 3: harness-model 协同进化回路](assets/fig3_co_evolution.png)

*Figure 3: harness-model 协同进化回路。agent $(\mathcal{M}_t, \mathcal{H}_t)$ 在固定验证器与可观测层下跑任务批 $B_t$，产生的 traces 与 rewards $(\tau, r)$ 进入共享 replay buffer $\mathcal{B}$；跨 harness 分组把同一任务在历代 harness 版本上的轨迹池化、计算组相对优势 $\hat{A}$。同一 buffer 驱动两份"在相同数据上"的更新：AEGIS harness 进化（Digester→Planner→Evolver→Critic，得 $\mathcal{H}_{t+1}$）与跨 harness GRPO（组采样 + clipped 目标，得 $\mathcal{M}_{t+1}$），两者都喂下一轮。关键洞察：不是"先改 harness 再训模型"的两阶段，而是同一轮内同一批 rollout 同时驱动两条更新——模型训练"搭便车"用 harness 进化已付的 rollout 成本，无需额外采样。*

#### 3.4.1 两个天花板

单边优化各撞一个天花板：
- **脚手架天花板（scaffolding ceiling）**：对能力受限的小模型，harness 进化终会撞顶——一旦 harness 暴露了对的工具/上下文/控制流，约束就变成冻结模型能否真正利用它们，没有 harness 编辑能补足模型自身欠缺的推理能力。
- **训练信号天花板（training-signal ceiling）**：固定 harness 下训模型也撞顶——新获能力当脚手架从不出示能引出它们的上下文/工具/控制流时得不到演练。

模型是 agent 的**认知核心**（推理、规划），harness 是其**执行装置**（决定模型感知什么、可调用什么、执行受何约束）。更锋利的装置补不了弱核心，更强的核心也补不了从不调用它的装置。协同进化瞄准此瓶颈。

#### 3.4.2 协同进化迭代

协同进化在 pair $(\mathcal{M}_t, \mathcal{H}_t)$ 上操作（$\mathcal{M}_t$ 为可训参数，放松 §3.3 的冻结假设），维护固定容量、FIFO 驱逐的 replay buffer $\mathcal{B}$。每轮：

1. **Rollout**：跑 $(\mathcal{M}_t, \mathcal{H}_t)$ 于适应批，可观测层把每 episode 记为完整 trace $\tau_i$。
2. **Verification**：固定验证器把每 trace 评成标量 $r_i$。固定验证器使跨 harness 版本奖励可比（跨 harness 优势所需）。
3. **Buffer 插入**：每条评分 trace 连同产生它的 harness 版本入 $\mathcal{B}$；FIFO 驱逐保 $\mathcal{B}$ 限近几轮。
4. **Harness 进化**（$\mathcal{H}_{t+1} \leftarrow \text{AEGIS}(\mathcal{H}_t, \mathcal{B})$，非参数）：meta-agent 读 buffered traces 作证据，提一条离散结构编辑，Critic+门控验证才入。
5. **行为 log-prob**：对刚加入的 trace，在生成模型 $\mathcal{M}_t$ 下前向传播得 token 级 log-prob $\pi_{\theta_{\text{old}}}(\tau_i)$ 并缓存；早期轮的 trace 复用各自插入时缓存的值。
6. **GRPO 更新**（$\mathcal{M}_{t+1} \leftarrow \text{GRPO}(\mathcal{M}_t, \mathcal{B})$，参数）：把 trace 按任务分跨 harness 组，赋组相对优势，取带 clip 的策略梯度步 + 对固定参考的 KL 锚。
7. **推进**：返回步骤 1，带 $(\mathcal{M}_{t+1}, \mathcal{H}_{t+1})$。

每条 trace 兼作 AEGIS 诊断证据与 GRPO 训练信号。harness 进化（步骤 4）与模型更新（步骤 5-6）读同一 buffer 但互不以对方输出为条件；二者须在下次 rollout 前都完成。

#### 3.4.3 跨 harness GRPO

采用 GRPO。关键设计是**跨 harness 分组准则**：所有共享任务标识的轨迹无论哪个 harness 或模型检查点产生都组成一个 GRPO 组，使组内变异反映**策略差异**而非仅采样噪声。对任务 $x$，轨迹组：

$$\mathcal{G}_x = \{\tau_i \in \mathcal{B} \mid \text{task}(\tau_i) = x\} = \bigcup_{k} \{\tau \sim \text{Agent}(\mathcal{M}_k, \mathcal{H}_k, x)\}$$

组相对优势：

$$\hat{A}(\tau_i) = \frac{r_i - \mu(\mathcal{G}_x)}{\sigma(\mathcal{G}_x) + \epsilon}$$

其中 $\mu(\mathcal{G}_x), \sigma(\mathcal{G}_x)$ 为组内奖励均值与标准差。进化的 harness 充当模型 RL 的**结构化探索算子**：每新版把一不同行为模式注入该任务的采样分布，优势把模型推向验证器评分最高的模式。单策略采样给不了的探索宽度由进化脚手架本身供给。

策略目标：

$$\mathcal{J}_{\text{GRPO}}(\theta) = \mathbb{E}_{x, \tau_i \sim \mathcal{B}} \left[ \min\!\left( \rho_i(\theta)\, \hat{A}(\tau_i),\; \text{clip}\!\left(\rho_i(\theta),\, 1-\epsilon_c,\, 1+\epsilon_c\right)\hat{A}(\tau_i) \right) \right] - \beta\, D_{\text{KL}}\!\left(\pi_\theta \,\|\, \pi_{\text{ref}}\right)$$

重要性比：

$$\rho_i(\theta) = \frac{\pi_\theta(\tau_i \mid x)}{\pi_{\theta_{\text{old}}}(\tau_i \mid x)}, \qquad \pi_{\theta_{\text{old}}} = \mathcal{M}_d$$

行为策略 $\pi_{\theta_{\text{old}}}$ 与参考策略 $\pi_{\text{ref}}$ 是不同对象：$\pi_{\text{ref}} = \mathcal{M}_0$ 全程固定，$\pi_{\theta_{\text{old}}}$ 按轨迹而变、须从 buffer 恢复。

**任务级对齐而非动作级**：跨 harness GRPO 做**任务级**对齐——不同 harness 版本的轨迹按任务标识分组、仅按验证器奖励比较。无需动作级对齐，故动作空间不兼容的 harness 版本（不同工具 schema、不同 prompt 结构、不同控制流 processor）可同组共存。算梯度时每 $\tau_i$ 在产生它的 harness 版本 $\mathcal{H}_k$ 下重放：模型的 log-prob $\pi_\theta(\tau_i \mid x)$ 在 $\mathcal{H}_k$ 每轮构造的 prompt/工具 schema/观测上下文下评估。GRPO 梯度完全作用于以 harness 特定上下文为条件的**模型输出 token**，而非 harness 结构动作或环境转移。这把 harness 进化（可跨版自由改动作空间）与模型训练（只需每轨迹自身 harness 上下文下的 token 级 log-prob）解耦。

#### 3.4.4 混合策略 buffer 上的离策略训练

replay buffer 本质离策略：第 $t$ 轮含检查点 $\mathcal{M}_0, \ldots, \mathcal{M}_t$ 在 harness $\mathcal{H}_0, \ldots, \mathcal{H}_t$ 下产生的轨迹。恢复每 buffered 轨迹的 $\pi_{\theta_{\text{old}}}$ 是中心离策略挑战。

- **行为策略 $\pi_{\theta_{\text{old}}}$**：在 buffer 插入时用一次 $\mathcal{M}_k$ 前向传播物化、缓存 token 级 log-prob 于磁盘、每梯度步复用，解耦缓存行为 log-prob 与每步重算的当前 log-prob $\pi_\theta(\tau_i)$。
- **有界离策略偏差**：FIFO 把 buffer 限为 $C$ 条；每轮 $s$ 采样则最大模型版本滞后 $\lfloor C/s \rfloor$ 轮，故每条缓存 $\pi_{\theta_{\text{old}}}$ 源于 $\pi_\theta$ 的有界窗口内，产生轨迹的策略永不会偏离被更新策略太远。
- **零额外 rollout 复用的回放复用**：agentic RL 的主导成本是 rollout（环境执行：解码、工具调用、验证）而非梯度更新。协同进化一轮探索产生一轨迹集同时驱动两更新：AEGIS harness 更新与跨 harness GRPO 模型更新。GRPO 消费这些轨迹靠重放、自身不发 rollout。加模型更新的边际成本限于 (i) 每轨迹一次缓存前向传播记 $\pi_{\theta_{\text{old}}}$、(ii) 梯度步本身，皆 rollout-free。无轨迹专为训模型而生成。**联合优化因此经济：以离线训练算力的价格买到模型改进，无超 harness 进化所付的额外 rollout。**

### 3.5 关键技术点

<p align="center"><b>表9：关键技术点</b></p>

| 技术点 | 描述 | 作用 | 论文对应位置 |
|-------|------|------|------------|
| 第一类对象 harness | $\mathcal{H}=(\mathcal{M},\mathcal{C})$，可序列化/比较/哈希/替换 | 使程序化进化成为可能 | §3.2 |
| 替换代数（substitution algebra） | 类型契约 + singleton group 排他的插拔 | 保类型良构的进化操作 | §3.2.2 |
| 操作镜像 | RL↔符号 harness 进化的 MDP 映射 | 把 RL 病理学转可预测设计风险 | §3.3.1 |
| 选择性调用四阶段 | meta-agent 自判"是否有足够信号继续" | 信号稀疏时干净 no-op 退出 | §3.3.4 |
| 确定性门控（seesaw） | 候选不得回归任何已解任务 | 防灾难性遗忘，剥离 LLM 判断与接受 | §3.3.2/§3.3.4 |
| Change manifest | 候选的证据/机制/预期效应/归因签名 | 每编辑可证伪，Critic 比对预测与下轮 trace | §4.6.5（附录） |
| 变体隔离 / Ensemble routing | 至多 K 变体 + 任务路由 | 解异构任务集停滞 | §3.3.6 |
| 跨 harness GRPO | 任务级分组、harness 版本特异上下文下算梯度 | 模型内化历代策略，打破两天花板 | §3.4.3 |
| 共享 replay buffer + FIFO | 同一 rollout 驱动两更新 | 零额外 rollout 成本的联合优化 | §3.4.4 |

### 3.6 方法设计的关键洞察

1. **类型让坏改动"可检测"而非"不发生"**——类比类型系统：类型不生成正确程序，但让错误程序可检出。带类型组件不防坏编辑，但让编辑作用域显式，使变体隔离有界。Global 策略因未用类型做隔离而退化（§5.3）；Compositional 不保证有界行为效应（$\tau^3$ Telecom 的次阈值耦合即证）。
2. **反馈信号丰富度界定了可安全进化的复杂度上限**——仅标量奖励下，三病理都不可检：分数变化无法区分奖励作弊与真改进、探索不足与收敛、灾难性遗忘与评估噪声。Trace 结构使各病理可诊。$\tau^3$ Telecom 案例示边界：虽 5 轮前序 trace，累积回归仍逃过 seesaw 因无单编辑过检测阈值。
3. **把进化拆成"探索"与"上线"两权，前者归 LLM、后者归确定性规则**——是 AEGIS 全部安全保证的支点。即使 LLM 子 agent 失败，安全属性仍因门控确定而成立。

### 3.7 与现有方法的核心区别

<p align="center"><b>表10：与现有方法的对比</b></p>

| 环节 | 现有方法做法 | HarnessX 做法 | 改变原因 |
|------|------------|--------------|---------|
| harness 复用 | 原语层只给积木、编排层固定模式、产品层端到端不透明 | harness 为带类型一类对象 + 替换代数 | 让"改 harness"从重写变插拔 |
| 进化范围 | 仅 prompt（APE/OPRO/EvoPrompt/Promptbreeder/DSPy）或仅 inter-component 关系（GPTSwarm/ADAS/AFlow） | 九维全覆盖含工具/记忆/控制流/可观测性 | prompt-only 收益有限，工作流结构可学但组件级仍静态 |
| 漂移防御 | 各自进化方案少有针对性防御 | 操作镜像预测三病理 + 四阶段各配一防御 + 确定性门控 | 让 AI 反复改自己再打分筛本质是优化流程，必防局部最优/遗忘/作弊 |
| 模型关系 | 多数只动外壳不碰模型 | 同 buffer 同时驱动 harness 进化与跨 harness GRPO | 轨迹海量且两改进正交互补，单边各撞天花板 |
| harness 改写 | SICA/Darwin Gödel Machine 改源码但无清晰组件边界 | 带类型 processor + manifest 使改动作用域与可证伪性显式 | 改源码方案无边界，改一处牵全局、有效改法难干净拆出 |

---

## 4. 代码实现分析

> 注：仓库 [github.com/Darwin-Agent/HarnessX](https://github.com/Darwin-Agent/HarnessX) 为 Beta v0.1.0，MIT 许可。论文 v1 摘要称代码"未来发布"，当前仓库已开源但与论文的对应存在**术语差异与部分未实现项**——这是本调研最重要的诚实发现，详见 §4.5、§4.8。

### 4.1 代码仓库概述

<p align="center"><b>表11：代码仓库信息</b></p>

| 项目 | 内容 |
|-----|------|
| 仓库地址 | github.com/Darwin-Agent/HarnessX |
| 主要语言 | Python 3.11+（pyproject.toml + uv + uv.lock） |
| 代码规模 | `harnessx/` 包约 160 文件、~41,800 LOC；`recipe/` 约 10,500 LOC；另含 React/TS Lab 前端 |
| 开源时间 | 2026 年，Beta |
| 依赖管理 | uv（pyproject.toml + uv.lock） |
| 许可 | MIT（每文件头 `Copyright 2026 Darwin-Agent`） |

### 4.2 目录结构

```
HarnessX/
├── harnessx/                  # 核心框架（~160 py 文件）
│   ├── core/                   #   Harness/Builder/RunLoop/State/Events/Trajectory
│   ├── processors/             #   7 类 processor（context/control/evaluation/memory/...）
│   ├── meta_harness/            #   ★ AEGIS 对应的 meta-agent（agent/journal/validate_workflow/...）
│   ├── rl/                      #   训练桥（RLConfigSpec/TaskBuilder）
│   ├── plugins/                 #   插件系统 + dimensions（light_memory/skill_runtime/...）
│   ├── providers/               #   6 模型后端 + agentic mixin
│   ├── tools/                   #   工具注册表 + builtins + MCP
│   ├── sandbox/                 #   Local/Docker/E2B
│   ├── tracing/                 #   HarnessJournal(JSONL)/OTel/Null tracer
│   ├── bundles/                 #   预组合能力 bundle
│   ├── api/                     #   FastAPI + SSE 供 Lab UI
│   └── cli.py                   #   CLI 入口（hx）
├── benchmarks/                 # 4 已集成 + 3 进行中
├── recipe/                     # slime RL 训练 recipe + verl_harnessX
├── examples/                   # coding/research/assistant/custom_processor
├── extensions/                 # docx/pdf/pptx/xlsx skills
├── frontend/                   # Lab UI（React + TS + Tailwind）
└── tests/                      # unit/integration/E2E
```

### 4.3 系统架构图

```mermaid
graph TB
    subgraph "论文概念层"
        H["H = (M, C) Harness 第一类对象"]
        AG["AEGIS 进化引擎<br/>Digester-Planner-Evolver-Critic"]
        CE["协同进化<br/>共享 buffer + 跨 harness GRPO"]
    end
    subgraph "harnessx/core 基座"
        MC["ModelConfig.agentic()"]
        HC["HarnessConfig = (P, S)"]
        RL["run_loop<br/>8 hook 事件发射"]
        PR["Processor 协议<br/>5 outcomes + 3 元数据"]
        EV["events.py 8 事件类"]
    end
    subgraph "harnessx/processors 九维实现"
        D2["context D2"]
        D3["memory D3"]
        D4["tools D4"]
        D7["control D7"]
        D8["observability D8"]
        D6["evaluation D6"]
    end
    subgraph "harnessx/meta_harness 进化引擎"
        MA["MetaAgent.evolve()"]
        TD["trajectory_digester worker"]
        EVV["EvolveValidator (Critic)"]
        JN["journal + gating_attribution"]
        RP["replay gate (smoke)"]
    end
    subgraph "harnessx/rl + recipe"
        TBR["trajectory.to_rl_records()"]
        VRL["recipe/verl_harnessX GRPO"]
    end
    MC --> H
    HC --> H
    H --> RL
    RL --> EV
    PR --> RL
    D2 -.挂 hook.-> PR
    D4 -.挂 hook.-> PR
    D8 -.挂 hook.-> PR
    AG --> MA
    MA --> TD
    MA --> EVV
    EVV --> RP
    EVV --> JN
    CE --> VRL
    TBR --> VRL
```

*HarnessX 系统架构图。上层为论文三概念（harness 一类对象、AEGIS、协同进化），中下层为代码实现映射。基座层 `harnessx/core` 实现 `agentic()`/`HarnessConfig`/`run_loop`/`Processor`/8 事件，是论文 §3.2 的忠实落地。processor 层把九维拆到 `processors/` 七子包 + `rl/` + `sandbox/`。进化引擎层 `meta_harness/` 是论文 AEGIS 的代码对应——但注意论文的"AEGIS 四阶段"在代码里不是四个类，而是 `MetaAgent.evolve()` + `trajectory_digester` worker + `EvolveValidator` 的多阶段编排（§4.5）。协同进化层 `recipe/verl_harnessX` 是单 harness GRPO 接 veRL，论文的跨 harness GRPO / 共享 buffer 在仓库属 planned。读者核心洞察：基座与 processor 层与论文高度一致；进化与协同层存在术语差与未实现项。*

### 4.4 模块依赖关系图

```mermaid
graph LR
    model_config["core/model_config.py<br/>ModelConfig + agentic()"]
    harness["core/harness.py<br/>Harness + HarnessConfig"]
    builder["core/builder.py<br/>HarnessBuilder 拓扑排序"]
    proc["core/processor.py<br/>Processor 协议 + 8 hook + 契约"]
    events["core/events.py<br/>8 事件 dataclass"]
    runloop["core/runloop.py<br/>run_loop()"]
    traj["core/trajectory.py<br/>StatefulTrajectory + to_rl_records"]
    procs["processors/*<br/>九维 processor 实现"]
    meta["meta_harness/agent.py<br/>MetaAgent.evolve()"]
    valid["meta_harness/validate_workflow.py<br/>EvolveValidator (Critic)"]
    journal["meta_harness/journal.py<br/>JournalEntrySpec + gating"]
    rl["rl/* + plugins/dimensions/rl.py<br/>RLConfigSpec/TaskBuilder"]
    verl["recipe/verl_harnessX<br/>GRPO adapter"]
    model_config --> harness
    builder --> harness
    proc --> runloop
    events --> proc
    runloop --> harness
    procs --> proc
    traj --> runloop
    meta --> valid
    valid --> journal
    meta --> traj
    rl --> traj
    verl --> rl
```

*模块依赖关系图。核心枢纽是 `core/processor.py` 与 `core/harness.py`：几乎所有 processor 与 run_loop 都依赖它们，是整个框架的承重墙。叶子节点是 `core/events.py`（不依赖其他模块，只被消费）与 `recipe/verl_harnessX`（依赖 rl/，不被框架内部依赖）。`meta_harness/` 三模块（agent/validate_workflow/journal）形成进化引擎的内部三角：MetaAgent 依赖轨迹、EvolveValidator 依赖 journal 记 gating。无循环依赖，分层清晰：core 基座 → processors/meta_harness/rl 上层 → recipe 外接适配。读者核心洞察：基座与进化层解耦良好——可只跑 harness 不跑进化，也可只读 trajectory 离线喂 GRPO。*

### 4.5 论文-代码对应关系（含术语差异）

<p align="center"><b>表12：论文概念与代码实现的对应关系</b></p>

| 论文概念 | 代码实现 | 文件位置 | 对应度 |
|---------|---------|---------|--------|
| `agent = model_config.agentic(harness_config)` | `ModelConfig.agentic()` | `harnessx/core/model_config.py:73` | 完全一致（API 字面相同） |
| $\mathcal{C}=(\mathbf{P},\mathbf{S})$ harness 配置 | `HarnessConfig` dataclass（processors 列表 + 槽位） | `harnessx/core/harness.py:743` | 一致 |
| Processor 协议 `process(event)->AsyncIterator` + 5 outcomes + 3 元数据 | `Processor` Protocol + `MultiHookProcessor` + `_after`/`_order`/`_singleton_group` | `harnessx/core/processor.py:343,512,606` | 完全一致 |
| 8 Hook 点 | `_DISPATCH` 表 + 8 事件 dataclass | `harnessx/core/processor.py:560` + `events.py` | 完全一致 |
| 九维分类法 | `processors/` 七子包 + `rl/`(D9) + `sandbox/`(D5)；UI schema `dimension_schema.py` 暴露 7 组 | `harnessx/processors/*`、`harnessx/api/dimension_schema.py` | 一致（UI 仅 7 组） |
| run loop 发射 task_start..task_end | `run_loop()` | `harnessx/core/runloop.py:116` | 一致 |
| **AEGIS = Digester+Planner+Evolver+Critic 由一 meta-agent 驱动** | `MetaAgent.evolve()`（planner+evolver）+ `trajectory_digester` worker（digester）+ `EvolveValidator.run()`（critic），编排于 `agent.py` | `harnessx/meta_harness/agent.py:538`、`workers/trajectory_digester.py`、`validate_workflow.py:857` | **术语差**：代码不用"AEGIS/Digester/Planner/Evolver/Critic"命名，四阶段非四类，而是多阶段编排 |
| 确定性门控 / seesaw 约束 | `EvolveValidator`（validity→policy→advisory）+ `check_novelty`(拒绝重复 reverted 假设) + per-recipe `_score_and_gate` + `run_replay_gate_strict`(smoke) + `journal.fill_gating` | `validate_workflow.py`、`recipe/gaia_evolver/run.py:1174`、`meta_harness/replay.py`、`journal.py:271` | **"seesaw"字面不在代码**；门控多层但跷跷板隐喻非字面 |
| 变体隔离 / Ensemble routing（至多 K 变体） | — 未实现 | `docs/ROADMAP.md:40`（"Genetic/evolutionary RL: spawn variant harnesses"列 planned） | **未实现** |
| 协同进化 / 共享 replay buffer / 跨 harness GRPO | 仅单 harness GRPO 接 veRL | `recipe/verl_harnessX/*`、`recipe/slime/*` | **未实现**（论文核心 C3） |
| change manifest schema（candidate_id/bucket/capability_evidence/file_changes/predicted_impact/attribution_signature） | `candidates.md`（agent 撰写，schema 在 `skills/analyze/SKILL.md`，C-NNN + lens×lever×intent 标签）+ `compute_changeset()`（结构 diff）+ `JournalEntrySpec` frontmatter（`predicted_affected`/`gating_attribution`/`hypothesis_id`） | `meta_harness/agent.py:439`、`meta_harness/journal.py:124`、`workspace/skills/analyze/SKILL.md` | **无单一 dataclass**；schema 是三制品的并集，字段名有差（`predicted_affected`≠`predicted_impact`） |

### 4.6 核心模块分析

#### 4.6.1 核心数据结构

`agentic()`（`core/model_config.py:73`）——论文与代码字面一致的入口：

```python
def agentic(self, harness_config: "HarnessConfig") -> "Harness":
    """Combine this model config with a harness config to produce a runnable agent.
    Args:
        harness_config: A fully built HarnessConfig (tools, processors, tracer, …).
                        Must contain NO model information — the model is provided here.
    Returns:
        A :class:`~harnessx.core.harness.Harness` ready for ``await agent.run(task)``.
    """
    from .harness import Harness
    return Harness(model_config=self, config=harness_config)
```

Processor Protocol（`core/processor.py:343`）——五种 outcomes 在 docstring 明示：

```python
@runtime_checkable
class Processor(Protocol):
    """
    Consumes an Event, can:
    - yield the same event (pass-through)
    - yield a modified event (transform)
    - yield multiple events (split, for multi-agent fork)
    - yield nothing (intercept/block)
    - raise an exception (interrupt)
    """
    async def process(self, event: Event) -> AsyncIterator[Event]: ...
```

#### 4.6.2 核心算法实现

AEGIS 四阶段在代码中的对应（论文的"一 meta-agent 驱动全四阶段"→ 代码为单 `MetaAgent.evolve()` + 子 worker + 验证器）：

```python
class MetaAgent:  # harnessx/meta_harness/agent.py:493
    async def evolve(  # :538 — 论文 Planner+Evolver 的代码落点
        self, *, current_config, trajectories_dir, output_dir,
        replay_model=None, ...
    ) -> Path:
        ...  # 读轨迹→起草候选→写 config.yaml + authored files→追加 journal

class EvolveValidator:  # harnessx/meta_harness/validate_workflow.py:857 — 论文 Critic 的代码落点
    async def run(  # validity→policy→advisory 三阶段门控
        self, *, out_yaml, current_config, scratch_dir, output_dir,
        elapsed, compute_changeset_fn,
    ) -> ValidateOutcome: ...
```

### 4.7 配置参数详解

<p align="center"><b>表13：进化协议超参（论文 Table 16）</b></p>

| 参数 | 含义 | 值 |
|------|------|----|
| $K_t$ | 每轮候选数 | 4 |
| seeds | 每 cell 随机种子 | 3 |
| 噪声阈值 | 忽略的单轮 pass-count delta | ±5% |
| $\mathcal{H}_0$ | round-0 harness | 手工基线（已含 benchmark 工具的"胜任"基座，非最小默认） |
| meta-agent | 驱动 Digester/Planner/Evolver/Critic | Claude Opus 4.6 |
| task agent | 跑 benchmark | Sonnet 4.6 / GPT-5.4 / Qwen3.5-9B |
| 并发 | 并行任务 rollout | 10 |
| max-steps | GAIA/WebShop=20；ALFWorld=15；$\tau^3$/SWE=200 | — |

协同进化训练设置：$8\times$H100、batch 256、lr $1\times10^{-6}$、GRPO clip $\epsilon_c=0.2$、无 KL 惩罚（系数 0）、每轮 5 训练步；buffer 为 4 轮滑动窗口（GAIA 824 trace / WebShop 400 trace）。

### 4.8 代码质量评估

<p align="center"><b>表14：代码质量评估</b></p>

| 维度 | 评分 | 说明 |
|------|------|------|
| 模块化 | ⭐⭐⭐⭐⭐ | core/processors/meta_harness/rl 分层清晰，无循环依赖；9 维→子包映射干净 |
| 可配置性 | ⭐⭐⭐⭐⭐ | `HarnessBuilder` + `\|` 算子 + singleton group 冲突检测（`HarnessConflictError` 无静默覆盖） |
| 可扩展性 | ⭐⭐⭐⭐ | 新 processor/工具/benchmark 适配有清晰 pattern（docs/agents.md 给了 5 类 pattern） |
| 与论文一致性 | ⭐⭐⭐ | 基座（C1）高度一致；AEGIS（C2）有术语差但机制在；变体隔离（C2 子项）与协同进化（C3）**未实现**，列于 ROADMAP |
| 文档 | ⭐⭐⭐⭐⭐ | README 中英双语 + docs/agents.md（给 AI coding 助手的实现指南）+ architecture.md + concepts/ |
| 测试 | ⭐⭐⭐⭐ | tests/ 含 unit/integration/E2E；pre-commit + CI |
| 可复现 | ⭐⭐⭐ | recipe/ 给了 GAIA evolver 与 verl GRPO 的复现路径；但论文的变体隔离/协同实验无对应 recipe |

### 4.9 复现指南

```bash
# 一键安装（交互式）
curl -sSf https://raw.githubusercontent.com/Darwin-Agent/HarnessX/main/scripts/install.sh | bash

# 手动（uv）
uv python install 3.12 && uv venv --python 3.12 .venv
source .venv/bin/activate && uv pip install -e .
cd frontend && npm install && npm run build && cd ..

# 运行
export ANTHROPIC_API_KEY=sk-...
hx "Research 2026 AI agent trends"     # 交互
hx -p "Write a Python fizzbuzz"        # 非交互
hx -c path/to/config.yaml              # 加载 YAML 配置
hx lab                                 # Lab UI @ localhost:8000

# Python SDK
model = ModelConfig(main=AnthropicProvider("claude-sonnet-4-6"))
harness = model.agentic(HarnessConfig())
result = await harness.run(BaseTask(description="What is 2+2?"))
```

复现论文 harness 进化：`recipe/gaia_evolver/`（README 报告 Qwen3.5-9B 在 GAIA R0=33%→R3=47%，+14pp；GPT-5 GAIA 62%→84%）。复现模型协同：`recipe/verl_harnessX/`（README 报告 Qwen3.5-9B harness-only 33.97%→41.67%，加 model evolution 到 55.77%，相对 +64%）。

> 注：README 的复现数字（GAIA Qwen R0=33%）与论文 Table 9（GAIA Qwen initial=20.3%）口径不同——README 似用"更默认"的 R0 基座，论文用"胜任基座"$\mathcal{H}_0$。复现时以仓库 recipe 为准。

---

## 5. 实验分析

### 5.1 实验设置

#### 数据集

<p align="center"><b>表15：实验数据集</b></p>

| 数据集 | 域 | 采样任务 | 验证器 |
|--------|----|---------|----|
| GAIA（Level 1-3） | 多步检索 | 103（39/52/12 分层） | 精确匹配 |
| ALFWorld | 具身规划 | 134（valid-unseen，6 类任务） | 目标完成 |
| WebShop | 网页交互 | 100（固定种子） | 属性匹配 |
| $\tau^3$-Bench | 多轮对话 | 3 域（Retail/Airline/Telecom） | 规则合规 |
| SWE-bench Verified | 软件工程 | 55（子采样） | patch resolution |

#### 评估指标

<p align="center"><b>表16：评估指标</b></p>

| 指标 | 定义 | 计算方式 |
|------|------|---------|
| pass@$k$ | 至少 $k$ 次 rollout 中有一次解开的概率（无偏估计） | $\text{Pass@}k = \frac{1}{\lvert D\rvert}\sum_i \left(1 - \frac{\binom{n-c_i}{k}}{\binom{n}{k}}\right)$ |
| $\Delta$ | 进化后峰值 - 初始 | 逐配置 |
| Final−Peak | 末轮 - 峰值（稳定性；负值=灾难性遗忘） | 逐策略 |

主曲线用 pass@2（每任务 2 独立 rollout，任一成功即解）：降低单 rollout 随机性、保严格任务级判据（代价是 mask 次阈值成功率漂移）。基础设施失败的 rollout 计为失败而非剔除，与官方 leaderboard 协议可比。

#### 实现细节

- **角色区分**：meta-agent（Claude Opus 4.6）驱动 AEGIS；task agent（Sonnet 4.6/GPT-5.4/Qwen3.5-9B）跑被进化 harness。
- **预算**：每 benchmark 100M-175M token，同 benchmark 内跨 task agent 恒定。
- **基线**：(1) Static Harness（固定）；(2) CC SDK v0.0.25（单 agent evolver，隔离 AEGIS 多阶段架构 vs 共享基础设施，兼 SICA 代理）。
- **运行**：每轮评全集（无子采样），$T=15$ 轮，$P=3$ 连续无上线即早停。并发 10；meta-agent 并发 4、200 步上限。协同训练 $8\times$H100。
- **范围**：所有增益在进化所用同一任务集上测；未见任务泛化未评。

### 5.2 主实验结果

![Figure 4: 进化轨迹](assets/fig4_evolution_curves.png)

*Figure 4: 进化轨迹（pass@2 成功率 vs 轮次）。虚线为 static-harness 基线。可见 ALFWorld/GPT-5.4 在 R4 早达峰、SWE-bench R2-R3 达峰、GAIA/Sonnet 需 11 轮（失败跨 4 组件类型）。读者核心洞察：收敛速度追踪失败模式集中度——失败聚于 1-2 类组件则快收敛，跨多类则需逐邻域探索。*

<p align="center"><b>表17：主实验结果（pass@2 成功率 %，Evolved=峰值）</b></p>

| Benchmark | Task agent | Initial | Evolved | $\Delta$ | Best round |
|-----------|-----------|---------|---------|---------|-----------|
| ALFWorld | Sonnet 4.6 | 83.6 | 94.8 | +11.2 | 7 |
| ALFWorld | GPT-5.4 | 76.9 | **97.8** | +20.9 | 4 |
| ALFWorld | Qwen3.5-9B | 53.0 | 97.0 | +44.0 | 9 |
| WebShop | Sonnet 4.6 | 60.0 | **76.0** | +16.0 | 7 |
| WebShop | GPT-5.4 | 55.0 | 73.0 | +18.0 | 8 |
| WebShop | Qwen3.5-9B | 36.0 | 49.0 | +13.0 | 7 |
| GAIA | Sonnet 4.6 | 73.8 | **83.5** | +9.7 | 11 |
| GAIA | GPT-5.4 | 73.8 | 73.8 | 0.0 | 4 |
| GAIA | Qwen3.5-9B | 20.3 | 37.4 | +17.1 | 4 |
| SWE-bench Verified | Sonnet 4.6 | 76.4 | **87.3** | +10.9 | 3 |
| SWE-bench Verified | GPT-5.4 | 45.5 | 63.6 | +18.2 | 3 |
| SWE-bench Verified | Qwen3.5-9B | 23.6 | 41.8 | +18.2 | 2 |
| $\tau^3$-Bench (Avg) | Sonnet 4.6 | 89.6 | **95.0** | +5.4 | — |
| $\tau^3$-Bench (Avg) | GPT-5.4 | 76.2 | 90.7 | +14.5 | — |
| $\tau^3$-Bench (Avg) | Qwen3.5-9B | 93.5 | 94.6 | +1.1 | — |

**总体表现**：进化改善 15 配置中 14 个，平均 +14.5%（最高 +44.0%）。GAIA/GPT-5.4 唯一停滞（$\Delta=0.0$，反映单 harness 在异构任务集上的根本局限，§5.3 变体隔离解决）。$\tau^3$-Bench Telecom 中途回归（R7 −14.0%，因累积同型编辑，R9 恢复，§5.5）。

**与基线性能的逆缩放（核心发现）**：跨 benchmark，最弱 task agent（Qwen3.5-9B）一致获益最大——ALFWorld +44.0%（基线 53.0%）、GAIA +17.1%（基线 20.3%）、SWE-bench +18.2%（基线 23.6%）。更强模型获益更少。例外 GAIA/GPT-5.4（$\Delta=0.0$）任务异质性所致。整体规律：**弱模型有更多可被 harness 级编辑纠正的行为缺口；基线足够高后，残余失败愈益需任务特异适应而非全局改进。**

**跨模型泛化**：Opus 4.6 meta-agent 跨模型族进化 harness 无需族特异适应。ALFWorld 上跨族 agent（GPT-5.4 +20.9%、Qwen3.5-9B +44.0%）获益超同族 agent（Sonnet 4.6 +11.2%），表明增益量级追踪基线表现而非与 meta-agent 族接近度。

**收敛速度追踪失败模式集中度**：ALFWorld/GPT-5.4 R4 达峰、SWE-bench 全 agent R2-R3 达峰（失败聚 1-2 类组件）；GAIA/Sonnet 4.6 需 11 轮（失败跨 prompt/tool/processor/config 四类，需顺序探索多邻域）。

**$\tau^3$-Bench 域内变异**：GPT-5.4 在 Telecom +25.4%（67.5%→93.0%@R2）、Retail +9.7%；但 Sonnet 4.6 在 Telecom 单轮回归 −14.0%（R7，累积同型编辑，R9 恢复）——揭示 per-edit 门控的结构局限：连续同型编辑的次阈值耦合累积至阈值才显化。

**SWE-bench 峰后退化**：GPT-5.4 R3 峰 63.6%（+18.2%）但 R5 退化至 50.9%（−12.7% vs 峰），末值仍超 static +5.4%。两因素加速退化：(1) 仅 55 任务，每翻转约 1.8%（vs n=103 的 1.0%）；(2) 结构代码编辑 blast radius 大于 prompt 编辑。与 GAIA/GPT-5.4 停滞同理，均 motivates 变体隔离。

### 5.3 进化策略对比（变体隔离消融）

<p align="center"><b>表18：进化策略对比（GAIA, GPT-5.4, AEGIS, 15 轮）</b></p>

| 策略 | Final (%) | Peak (%) | Final−Peak | Tokens |
|------|-----------|----------|-----------|--------|
| Ensemble（至多 K 变体） | **87.4** | 87.4 | 0.0 | 107.8M |
| Global（单 harness） | 49.5 | 73.8 | −24.3 | 143.7M |

**Global 失败机制**：单 harness 服务全 103 任务，R4 早达峰 73.8% 后稳步退化——后续编辑引入 pass@2 二值信号下不可检的次阈值回归，复合成聚合下降。Peak−final gap −24.3% 远超每轮二项 95% CI（±8.5%@n=103），排除评估噪声，确认灾难性遗忘。这解释 Table 17 GAIA/GPT-5.4 的 $\Delta=0.0$：Global 无法在异构任务集上持续改进。

**Ensemble 防跨变体遗忘**：至多 K 变体 + 任务路由到历史成功率最高变体。编辑按变体提议评估，一簇改进不能回归另一簇。三预测性质验证：(1) 非退化轨迹（peak=final）；(2) 更晚达峰（R14 vs R4，持续生产性探索）；(3) 更低 token（107.8M vs 143.7M，每编辑只评目标簇而非全集）。

**小结**：变体隔离把 GAIA/GPT-5.4 从 $\Delta=0.0$ 抬到 +13.6%（87.4%，非退化）。

### 5.4 Meta-Agent 架构有效性

<p align="center"><b>表19：Meta-agent 架构对比（GAIA, GPT-5.4, 变体隔离, 15 轮，均 Opus 4.6）</b></p>

| Evolver | Accuracy (%) | Best round | Tokens |
|---------|-------------|------------|--------|
| AEGIS | **87.4** | R14 | 107.8M |
| CC SDK | 86.4 | R12 | 123.1M |

**精度可比、效率不同**：1.0% 精度差在一标准误内（~3.3%@n=103），表明四阶段分解在此 meta-agent 能力级不提升末精度。但单 agent 多耗 ~14% token（123.1M vs 107.8M），归因 Digester 压缩（~10M 原始 trace → ~10K 结构化摘要）；无此阶段单 agent 须截断 trace 适配上下文，产更欠考虑编辑、门控更频拒、浪费 token 于失败提议。

**含义**：有能力的 meta-agent + 变体隔离下，精度增益主要来自 HarnessX 基础设施（带类型组件使隔离、结构化 trace 使诊断）而非 evolver 内部架构。四阶段贡献效率（~12% 少 token）与可解释性（可审计中间制品）而非此规模下的可测精度。

### 5.5 失败分析（三种病理的实证）

![Figure 6: 失败案例（按病理组织）](assets/fig6_failure_cases.png)

*Figure 6: 失败案例按病理组织（行：奖励作弊、灾难性遗忘、探索不足）。三案例各示"首次浮现的检测信号→trace 分析定位的根因→自愈或需人工的结局"。读者核心洞察：论文主动暴露系统自改代码时踩的坑（含一个根本没起作用的小工具），这种坦诚不常见——每案例都可被后续研究者复现与改进。*

**奖励作弊（GAIA, Sonnet 4.6, R10）**：R10 上线复合编辑（tool+prompt+config）manifest 预测改进检索，过 seesaw、精度 74.8%→79.6%。R11 trace 分析揭示：工具确修了多数新通过任务的检索，但子集靠利用验证器格式规律而非真检索通过。R12 Planner 标此路径，编辑引入守卫把工具限于可对第二条检索路径交叉校验的任务。详见 §6.2 的 R10 WikiTextFetch 工作示例。

**灾难性遗忘（$\tau^3$, Sonnet 4.6, Telecom, R7）**：R2-R6 连续五轮同型 prompt/processor 编辑（各加一"提醒"规则），合规 89.5%→100%@R4→94.7%@R6（后规则与前规则冲突）。R7 Critic 标集中风险（"前 5 ship 占同一桶"）仍批准（因 ship-prediction 准确高 23/24,5/6,4/5,7/7,2/3 且无回归记录）。第六提醒致 94.7%→80.7%（−14.0%），经跨规则冲突。此回归逃过 seesaw 因 pass@2 仅记逐任务二值翻转、不记次阈值耦合。R9 自愈（Planner 诊集中模式、提结构编辑替换冲突提醒栈）。

**探索不足（ALFWorld, Sonnet 4.6, R4-R7）**：R4-R7 主要 prompt 级编辑，每轮 <1% 增益。ship-prediction 准确 80%(R3)→0%(R7)，示 prompt 空间耗尽。唯一结构编辑（R6 processor 级）仅 14% ship-prediction（1/7 预测实现），示 Planner 缺足够结构编辑历史以校准 prompt 邻域外假设。

### 5.6 实验结果总体分析

从全局视角综合解读五组实验，验证层次为：**现象验证 → 自动化验证 → 协同验证**。

1. **现象层（主实验 §5.2）**：harness 进化在 5 基准 × 3 模型族的 15 配置上改善 14 个，证"harness 是可改进的一类对象"；逆缩放规律证"基线越弱、harness 收益越大"，提示 harness 进化补的是弱模型自身无法自纠的行为缺口。GAIA/GPT-5.4 的 $\Delta=0.0$ 与 SWE-bench 峰后退化暴露单 harness 在异构任务集与小编号集上的局限。
2. **自动化层（策略对比 §5.3 + meta-agent §5.4）**：变体隔离把停滞抬到 +13.6% 非退化，证"类型化组件使隔离、隔离使稳定"——组合结构是稳定进化的前提，非可选优化。meta-agent 对比证精度主要来自基础设施而非四阶段架构，但四阶段供效率与可审计性。
3. **协同层（§5.7 协同进化）**：跨 harness GRPO 把 GAIA 37.4%→41.7%（+4.3%）、WebShop 49.0%→54.0%（+5.0%），均 +4.7%，证"同 rollout 驱动两更新可破两天花板"。

**核心结论与边界**：(1) harness 进化是模型缩放外有效的互补杠杆，尤其对弱模型；(2) 稳定进化需类型化组合基座（变体隔离前提）+ 结构化 trace（病理可诊）；(3) 协同进化可破单边天花板但需"联合控制 harness 与模型训练"的组织前提。**边界**：所有增益在进化集本身测（选偏 + 可能过拟合，无 held-out）；仅离散动作空间；闭源 meta-agent（Opus 4.6）才能做多文件代码生成 + 结构化 trace 分析；$\tau^3$ 仅 3 域、SWE 仅 55 任务，逆缩放未必泛化。

### 5.7 协同进化实验

![Figure 5: 协同进化 vs harness-only](assets/fig5_coevolution_curves.png)

*Figure 5: 协同进化 vs harness-only（AEGIS，模型冻结）在 GAIA 与 WebShop。星标各方法峰值；阴影带为协同增益。两曲线 R4 前重合（联合训练生效），后分离，协同全程 ≥ harness-only，gap 持续到末轮且 WebShop 更宽（更多模型级改进空间）。读者核心洞察：协同抬升的是末轮精度非仅峰值——真正破了脚手架天花板。*

**协同超 harness-only**：跨 harness GRPO 与 harness 进化在共享 buffer 上交错，GAIA 37.4%→41.7%（+4.3%）、WebShop 49.0%→54.0%（+5.0%），均 +4.7%。gap 持续到末轮（GAIA 36.4%→39.8%、WebShop 46.0%→50.0%），WebShop 更宽（模型级改进空间大）。协同抬末轮精度非仅峰值。

**破脚手架天花板**：harness-only 在 GAIA ~37%、WebShop ~49% 平台化；协同清这些平台：跨 harness GRPO 让模型内化历代 harness 版本策略，后续编辑建立在已学行为而非补偿固定模型内在局限。

### 5.8 各 Benchmark 进化深度分析（附录）

附录为每 benchmark 给出三联图：(a) 失败簇及成因、(b) 每模型 shipped 编辑杠杆分布、(c) 模型×杠杆的 hit-rate 热图（翻转/预测）。依次读：什么失败为何、各模型怎么进化、进化是否闭合失败。

#### GAIA

![Figure 7: GAIA 进化分析](assets/fig7_gaia_detail.png)

*Figure 7: GAIA 进化分析（103 任务，精确匹配）。(a) 失败簇：blocked-source 39%（页面返空/需 JS 渲染超时/信息不全）、reasoning 33%（多跳推理/实体消歧/数值计算）、figure/visual 11%、document/table 解析 11%、scope ambiguity 6%。(b) Sonnet 单跑就 ship 11 prompt/7 processor/7 config/6 tools（唯一四杠杆全用的 benchmark）；GPT-5.4 重 prompt（45%）；Qwen3.5 单次 tools ship 是全表最高产（0.67 hit-rate）。(c) 最大改进来自 blocked-source 簇（WikiTextFetch 替不可靠浏览器检索）。读者核心洞察：GAIA 是杠杆最 diverse 的基准，失败聚于证据检索与多步推理；prompt 改推理簇、tool 改检索簇，残余在视觉/文档。*

#### ALFWorld

![Figure 8: ALFWorld 进化分析](assets/fig8_alfworld_detail.png)

*Figure 8: ALFWorld 进化分析（134 任务，目标完成）。(a) search/step-ceiling 89% 主簇（搜索低效或超步限）、prompt-rule 副作用 7%、object 混淆 4%。(b) prompt 主导性逆基模型强度缩放：强 Sonnet 几全靠 prompt；弱 Qwen3.5 需最多样 mix（含拦截推理文本重发 tool call 的 processor）。(c) Qwen3.5 的 processor/config hit-rate 0.84/0.71（机械地补 missed tool call + 调执行预算，直接补 +44.0%）；Sonnet prompt 0.49 足够。读者核心洞察：越弱基模型，进化越早从 prompt 转向 config/processor 强制——可见非 prompt 段从 Sonnet 到 Qwen 增长。*

#### WebShop

![Figure 9: WebShop 进化分析](assets/fig9_webshop_detail.png)

*Figure 9: WebShop 进化分析（100 session）。(a) 残余多在产品判断：wrong product 46%、分页循环 21%、颜色匹配 17%、属性检查 17%（进化先驯服早期搜索/分页循环，残余转向产品选择判断）。(b) prompt 驱动改进、processor 次之（匹配主控制流失败）；弱模型加 config 维持长会话上下文。(c) prompt 最一致有效（0.37-0.50）；advisory processor 仅 modest（0.20-0.25）；颜色匹配工具 0.0 hit-rate（根本没起作用）。读者核心洞察：WebShop 是论文坦承"一个小工具压根没用"的基准——诚实暴露进化非万能。*

#### $\tau^3$-Bench

![Figure 10: $\tau^3$-Bench 进化分析](assets/fig10_tau3_detail.png)

*Figure 10: $\tau^3$-Bench 进化分析（airline/retail/telecom 池化）。(a) 失败判断重：premature/unverified action 28%（前置条件未满足就 commit）、wrong selection/count 24%（何时 commit、选什么而非机械执行）；tail 含 capability-boundary confusion 5%（$\tau^3$ 特有：某些 telecom 故障在用户手机侧、agent 无设备侧工具）。(b) 每模型 prompt+processor 驱动、零 tools 编辑（工具集固定、无簇可被新工具闭合）。(c) config 最锋利但罕发（Qwen3.5 0.67）；高量 prompt/processor 中等有效（0.27-0.35）。增益追基模型 headroom：GPT-5.4 最低 76.2% 增 +14.5%、近天花板 Qwen3.5 仅 +1.1%。读者核心洞察：$\tau^3$ 的控制流/判断错由编码策略排序约束的 prompt + 强制它们的 processor 闭合最可靠。*

#### SWE-bench Verified

![Figure 11: SWE-bench Verified 进化分析](assets/fig11_swebench_detail.png)

*Figure 11: SWE-bench Verified 进化分析（55 任务，resolved-rate）。(a) incomplete fix 62%（覆盖 gold patch 的一个分支/调用点而非全部）、wrong diagnosis 19%、mechanical tail（no-edit 6%、anchor mismatch 5%、budget 4%）。注：与奖励作弊相反——失败是 under-fix 非 gamed，因 harness 先 apply gold test patch 再 block test 文件写。(b) 每模型 prompt-first、零 tools；次杠杆随基模型强度从 processor（Sonnet）→config（GPT-5.4）→varied（Qwen3.5）。(c) 锐利能力地板：强模型 productive 杠杆真闭合失败（GPT-5.4 config 0.48/prompt 0.39、Sonnet prompt+processor 0.40），但 Qwen3.5 每杠杆塌到 ~0.05（比强模型低一数量级，9B 基无法执行预测修复）。读者核心洞察：同一套进化流程在 GPT-5.4 上 45%→64% 峰、在 Qwen3.5 上只产噪声——存在"进化无法复利"的能力地板。*

#### 各 benchmark 小结

<p align="center"><b>表20：各 benchmark 进化模式对比</b></p>

| Benchmark | 主失败簇 | 主杠杆 | 是否用 tools | 弱模型增益特征 |
|-----------|---------|--------|------------|--------------|
| GAIA | blocked-source / reasoning | 全四杠杆（最 diverse） | 是（WikiTextFetch 最高产） | Qwen +17.1%，单 tools ship 0.67 |
| ALFWorld | search/step-ceiling | prompt→随弱化转 processor/config | 少 | Qwen +44.0%，processor 0.84 |
| WebShop | wrong product / 分页 | prompt + processor | 是（颜色匹配工具 0.0 失效） | Qwen +13.0% |
| $\tau^3$ | premature action / wrong selection | prompt + processor | 零（工具集固定） | GPT-5.4 增 +14.5%，Qwen 近天花板仅 +1.1% |
| SWE-bench | incomplete fix / wrong diagnosis | prompt + processor/config | 零（无机械检索簇） | Qwen 每杠杆塌到 ~0.05，能力地板 |

---

## 6. 工作示例：GAIA / Sonnet 4.6 第 10 轮

附录给出一个完整 AEGIS 周期实例——选 GAIA/Sonnet 4.6 R10 的复合编辑（tool+prompt+config），该轮产生全程最大单轮增益，比单杠杆编辑更富说明性。

**失败证据**：R10 前成功率 74.8%（从 R9 峰 77.7% 因 R9 回落）。Digester trace 分析揭示系统性失败：每轮 R10 trace 中每次 Wikipedia WebFetch 返 0 字符（Wikipedia 新前端在需 JS 时超时/返空体）。trace 直白：`db4fd70a`（rail line 站数）`db4fd70a_r0.jsonl#step_0/1` Wikipedia WebFetch 返 0 字；`f0f46385`（ASEAN 成员）三次连返 0；全轮十次空响应。

**Planner 综合**：Digester 把 23 失败任务按失败模式分组，浮现一关键工具级问题（R9 Critic 已标：tools 组件连续 9 轮未 ship 修复）。Planner 收两目标：(1) 解顽固工具级源访问失败；(2) revert R9 回落肇因的 prompt 与 budget-processor 改动。

**Evolver 编辑（C-R10-02，跨三桶）**：(i) tools——新 `WikiTextFetch` 工具绕开浏览器、用 MediaWiki API 取纯文本（rail line 10,529 字、ASEAN 80,028 字）；(ii) prompt——工具使用节加一句指引用 `WikiTextFetch` 先查 Wikipedia；(iii) config——恢复 R8 基线、注册 `WikiTextFetch`、移除有问题的 budget processor。manifest capability evidence 含 Level-2 round-trip 检查（内容被 provider 序列化为 10,529 字串）；attribution signature 要求至少一次 `WikiTextFetch` 调用。

**Critic 判决**：仅批 `C-R10-02`，拒竞争的 revert-only `C-R10-01`。理据三方面：(i) 交互——`C-R10-02` 是 `C-R10-01` 严格超集，均恢复 R8，budget-processor 移除是 intentional 非意外重叠；(ii) round-trip 证据——Level-2 验证（工具输出到模型为全串非截断标记）；(iii) portfolio——10 轮来首次 tools-bucket ship，持久零字符返回的 trace 证据证干预合理。

**实现 delta**：上线后 GAIA 74.8%(R9)→79.6%(R10)（+4.9pp，5 任务翻转为通过），全程最大单轮增益；7 个预测受影响任务中 5 翻转（hit-rate 0.71，全 19 跑中最高）；改进主要在 Level 2（+4）与 Level 3（+2）。因工具触发了目标任务，attribution 条件满足。

此案例对应微信文章"案例 1：浏览器超时问题"的描述——AEGIS 诊断、写新工具绕浏览器、查 MediaWiki API 取纯文本、失败任务解锁。另一经典案例（WebShop 分页循环）对应 §5.8 WebShop：未只调 prompt 而建一 advisory processor 检测重复导航、注入警告强制决策，治好循环。

---

## 7. 相关工作

### 7.1 相关工作列表

<p align="center"><b>表21：相关工作列表</b></p>

| 论文/方法 | 年份 | 核心思想 | 与本文关系 |
|----------|------|---------|-----------|
| LangChain / LlamaIndex / Smolagents | — | 原语层：prompt/tool/retrieval/memory 积木 | 本文组合基座的对比层（不可 harness 级组合） |
| LangGraph / AutoGen / CrewAI / Letta | — | 编排层：状态图/多 agent 对话/角色/持久记忆 | 本文对比层（强加固定控制环） |
| Claude Code / Cursor / Manus / DeerFlow | — | 产品化 domain-specific harness | 本文对比层（架构静态、仅人工迭代） |
| APE / OPRO / EvoPrompt / Promptbreeder | — | prompt 黑盒优化 | 本文 prompt-only 进化的对比（范围窄） |
| ProTeGi / TextGrad / DSPy / MIPRO | — | 文本梯度/编译式 prompt 优化 | 本文 prompt 可学组件的对比 |
| Memento / MIA | 2026 | case-based/参数-非参数记忆复用 | 本文记忆维度相关 |
| GPTSwarm / ADAS / AFlow / A²Flow / AgentSwift / ResMAS / EvoAgentX | — | 搜协作策略/agent 序/聚合 | 本文工作流结构可学的对比（组件级仍静态） |
| SICA | 2025 | 直接优化 SWE-bench agent 源码 | 本文 harness 改写的对比（无清晰边界） |
| Darwin Gödel Machine | 2025 | agent 变体库的开放式优化 | 本文同方向对比 |
| AHE / Life-Harness / Meta-Harness / HyperAgents | 2026 | 可观测性/源码改写/采样效率 | 本文同期 harness 进化工作 |
| K² Agent | 2026 | 协同 know-what 与 know-how | 本文协同进化思想的平行实例 |
| Claude Code Dynamic Workflows | 2026 | 运行时生成任务特异 harness 脚本 | 本文同期：但单 session、无持久 trace 优化/跨会话/协同训练 |
| DeepSeek-R1 / GRPO | 2024 | group-relative policy optimization | 本文协同进化的 RL 算法基础 |

### 7.2 本文与相关工作的区别

论文自评两结构性缺口贯穿现有三层（原语/编排/产品）：(1) 无层把 harness 暴露为可替换的带类型元素实体——构建 per-task harness 永远是重写；(2) 无 in-loop 改进机制——一旦定义，harness 只在发布间靠人工迭代。HarnessX 以"harness 适应为多轮、trace 驱动的学习问题 + 类型化组合使变体隔离 + 结构化可观测性使病理检出 + 共享 buffer 闭合 harness-model 回路"同时解两缺口。

与 Claude Code Dynamic Workflows 的关键区别：后者让模型运行时生成任务特异 harness 脚本，是迈向自适应 harness 的一步，但**单 session 内、无持久 trace 优化、无跨会话进化、无 harness-model 协同训练**。HarnessX 把 harness 适应做成多轮、trace 驱动、带类型化组合与结构化可观测性的学习问题。

与 SICA/Darwin Gödel Machine 等 harness 改写工作区别：后者无统一理论框架把观测到的失败模式连到原则性防御——HarnessX 以操作镜像提供该框架。

---

## 8. 局限性分析

### 8.1 论文声明的局限性

1. **无 held-out 评估**——所有增益在进化所用同一任务集上测，报峰值且评适应集本身，故数字带选偏与可能过拟合；同分布未见任务泛化合理但未测。
2. **仅离散动作空间**——全实验用离散文本动作空间；连续动作空间（如机器人控制）未测。
3. **闭源 meta-agent**——AEGIS 需能多文件代码生成 + 结构化 trace 分析 + 多步规划的 meta-agent；接近此能力的开源权重（Qwen3.5-72B、Llama-4-Maverick）未作 meta-agent 测。
4. **联合控制假设**——协同进化需对 harness 进化与模型训练的联合控制；实践中常跨团队/组织分离，共享 buffer 无跨团队协调则不现实。
5. **benchmark 覆盖**——SWE-bench Verified 仅 55 任务子采样、$\tau^3$ 仅 3 域；结论（尤其逆缩放）未必泛化到不同任务异质性或更大评估集的域。

### 8.2 发现的潜在问题

<p align="center"><b>表22：潜在问题分析</b></p>

| 问题类型 | 描述 | 影响 |
|---------|-----|------|
| 方法层面 | 操作镜像是设计启发式非形式框架；不预测哪病理主导、何时、相对严重度 | 三病理代表性非穷尽，分布漂移/奖励稀疏可能另有失败模式 |
| 方法层面 | per-edit 门控的结构局限：次阈值耦合累积至阈值才显化（$\tau^3$ Telecom R7） | 即使 5 轮前序 trace 仍逃过 seesaw，无法仅靠 per-edit 门控预防 |
| 实验层面 | 增益在进化集本身测、报峰值，无 held-out | 选偏 + 过拟合风险，泛化未证 |
| 代码层面 | 仓库 Beta，论文 C3（协同进化）/变体隔离属 planned 未实现 | 论文核心贡献无完整开源对应，复现门槛高 |
| 应用层面 | 协同需联合控制 + 闭源 meta-agent | 实际落地受组织与成本约束 |

### 8.3 未来工作方向

论文与仓库 ROADMAP 指向：贝叶斯优化在 ~$10^6$ 配置空间搜（Meta-Harness auto config search）；HarnessHUB 社区 marketplace（`hx pull coding-agent@v1.2`）；多模态记忆后端；harness 记忆进化闭环；遗传/进化 RL 的种群级 harness 变体（即论文变体隔离的代码化）；LoCoMo 长上下文记忆基准。

---

## 9. 个人评价

### 9.1 优点

1. **理论框架统一且可预测**：操作镜像把 harness 进化映射为符号空间 MDP，从而把成熟 RL 病理学转为可预测的设计风险，并为每病理配一防御——这是"事前防御"而非"事后补救"，远胜同期改源码工作。
2. **类型化组合基座是真正的工程贡献**：8 hook + processor 协议 + singleton group + 替换代数让"改 harness"从重写变插拔，且每改动作用域显式——这是变体隔离与可证伪 manifest 的前提。代码与论文高度一致（`agentic()` 字面相同）。
3. **实验诚实**：主动暴露三病理各一失败案例（含自愈）、坦承 WebShop 颜色匹配工具 0.0 hit-rate、$\tau^3$ Telecom −14.0% 回归、SWE-bench 峰后退化——这种坦诚在论文中罕见，使后续工作可复现改进。
4. **逆缩放规律有实际意义**：基线越弱、harness 收益越大（Qwen3.5-9B ALFWorld +44.0%），为预算受限团队提供"先优化 harness 再升级模型"的实证依据。
5. **协同进化的经济学设计巧妙**：同一 rollout 驱动两更新、GRPO 靠重放零额外 rollout，把模型改进的边际成本压到离线训练算力——是论文最优雅的工程贡献。

### 9.2 不足

1. **论文与代码脱节**：仓库为 Beta，论文 C3（协同进化/共享 buffer/跨 harness GRPO）与变体隔离属 planned 未实现，AEGIS 四阶段有术语差（非四类）——读者据论文复现核心实验会落空，需以 recipe 为准。
2. **无 held-out 评估是硬伤**：增益在进化集本身测且报峰值，选偏与过拟合风险无法排除；逆缩放规律虽诱人但泛化性未证。论文自身承认但仍是可信度上限。
3. **闭源 meta-agent 门槛高**：AEGIS 需 Opus 4.6 级多文件代码生成 + 结构化 trace 分析能力，开源权重未验——直接削弱"对弱模型有效"主张的可及性（弱模型是 task agent，meta-agent 仍是强闭源）。
4. **per-edit 门控有不可消除的结构盲区**：$\tau^3$ Telecom 案例证明次阈值耦合累积可逃过 seesaw，且无论多少前序轮"表观稳定"都无法预防——这是论文诚实暴露但未解的根本局限。
5. **协同进化的组织前提未充分讨论可行性**：联合控制 harness 与模型训练在跨团队/组织分离的现实中常不可行，论文列为局限但未给折中方案。

### 9.3 适用场景

- 预算受限、基线弱的 task agent（尤其开源小模型如 Qwen3.5-9B）在固定 benchmark 上提分——harness 进化的逆缩放收益最大。
- 需可审计、可回滚的自进化 agent 系统（manifest + 确定性门控保证安全属性）。
- 同时控制 harness 与模型训练的团队（如小米 Darwin Agent 自身），可走协同进化破单边天花板。

### 9.4 不适用场景

- 需 held-out 泛化保证的生产部署（论文无泛化评估，过拟合风险）。
- 跨团队/组织无法联合控制 harness 与模型训练的场景（协同进化不现实）。
- 无 Opus 4.6 级 meta-agent 资源的团队（AEGIS 进化引擎跑不起来，开源 meta-agent 未验）。
- 连续动作空间任务（如机器人控制，论文仅离散文本动作）。

---

## 10. 启发与思考

### 10.1 技术启发

1. **把"自我改进"映射到已知优化理论**比从零设计防御更强——操作镜像让 RL 病理学直接可用，是值得复用的方法论（任何"让 LLM 反复改自己再打分"的系统都该先问"这等价于什么优化问题、有何病理"）。
2. **类型让坏改动可检测而非不发生**——类比类型系统的洞察可推广到所有"agent 自我修改"系统：与其防错，不如让错误的作用域显式、可隔离、可回滚。
3. **"LLM 探索、确定性规则上线"的两权分离**是自进化系统安全保证的通用范式，不依赖 LLM 可靠性。
4. **同一 rollout 驱动参数与非参数两更新**的经济学，可推广到任何"系统改进与底层训练共生"的场景（如编译器优化与硬件协同设计）。

### 10.2 可借鉴之处

- **8 hook + processor 协议**可作为自研 agent 框架的组合基座参考（事件驱动、类型契约、singleton group 排他）。
- **change manifest 的可证伪设计**（predicted_impact + attribution_signature + capability_evidence）可借入任何"AI 改代码"系统的审计层。
- **跨 harness GRPO 的任务级对齐**思想（不要求动作级对齐、在各自 harness 上下文下算梯度）可用于任何"策略结构跨版本变化"的 RL。

### 10.3 潜在改进方向

1. **补 held-out 评估**：在同分布/异分布未见任务上测泛化，回应选偏批评。
2. **开源 meta-agent 验证**：用 Qwen3.5-72B/Llama-4-Maverick 作 meta-agent，验证 AEGIS 在开源权重下的可行性与精度损失。
3. **次阈值耦合的检测**：$\tau^3$ Telecom 暴露的 per-edit 门控盲区可引入"同型编辑累积计数 + 软回归检查"缓解。
4. **协同进化的去耦合版本**：为无法联合控制的组织设计"harness 进化产出轨迹 → 离线喂模型训练 → 模型升级后再进化 harness"的松耦合版本，放宽组织前提。
5. **代码补齐**：把论文的变体隔离与跨 harness GRPO 在仓库实现（现属 ROADMAP），使核心贡献可复现。

### 10.4 后续行动

- [ ] 深读 GRPO 原文与 veRL 适配，验证跨 harness 分组的离策略偏差有界性
- [ ] 复现 `recipe/gaia_evolver/` 的 harness 进化（Qwen3.5-9B GAIA）
- [ ] 尝试用开源 72B 作 meta-agent，量化 AEGIS 精度损失
- [ ] 探索 manifest 可证伪设计在自研 agent 系统的移植

---

## 参考文献

> 论文中引用的关键文献

```bibtex
@article{harnessx2026,
  title={HarnessX: A Composable, Adaptive, and Evolvable Agent Harness Foundry},
  author={Chen, Tingyang and Lu, Shuo and Zhao, Kang and Meng, Weicheng and Shao, Kun and Luan, Jian and others},
  journal={arXiv preprint arXiv:2606.14249},
  year={2026}
}

@article{shao2024deepseekmath,
  title={DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models},
  author={Shao, Zhihong and others},
  journal={arXiv preprint arXiv:2402.03300},
  year={2024}
}

@inproceedings{kirkpatrick2017overcoming,
  title={Overcoming catastrophic forgetting in neural networks},
  author={Kirkpatrick, James and others},
  journal={PNAS},
  year={2017}
}

@article{ladosz2022exploration,
  title={Exploration in deep reinforcement learning: A comprehensive survey},
  author={Ladosz, Pawel and others},
  journal={arXiv preprint arXiv:2109.11857},
  year={2022}
}
```

---

## 附录

### A. 关键图表索引

<p align="center"><b>表23：关键图表索引</b></p>

| Figure | 描述 | 报告内位置 |
|--------|------|-----------|
| Figure 1 | HarnessX 系统总览（Compose/Adapt/Evolve） | §3.1 方法概述 |
| Figure 2 | AEGIS 进化回路（单 meta-agent 驱动四阶段） | §3.3 方法-AEGIS |
| Figure 3 | harness-model 协同进化回路（共享 buffer） | §3.4 方法-协同进化 |
| Figure 4 | 进化轨迹（pass@2 vs 轮次） | §5.2 主实验结果 |
| Figure 5 | 协同进化 vs harness-only 曲线 | §5.7 协同进化实验 |
| Figure 6 | 失败案例（按三病理组织） | §5.5 失败分析 |
| Figure 7 | GAIA 进化分析三联图 | §5.8 GAIA |
| Figure 8 | ALFWorld 进化分析三联图 | §5.8 ALFWorld |
| Figure 9 | WebShop 进化分析三联图 | §5.8 WebShop |
| Figure 10 | $\tau^3$-Bench 进化分析三联图 | §5.8 $\tau^3$ |
| Figure 11 | SWE-bench Verified 进化分析三联图 | §5.8 SWE-bench |

### B. 流程图索引

<p align="center"><b>表24：Mermaid 流程图索引</b></p>

| 图表 | 描述 | 报告内位置 |
|------|------|-----------|
| 系统架构图 | 论文三概念→harnessx 代码各层映射 | §4.3 |
| 模块依赖关系图 | core/processors/meta_harness/rl 模块 import 依赖 | §4.4 |

### C. 辅助参考资料

`references/` 下 5 篇微信公众号解读（目录名=文章原标题，与 `.md` 首标题一致）：

1. 小米 Darwin Agent 团队发布 HarnessX：Agent Harness 也能「进化」，弱模型最高 +44%（Hyman的杂货铺）
2. 小米发布可进化HarnessX：面向 AI 智能体的可组合、自适应、可进化运行框架（Harness）生成系统（CY编译）
3. 小米提出 harnessX：自动进化的 agent 外壳（季伯常 / 大模型最新论文）
4. 小米的 HarnessX：让 AI 自己重写自己的代码（AI猿）
5. 小米这篇论文，把 Agent Harness 做成了能自己进化的工厂（张新宇）

### D. 调研信息

- 调研人：Claude
- 调研时间：2026-07-16
- 论文版本：arXiv v2（2026-07-02）
- 参考来源：arXiv e-print 源文件、官方仓库 [Darwin-Agent/HarnessX](https://github.com/Darwin-Agent/HarnessX)、5 篇微信解读（见附录 C）

---

*模板版本：v2.2（paper-research-template）*
