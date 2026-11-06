---
name: research-open-source
description: 对开源库、框架、中间件、算法库、应用或工具开展架构与源码调研，分析核心流程、扩展机制、工程质量和适用场景。一般功能开发或修复不属于该技能。
---

# 开源项目调研规范

## 与公共流程的关系

本技能提供对象类型规范，不另建一套保存、搜索或清理流程。

- 从 [research](../research/SKILL.md) 路由进入时，把这里的维度用于当前 fields，随后由 [research-deep](../research-deep/SKILL.md) 执行、[research-report](../research-report/SKILL.md) 成稿。
- 用户直接调用本技能时，复用 research 的计划建立步骤，固定类型为 `open-source`，再接入相同执行与成稿阶段；不重复进行类型路由。
- 单对象和对比均适用。用户仅要某个维度或计划时，按该范围裁剪。

## 类型重点

固定版本或提交，沿关键入口、调用链、数据结构与错误路径阅读源码。按 [项目类型裁剪](references/project-types.md) 选择分析视角。下载、构建、执行测试与源码阅读是不同证据层级，不因仓库有测试文件就声称测试已通过。

## 按阶段读取

- 规划问题和组织报告时读取 [报告模板](references/report-template.md)，根据主题与深度裁剪，保留研究目标所需内容。
- 搜集证据与交付前读取 [检查清单](references/checklist.md)。
- 来源、事实与推断遵循 [证据规范](../research/references/evidence-policy.md)，保存与清理遵循 [交付规范](../research/references/delivery-policy.md)。
