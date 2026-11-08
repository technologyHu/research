---
name: research-add-items
description: 为主题计划或已有调研追加对象，按同类型、跨类型和分析来源分别处理，复用已有成果并定位实际补查范围；向调用方返回新增内容、任务配置和缺口。
---

# Research Add Items：补充对象与来源

先读 [路由规则](../research-common/references/routing.md) 并核对已有成果，明确新增内容的性质，再决定修改哪个任务。仅维护主题计划时按 [主题计划维护](../research-common/references/theme-planning.md) 去重、登记任务／来源和验收、记录修订后结束，不要求 outline、fields 或 .tmp 存在。

## 先分流追加内容

| 新增内容 | 处理方式 |
| --- | --- |
| 与当前对象调研相同类型的新对象 | 在本任务扩充 items；新增第二个对象时改 comparison，沿用本任务输出位置 |
| 与当前对象调研不同类型的对象 | 先寻找其已有报告或独立任务，成果满足本轮问题则复用；有缺口才建立／恢复该类型任务。不将其加入原 items，不改变原报告类型或目录 |
| analysis 使用的一份已有报告、贡献者观点或其他依据 | 更新来源／观点记录并复核实际依赖的判断；不新增来源对象到 items，不因来源增加修改 mode |
| analysis 新增的分析主题／问题或待比较对象 | 仍使用 analysis；同一判断的细化问题交给 [增加维度](../research-add-fields/SKILL.md)，确需比较独立主题／问题时再追加 analysis item 并更新 mode |

跨类型成果需要主题综合或洞察时，创建或复用独立 analysis，记录它与来源成果的实际依赖。基础成果已足够时不重复调研；用户只要求新增来源或维护计划时不自行扩成整轮分析。使用用户给定对象；仅在用户需要推荐时补充搜索。按名称、版本、来源及研究范围去重，不能把不同版本自动合并。

## 修改被选中的任务

1. 定位本轮实际要修改的报告／任务，按 [任务管理](../research-common/references/task-management.md) 使用返回的真实配置路径；只因新增另一类型任务，不派生原任务或改写原报告。已有成果可复用但执行目录已清理时，只为本轮缺口重建需要的证据。
2. 需要修改已交付报告时，旧 full 证据仍有效可先 derive，再按 [局部更新流程](../research-common/references/report-updates.md) 登记范围。light 只在增加对象、需要逐字段续查或处理实质冲突时 promote；分析仅增加依据且仍符合单对象 brief 时可保留 light。
3. 对真正新增的对象／分析主题生成稳定 id，补充实际类型、版本和问题，保持单次任务的 items 类型一致。检查 fields 的 applies_to／item_ids，仅将新增对象和语义改变涉及的字段标 pending／stale；其余仍有效结果和原访问日期保留。分析来源按 [配置约定](../research-common/references/research-config.md#分析洞察引用已有报告) 登记，修改采用范围后重新核对依赖判断，不能只更新散列接受变化。
4. 实质范围变化时更新所选 outline 的 revision，并按 [范围对照](../research-common/references/theme-planning.md#本次执行范围快照与回写前对照) 同步本次口径。只改长期待办时不改原执行快照。按 [依赖规则](../research-common/references/theme-planning.md#依赖的满足失效与复核) 记录前置成果、接受条件及受影响下游，保留原关系和接受记录。
5. 关联主题计划时回写新增对象／问题／来源、实际成果、类型评估和补查任务。对象背景按实际类型与问题需要核查；analysis 优先检查成果依据、解释目标、样本范围及实际观点归属，不对每份来源重做机构或资金调查。
6. 用户要求继续交付时，对象证据的实际缺口可由 [research-deep](../research-deep/SKILL.md) 补查；分析来源采用、判断更新及其受影响范围返回调用方执行。证据齐备时可使用 [research-report](../research-report/SKILL.md) 成稿与校验，不调用顶层入口。只改计划或登记来源时汇报实际修改与剩余缺口后结束。

最终保存与清理遵循 [交付规范](../research-common/references/delivery-policy.md)，不为分类或追加搬迁已有资料。
