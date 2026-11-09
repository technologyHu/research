---
theme_id: organization-agent
title: 组织 Agent 调研计划
status: active
revision: 18
created_at: "2026-11-09"
updated_at: "2026-11-09"
archived_at: null
changes:
  - "2026-11-09 r1 基于既有 Claude Tag 报告补建计划"
  - "2026-11-09 r2 回填 CI 案例与试点验收成果"
  - "2026-11-09 r3 清空核心问题及编号引用"
  - "2026-11-09 r4 合并为两张表，保留 T001 的验收与成果"
  - "2026-11-09 r5 将类型评估与证据独立成列，明确排序依据"
  - "2026-11-09 r6 明确类型评估中的调研必要性与重要性"
  - "2026-11-09 r7 复核 T001 的主体地位、产品采用证据和 P1 理由"
  - "2026-11-09 r8 精简 T001 的类型评估与证据"
  - "2026-11-09 r9 明确 T001 的采用影响待核实"
  - "2026-11-09 r10 优先级只填级别，精简表格文字"
  - "2026-11-09 r11 改用更直白的表格文字"
  - "2026-11-09 r12 下一步只保留调研和确认工作"
  - "2026-11-09 r13 将任务表标题改为调研任务"
  - "2026-11-09 r14 将 Claude Tag 的对象 ID 和报告目录改为 claude-tag"
  - "2026-11-09 r15 更新简短开头修订后的报告链接"
  - "2026-11-09 r16 增加调研人和最近修订时间"
  - "2026-11-09 r17 使用已确认的 GitHub 账户署名"
  - "2026-11-09 r18 修正局部复查状态和归档日期"
---

# 组织 Agent 调研计划

## 核心问题

| ID | 主题共同研究问题 | 范围与判断标准 | 关联任务 | 当前回答与缺口 |
| --- | --- | --- | --- | --- |

## 调研任务

| ID | 类型／对象 | 对象 ID | 主题问题 | 本次目标 | 类型评估与证据 | 优先级 | 前置任务 | 状态 | 调研人 | 调研或修订时间（北京时间） | 实际 run_id | 交付与验收 | 实际成果 | 缺口与下一步 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | product／Claude Tag | claude-tag | | 参考已有的产品、源码和第三方资料。核对公开的持续集成（CI）案例用到哪些信息、给出什么结果、如何衡量效果，制定试点验收标准。 | **Anthropic 的行业地位。** 它发起的 MCP 协议用于连接 AI 和工具，已被多家平台采用，是 Agentic AI Foundation 的创始项目之一。[Linux Foundation 公告](https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation)<br>**能力可信度为中。** 文档和内部 CI 案例说明了怎样排查告警、怎样由人复核。运行是否稳定、实际能省多少人工时间，仍待验证。[产品总览](product/claude-tag__20261109-154839/references/article-faa09f0bec99b66b.md) · [内部 CI 案例](product/claude-tag__20261109-154839/references/article-6eea4a089f0fab4b.md)<br>**实际使用范围和影响待核实。** Anthropic 披露 Carvana 和 Insight Health 用 Claude Tag 排查生产告警。结合内部案例，可为值班试点明确谁负责处理、检查结果和交接。还不清楚它被多少团队持续使用、对行业有多大影响。[Carvana 案例](https://claude.com/customers/carvana) · [Insight Health 案例](https://claude.com/resources/articles/how-healthcare-organizations-use-claude-tag)<br>**口碑和用户量待核实。** 缺少独立长期反馈，未查到活跃用户数或使用它的组织数。[公司招股文件](https://www.sec.gov/Archives/edgar/data/2130357/000162828026068676/anthropicpbc-sx1ax1.htm)（2026-11-09 核对） | P1 | 无 | done | technologyHu | 2026-11-09 15:48:39（最近修订） | 20261109t074836z-3b876ccb | 更新原报告。核对案例原文、适用条件和效果怎样衡量，选用有助理解的素材。列出试点怎样算通过、需要记录什么。 | [Claude Tag 产品调研](product/claude-tag__20261109-154839/report.md)于 2026-11-09 交付。用了两张案例原图，说明首份分析的耗时怎么算，并在试点验收表中列明重跑历史事件时要检查什么。任务从计划第 1 版开始。已核对任务范围，报告通过检查。试点尚未开始。 | 复查 Claude Tag 是否公开核心源码，核对公开资料能确认的服务端实现。 |
