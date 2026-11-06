---
name: research-paper
description: 深入调研一篇或多篇论文，分析研究问题、方法、实验、创新、局限及复现条件。适用于论文精读或论文比较；仅实现论文代码时不启动完整调研。
---

# 论文调研规范

## 与公共流程的关系

本技能提供对象类型规范，不另建一套保存、搜索或清理流程。

- 从 [research](../research/SKILL.md) 路由进入时，把这里的维度用于当前 fields，随后由 [research-deep](../research-deep/SKILL.md) 执行、[research-report](../research-report/SKILL.md) 成稿。
- 用户直接调用本技能时，复用 research 的计划建立步骤，固定类型为 `paper`，再接入相同执行与成稿阶段；不重复进行类型路由。
- 单对象和对比均适用。用户仅要某个维度或计划时，按该范围裁剪。

## 类型重点

按研究目标阅读原论文的相关方法、实验和必要附录；需要整体评价论文时再覆盖全文及补充材料，局部问题不强制扩成整篇精读。对齐论文版本，区分论文报告结果、作者解释和自行复现结果。不要把代码仓库的工程实现代替论文方法或实验论证。

## 按阶段读取

- 规划问题和组织报告时读取 [报告模板](references/report-template.md)，根据主题与深度裁剪，保留研究目标所需内容。
- 搜集证据与交付前读取 [检查清单](references/checklist.md)。
- 来源、事实与推断遵循 [证据规范](../research/references/evidence-policy.md)，保存与清理遵循 [交付规范](../research/references/delivery-policy.md)。
