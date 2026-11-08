---
name: research-add-fields
description: 为主题计划或现有调研新增或细化问题与分析维度，指定适用对象、证据和验收要求，并定位需要补查的结果。用于补充问题、比较指标或章节关注点。
---

# Research Add Fields：补充维度

仅维护主题计划时，先按 [主题计划维护](../research/references/theme-planning.md) 定位长期 Markdown，新增或细化核心问题，更新对应任务、验收口径、覆盖缺口及修订记录；保存汇报后结束，不要求存在 fields 或 .tmp。已有完成项不能默认回答新问题；确需同步执行中的单次任务时，再按下列步骤补查。

本次问题或验收实质改变时，按主题计划的范围对照规则保留原 scope 快照，定位受影响字段并同步配置，再为新执行口径新增快照；不能只改当前计划或换新快照，就把旧证据视为已复核。无关问题的新增不使本次范围自动过期。

新问题、验收或版本影响依赖条件时，按 [依赖规则](../research/references/theme-planning.md#依赖的满足失效与复核) 更新所需片段、条件及实际影响；旧“满足”不自动沿用。保留原接受记录，复核真正使用变化成果的直接下游，产出也改变时再逐层检查，不把无关任务整体重置。

1. 按 [任务管理](../research/references/task-management.md) list/show 定位任务，使用返回的 outline、fields 实际路径，不按固定扩展名另建配置。尚未交付的调研原地扩展；已有报告需更新且旧 full 证据仍有效时先 derive 为新任务，再按 [局部更新流程](../research/references/report-updates.md) 保存基线。light 先 promote 并核对逐字段证据；结合类型模板检查已有问题。
2. 将用户要求转成可回答的问题，先核对已有成果对新增问题的覆盖；指标写明定义、单位、时间和条件。去除语义重复项，保留稳定字段 id，不因改中文标题而改变 id。analysis 的字段描述需分析的模式、联系、解释、机会或取舍问题；来源报告是依据，不因新增字段将其改为论文／产品等 items。
3. 用 `applies_to` 限定类型，必要时用 `item_ids` 限定对象。按研究目标确定 `core`，默认 true，附加资料可设为 false。对用户明确提出的维度直接更新；只有真正存在不同研究方向时再澄清，不为例行追加反复确认。
4. 更新实际 fields 文件与 outline revision，标记新增或语义发生变化的字段及受影响对象需要补查。其他证据继续复用，保留来源原访问日期；不能把旧结果无条件标为全新或全部作废。原任务已清理时，从报告与来源重建需要的证据。
   若关联主题计划，按 [主题计划维护](../research/references/theme-planning.md) 同步核心问题、任务映射、覆盖缺口和变更原因；新增问题未被旧成果回答时明确标为待补查。
5. 用户要求更新报告时，对象调研交给 [research-deep](../research-deep/SKILL.md) 补查缺口；analysis 交给 [research-analysis](../research-analysis/SKILL.md) 复用报告、采用观点并复核推导，基础事实不足按 [执行交接](../research/references/routing.md#执行交接与基础补查) 定向补查后返回原分析。两条路径再交由 [research-report](../research-report/SKILL.md) 更新；不能先把未核实的新列填成确定事实。

执行过程遵循 [执行规范](../research/references/execution-policy.md)，最终保存遵循 [交付规范](../research/references/delivery-policy.md)。
