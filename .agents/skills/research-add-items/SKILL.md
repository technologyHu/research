---
name: research-add-items
description: 为已规划或进行中的调研追加对象、去重并确定对象类型，更新计划并标记新增对象待补查。用于扩大现有调研范围，独立新主题由 research 规划。
---

# Research Add Items：补充对象

1. 按 [任务管理](../research/references/task-management.md) list/show 定位任务，使用返回的 outline、fields 实际路径；不按固定扩展名另建配置。尚未交付的调研原地扩展；已有报告需更新且旧 full 证据仍有效时先 derive 为新任务，再按 [局部更新流程](../research/references/report-updates.md) 保存报告基线。light 先 promote 并核对逐字段证据；旧任务已清理时从报告和来源重建需要的证据。
2. 使用用户给定对象；只有用户需要推荐更多对象时才补充搜索。按规范化名称和来源链接去重，保留别名，不能把同项目不同版本自动合并。
3. 按 [路由规则](../research/references/routing.md) 指定类型，生成稳定 `id`，补充版本和种子来源。新增第二个对象时将 `mode` 改为 `comparison`，保留原主题与输出目录。
4. 更新实际 outline 文件并增加 revision；检查 fields 的 applies_to／item_ids 是否覆盖新增对象，不随意扩大原本限定的字段。在临时进度中仅将新增对象的适用字段标记 pending，保留已完成且仍有效的结果。问题、版本或时间口径改变时，相关旧字段仍须复查。
5. 若用户要求继续完成调研，按 [增量执行规范](../research/references/execution-policy.md) 补查新增对象并更新报告；仅要求改计划时说明改动后结束。

字段定义、对象与报告之间的关系遵循 [配置约定](../research/references/research-config.md)，最终保存遵循 [交付规范](../research/references/delivery-policy.md)。
