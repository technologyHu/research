# 调研类型路由

类型回答“怎样分析”，模式回答“研究一个还是比较多个”。对象的资料形式与研究目标共同决定类型：产品附带论文不等于用户要论文精读。

先判断是否需要调研流程：尚无 research 执行上下文且仅需函数解释、源码导览或调用链追踪时，直接使用 [code-understanding](../../code-understanding/SKILL.md)；用户要求完整技术调研、系统比较或已有 research 任务时，再按下表选择研究类型。生成一份代码导览文档本身不要求新建 research 任务。

| type | 目标 | 类型技能 |
| --- | --- | --- |
| `paper` | 理解或比较论文的问题、方法与实验证据 | [research-paper](../../research-paper/SKILL.md) |
| `open-source` | 分析公开项目的架构、源码和工程机制 | [research-open-source](../../research-open-source/SKILL.md) |
| `product` | 理解产品能力、使用流程、公开机制与约束 | [research-product](../../research-product/SKILL.md) |
| `benchmark` | 理解评测任务、数据、指标、协议及可比性 | [research-benchmark](../../research-benchmark/SKILL.md) |
| `topic` | 建立技术方向的分类、路线、演进与综合判断 | [research-topic](../../research-topic/SKILL.md) |

## 决策方法

- 给定单篇论文并要求方法／实验调研：paper。围绕公开项目开展架构／源码与工程机制调研：open-source。
- 对闭源产品开展分析：product；公开的集成包可作为源码证据，不能据此宣称掌握服务端实现。
- 同一个开源项目也可能采用 product 视角，取决于用户希望回答的问题。
- 混合类型比较：outline 使用 topic 统筹，各 item 单独指定 type；共同字段只用于可比较的部分。
- 某技术方向中的文献是来源，只有需要单独深查与比较时才成为 items；不要给每一条参考链接都启动一份报告。
- 无需澄清的小范围类型边界可说明假设后执行；目标差异会显著改变产出时再询问。

## 模式与深度

- `single`：一个明确的分析对象；技术专题本身也可作为一个对象。
- `comparison`：至少两个对象，保留同一比较目标与可比口径。
- `brief`：目标、核心机制、证据与边界；`standard`：主要维度；`detailed`：进一步展开关键实现、实验或协议。深度不是必须填满全部模板章节。
