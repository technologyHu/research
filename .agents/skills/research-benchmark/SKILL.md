---
name: research-benchmark
description: 调研 benchmark、评测数据集或评估体系，分析任务、数据、指标、协议、基线、结果可比性及复现条件。适用于评测选型与评测方法分析，单次跑分不自动扩展为完整调研。
---

# 评测调研规范

## 与公共流程的关系

本技能提供对象类型规范，不另建一套保存、搜索或清理流程。

- 接收已明确的对象与问题，将本类型维度用于当前 fields；需要执行和成稿时可分别使用 [research-deep](../research-deep/SKILL.md) 与 [research-report](../research-report/SKILL.md)，不回调顶层入口。
- 用户直接调用本技能时，按 [共用计划规则](../research-common/references/theme-planning.md) 明确问题与范围，固定类型为 `benchmark`，再按需使用执行与成稿子技能；不重复进行类型路由，也不回调顶层入口。
- 单对象和对比均适用。用户仅要某个维度或计划时，按该范围裁剪。

## 类型重点

明确评测版本、划分、指标分母和执行条件。比较结果前核对模型版本、工具、预算、采样、测试次数和判分器；排名与数值保留日期，数据泄漏、公平性与方差按证据讨论。

## 按阶段读取

- 选择／排序评测，或分析其权威性、影响力与主办／资助背景时，读取 [类型评估与背景标准](references/selection-criteria.md)，使用评测定义及“计划中的背景字段”，不套用参评模型或运营公司的规模指标。
- 规划问题和组织报告时读取 [报告模板](references/report-template.md)，根据主题与深度裁剪，保留研究目标所需内容。
- 搜集证据与交付前读取 [检查清单](references/checklist.md)。
- 来源、事实与推断遵循 [证据规范](../research-common/references/evidence-policy.md)，保存与清理遵循 [交付规范](../research-common/references/delivery-policy.md)。
