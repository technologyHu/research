# TokenPilot：浙大团队让AI Agent省钱87%的秘密——缓存感知上下文管理新框架

# ![image](https://mmbiz.qpic.cn/mmbiz_jpg/BeqSTPIvvD9v2o9kZfZS4OtpjhcquicrGoS96RbBaI2KHcGkjQLe8RSGL61UIaN7XEdFXZpOvkBuUMVgAae5JH3fPQiazCAm9o1MDrXg947J0/640?wx_fmt=jpeg)

> 你的 AI Agent 正在变得越来越"聪明"——它能调用工具、管理文件、执行跨应用工作流。但有一个隐形的成本杀手在悄悄吞噬你的预算：**上下文累积**。
> 每次对话，Agent 都要把之前所有的操作记录塞进提示词里。几十轮对话后，上下文可能膨胀到几万 Token。这不仅是"文本太长"的问题，而是**每次调用都要重新计算这些 Token 的 KV 缓存**，直接推高推理成本。
> 浙大团队最近开源的 **TokenPilot** 框架，解决了这个难题。在真实评测中，它让 Agent 的推理成本降低了 **61%-87%**，同时保持了任务完成准确率。论文已被 arXiv 收录，代码已集成到 LightMem2 中开源。

## 一、问题：为什么你的 AI Agent 越来越贵？

想象你和 AI Agent 的一段对话：

- 第一轮：你让它查天气 → Agent 调用天气 API，返回结果
- 第二轮：你让它订机票 → Agent 调用订票工具，返回结果
- 第三轮：你让它写报告 → Agent 调用文档工具，返回结果

到第三轮时，Agent 的提示词里包含了：**第一轮的天气查询过程 + 第二轮的订票过程 + 你自己的指令 + 当前任务**。这就像是每轮对话都把所有历史记录复印一份塞进新的信封里。

这就是 **"上下文累积"（context accumulation）** 问题。

### 为什么上下文累积这么贵？

大模型推理时，每个 Token 都需要计算一个 **KV 缓存（Key-Value Cache）**。这是模型理解上下文的基础数据结构。当上下文很长时：

- **显存占用**：KV 缓存可能占用数 GB 显存
- **计算成本**：每轮对话都要重新计算新 Token 的 KV 值
- **API 费用**：OpenAI、Anthropic 等按 Token 计费，长上下文 = 高账单

更关键的是，现在的 API 提供商（如 OpenAI、Anthropic）推出了 **Prompt Caching** 机制：如果新请求的前缀和之前缓存的一致，这部分 Token 可以享受 **折扣价**（通常是正常价格的 10%-50%）。但如果你的上下文管理不当，每次请求的"前缀"都在变，缓存就**失效**了，所有 Token 都要按全价计算。

### 现有方法的困境

目前的研究主要从"内容压缩"角度解决：

- **文本压缩**：LLMLingua-2、SelectiveContext 等，压缩低价值 Token
- **动态分页**：LCM、Pichay 等，把历史记录分页存储，按需加载
- **摘要替换**：Summary 方法，把长历史变成短摘要

这些方法确实减少了 Token 数量，但有一个致命问题：**它们在压缩时会改变文本序列的布局，导致前缀不匹配，缓存失效**。

打个比方：

- 原始序列是 `[A, B, C, D, E]`，缓存了 `[A, B, C]`
- 压缩后变成 `[A, B, D, E]`，前缀 `[A, B, C]` 的缓存就用不上了
- 结果：虽然 Token 少了，但缓存命中率暴跌，实际成本反而更高

这就是论文指出的 **"文本稀疏性与提示缓存连续性之间的关键权衡"**。

## 二、TokenPilot：双粒度上下文管理框架

浙大团队（Zhejiang University）联合电子科大、西安电子科大、HomologyAI 提出的 **TokenPilot**，是一个**双粒度（dual-granularity）** 的上下文管理框架。

| 层级 | 机制 | 作用 |
| --- | --- | --- |
| **全局层** | 摄入感知压缩（Ingestion-Aware Compaction） | 在"入口"处稳定前缀，消除环境噪声 |
| **局部层** | 生命周期感知淘汰（Lifecycle-Aware Eviction） | 监控轨迹的残余效用，保守批量淘汰 |

### 全局层：Ingestion-Aware Compaction（摄入感知压缩）

传统的压缩方法是**事后处理**——等上下文累积到一定长度后，再回头压缩。TokenPilot 的做法是**事前预防**——在数据进入系统的那一刻就优化布局。

它把消息分为两类：

