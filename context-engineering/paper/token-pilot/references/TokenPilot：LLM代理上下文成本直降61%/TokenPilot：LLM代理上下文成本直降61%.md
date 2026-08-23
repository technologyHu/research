# TokenPilot：LLM代理上下文成本直降61%

# TokenPilot: Cache-Efficient Context Management for LLM Agents

> **作者**：Buqiang Xu, Zirui Xue, Dianmou Chen, Chenyang Fu, Chiyu Wu, Caiying Huang, Chen Jiang, Jizhan Fang, Xinle Deng, Yijun Chen, Yunzhi Yao, Xuehai Wang, Jin Shang, Gong Yu, Ningyu Zhang**核心发表机构**：Zhejiang University、University of Electronic Science and Technology of China、Xi'an University of Electronic Science and Technology、HomologyAI**论文链接**：arXiv:2606.17016v1**发布于**：arXiv 预印本（cs.CL）

## 一、核心贡献 / Core Contributions

- **揭示并建模了文本稀疏性与提示缓存连续性之间的根本权衡**：现有方法通过剪枝或驱逐减少 token 足迹，但会破坏序列布局导致前缀不匹配和 KV 缓存失效。TokenPilot 明确将缓存连续性作为一阶约束纳入上下文管理设计。
- **提出双粒度上下文管理框架 TokenPilot**：全局层面采用“摄入感知压缩”（Ingestion-Aware Compaction）在数据入口稳定提示前缀并消除环境噪声；局部层面采用“生命周期感知驱逐”（Lifecycle-Aware Eviction）基于残差效用保守调度，仅在任务相关性彻底过期时才卸载内容段。
- **在 PinchBench 和 Claw-Eval 两个基准上实现显著成本降低**：孤立模式下成本降低 61%（PinchBench）和 56%（Claw-Eval）；连续模式下成本降低 61%（PinchBench）和 87%（Claw-Eval），同时保持与先前系统相当或更优的任务性能。
- **设计了基于模型的状态估计器和恢复工具**：使用零样本验证器 (Qwen3.5-35B-A3B) 在线估算段落残差效用，并通过恢复工具动态取回被压缩的完整载荷，打破因信息缺失导致的补偿性重试循环。
- **开源集成到 LightMem2 框架**：TokenPilot 已集成至 https://github.com/zjunlp/LightMem2，便于复现与扩展。

## 二、研究背景与动机 / Background & Motivation

LLM Agent 在长期会话中会持续积累上下文，每轮交互都追加新的观察、思考和工具调用结果，导致输入 token 数量快速增长，推理成本随之飙升。以 GPT-5.4-mini 等大模型为例，KV 缓存命中与未命中的定价差异可达 10 倍（，）。因此，如何降低 token 足迹并维持缓存利用率成为部署关键。

现有方法分为两类：文本修剪（如 LLMLingua-2、SelectiveContext）通过剪枝或压缩直接减少 token 数量；动态内存驱逐（如 Pichay、MemoBrain、AgentSwing）则基于价值保留或分页策略动态调整上下文窗口。然而，这些方法均存在共同缺陷：它们会无约束地改变输入序列的布局——删除中间段、移动消息顺序、替换内容为摘要——这使得后续请求的提示前缀与历史 KV 缓存中已计算的前缀产生字节级差异，进而导致**前缀不匹配**和**缓存失效**。前者迫使系统重新计算大量前缀的 KV 状态，后者则完全破坏缓存复用。

