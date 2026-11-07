---
name: research-add-items
description: 为主题计划或已进行的调研追加对象、去重并确定对象类型，更新计划与受影响的执行任务。用于扩大现有调研范围，独立新主题由 research 规划。
---

# Research Add Items：补充对象

仅维护主题计划时，先按 [主题计划维护](../research/references/theme-planning.md) 定位长期 Markdown，去重并追加实际类型的对象／任务，补充问题关联、类型评估、依赖、预期成果与验收，递增修订并记录原因；保存汇报后结束，不要求存在 outline、fields 或 .tmp。涉及正在执行的单次调研时，再执行下列步骤并回写同一主题计划。

更新本次执行对象／版本／范围时，按主题计划的范围对照规则保留原 scope 快照，列明受影响内容并在同步后新增口径；只改长期待办时不改写既有执行快照，后续恢复或交付须对照当前计划。

按 [依赖规则](../research/references/theme-planning.md#依赖的满足失效与复核) 为新增、替代或拆并任务记录实际所需成果、hard／soft 和接受条件，检查 ID、摘要一致性与循环；前置被取消或替换时保留旧关系及原因，核对现存成果再判断下游，不默认为满足或一律作废。

1. 按 [任务管理](../research/references/task-management.md) list/show 定位任务，使用返回的 outline、fields 实际路径；不按固定扩展名另建配置。尚未交付的调研原地扩展；已有报告需更新且旧 full 证据仍有效时先 derive 为新任务，再按 [局部更新流程](../research/references/report-updates.md) 保存报告基线。light 先 promote 并核对逐字段证据；旧任务已清理时从报告和来源重建需要的证据。
2. 使用用户给定对象；只有用户需要推荐更多对象时才补充搜索。按规范化名称和来源链接去重，保留别名，不能把同项目不同版本自动合并。
3. 按 [路由规则](../research/references/routing.md) 指定类型，生成稳定 `id`，补充版本和种子来源。新增第二个对象时将 `mode` 改为 `comparison`，保留原主题与输出目录。
4. 更新实际 outline 文件并增加 revision；检查 fields 的 applies_to／item_ids 是否覆盖新增对象，不随意扩大原本限定的字段。在临时进度中仅将新增对象的适用字段标记 pending，保留已完成且仍有效的结果。问题、版本或时间口径改变时，相关旧字段仍须复查。
   若关联主题计划，按 [主题计划维护](../research/references/theme-planning.md) 同步新增对象、来源主体／团队和适用的资金背景、问题关联、权威性／影响力及核实依据、优先级理由、依赖和预期成果，保留稳定任务 ID 和已有完成记录；未核实评估注明暂定，不把新增待办直接标为已调研。
5. 若用户要求继续完成调研，按 [增量执行规范](../research/references/execution-policy.md) 补查新增对象并更新报告；仅要求改计划时说明改动后结束。

字段定义、对象与报告之间的关系遵循 [配置约定](../research/references/research-config.md)，最终保存遵循 [交付规范](../research/references/delivery-policy.md)。
