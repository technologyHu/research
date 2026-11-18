---
theme_id: agent-os
title: Agent OS 调研计划
status: active
revision: 5
created_at: "2026-11-18"
updated_at: "2026-11-18"
archived_at: null
changes:
  - "2026-11-18 r1 创建计划并登记 Muse Gadget SDK 调研。"
  - "2026-11-18 r2 回填 T001。核对 r1 执行范围与验收条件，交付范围一致，无前置任务。"
  - "2026-11-18 r3 修订 T001。核对 r2 的目标及验收，复查 SDK 与 Muse 的依赖边界、设备权限和消息确认，并补跑两项 Linux Link 模拟 VM 测试。"
  - "2026-11-18 r4 修订 T001。核对 r3 的目标及验收，补充配对、Link 调用和消息确认三张内联图，并验证渲染。"
  - "2026-11-18 r5 将 T001 类型改为图谱使用的 open-source 标识。"
---

# Agent OS 调研计划

## 核心问题

| ID | 主题共同研究问题 | 范围与判断标准 | 关联任务 | 当前回答与缺口 |
| --- | --- | --- | --- | --- |

## 对象与任务

| ID | 类型／对象 | 对象 ID | 主题问题 | 本次目标 | 类型评估与证据 | 优先级 | 前置任务 | 状态 | 调研人 | 调研或修订时间（北京时间） | 实际 run_id | 交付与验收 | 实际成果 | 缺口与下一步 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | open-source／Muse Gadget SDK | muse-gadget-sdk | | 以提交 `6a44074` 为基线，覆盖指定本地参考报告的产品背景、场景、能力、协议、源码、扩展示例、安全及验证范围。 | Meta 在 `facebookincubator` 发布的设备端实现，有固定提交、协议及测试可核。云端以官方资料为依据。 [官方仓库](https://github.com/facebookincubator/muse-gadget-sdk) · 2026-11-18 | P0 | 无 | partial | technologyHu | 2026-11-18 15:55:15 | 20261118t074654z-19edf162 | 逐主题覆盖参考报告及场景图，给出源码依据、适用条件及验证边界。 | [Muse Gadget SDK 调研](open-source/muse-gadget-sdk__20261118-155515/report.md)。保留参考七个主题和原图，增加三张 Mermaid 图，渲染及报告文件校验通过。初版 Linux 103 项、ESP32 源码契约 37 项通过，r3 补跑两项 Linux Link 模拟 VM 测试通过。 | 正式 Muse App 的令牌申请顺序、VM 内部路由和工具选择策略缺直接证据。实机配对、通话和固件联调留待可用设备及服务环境。 |