- **内部意图消息（Ωint）**：系统或模型自己生成的，包括任务提示、思考过程、工具调用、最终回复。这些消息**内在价值密度高**，保留。
- **开放世界环境反馈（Ωenv）**：外部工具返回的原始结果，比如网页 HTML、API 返回的 JSON。这些消息**结构杂乱、噪声多**，需要压缩。

具体怎么做？

**1. 冻结易变字段（Freeze Volatile Fields）**

Agent 的提示词里通常有一些每次都会变的字段：

```
`Agent ID: "example-agent-1"  ← 每次可能不同Working Directory: "/tmp/agent/1/..."  ← 每次可能不同Time: 2026-05-01 10:30:00  ← 每次都在变`
```

这些字段虽然只是"元信息"，但会让整个前缀不稳定。TokenPilot 用**占位符**替换它们：

```
`Agent ID: <AGENT_ID>Working Directory: <WORKDIR>Time: <TIMESTAMP>`
```

这样，从第一轮开始，提示词的前缀就是**字节级一致**的，缓存可以持续命中。

**2. 工具定义后移（Shift Tool Definitions Downstream）**

工具定义（Tool Description）通常很长，放在提示词前面。TokenPilot 把它移到**后面**，确保前缀主要是稳定的系统提示和任务指令，而不是每次可能变化的长工具定义。

**3. 环境反馈结构化压缩（Compact Observation Content）**

对于外部工具返回的原始 HTML、JSON，TokenPilot 把它压缩成结构化摘要：

```
`原始 HTML（几百行）:<html>  <head>...</head>  <body>    <nav>...</nav>    <div class="content">...</div>  </body></html>压缩后（几行）:{  "url": "example.com",  "title": "Example Page",  "main_text": "...",  "tables": [...],  "links": [...],  "ts": "2026-05-01",  "hash": "h(m)"}`
```

压缩时保留了关键信息（主文本、表格、链接），去掉了噪声（样式、脚本、嵌套标签）。

### 局部层：Lifecycle-Aware Eviction（生命周期感知淘汰）

全局层解决了"入口"问题，但对话进行多轮后，上下文还是会膨胀。局部层负责**什么时候该删除哪些内容**。

核心洞察：**不是所有历史都同等重要**。有些任务已经"完成了"，相关的历史就可以淘汰；有些任务还在"进行中"，历史必须保留。

TokenPilot 把上下文分成**片段（segments）**，每个片段对应一个任务轨迹。然后监控每个片段的**残余效用（residual utility）**：

```
`状态流转：Active（活跃） → Completed（完成） → Evictable（可淘汰）- Active：当前任务还在进行，必须保留- Completed：任务已完成，但可能还有参考价值的证据- Evictable：任务完全结束，且残余效用为 0，可以安全淘汰`
```

关键设计：**保守淘汰（conservative eviction）**

TokenPilot 不会频繁淘汰，而是采用**批量轮次调度（batch-turn schedule）**——每 N 轮对话执行一次淘汰，一次性把所有"可淘汰"的片段清掉。这样避免了"每轮都变"导致的前缀不稳定。

残余效用怎么算？论文用 **Qwen3.5-35B-A3B** 作为轻量级零样本验证器（Estimator），评估每个片段对后续任务的价值。整个评估过程的成本极低——在 PinchBench 连续模式下，总开销不到 **$0.03**。

## 三、实验结果：省钱 61%-87%，性能不打折

论文在 **PinchBench** 和 **Claw-Eval** 两个基准上做了评测，分别测试了**隔离模式**（每个任务独立，上下文重置）和**连续模式**（任务间上下文保留，更真实）。

### PinchBench 结果（Kilo Code 团队开发，50+ 模型已测试）

| 方法 | 隔离模式成本 | 连续模式成本 | 准确率 |
| --- | --- | --- | --- |
| Vanilla（原始） | $5.16 | $81.52 | 64.5% |
| LLMLingua-2 | $4.44 | $82.91 | 61.9% |
| Summary | $3.16 | — | 62.0% |
| MemoBrain | $6.69 | — | 58.0% |
| **TokenPilot** | **$3.22** | **$4.87** | **63.1%** |

| 对比 | 隔离模式 | 连续模式 |
| --- | --- | --- |
| 相比 Vanilla | **省钱 37.6%** | **省钱 94.0%** |
| 相比 MemoBrain | **省钱 51.9%** | — |
| 相比 LLMLingua-2 | **省钱 27.5%** | **省钱 94.1%** |

**连续模式下的成本从 降到4.87，降低了 94%，相当于只花了原来的 1/17。**

### Claw-Eval 结果（300 真实任务，端到端评测）

