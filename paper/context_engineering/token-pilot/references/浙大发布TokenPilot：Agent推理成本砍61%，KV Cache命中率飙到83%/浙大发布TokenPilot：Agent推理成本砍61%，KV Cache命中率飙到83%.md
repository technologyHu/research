# 浙大发布TokenPilot：Agent推理成本砍61%，KV Cache命中率飙到83%

**一句话讲清楚👉🏻** 浙大 TokenPilot 抓了一个常被忽视的矛盾： Agent 上下文剪短了， KV Cache 前缀却对不上，账单反而更贵。做法是在消息入口稳住前缀、按任务生命周期再驱逐旧段——Claw-Eval 长会话费用从 81.52 美元压到 10.58 美元，精度只掉 2.6 分。

![image](https://mmbiz.qpic.cn/sz_mmbiz_png/6lygMduFLGQWEnBKFQDWW1mn90jJ4oJe4CpHcC0EAuoPeFib3ic8SlJFtNib1Ig9dibDIhnz0XXPia2U7zv7DK4tbrTaDCAFu6DrZQvs0keWOk4w/640?wx_fmt=png&from=appmsg)

- 论文标题：TokenPilot: Cache-Efficient Context Management for LLM Agents
- 论文链接：https://arxiv.org/abs/2606.17016
- Github 链接：https://github.com/zjunlp/LightMem

## 长会话 Agent 的隐形账单

大模型已经从「聊天助手」演进到能调度工具、读写文件、跨应用编排的 **stateful execution controller**。 OpenClaw 、 Claude Code 这类系统里， Agent 一轮接一轮地调用 API 、写日志、抓网页，**上下文像滚雪球一样堆高**——每一轮推理都要为越来越长的 prompt 买单。

社区的主流解法很直接：剪枝低价值 token 、折叠中间推理、把历史轨迹 offload 到外部存储。**文本层面的确变短了**，但背后有个常被忽略的硬件机制：**Prompt Caching**。

商用 API （ OpenAI 、 Anthropic 等）对「前缀完全一致」的 prompt 片段按折扣价计费（ cache read ），只有前缀变了才触发全价 pre-fill （ cache miss ）。传统上下文管理在截断、压缩、换页时**不断改写序列布局**，前缀对不上， KV Cache 大面积失效——省下来的 token 费，抵不过 cache miss 的惩罚。

![image](https://mmbiz.qpic.cn/sz_mmbiz_png/6lygMduFLGTZVbMyhhZxc4DbtZJhKWuibBYyD7MlmFydcrQj2CC8QWo9NF9T7GjwicGlxZIR3gp2qjAZ4Tqnut2Hhh4TPfhPib3Tiaicic2K4ibxTE/640?from=appmsg)

原始 Agent 循环保持连续布局以累积 cache hit ；传统管理系统截断/压缩会突变输入边界，触发严重 KV cache miss 。

论文用 Figure 1 把矛盾画得很清楚：左边 Original Agent Loop 每轮前缀稳定，绿色 cache hit 一路叠加；右边 Prior Management System 在 Turn N 做 truncation/compaction ， Part 1/2/3 边界被打乱，后续轮次全是红色 cache miss 。**文本稀疏度和 prompt cache 连续性之间存在硬权衡**——TokenPilot 就是要同时优化两边。

## TokenPilot 的双层设计

TokenPilot 是一个 **dual-granularity**（双粒度）上下文管理框架，论文称已合入同团队 LightMem2 ；当前可访问的前代开源项目为 LightMem （链接见文首论文信息）。

![image](https://mmbiz.qpic.cn/mmbiz_png/6lygMduFLGSYcUqKg8z9ENOWE0VtRwgYFbGlcgDydLBUQBqqm0Y19eSBKjPCBMVcJUGJGweAMDcymxn8QALbCmNX6DibSib5siaAd1fHl8ia1lQ/640?from=appmsg)

TokenPilot 系统架构：全局 Ingestion-Aware Compaction + 局部 Lifecycle-Aware Eviction 。

### 优化目标：效用除以服务成本

优化目标用白话讲：**核心是在保住任务所需信息的前提下，让每条保留消息的花费尽量走 cache read**。商用 API 里 cache hit 的 token 很便宜（系数 ）， cache miss 要全价 pre-fill——所以要让更多 token 走折扣通道，而不是反复触发全价 pre-fill 。

形式化写法：给定原始历史 ，管理框架  产出优化后的运行时上下文 ，最大化上下文效用与维护成本的比值：

其中  估计消息  对后续 Agent 行为的边际贡献；服务成本  由后端 KV prompt-caching 机制决定：

是 cache read 的折扣系数， 和  分别是从缓存读取和全价 pre-fill 的 token 数，且满足长度约束 。

### 全局层： Ingestion-Aware Compaction

这一层在**摄入边界** 做确定性整理，在消息进入上下文之前就规范布局，避免事后压缩已有 cache 。

消息空间被分成两类： - ：**内部意图消息**——任务 prompt 、 thinking trace 、 tool call 、最终回复，天然高信息密度 - ：**开放世界环境反馈**——工具返回的原始 HTML 、日志、 JSON ，结构噪音多

对每条入站消息 ，边际效用密度定义为：

是环境反馈的基础效用密度；𝟙 是摄入门——当内容哈希  的访问频率  超过阈值  时，门打开，恢复完整内容交付。

**Prefix Stabilization （前缀稳定）** 是全局层最关键的操作。跨任务 KV cache 复用常被运行时易变字段打断： Agent ID 、工作目录、时间戳、工具 schema 每次变一点，物理前缀就对不上。 TokenPilot 还会把 **tool definitions 下移到序列后部**，让 system prompt 前缀尽可能长且稳定。规范化算子  把易变字段替换成静态占位符：

从第一轮起就保证 **byte-identical prompt prefix**，后续任务直接继承 warm start ，避免全价 pre-fill 。

**Observation Reduction （观测压缩）** 针对  的环境消息，在摄入门做确定性缩减：

是存入工作记忆的紧凑预览； 是按内容哈希索引的外部 artifact 注册表。如果 Agent 执行时发现压缩版缺关键信号，可调用轻量 recovery tool 按需拉回完整 payload ，并关闭该路径的后续截断——**压缩是默认策略，完整内容是按需回退**。

### 局部层： Lifecycle-Aware Eviction

局部层按**段（ segment ）** 跟踪上下文的生命周期，状态  维护在框架注册表  中。

段  的边际效用：

𝟙是段的**残余效用**——任务做完了，只要后续交互还可能引用这段内容，就不立刻删，保住物理 cache slot 。

状态转移由在线估计器  驱动，按 batch size  的保守节奏批量触发，避免每轮都跑一遍校验：

是子任务完成的显式证据， 是残余效用信号。门控流水线：

段进入 evictable 后，框架做一次结构 purge ，构造优化窗口：

估计器  用 **Qwen3.5-35B-A3B** 做 zero-shot 校验：每  轮把压缩后的历史视图  和当前注册表  喂进去，输出各段的完成证据  和残余效用 ，驱动状态转移。连续 PinchBench 流上总花费不到 **$0.03**。

## 实验设置

### Benchmark 与评测模式

在两个 Agent benchmark 上评测： - **PinchBench**：覆盖生产力、研究、写作、编码、分析、 CSV/日志/会议分析、记忆、技能、集成等 11 类任务 - **Claw-Eval**：覆盖工作流、运维、金融、办公 QA 、通信、终端、多模态等场景

每种 benchmark 分两种模式： - **Isolated**：每个任务边界重置上下文 - **Continuous**：历史贯穿整个任务序列，更贴近真实长会话部署

所有方法的 Agent backbone 统一为 **GPT-5.4-mini**。 cache hit/miss token 数直接从提供商 API 元数据读取，不做客户端估算。对比基线包括文本压缩（ LLMLingua-2 、 SelectiveContext 、 Keep-Last-N ）和动态分页/摘要（ Summary 、 LCM 、 Pichay 、 MemoBrain 、 AgentSwing 、 MemOS ）。

## 主实验结果

### Isolated 模式：最便宜且精度能打

| Benchmark | 本文成本 | 最强基线成本 | 任务精度 |
| --- | --- | --- | --- |
| PinchBench | **3.36 (MemoBrain) | **81.0** |  |
| Claw-Eval | **2.54 (AgentSwing) | 63.1 |  |

PinchBench 上 TokenPilot 总推理费用 **，低于所有基线；精度，与（）和（）同档。相对的8.31**，isolated 模式费用降 61%**。 Claw-Eval 上**同样最低，相对的5.16 **降 56%**。

文本压缩类方法（ LLMLingua-2 、 SelectiveContext ）确实降了 token 数，但激进语义剪枝拖累任务表现——PinchBench Overall 掉到 72–79 区间。动态框架保精度，却管不住 prompt cache ， cache miss 惩罚把账单拉回去。

### Continuous 模式：长会话才是分水岭

Continuous 模式下历史无限累积，差距被放大几个数量级：

| Benchmark | TokenPilot | Vanilla | 降幅 |
| --- | --- | --- | --- |
| PinchBench 费用 | **7.24 | **61%** |  |
| PinchBench 精度 | **81.3** | 79.2 | +2.1 |
| Claw-Eval 费用 | **81.52** | **87%** |  |
| Claw-Eval 精度 | 60.8 | 63.4 | -2.6 |

PinchBench continuous ： TokenPilot Overall **81.3**（全场最高），费用 **2.79 美元**， cache miss 仅 **1.549M** tokens 。 Claw-Eval continuous ： Vanilla 费用飙到 **81.52 美元**， TokenPilot 压到 **10.58 美元**——**87% 的费用削减**，在长会话部署场景下意义极大。

![image](https://mmbiz.qpic.cn/sz_mmbiz_png/6lygMduFLGQRx8sTJpzfm94RdicFOZDqoT6dW8r9ItvuFOHf9kaHNHJUGoMybsqXIibxC1yiaK7CibztGFJJrFl8lZ8QcagpuCkpVxpRdQr0EwY/640?from=appmsg)

连续 Meeting Analysis 会话中，每轮调用的上下文 token 体积变化——TokenPilot 周期性下压峰值。

## 消融实验：两层各贡献多少

PinchBench continuous 上的渐进消融（ Table 3 ）：

| 配置 | Overall | 费用 | Cache Hit (M) | Cache Miss (M) |
| --- | --- | --- | --- | --- |
| Vanilla | 79.2 | $7.24 | 25.015 | 5.943 |
| + Global （摄入门） | 79.9 | $4.22 | 26.716 | 1.589 |
| + Local （生命周期驱逐） | **81.3** | **$2.79** | 8.551 | 1.549 |

**全局层单独贡献**：费用从 7.24 美元降至 4.22 美元（**-42%**）， cache miss 从 5.943M → 1.589M 。规则剪枝压低上下文峰值；前缀稳定把昂贵 pre-fill 转成 cache read 。

**加上局部层**：费用再降到 2.79 美元， cache read 从 26.716M → 8.551M （**-65%**），说明生命周期驱逐有效限制了活跃内存窗口。 Figure 3 的周期性下跌曲线印证： batch-turn 调度只在残余效用耗尽时才 offload 。

### 摄入门三组件拆解

| 配置 | Overall | 费用 | Cache Miss (M) |
| --- | --- | --- | --- |
| Vanilla | 80.47 | $8.31 | 8.753 |
| + Cache Stabilization | 80.81 | $4.35 | 2.818 |
| + Reduction Pass | 80.92 | **$2.87** | 1.493 |
| - Recovery Tool | 77.12 | $4.03 | 2.539 |

仅加稳定占位符，费用就从 8.31 美元砍到 4.35 美元；再加 reduction pass 到 **2.87 美元**。去掉 recovery tool 后精度掉到 77.12 、费用反弹到 4.03 美元——Agent 会反复重试工具调用，反而膨胀上下文。**按需回退是性能边界的关键保险**。

### 前缀稳定对 Cache Hit Rate 的影响

稳定占位符把首轮 cache read 从「冷启动」变成「暖启动」。宏观 cache hit rate ： - PinchBench ：**38.7% → 79.2%** - Claw-Eval ：**67.2% → 83.1%**

PinchBench 上不稳定主要来自目录路径、时间戳等通用易变字段； Claw-Eval 则是工具 schema 抖动更严重。占位符替换后，绝大多数任务首轮就能读到 6k–12k 的 warm-start cache 。

![image](https://mmbiz.qpic.cn/mmbiz_png/6lygMduFLGRma3qQmb3KEjUd035Y5nlWyJXQKDiaq2r7a0SribIAzcAs7In6S5Ckzel7mY9tCw96gePTBfR760CGJicvyJehuaOmKAkcbQeyvw/640?from=appmsg)

PinchBench 与 Claw-Eval 各任务 cache hit rate 对比（ Vanilla vs 稳定占位符）。

### 压缩收益： HTML 瘦身 + 执行输出截断

两套 reduction pass 针对不同噪音源： - **HTML Slimming**：剥掉 nav 、 script 、 style 等结构噪音。`oss_alternative_research` 单任务省 **115k** 字符 - **Exec Output Truncation**：截断冗长终端日志。`meeting_gov_recommendations` 省 **883k** 字符

在框架边界消掉的 token 不会在多轮窗口里累积——这是 compounding savings 的来源。

![image](https://mmbiz.qpic.cn/mmbiz_png/6lygMduFLGT3n3kYOsIhj49ibRakklFu1gnibh4LYjSVGQNiaE4RQ69C5HhEEnwicqUrx6dFM9tqqYuLmfrVhEWqhyiaicrWAXQKJIibbHB3T4OBZw/640?from=appmsg)

执行输出截断 pass 在各任务上的字符节省量（ Top tasks ）。

## 生命周期驱逐： Batch Size 怎么选

论文扫描了 turn batch size ：

■（关闭驱逐）：上下文窗口和等效费用都顶到峰值■（每轮驱逐）：过早截断破坏布局一致性， cache miss 反升■较大 ：前缀连续性更好， hit rate 更高■**经验最优**：在任务精度、内存缩减、 API 调用次数之间取得平衡

![image](https://mmbiz.qpic.cn/mmbiz_png/6lygMduFLGReKndgtONP0O5EfTElDKGmRD6OSfdWKGR2xLfiaaZ0sQVthwQib0tUnmhh5Xmia0QMzYUd8wED7M7ONG1F6hU447UJIriautHo1rU/640?from=appmsg)

Meeting Analysis 类别上不同 turn batch size 的 cache miss 、 cache read 、上下文窗口、等效输入 token 及 cache hit rate 。

### Case Study ：残余效用估计的价值

在 `transcript.md` 的四任务会话里，有残余效用估计的 TokenPilot 在任务完成后**保留上下文段**，后续任务直接访问相关文档片段；没有残余效用估计时，每个任务从头读文件，发出多次顺序 partial read 定位同一内容。

![image](https://mmbiz.qpic.cn/mmbiz_png/6lygMduFLGRaiaGIm2bFczPh0oatj7owXCAG1pruEgCneVPNjGlgBkIjDyMHVicqqspTIEVfAA3WawB4EURQw39Ov0ibI97I6RWcTqCSaPIAy8/640?from=appmsg)

四任务会话中的 tool call 模式对比： TokenPilot 保留已完成任务的上下文段，避免重复文件读取。

这个 case 很直观地说明：**盲目驱逐和永不驱逐都是错的**——关键是判断「这段历史对后续还有没有残余引用价值」。

## 工程视角：落地可以先做哪两步

Prompt Caching 已是商用 LLM API 的标配定价维度，但不少 Agent 框架仍只盯着「上下文窗口能塞多少 token 」，忽略了 **layout stability**（布局稳定性）。

如果你正在搭长会话 Agent ，可以先试两件几乎零成本的事：**把 system prompt 里的时间戳、工作目录换成固定占位符**；**对 HTML/日志类工具返回做摄入时压缩，并保留 recovery 回退路径**。论文里单做前缀稳定就能把 PinchBench macro cache hit rate 从 38.7% 拉到 79.2%。 Recovery tool 更是压缩策略的安全阀——去掉它精度掉 3+ 分， Agent 会反复重试工具调用把上下文撑爆。驱逐节奏上， 的 batch-turn 调度比逐轮 paging 更稳，避免频繁布局突变触发 cache miss 。

和 MemGPT 、 AgentSwing 这类「把历史 offload 到外部存储再按需召回」的方案比， TokenPilot 把治理前移到摄入门：先规范布局，再在序列层按残余效用保守驱逐。适合工具调用密集、环境反馈噪音大、且 backbone 支持 prompt caching 的部署场景；如果任务之间几乎无共享前缀，收益会打折扣。

## 局限与未来方向

论文没回避短板。 Claw-Eval 连续模式下精度 60.8 ，比不做任何管理的 Vanilla （ 63.4 ）还低 2.6 分——激进驱逐在长链路金融/运维任务里可能丢掉关键上下文。占位符策略还假设工具 schema 相对稳定； Agent 如果经常热更新工具定义，需要额外做版本化占位符，否则前缀稳定会失效。估计器  也依赖 Qwen3.5-35B-A3B 的 zero-shot 判断能力，换更弱的模型可能影响残余效用估计的准确度。

后续方向包括与模型侧 prefix caching 更深耦合、跨 Agent 实例 cache 共享，以及在 continuous 模式下进一步压低精度损失。即便如此， GPT-5.4-mini backbone 上 PinchBench continuous 费用从 7.24 美元降至 2.79 美元、 Claw-Eval continuous 从 81.52 美元降至 10.58 美元，已经足够说明 cache-aware 上下文治理在长会话部署里的经济价值。

⭐️关注我，实时跟进 AI 最新进展⭐️
