---
theme_id: team-agent
title: Team Agent 调研计划
status: active
revision: 21
created_at: "2026-11-09"
updated_at: "2026-11-11"
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
  - "2026-11-11 r19 将主题更名为 Team Agent 并迁移主题目录"
  - "2026-11-11 r20 同步内部主题 ID 为 team-agent"
  - "2026-11-11 r21 登记首轮 11 款 Team Agent 产品与实测重点，沿用 Claude Tag 基线"
---

# Team Agent 调研计划

## 核心问题

| ID | 主题共同研究问题 | 范围与判断标准 | 关联任务 | 当前回答与缺口 |
| --- | --- | --- | --- | --- |

## 调研任务

| ID | 类型／对象 | 对象 ID | 主题问题 | 本次目标 | 类型评估与证据 | 优先级 | 前置任务 | 状态 | 调研人 | 调研或修订时间（北京时间） | 实际 run_id | 交付与验收 | 实际成果 | 缺口与下一步 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | product／Claude Tag | claude-tag | | 参考已有的产品、源码和第三方资料。核对公开的持续集成（CI）案例用到哪些信息、给出什么结果、如何衡量效果，制定试点验收标准。 | **Anthropic 的行业地位。** 它发起的 MCP 协议用于连接 AI 和工具，已被多家平台采用，是 Agentic AI Foundation 的创始项目之一。[Linux Foundation 公告](https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation)<br>**能力可信度为中。** 文档和内部 CI 案例说明了怎样排查告警、怎样由人复核。运行是否稳定、实际能省多少人工时间，仍待验证。[产品总览](product/claude-tag__20261109-154839/references/article-faa09f0bec99b66b.md) · [内部 CI 案例](product/claude-tag__20261109-154839/references/article-6eea4a089f0fab4b.md)<br>**实际使用范围和影响待核实。** Anthropic 披露 Carvana 和 Insight Health 用 Claude Tag 排查生产告警。结合内部案例，可为值班试点明确谁负责处理、检查结果和交接。还不清楚它被多少团队持续使用、对行业有多大影响。[Carvana 案例](https://claude.com/customers/carvana) · [Insight Health 案例](https://claude.com/resources/articles/how-healthcare-organizations-use-claude-tag)<br>**口碑和用户量待核实。** 缺少独立长期反馈，未查到活跃用户数或使用它的组织数。[公司招股文件](https://www.sec.gov/Archives/edgar/data/2130357/000162828026068676/anthropicpbc-sx1ax1.htm)（2026-11-09 核对） | P1 | 无 | done | technologyHu | 2026-11-09 15:48:39（最近修订） | 20261109t074836z-3b876ccb | 更新原报告。核对案例原文、适用条件和效果怎样衡量，选用有助理解的素材。列出试点怎样算通过、需要记录什么。 | [Claude Tag 产品调研](product/claude-tag__20261109-154839/report.md)于 2026-11-09 交付。用了两张案例原图，说明首份分析的耗时怎么算，并在试点验收表中列明重跑历史事件时要检查什么。任务从计划第 1 版开始。已核对任务范围，报告通过检查。试点尚未开始。 | 复查 Claude Tag 是否公开核心源码，核对公开资料能确认的服务端实现。 |
| T002 | product／千问办公 2.0 · 协作空间 | qwenwork |  | 用钉钉消息、审批和待办串一次跨部门交接。验证触发任务能否写回同一条团队待办，创建人离开后由谁接手。<br>首轮共用验收以 T001 Claude Tag 为对照。让业务事件触发工单，安排两人或两个 Agent 同时处理，移除发起人后重放事件。检查团队成员能否查看有权限的决策依据、继续推进同一条记录，并追溯每次更新的执行身份与来源。记录版本、套餐、连接权限与实测范围。 | 阿里巴巴在 2026-11-09 的客户端更新中公布了协作空间、数字员工和事件触发。能力可信度为中，空间和触发任务能否共用同一业务状态、持续采用情况待核实。作为首轮跨系统基准。[更新日志](https://docs.qwenwork.cn/release-notes/desktop) · [协作空间](https://docs.qwenwork.cn/desktop/collaboration) · [自动任务](https://docs.qwenwork.cn/desktop/scheduled-tasks) · [Team Agent 判断依据](https://mp.weixin.qq.com/s/2O_NVmkSAy0yhoe59RETXw)（2026-11-11 核对） | P1 | 无 | planned | technologyHu |  |  | 预期 `product/qwenwork__YYYYMMDD-HHmmss/report.md`。核对同一待办的 ID、责任人、原消息或审批凭据。重复事件后检查记录数量和状态，换人后确认谁能继续推进。 |  | 核对企业账号可用的触发事件、云端执行条件及空间、自动任务和连接器的归属。 |
| T003 | product／腾讯 WorkBuddy Enterprise · 项目与任务 | workbuddy-enterprise |  | 用两个项目成员验证任务分享、流转和共享资料，追踪任务流转前后两条会话的状态与产物。 | 腾讯云文档说明项目共享指令、技能、资料和连接器。任务流转会复制上下文到新会话，项目定时任务文档列出按时间触发。能力可信度为中，项目功能的实际采用及长期表现待核实。适合对照会话复制后的交接。[项目与任务](https://cloud.tencent.com/document/product/1831/138797)（2026-11-11 核对） | P1 | 无 | planned | technologyHu |  |  | 预期 `product/workbuddy-enterprise__YYYYMMDD-HHmmss/report.md`。记录原会话与新会话的 ID、状态与产物版本。测试原任务更新后接手方能看到什么，以及项目定时任务能否由其他成员接管。 |  | 核对专享版项目自动化、所有者权限、连接器授权和任务流转后的更新规则。 |
| T004 | product／飞书 aily · 企业工作伙伴 | feishu-aily-enterprise |  | 用项目群与多维表格测试事件触发、分派和写回，核对群记忆、个人记忆及企业知识的权限。 | 飞书帮助中心明确企业工作伙伴面向团队，支持按人或群隔离记忆，并文档化了任务触发和应用身份。能力可信度为中，跨成员接续和实际采用待核实。适合作为国内协作平台样本。[企业工作伙伴](https://aily.feishu.cn/hc/1u7kleqg_ef4valfx) · [任务触发](https://aily.feishu.cn/hc/1u7kleqg_xb36mver) · [OpenAPI](https://aily.feishu.cn/hc/1u7kleqg_t973w36g)（2026-11-11 核对） | P1 | 无 | planned | technologyHu |  |  | 预期 `product/feishu-aily-enterprise__YYYYMMDD-HHmmss/report.md`。让具备不同权限的两位成员查看或处理同一事项，核对表格最终状态、写入身份和操作日志。 |  | 核对项目群事件是否可触发所选技能，以及应用身份可读写哪些表格。 |
| T005 | product／百度办公搭子 Dumate 企业版 | baidu-dumate-enterprise |  | 核对企业知识、技能和产物如何共享。以跨成员接续任务为主，查业务事件触发和操作审计。 | 百度智能云介绍企业版支持知识和技能沉淀、协作共享及内部系统接入，公开产品页以能力说明为主。团队任务流转的能力可信度和实际采用均待核实。适合对照企业接入与交付形态。[企业版产品页](https://cloud.baidu.com/product/dumate.html)（2026-11-11 核对） | P1 | 无 | planned | technologyHu |  |  | 预期 `product/baidu-dumate-enterprise__YYYYMMDD-HHmmss/report.md`。核对交接前后的任务记录、负责人和产物是否连续，记录自动触发和关键操作是否有日志。仅有公开资料时标注具体实测缺口。 |  | 核对可体验的企业版本、项目角色和事件触发文档。 |
| T006 | product／Dust Pods | dust-pods |  | 研究 Pods 中的人、Agent、会话、文件和任务如何围绕同一目标协作，验证共同认领和更新任务。 | Dust 文档描述了共享项目空间及可由人或 Agent 维护的任务。能力可信度为中，并发认领的处理和实际采用待核实。适合作为共享任务状态对照。[Pods 概览](https://docs.dust.tt/docs/user-documentation/pods/overview) · [任务文档](https://docs.dust.tt/docs/pods-tasks)（2026-11-11 核对） | P1 | 无 | planned | technologyHu |  |  | 预期 `product/dust-pods__YYYYMMDD-HHmmss/report.md`。两位成员或两个 Agent 同时处理同一个任务。核对最终负责人、进度、关联会话和产物，检查是否重复执行。 |  | 核对 Pod 权限、任务认领规则、外部触发和任务历史。 |
| T007 | product／Kylon | kylon |  | 比较共享房间和 Agent 记忆怎样支撑跨成员接手，核对任务进度如何留在共享房间或外部业务系统。 | Kylon 官方说明多人和 Agent 共用房间对话与文件，支持共享知识和 Agent 记忆。共享上下文的能力可信度为中，持久工作状态、事件触发深度和实际采用待核实。适合与 Dust Pods 对照。[共享房间](https://kylon.io/multiplayer-ai) · [Agent 记忆](https://kylon.io/product/memory)（2026-11-11 核对） | P1 | 无 | planned | technologyHu |  |  | 预期 `product/kylon__YYYYMMDD-HHmmss/report.md`。让第二位成员接续未完成事项，核对其可见背景、执行权限和最终产物。确认进度从哪里读取、由谁更新。 |  | 核对工作流触发、共享房间权限及原发起人离开后的接续条件。 |
| T008 | product／Grok Bot · Team Bots | grok-team-bots |  | 查团队共享记忆、Slack 线程接续和工作派发。验证 Bot 所有者离开时凭证、例行任务和未完工单能否交接。 | xAI 发布说明给出了团队分流工单和派发修复的案例，共享 Bot 文档说明了权限与所有者连接。能力可信度为中，厂商案例以外的持续采用待核实。适合核对共享 Bot 对个人配置的依赖。[Team Bots 案例](https://x.ai/news/team-bots) · [共享 Bot](https://docs.x.ai/grok-bot/shared-bots)（2026-11-11 核对） | P1 | 无 | planned | technologyHu |  |  | 预期 `product/grok-team-bots__YYYYMMDD-HHmmss/report.md`。用两位成员接续同一工单，核对共享记忆、工具身份和运行结果。移除原所有者后，记录连接和例行任务是否仍可用、由谁恢复。 |  | 核对 Manager 权限、所有权交接和组织服务账号可用范围。 |
| T009 | product／Town Teams · Background Routines | town-teams |  | 以团队拥有的后台例行任务做工单分流。测试更换维护人、连接凭证失效和重复事件后的状态。 | Town 文档明确 Background Routines 由团队共同拥有，成员退出后仍可运行，付费团队方案提供该能力。能力可信度为中，并发写入与实际采用待核实。适合直接检验团队任务归属。[Town Teams](https://www.town.com/docs/teams)（2026-11-11 核对） | P1 | 无 | planned | technologyHu |  |  | 预期 `product/town-teams__YYYYMMDD-HHmmss/report.md`。核对成员退出后同一个团队任务能否继续。记录凭证失效如何告警及恢复，重复事件后检查最终工单数量和负责人。 |  | 核对付费团队的事件触发、运行日志和连接器权限。 |
| T010 | product／ChatGPT Workspace Agents | chatgpt-workspace-agents |  | 研究共享 Agent 的多人维护、计划或 API 触发，以及所有者离开后的应用连接、技能和部署交接。 | OpenAI 文档说明工作区 Agent 可共享给成员或组，并由多位成员维护，部分应用和配置仍关联所有者。能力可信度为中，交接效果与独立采用证据待核实。适合对照共享配置和执行权限。[Workspace Agents](https://help.openai.com/en/articles/20001143-chatgpt-workspace-agents-for-enterprise-and-business) · [官方案例](https://openai.com/index/introducing-workspace-agents-in-chatgpt/)（2026-11-11 核对） | P1 | 无 | planned | technologyHu |  |  | 预期 `product/chatgpt-workspace-agents__YYYYMMDD-HHmmss/report.md`。由两位维护人配置和运行同一 Agent。核对触发、接管和重新授权前后的执行身份、连接可用性及结果记录。 |  | 核对组织套餐、编辑角色、连接器身份和所有权转移条件。 |
| T011 | product／Asana AI Teammates | asana-ai-teammates |  | 在 Asana 任务中比较多人委派、审阅、共享记忆与权限。跟踪事件或自动化如何把任务交给 AI Teammate。 | Asana 文档说明多位成员可分派任务，记忆的可见性受来源任务权限约束。能力可信度为中，配置切换后的状态一致性和持续采用待核实。适合对照团队记忆和工单权限。[AI Teammates](https://help.asana.com/s/article/ai-teammates) · [访问控制](https://help.asana.com/s/article/understanding-access-control-for-ai-teammates)（2026-11-11 核对） | P1 | 无 | planned | technologyHu |  |  | 预期 `product/asana-ai-teammates__YYYYMMDD-HHmmss/report.md`。用两位权限不同的成员分派、审阅和接续同一任务。核对可见记忆、负责人、写入记录和最终状态。 |  | 核对 AI Teammates 与 AI Studio 的触发分工，以及哪些来源可成为共享记忆。 |
| T012 | product／ClickUp Super Agents | clickup-super-agents |  | 测试工单分配触发、共享记忆、活动日志和私有资料访问，核对多人更新同一工单后的状态。 | ClickUp 文档说明 Super Agents 可受任务分配触发，提供活动日志，并允许明确授权私有资源。能力可信度为中，去重、权限边界和持续采用待核实。适合对照团队共享 Agent 的数据可见性。[触发与记忆](https://help.clickup.com/hc/en-us/articles/37092796379927-Super-Agent-instructions-Skills-triggers-knowledge-and-memory) · [权限](https://help.clickup.com/hc/en-us/articles/36926065055127-Super-Agent-privacy-security-and-permissions) · [活动记录](https://help.clickup.com/hc/en-us/articles/36455020912919-Super-Agent-Activity)（2026-11-11 核对） | P1 | 无 | planned | technologyHu |  |  | 预期 `product/clickup-super-agents__YYYYMMDD-HHmmss/report.md`。测试 Agent 与成员近同时更新一条工单，并重放触发事件。核对最终状态、重复写入、日志记录及不同角色可见的输出。 |  | 核对可用套餐、触发范围和私有数据授权对共享输出的影响。 |