| 方法 | 隔离模式成本 | 连续模式成本 | 准确率 |
| --- | --- | --- | --- |
| Vanilla | $5.16 | $81.52 | 63.4% |
| LLMLingua-2 | $4.44 | $82.91 | 59.0% |
| Summary | $3.16 | — | 61.6% |
| **TokenPilot** | **$2.27** | **$10.41** | **63.1%** |

| 对比 | 隔离模式 | 连续模式 |
| --- | --- | --- |
| 相比 Vanilla | **省钱 56.0%** | **省钱 87.2%** |
| 相比 Summary | **省钱 28.2%** | — |
| 相比 LLMLingua-2 | **省钱 48.9%** | **省钱 87.5%** |

### 关键发现

- **连续模式比隔离模式更省钱**：在真实场景中，Agent 的上下文是连续累积的，TokenPilot 的缓存命中率优势被放大
- **Cache Read 占比大幅提升**：TokenPilot 的 Cache Read（缓存命中）Token 数量显著高于其他方法，说明前缀稳定策略有效
- **Cache Miss 大幅降低**：TokenPilot 的 Cache Miss（全价计算）Token 数量远低于其他方法，这是省钱的核心
- **准确率不降反升**：在 PinchBench 上，TokenPilot 的准确率（63.1%）甚至高于 Vanilla（64.5% 到 63.1%，虽然略低但在误差范围内，且成本大幅降低）

### 为什么其他方法省钱效果差？

论文分析了其他方法的问题：

- **LLMLingua-2**：虽然压缩了文本，但改变了序列布局，前缀缓存频繁失效，Cache Miss 反而增加（37.2M vs TokenPilot 的 1.15M）
- **Summary**：摘要替换丢失了细节信息，导致 Agent 在复杂任务上准确率下降
- **MemoBrain**：虽然压缩率高，但 Cache Miss 高达 5.1M，实际成本反而更高
- **Pichay**：压缩率太高，丢失了太多环境信息，准确率从 64.5% 降到 59.3%

## 四、工程实现：已集成到 LightMem2

TokenPilot 不是停留在论文里的概念，而是已经**工程化**并集成到 **LightMem2** 中。

### LightMem 是什么？

LightMem 是浙大团队（zjunlp）开发的**轻量级记忆增强生成框架**，已获 **ICLR 2026** 接收。GitHub 上已获得大量关注，支持：

- 云 API（OpenAI、DeepSeek）和本地模型（Ollama、vLLM）
- 多种压缩器（LLMLingua-2、Entropy Compress）
- 多种检索器（Qdrant、FAISS、BM25）
- MCP 协议支持

### TokenPilot 集成后的 LightMem2

TokenPilot 作为 LightMem2 的上下文管理模块，提供：

- **双粒度管理**：全局摄入压缩 + 局部生命周期淘汰
- **缓存感知**：所有优化都以"不破坏前缀连续性"为前提
- **低开销**：Estimator 用 Qwen3.5-35B-A3B，单次评估成本 <$0.03
- **即插即用**：通过配置文件启用，无需修改现有代码

## 五、核心启示：为什么 TokenPilot 值得关注？

### 1. 它解决了"真问题"

Agent 应用落地时，成本是一个硬约束。一个每天处理 1000 次对话的 Agent：

- 用 Vanilla 方法：每天成本可能 $800+
- 用 TokenPilot：每天成本可能 $100+

**省下的钱 = 产品的可行性**。

### 2. 它的思路可以借鉴

即使你不直接用 TokenPilot，它的核心思路也值得学习：

- **冻结易变字段**：用占位符稳定前缀，提高缓存命中率
- **环境反馈结构化**：不要塞原始 HTML/JSON 给 Agent，先提取关键信息
- **保守淘汰**：不要频繁删内容，批量、低频地淘汰过期内容
- **残余效用评估**：用轻量级模型判断哪些历史还有价值

### 3. 它代表了 Agent 基础设施的进化方向

早期的 Agent 框架关注"能做什么"（工具调用、工作流编排）。现在的 Agent 框架关注"怎么做得更省"（上下文管理、缓存优化、成本控制）。TokenPilot 代表了**第二代 Agent 基础设施**的方向：不是让 Agent 更强大，而是让 Agent 更可持续。

## 六、快速上手

TokenPilot 已集成到 LightMem2，GitHub 地址：`https://github.com/zjunlp/LightMem2`

```
`# 克隆仓库git clone https://github.com/zjunlp/LightMem2.gitcd LightMem2# 安装依赖pip install -e .# 配置 TokenPilot 模块（在配置中启用）# 详见 LightMem2 文档`
```

论文地址：`https://arxiv.org/abs/2606.17016`

### 引用链接

[1]https://github.com/zjunlp/LightMem（TokenPilot: *https://github.com/zjunlp/LightMem%EF%BC%88TokenPilot*
