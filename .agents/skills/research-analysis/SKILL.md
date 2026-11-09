---
name: research-analysis
description: 基于已有调研输出，围绕某一主题或问题开展综合分析，形成模式、关联、机制解释、争议或研究机会等分析洞察。适用于主题综合、问题解释及应用启示，贡献者观点可选；不替代基础对象调研，单篇 survey 仍归 paper。
---

# 分析洞察

交付围绕某一主题或问题的分析／洞察报告：从已有调研中归纳发现、解释联系和差异，说明这些认识的依据、意义与边界。内部类型为 `analysis`，目录为 `analysis-reports/<主题名>[__<专题>]__<时间>/report.md`，兼容读取旧报告。公共规则按需读取 [research-common](../research-common/SKILL.md)，不调用其他顶层入口。

## 进入与范围

用户只要求登记主题或子主题时，按 [主题注册表](../research-common/references/theme-registry.md) 更新 `themes.yaml`，校验后即可交付。分析计划按共用的 [纳入条件](../research-common/references/theme-planning.md#计划纳入条件) 维护。仅有主题名称时，先明确具体分析目标或要维护的已有报告。

- 先读取项目根的 themes.yaml，按 [统一主题词表](../research-common/references/theme-registry.md) 选择稳定主题 ID，新主题先登记。主题可有多级，主题各级、主题与专题之间都用 `__` 连接，例如 agent__memory__architecture__mechanisms__tradeoffs；每级 slug 内的单词仍用 `-`。analysis-reports 中只创建一层带时间后缀的报告目录，分类记录保留规范主题 ID。专题标识与主题相同时不重复拼接；旧名称原地维护，修订不自动转换。

- 直接接收分析目标与已有成果，沿用已明确目标、来源和任务，不重复规划；通过 [research-report](../research-report/SKILL.md) 成稿与校验。
- 持续主题、分阶段分析或明确要求计划时，按共用的 [计划规则](../research-common/references/theme-planning.md) 和 [两表模板](../research-common/references/theme-plan-template.md) 维护 `analysis-reports/<主题名>.plan.md`，新计划主题名按层级用 `__` 连接，已有计划原地复用。核心问题表填写用户已确认的共同问题。分析专题及本轮问题写入任务行，按 analysis 口径评估后排序。输入报告作为依据，基础补查链接到 research-reports 的对应任务。只要计划时保存后结束。
- 按共用的 [任务管理](../research-common/references/task-management.md) 为 `--type analysis` 创建或恢复任务；工具自动选择 analysis-reports。专题 target 可用 `__` 分隔多个命名片段，片段内用 `-` 连接单词，数量不固定；旧名称原样维护，详见 [目录命名](../research-common/references/delivery-policy.md#目录命名)。单主题 brief 可用 light，其余按复杂度用 full；结论更新先按 [局部更新](../research-common/references/report-updates.md) 登记范围。两边同名主题的计划分别维护各自工作，相互引用，不复制为两份同范围计划。
- 分析对象是一个主题、问题或需要比较的分析对象，输入报告是依据。一个主题可以有多个分析维度；采用多份、不同类型报告不自动增加 items 或改成 comparison，也不恢复 topic 类型。
- 按 [成果核对](../research-common/references/routing.md#已有成果核对与复用) 定位相关报告，明确本轮关注点、样本选择、版本／时间和覆盖边界。贡献者思考是可选输入，没有预设观点也可以开展明确标为“本次分析”的综合与推导。
- 基础事实有缺口时按 [补查规则](../research-common/references/routing.md#执行交接与基础补查) 界定问题、实际对象类型和接受条件；授权允许补查时直接使用 [research-deep](../research-deep/SKILL.md) 取得必要证据，返回当前分析。限定只用已有成果时保留缺口，不扩成全量对象调研或外部搜索。

## 按目标选择分析方式

按问题组合下列方式，不要求每篇覆盖全部形式。

| 本轮目标 | 分析重点 |
| --- | --- |
| 主题综合 | 对照已有成果，归纳共同特征、差异与主要认识 |
| 模式与关联 | 识别反复出现的设计、约束或联系，说明样本与反例 |
| 机制与争议解释 | 解释差异为何出现，检查版本、场景、定义和替代解释 |
| 演进与研究机会 | 对照有时间依据的变化，提出有条件的趋势、缺口与可检验问题 |
| 应用启示或方案取舍 | 按需要讨论适用场景、代价、建议；选型时再明确硬约束、偏好与优先级 |

## 从成果到分析洞察

1. 明确主题／问题和本轮想解释或发现什么。把范围、时间、样本选择及会影响结论的假设写入 goal／time_range 或字段描述，notes.md 保留输入原文与归属；不为一般主题分析强求选型标准或个人观点。
2. 阅读采用的报告，登记实际版本／日期、相关主张、散列、完成度和限制；决定性的原始引用按实际影响回查。区分已有事实、来源作者推断、贡献者观点与本次归纳，不把多次转述算作独立证据。
3. 通过对照、归纳、机制解释或证据对话形成分析，串起“依据 → 分析过程／假设 → 核心发现 → 意义 → 适用边界”。洞察应解释发现了什么联系、为何成立及对问题的意义；证据仅支持有限认识时如实表达，不为凑新颖结论编造模式或共识。
4. 检查反例、替代解释和不可比条件。小样本共同现象不自动代表全领域趋势，相关性不自动证明因果，未知项不当作差异。按 [评价口径](../research-common/references/analysis-criteria.md) 检查依据可靠性、分析与解释价值、问题相关性和洞察稳健性。
5. 对重要主张说明证据质量、关键假设和适用边界。趋势类说明可能失效的条件，取舍类说明何时建议改变；不为每篇报告强求排名、硬约束、置信分数或行动建议。
6. 新来源或范围变化时只复核依赖它们的分析与发现，保留原日期和未复核范围；不能只更新笔记、散列或措辞来接受变化。

## 记录、引用与交付

按 [报告结构](references/report-template.md) 分开任务输入、来源与证据字段。新任务优先用 insight 记录核心分析发现；judgment 仍可用于方案判断，旧字段与历史报告不改名、不迁移。只将需要核查／论证的主张设为字段，不把每个章节或个人偏好都变成证据字段。

直接证据支持的事实可为 confirmed；归纳、解释、洞察或建议通常为 inferred，reason 写清分析过程、假设与边界，evidence 指向实际依据；无法回答的问题为 unknown。分析完成度不代表洞察已经实测或具有高置信程度。

本地已有报告沿用 repo: 登记、实际版本／日期与 sha256，并在正文使用相对链接和章节定位，详见 [来源配置](../research-common/references/research-config.md#分析洞察引用已有报告)。repo: 仅允许项目内持久报告，不指向计划、临时文件、技能或自身输出；外部原始 HTTP(S) 来源仍按公共规则引用。保留实际阅读状态，来源变化后先复核再接受新散列。

典型用法见 [主题综合与洞察示例](references/topic-insights-example.md)；选型类见 [记忆部署取舍示例](references/worked-example.md)。成稿前使用 [检查清单](references/checklist.md)，保存与清理只遵循 [交付规范](../research-common/references/delivery-policy.md)。同主题只维护一份当前分析计划，不另存快照；本技能不自动提交、推送或发布，配图沿用项目图像能力约束。

需要配图时可直接使用 [draw-diagram](../draw-diagram/SKILL.md)，按共用写作规则核对证据、来源与图像能力条件。本技能在分析报告交付与计划回写后完成，不执行 Git 提交、推送或发布。
