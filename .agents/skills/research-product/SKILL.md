---
name: research-product
description: 调研产品的定位、能力、用户流程、公开技术机制、集成方式、限制与适用场景。适用于产品深入分析或横向比较，源码分析可另选开源项目规范。
---

# 产品调研规范

## 与公共流程的关系

本技能提供对象类型规范，不另建一套保存、搜索或清理流程。

- 从 [research](../research/SKILL.md) 路由进入时，把这里的维度用于当前 fields，随后由 [research-deep](../research-deep/SKILL.md) 执行、[research-report](../research-report/SKILL.md) 成稿。
- 用户直接调用本技能时，复用 research 的计划建立步骤，固定类型为 `product`，再接入相同执行与成稿阶段；不重复进行类型路由。
- 单对象和对比均适用。用户仅要某个维度或计划时，按该范围裁剪。

## 类型重点

从官方产品资料、实际可见行为及可信外部资料建立能力边界。区分已发布、预览、路线图和宣传主张；闭源部分只解释公开接口或有依据的推断，不编造内部实现。

## 按阶段读取

- 规划问题和组织报告时读取 [报告模板](references/report-template.md)，根据主题与深度裁剪，保留研究目标所需内容。
- 搜集证据与交付前读取 [检查清单](references/checklist.md)。
- 来源、事实与推断遵循 [证据规范](../research/references/evidence-policy.md)，保存与清理遵循 [交付规范](../research/references/delivery-policy.md)。