![image](https://mmbiz.qpic.cn/sz_mmbiz_png/HBrA90swpQOsO83rNXfJwuibew5z8tD6FfFPuic4AnmMN20iaJ96MtyfHHVpbjDlxEpEoeribl74dQww80w9JibRH8rBqOgicsDtic59vALLBOzj9M/640?wx_fmt=png&from=appmsg)

Comparison of cache alignment behaviors. While the Original Agent Loop上图展示了两种缓存对齐行为的对比。原始 Agent 循环 (Original Agent Loop) 即便有少量上下文积累，其提示前缀保持稳定，缓存命中率高；而现有修剪/驱逐方法会导致前缀频繁变动，缓存命中率骤降。这揭示了一个核心权衡：**文本稀疏性**（减少 token 量）与**提示缓存连续性**（保持缓存命中）之间存在根本性矛盾。一个有效的上下文管理框架必须同时协调二者，在压缩文本的同时确保前缀字节一致性，并推迟结构性驱逐直到任务相关性彻底消失。TokenPilot 正是为此设计的双粒度框架。

## 三、方法 / Methodology

### 3.1 总体框架 / Overall Architecture

TokenPilot 是一个双粒度上下文管理框架，包含全局和局部两个互补的操作层面。全局层面通过“摄入感知压缩”（Ingestion-Aware Compaction）在信息摄入边界标准化布局、净化消息，并稳定提示前缀。局部层面通过“生命周期感知驱逐”（Lifecycle-Aware Eviction）监控上下文段落的残差效用，仅在任务相关性彻底过期时才卸载内容段。两个模块协同工作：全局模块确保缓存连续性，局部模块进一步压缩内存足迹而无需牺牲缓存命中率。

![image](https://mmbiz.qpic.cn/sz_mmbiz_png/HBrA90swpQMPznJpYhHr4MWzmOicBJGSI5ok954DSrLNIiboDWdchnOoJcfeEkkwonaCEqjLoHVzJ3YAcSsHCd9icwTibcJgFDCc2mQ7N1Ps4EA/640?wx_fmt=png&from=appmsg)

The system architecture of TokenPilot, featuring Ingestion-Aware Compaction at the global framework harness level and Lifecycle-Aware Eviction at the local context sequence level.系统架构如上图所示。Agent 的交互循环中，每轮输入经过全局单元的“摄入感知压缩”处理（包括前缀稳定化和观察缩减），然后进入工作记忆。局部单元中的“生命周期感知驱逐”模块定期（以批处理窗口 B=3 轮次触发）调用状态估计器，输出段落状态更新，最终由驱逐执行器构建优化后的上下文窗口。

### 3.2 关键模块 / Key Modules

#### 3.2.1 摄入感知压缩（Ingestion-Aware Compaction）

该模块在数据摄入阶段对消息进行标准化，分为两个子功能：

**缓存稳定化（Cache Stabilization）**：旨在确保跨轮次提示前缀的字节一致性。方法是将系统提示中的运行时易变字段（如工作目录、时间戳、会话 ID）替换为静态占位符；同时将工具定义从系统提示头部移至末尾紧邻动态上下文块，避免因不同任务所需工具不同而导致的结构性前缀变化。形式化地，通过规范化算子  拦截内部消息，令  确保 。

**观察缩减（Observation Reduction）**：针对环境反馈消息（如工具输出、网页内容），采用一组确定性的缩减变换  生成紧凑结构化预览。具体包括：

- 去重：通过哈希对重复的工具调用结果去重。
- 截断：对过长参数和执行输出进行截断。
- 恢复机制：Agent 配备一个专用恢复工具，可在需要时从外部工件注册表  中动态取回完整载荷 。一旦恢复发生，该路径的后续截断被禁止。
- 多模态优化：对 HTML 内容进行精简，对嵌入图像进行缩放压缩。
- 格式清理：移除代码围栏、行号、无效符号，标准化空白。

消息空间被划分为内部意图消息 （系统/模型原生生成）和开放世界环境反馈 。边际效用密度定义为：

其中  是摄入门控，当内容被频繁访问时升级密度以保留完整内容。

#### 3.2.2 生命周期感知驱逐（Lifecycle-Aware Eviction）

该模块在局部序列层面管理段落生命周期。每个上下文段  在注册表  中跟踪三个渐进状态：。边际效用公式为：

其中  表示量化的残差效用。即使段落完成执行路径，只要残效应对当前交互非零，就保留物理缓存槽。

状态更新由在线估计器  执行，实例化为 Qwen3.5-35B-A3B（零样本验证器，在连续 PinchBench 流中总成本 < ）。估计器以稳定批量B轮触发（而非每步），抑制虚假转换。每批量输入压缩的历史视图\mathcal{V}_i，输出状态更新\Delta\mathcal{R}_i^{(j)} = \langle E_j,\, \Psi_j \rangle，其中E_j是解决证据，\Psi_j$ 是残差效用信号。

状态转换管道为：

只有有效转换才会被系统验证并执行。一旦段落降为 ，框架执行单次结构驱逐：

## 四、实验 / Experiments

### 4.1 数据集与评估指标 / Datasets & Metrics

**数据集**：

- **PinchBench**：包含 11 个任务类别、共 123 个真实世界 Agent 任务。
- **Claw-Eval**：容器化 Agent 评估平台，实验使用其 “General” 任务组（161 个多步骤服务编排和独立分析任务）。

**评估模式**：

- **孤立模式（Isolated Mode）**：每个任务独立运行，上下文重置。
- **连续模式（Continuous Mode）**：将同类别任务分组到连续会话中，模拟长期多任务轨迹。PinchBench 上连续模式将 11 个类别各分为一个连续会话；Claw-Eval 上使用 General 组重叠任务构成连续会话。

**评估指标**：

- **任务分数**：Claw-Eval 使用 ；PinchBench 采用聚合输出验证检查。
- **推理成本**：，其中 ，，（基于 GPT-5.4-mini 定价）。缓存命中/未命中 token 来自 API 返回元数据。

**对比基线**：包括压缩方法（LLMLingua-2, SelectiveContext, Keep-Last-N）和动态方法（Summary, LCM, Pichay, MemoBrain, AgentSwing, MemOS）。所有方法使用 GPT-5.4-mini 作为 agent 骨干。

### 4.2 主实验结果 / Main Results

**PinchBench 结果**（连续模式）：

| 方法 | 总体分 | 成本 ($) | Cache Hit (M) | Cache Miss (M) | Output (M) |
| --- | --- | --- | --- | --- | --- |
| Vanilla | 79.2 | 7.24 | 25.015 | 5.943 | 0.202 |
| TokenPilot | **81.3** | **2.79** | 8.551 | 1.549 | 0.219 |

TokenPilot 在 PinchBench 连续模式下取得最高性能 81.3，同时成本仅为 $2.79，相比 Vanilla 降低 61.4%。Cache Miss 仅 1.549M，远低于 Vanilla 的 5.943M，证明其出色的缓存稳定性。

**Claw-Eval 结果**（连续模式）：

| 方法 | 总体分 | 成本 ($) | Cache Hit (M) | Cache Miss (M) |
| --- | --- | --- | --- | --- |
| Vanilla | 62.0 | 81.52 | 709.845 | 21.981 |
| TokenPilot | 60.8 | **10.58** | 21.430 | 9.928 |

Claw-Eval 连续模式下，Vanilla 成本飙升至 ，降至10.58，降幅 87%。Cache Hit 大幅减少（从 709.845M 降至 21.430M）是因为主动驱逐了大量已过期的历史段落，而 Cache Miss 也远低于 Vanilla，表明驱逐并未牺牲缓存命中。

**孤立模式**：

- PinchBench：TokenPilot 成本 ，降低2.27，降低 56%。性能均保持竞争水平（具体分数见源码笔记）。

下图展示了连续会议分析任务中每轮上下文 token 量和缓存命中趋势：

![image](https://mmbiz.qpic.cn/mmbiz_png/HBrA90swpQPD4YqicwFE4PMRQ4RPtwNgPpBgkUS9dV3futyW90EHPDcc2UBgxAu184Dibt73bDHvJLv8EWwb8t00Skgv8YJVrpMYqXYG6etRk/640?wx_fmt=png&from=appmsg)

Per-call context token volume across a continuous Meeting AnalysisTokenPilot 的输入 token 量在驱逐后显著下降，而缓存命中 token 仍保持较高水平，体现出保守驱逐策略的效果。

### 4.3 消融实验 / Ablation Study

#### 4.3.1 渐进式消融

在 PinchBench 连续模式下，逐步添加两个模块：

| 方法 | 总体分 | 成本 ($) | Cache Hit (M) | Cache Miss (M) | Output (M) |
| --- | --- | --- | --- | --- | --- |
| Vanilla | 79.2 | 7.24 | 25.015 | 5.943 | 0.202 |
| + 全局模块 | 79.9 | 4.22 | 26.716 | 1.589 | 0.227 |
| + 局部模块 | **81.3** | **2.79** | 8.551 | 1.549 | 0.219 |

全局模块（摄入感知压缩）使 Cache Miss 从 5.943M 降至 1.589M，成本降低 42%，性能略有提升。再加入局部模块（生命周期感知驱逐）后，Cache Hit 大幅下降（从 26.716M 降至 8.551M），表明大量已过期段落被清除，但 Cache Miss 保持稳定，成本进一步降低 34%，性能提升至 81.3。两个模块协同作用：全局模块稳定前缀，局部模块压缩内存足迹。

#### 4.3.2 摄入感知压缩组件分析

**缓存稳定化单独效果**（孤立模式 PinchBench）：仅引入静态占位符，成本从 降至4.35。叠加缩减通道后成本进一步降至 $2.87。缓存命中率在 PinchBench 上从 38.7% 提升至 79.2%，在 Claw-Eval 上从 67.2% 提升至 83.1%。

**恢复工具必要性**：完全禁用恢复工具导致性能从 80.9 降至 77.1，成本升至 $4.03。因为缺少完整内容时 agent 会执行补偿性重试，引入新反馈，破坏规则化压缩循环。恢复工具通过按需提供载荷打破此循环。

**缩减节省字符数**：HTML 瘦身最多削减 115k 字符（如 oss_alternative_research 任务）；执行输出截断最多削减 883k 字符（如 meeting_gov_recommendations 任务）。下图展示了各任务中的字符节省情况：

![image](https://mmbiz.qpic.cn/sz_mmbiz_png/HBrA90swpQOFZPnXA0LZDqRo1Ww2icSZ4Prgw0ibdDBGPJ2HKeicxGicpGhErIlDCUyOJ99ov9kqZWibhfnd73C5BEbaEYrlxWTn71qpOvgzRq9w/640?wx_fmt=png&from=appmsg)

Per-Task Character Savings from Reduction Passes.

![image](https://mmbiz.qpic.cn/sz_mmbiz_png/HBrA90swpQP99iaEIyAhoLtzb5mkQiaQEDZ6gVTMyJ4NQa6iaDzY9ZFtxNgaPyXwIZtzDMSn4JZaHGmdAUSSRa8licUMPfOnUFazZ7dT7fle6ia8/640?wx_fmt=png&from=appmsg)

Per-Task Character Savings from Reduction Passes.#### 4.3.3 生命周期感知驱逐参数分析

**批量触发间隔 B**：实验取 B = 1, 3, 5, 7, 9，发现 B=3 是最优值。过激进（B=1）导致过早截断，增加缓存未命中；过保守（B 过大）则成本上升。下图展示了不同 B 下的 token 分解和缓存命中率：

![Average per-task Cache Miss, Cache Read, Context Window, and Equal Input tokens, alongside Cache Hit Rate, across turn batch sizes $B \1, 3, 5, 7, 9, ](https://raw.githubusercontent.com/Marverlises/PicGo/main/arxiv-papers/2026-06-23-14-50/2606.17016/turnbatch_token_mix_hitrate_13579.png)

**残差效用缓冲必要性**：通过一个四任务会话案例（操作 transcript.md 文件）说明。TokenPilot 保留残差效用段，下游任务可直接访问文档部分；而无残差效用估计的变体立即驱逐已完成任务，导致每个子任务重新读取文件，发出多次部分顺序读取。

![image](https://mmbiz.qpic.cn/mmbiz_png/HBrA90swpQMgsIGUhmzaq2lCRjRtNAUm1ibmE0icQYH3jtr6zqTzs4c7JPEul9vwhiaYo2cEZF6MgTFEkHKwQ5vJCxX1ujgGYNrXria18ZibeqvM/640?wx_fmt=png&from=appmsg)

Tool call patterns across a four-task session on transcript.md**提示模板消融**：为验证残差效用估计的必要性，设计了两种系统提示模板。完整估计器包含“联合跟踪完成证据”和“显式缓存驱逐信号”；而去除残差效用估计的模板仅保留完成证据跟踪。两种模板的差异体现了驱逐策略中显式信号的重要性。

![image](https://mmbiz.qpic.cn/sz_mmbiz_png/HBrA90swpQMaicGF24uYQqiaMZIz2Yhl8p8R4ZE3Ys2w34ppuz1U5LibwwmUDyIdt3aicickPxzJaQtFbxkxzHKztiaeF196N22bAxua2WrjvfjZQ/640?wx_fmt=png&from=appmsg)

System prompt template for TokenPilot's Primary Estimator, featuring joint tracking of completion evidence and explicit cache eviction signaling.

![image](https://mmbiz.qpic.cn/mmbiz_png/HBrA90swpQNA9Via4kAMNG5lpVA9FRNUDWCJHUYLTzJMDoNhlicwgy4rwkl7c73hk9EabekFscUkssnOuTPFwHo2vSM8CY2KicV39AxjyAsfRE/640?wx_fmt=png&from=appmsg)

System prompt template for the Estimator without Residual Utility Estimation, configured to strip out the caching buffer for the ablation study.#### 4.3.4 缓存命中率对比

下图展示了各方法在 PinchBench 和 Claw-Eval 上的逐任务缓存命中率。TokenPilot 显著优于基线。

![image](https://mmbiz.qpic.cn/sz_mmbiz_png/HBrA90swpQO4gARAV3xkXRT7uQcz77ICO7u0ZHORicj6QibSpzvCxt9psIw5OjicDKhexBT455iadFIHIQxXvq5j5KBepNgO3V1JosRbovvgOao/640?wx_fmt=png&from=appmsg)

Per-Task Cache Hit Rate on PinchBench and Claw-Eval.

![image](https://mmbiz.qpic.cn/mmbiz_png/HBrA90swpQNkEunfDawgchV8xOPVNxUxuI0HUn0jUfufv6H1FqdWTr6QOvrzJAANT1WQb0oWeCpAT89jsq7yxl13OT0J9lLUicphn4po6rAw/640?wx_fmt=png&from=appmsg)

Per-Task Cache Hit Rate on PinchBench and Claw-Eval.

![image](https://mmbiz.qpic.cn/mmbiz_png/HBrA90swpQNTMba7ClaKnkHnyMgfkfrgZeE2HDoTEyt9mGEpxvhZzfAt9aYDZC70nwEaKIjiatU2g3OIrGD0NYzWALt5z7d7AGwge6P8hIA4/640?wx_fmt=png&from=appmsg)

Per-Task Cache Hit Rate on PinchBench and Claw-Eval.

![image](https://mmbiz.qpic.cn/sz_mmbiz_png/HBrA90swpQPNDZwhGOQljVjDnJibWc1qxMdIXicM7E49A7SfVMBx7tIlxevMJsuE4vSYPO9KxH3tCLCUK9Tj13ic2Kr3dFCib6f2n36qe20Jam8/640?wx_fmt=png&from=appmsg)

Per-Task Cache Hit Rate on PinchBench and Claw-Eval.## 五、相关工作 / Related Work

**静态内容压缩/摘要方法**：早期工作如 LLMLingua-2、SelectiveContext、MemGPT、LightMem、LCM 等专注于过滤或压缩历史轨迹以提高实用密度。然而它们均未考虑对硬件缓存连续性（KV 缓存命中率）的影响。TokenPilot 的摄入感知压缩在设计之初就旨在保障前缀连续性，这是本质区别。

**动态/运行时调度方法**：现代框架如 Pichay、AgentSwing、MemoBrain、MemOS、ClawVM 将上下文窗口视为操作系统资源进行实时调度，但它们通常缺乏双粒度协调，且驱逐策略不够保守。TokenPilot 的双粒度设计（全局缰绳 + 局部生命周期驱逐）从入口到内存管理全路径保护缓存对齐，并提供明确的残差效用缓冲状态防止过度驱逐，这是已有工作未系统解决的。

**与多 Agent 系统的关系**：现有运行时调度已扩展到多 Agent 环境，利用去中心化角色感知路由、中心化经验缓存或跨上下文 KV 缓存通信拓扑最小化分布式 token 足迹。TokenPilot 的贡献聚焦于单 Agent 长期会话，但其设计原理可推广至多 Agent 上下文共享场景。

## 六、局限性与展望 / Limitations & Future Work

- **状态估计器误差**：在高度模糊或稀疏的交互模式下，基于模型的估计器 (Qwen3.5-35B-A3B) 可能误分类上下文段落，导致过早驱逐或保留无关内容。未来可探索更鲁棒的估计器设计，如引入贝叶斯不确定性量化。
- **超参数敏感**：频率阈值  和批处理大小  需要针对不同部署环境和任务分布进行调整。虽然  在实验中表现最优，但通用性仍需验证。自动搜索最优超参数的方法（如贝叶斯优化）可增强实用性。
- **依赖后端前缀缓存支持**：前缀稳定化组件依赖于 LLM 推理后端对 prefix caching 的实现。对于缺乏此功能的提供商（如某些本地推理引擎），缓存稳定化带来的收益将受限。可考虑结合 token 级缓存（如 radix attention）进行适配。
- **对任务流类型的敏感性**：连续模式评估将同类别任务分组（模拟领域特定工作流）。在高度异质的混合类别任务流中，由于工具模式持续变化，前缀重用率自然会降低。未来应研究跨任务前缀共享策略或动态重新映射方法。
- **成本计算通用性**：当前成本降低依赖于特定云 API 定价模型（折扣因子 ）。在不同定价策略下实际节省可能变化。可探索以 cache miss 为核心指标，减少对绝对货币值的依赖。
- **恢复工具带来的额外开销**：虽然恢复工具有效避免了补偿性重试，但在极端高频环境中可能引入少量延迟。未来可设计预测式预取机制，在估计到需要时才触发恢复。

## 七、总结 / Conclusion

TokenPilot 提出了一个双粒度上下文管理框架，解决了 LLM Agent 长期运行中文本稀疏性 vs. 提示缓存连续性的核心矛盾。全局模块通过摄入感知压缩稳定前缀、减少环境噪声；局部模块通过生命周期感知驱逐保守地管理历史窗口。在 PinchBench 和 Claw-Eval 上的实验验证了其成本降低 56%–87% 同时保持竞争性能的有效性。消融研究证明了两个模块的协同作用以及残差效用估计、恢复工具、前缀稳定化等关键设计的重要性。TokenPilot 已集成至 LightMem2 开源框架，为 LLM Agent 的实用部署提供了缓存高效的上下文管理方案。未来工作将聚焦于异构任务流、多 Agent 共享上下文以及自动超参数调优，进一步拓展其适用范围。

**原文摘要:** As LLM agents are deployed in long-horizon sessions, context accumulation drives up inference costs. Existing approaches utilize text pruning or dynamic memory eviction to minimize token footprints; however, their unconstrained sequence mutations alter layouts, introducing prefix mismatches and cache invalidation. This reveals a critical trade-off between text sparsity and prompt cache continuity. To address this, we present TokenPilot, a dual-granularity context management framework. Globally, Ingestion-Aware Compaction acts as a framework harness to stabilize prompt prefixes and eliminate open-world environmental noise at the ingestion gate. Locally, Lifecycle-Aware Eviction monitors the ongoing residual utility of context segments, enforcing a conservative batch-turn schedule to offload content segments only when task relevance expires. Experiments on PinchBench and Claw-Eval under both isolated and continuous modes demonstrate that TokenPilot reduces costs by 61% and 56% in isolated mode, and 61% and 87% in continuous mode, while maintaining competitive performance compared to prior systems. TokenPilot has been integrated into LightMem2 at https://github.com/zjunlp/LightMem2.

**PDF链接:** https://arxiv.org/pdf/2606.17016v1
