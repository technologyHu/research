---
name: research-paper
description: 深入调研一篇或多篇论文，分析研究问题、方法、实验、创新、局限及复现条件；survey 论文侧重分类、覆盖与综合论证。适用于论文精读或论文比较；仅实现论文代码时不启动完整调研。
---

# 论文调研规范

## 与公共流程的关系

本技能提供对象类型规范，不另建一套保存、搜索或清理流程。

- 从 [research](../research/SKILL.md) 路由进入时，把这里的维度用于当前 fields，随后由 [research-deep](../research-deep/SKILL.md) 执行、[research-report](../research-report/SKILL.md) 成稿。
- 用户直接调用本技能时，复用 research 的计划建立步骤，固定类型为 `paper`，再接入相同执行与成稿阶段；不重复进行类型路由。
- 单对象和对比均适用。用户仅要某个维度或计划时，按该范围裁剪。

## 类型重点

按研究目标阅读原论文的相关方法、实验和必要附录；需要整体评价论文时再覆盖全文及补充材料，局部问题不强制扩成整篇精读。对齐论文版本，区分论文报告结果、作者解释和自行复现结果。不要把代码仓库的工程实现代替论文方法或实验论证。

## Survey 论文

survey 仍为 `paper`，单篇对象目录使用 `survey-<paper-id>`；多篇 survey 比较可使用 `compare-survey-<slug>`。按 [survey 阅读规范](references/survey.md) 设计问题与成稿，不要求综述具备原创算法、实验或复现代码。贡献者基于多份既有成果形成的分析判断另归 analysis。

## 按阶段读取

- 选择／排序论文，或分析其权威性、影响力与机构／资助背景时，读取 [类型评估与背景标准](references/selection-criteria.md)，使用论文定义及“计划中的背景字段”；不以期刊／机构名称单独赋级。
- 规划问题和组织报告时读取 [报告模板](references/report-template.md)，根据主题与深度裁剪，保留研究目标所需内容。
- 搜集证据与交付前读取 [检查清单](references/checklist.md)。
- 来源、事实与推断遵循 [证据规范](../research/references/evidence-policy.md)，保存与清理遵循 [交付规范](../research/references/delivery-policy.md)。
