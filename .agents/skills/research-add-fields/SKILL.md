---
name: research-add-fields
description: 为现有调研新增或细化分析维度，指定适用对象与证据要求，并定位需要补查的结果。用于补充问题、比较指标或章节关注点。
---

# Research Add Fields：补充维度

1. 按 [任务管理](../research/references/task-management.md) list/show 定位任务，使用返回的 outline、fields 实际路径，不按固定扩展名另建配置。尚未交付的调研原地扩展；已有报告需更新且旧 full 证据仍有效时先 derive 为新任务，再按 [局部更新流程](../research/references/report-updates.md) 保存基线。light 先 promote 并核对逐字段证据；结合类型模板检查已有问题。
2. 将用户要求转成可回答的问题；指标写明定义、单位、时间和条件。去除语义重复项，保留稳定字段 id，不因改中文标题而改变 id。
3. 用 `applies_to` 限定类型，必要时用 `item_ids` 限定对象。按研究目标确定 `core`，默认 true，附加资料可设为 false。对用户明确提出的维度直接更新；只有真正存在不同研究方向时再澄清，不为例行追加反复确认。
4. 更新实际 fields 文件与 outline revision，标记新增或语义发生变化的字段及受影响对象需要补查。其他证据继续复用，保留来源原访问日期；不能把旧结果无条件标为全新或全部作废。原任务已清理时，从报告与来源重建需要的证据。
5. 用户要求更新报告时先补查受影响字段，再交由 [research-report](../research-report/SKILL.md) 更新；不能先把未核实的新列填成确定事实。

执行过程遵循 [执行规范](../research/references/execution-policy.md)，最终保存遵循 [交付规范](../research/references/delivery-policy.md)。
