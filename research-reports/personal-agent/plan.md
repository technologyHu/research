---
theme_id: "personal-agent"
title: "Personal Agent 调研计划"
status: draft
revision: 1
created_at: "2026-11-11"
updated_at: "2026-11-11"
archived_at: null
changes:
  - "2026-11-11 r1 建立计划，登记 16 款通用个人助理及横向对比任务"
---

# Personal Agent 调研计划

## 核心问题

| ID | 主题共同研究问题 | 范围与判断标准 | 关联任务 | 当前回答与缺口 |
| --- | --- | --- | --- | --- |

## 对象与任务

| ID | 类型／对象 | 对象 ID | 主题问题 | 本次目标 | 类型评估与证据 | 优先级 | 前置任务 | 状态 | 调研人 | 调研或修订时间（北京时间） | 实际 run_id | 交付与验收 | 实际成果 | 缺口与下一步 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T001 | product／Meta Muse | meta-muse | | 以消费版建立生活事务基线。观察长期目标如何触发建议，以及跨商家比价、下单确认和结果回传。 | Meta 官方资料说明目标跟踪与购物结账。能力可信度为中，适合作为购物主样本。持续采用和跨商家履约待核实。2026-11-11 核对。[Meta 发布说明](https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent/) | P1 | 无 | planned | technologyHu | | | 预期在对比报告中交付产品记录。验证第二轮购物是否复用偏好，记录缺货处理、含配送费总价和订单状态。 | | 核对可用地区、商家和结账方式，准备两轮购物用例。 |
| T002 | product／Instinct | instinct | | 研究从日常消息交办后，助理能否保存任务背景、联系外部服务并跨天继续。 | Spear Street Technology 的产品与隐私资料确认其个人助理服务。能力可信度待核实，消息入口和跨天跟进是主要选样理由，持续采用待核实。2026-11-11 核对。[官网](https://instinct.com/) · [运营主体与服务说明](https://instinct.com/privacy-policy) | P1 | 无 | planned | technologyHu | | | 预期在对比报告中交付产品记录。验证预约改期时是否接续旧任务、拿到确认并保留用户介入记录。 | | 核对账号开放和可用消息渠道，确认外部服务沟通权限。 |
| T003 | product／OpenAI dots | openai-dots | | 研究个人 dot 怎样使用记忆与授权应用，以及离线推进、请示和暂停。按个人账号权限取证。 | OpenAI 文档说明成员各自创建个人 dot，个人账号分批开放。能力可信度为中，真实使用规模和长期效果待核实。2026-11-11 核对。[产品帮助](https://help.openai.com/en/articles/20001530-getting-started-with-your-dot) · [工作区权限](https://help.openai.com/en/articles/20001554-managing-dots-in-chatgpt-workspaces) | P1 | 无 | planned | technologyHu | | | 预期在对比报告中交付产品记录。记录主动发现、后台推进、暂停和权限撤销各步的可见结果。 | | 核对个人账号资格，测试跨会话偏好和连接器权限。 |
| T004 | product／Claude Duet | claude-duet | | 研究 Duet 如何从个人邮箱、日历中发现该处理的事项，准备下一步并请求用户授权。 | Anthropic 以候补制研究预览发布 Duet。产品流程有官方说明，能力可信度为中，主动判断的准确性和持续采用待核实。2026-11-11 核对。[Claude 帮助](https://support.claude.com/en/articles/17631495-get-started-with-claude-duet) | P1 | 无 | planned | technologyHu | | | 预期在对比报告中交付产品记录。有资格时验证改期、误提醒和授权等待。仅有公开资料时记录预览条件及待测步骤。 | | 核对访问资格和连接器范围，再安排可执行用例。 |
| T005 | product／Gemini Spark | gemini-spark | | 比较定时、邮件事件和主题监测如何触发个人任务，追踪 Google 生态内外的处理结果。 | Google 文档区分几类触发方式并要求个人账号。能力可信度为中，产品的持续使用规模和事件漏报率待核实。主要提供事件触发对照。2026-11-11 核对。[调度文档](https://support.google.com/gemini/answer/17094710?hl=en) | P2 | 无 | planned | technologyHu | | | 预期在对比报告中交付产品记录。验证邮件触发的执行结果，并记录延迟、重复提醒与日历更新。 | | 核对当前套餐、地区和邮件过滤条件。 |
| T006 | product／Grok Bot（个人 Bot） | grok-bot | | 比较个人 Bot 的持久运行、授权连接和例行任务。Team Bots 资料用于判定产品边界。 | xAI 的资料明确个人 Bot 和共享 Bot 两种形态。能力可信度为中，个人场景的持续采用待核实。适合比较有明确触发规则的个人委托。2026-11-11 核对。[Grok Bot 文档](https://docs.x.ai/grok-bot/overview) · [共享 Bot](https://docs.x.ai/grok-bot/shared-bots) | P2 | 无 | planned | technologyHu | | | 预期在对比报告中交付产品记录。用个人账号验证续费跟进或改期，记下触发、处理和审批行为。 | | 核对个人套餐的邮箱、日历和后台任务条件。 |
| T007 | product／蚂蚁灵光 2.0 | lingguang | | 建立国内生活服务对照。查看事务如何从主动跟进推进到授权、服务操作与结果确认。 | 蚂蚁集团公布主动跟进与账户授权能力。能力可信度为中，持续使用和跨生态履约待核实。国内服务路径与其他候选互补。2026-11-11 核对。[蚂蚁集团发布说明](https://www.antgroup.com/en/news-media/press-releases/1793066400000) | P1 | 无 | planned | technologyHu | | | 预期在对比报告中交付产品记录。记录提醒、下一步准备、授权和服务结果各自是否可验证。 | | 核对可接入的生活服务和授权边界，筛选可复跑场景。 |
| T008 | product／Today AI | today-ai | | 优先体验国内版。测试对日程、人物和偏好的长期记忆，以及日程变化后的主动处理。海外版的连接器条件分别记录。 | Today 官方资料说明可编辑记忆和对外操作前的确认。能力可信度为中，版本间差异与持续采用待核实。是验证偏好更新的首批样本。2026-11-11 核对。[国内版](https://todayai.cn/) · [产品说明](https://today.ai/articles/zh-Hans/blog/what-is-today) | P1 | 无 | planned | technologyHu | | | 预期在对比报告中交付产品记录。修改一次偏好并跨天复跑，记录用到的背景、主动建议和最终日程状态。 | | 核对国内版的邮箱和日历支持，建立跨天观察记录。 |
| T009 | product／Hark Pro | hark-pro | | 验证持续记忆、定时任务和 Handoff 网页操作能否配合完成购物或预约。 | Hark 提供 Handoff 和平台使用说明。能力可信度为中，稳定性和持续采用待核实。可和 Muse 用同一购物题比较。2026-11-11 核对。[产品说明](https://hark.com/using-hark) · [Handoff](https://hark.com/articles/introducing-hark-handoff) | P1 | 无 | planned | technologyHu | | | 预期在对比报告中交付产品记录。保留一条正常履约路径和一条网页受限或商品缺货的失败路径。 | | 确认可访问站点、账号登录和支付确认要求。 |
| T010 | product／Poke | poke | | 研究消息入口怎样复用邮箱、日历和偏好。明确 Poke Human 在预约等流程中的接手位置。 | The Interaction Company 文档说明消息入口与连接器，并披露真人代办服务。能力可信度为中，AI 独立完成的比例与持续采用待核实。适合检验人工接手的影响。2026-11-11 核对。[官方文档](https://poke.com/docs) · [Poke Human](https://poke.com/faq) | P1 | 无 | planned | technologyHu | | | 预期在对比报告中交付产品记录。每次运行标明 AI 操作、平台人工和用户操作，并保留最终确认。 | | 查可用消息渠道、地区和人工代办费用。 |
| T011 | product／Fo（Wajo 个人版） | wajo-fo | | 优先测试电话或邮件往返怎样完成预约改期，观察身份、授权和人工协助。 | Wajo 公开说明 Fo 可联系商家、预约和支付，遇到部分任务可请求人工。能力可信度为中，持续采用待核实。为跨商家执行补充电话路径。2026-11-11 核对。[Fo 官网](https://wajo.ai/) · [个人账号说明](https://wajo.ai/support) | P1 | 无 | planned | technologyHu | | | 预期在对比报告中交付产品记录。验证联系、获准操作、拿到商家确认和结果回传。记录人工接手及用量。 | | 核对可拨打的地区、账号资格和合适的测试商家。 |
| T012 | product／Cue by Manus | manus-cue | | 研究用户怎样授权带独立邮箱、电话、电脑和钱包的代理订购或预约，核对权限与执行记录。 | Manus 发布说明和应用商店可查，App Store 列明邀请码。能力可信度为中，实际履约和持续采用待核实。适合对照代理使用独立身份的流程。2026-11-11 核对。[Manus 发布说明](https://www.manus.im/blog/introducing-manus-2-0) · [App Store](https://apps.apple.com/us/app/cue-by-manus/id6808613358) | P1 | 无 | planned | technologyHu | | | 预期在对比报告中交付产品记录。获得资格后验证授权、支付确认和交易凭据。仅有公开资料时标记可确认的范围。 | | 核对邀请状态和预约、购物、支付的地区限制。 |
| T013 | product／千问 Go! | qwen-go | | 研究千问 App 中的生活代办流程，重点看跨平台价保、预约或改期能推进到哪一步。 | 阿里巴巴的服务接入平台可查，媒体转述了千问 App 内邀测入口。Go! 能力可信度与持续采用待核实。国内服务生态对比价值高，实测依赖资格。2026-11-11 核对。[千问开放平台](https://open.qianwen.com/) · [邀测报道](https://static.cdsb.com/micropub/Articles/202610/fc4b7dd99366d80c5ab38bcd960e072d.html) | P1 | 无 | planned | technologyHu | | | 预期在对比报告中交付产品记录。获得资格后核对一项交易或预约的最终状态，以及从生态内服务转至外部服务的交接点。 | | 复核邀测状态，分别查千问 Go! 和千问 App 通用办事功能的覆盖。 |
| T014 | product／Town（个人 Townie） | town | | 查看个人 Townie 如何从个人连接器、记忆与例行任务持续跟进。团队所有的 Background Routines 用于判定产品边界。 | Town 官方文档分别说明个人和团队拥有的例行任务。能力可信度为中，个人持续采用待核实。作为个人与团队形态并存的对照。2026-11-11 核对。[个人助理](https://www.town.com/docs/using-town/assistant) · [Teams 文档](https://www.town.com/docs/teams) | P2 | 无 | planned | technologyHu | | | 预期在对比报告中交付产品记录。验证个人邮箱或日历触发时，任务、记忆、权限和结果归属。 | | 核对个人版可用事件及套餐，准备例行跟进测试。 |
| T015 | product／Pally | pally | | 比较个人助理在群聊、私聊和助理间协作时如何取得权限、协调日程和报告结果。 | Pally 官方说明个人任务在各自账号执行，授权可在私聊处理。能力可信度为中，群聊场景的持续使用待核实。主要补充个人之间的协作。2026-11-11 核对。[群聊说明](https://pally.com/group-chats) · [Trusted Pals](https://pally.com/trusted-pals) | P2 | 无 | planned | technologyHu | | | 预期在对比报告中交付产品记录。验证协调一次改期时各方能看到的内容、审批动作及日历结果。 | | 核对群聊与私聊支持，准备两个测试账号。 |
| T016 | product／Tomo | tomo | | 研究 Mapo Labs 的 Tomo 如何用消息、日历和个人目标提供持续提醒，观察它能推进哪些后续操作。 | Tomo 官方说明主动联系、日历和邮件接入。能力可信度为中，主动执行深度和持续采用待核实。补充以个人目标和日常节奏为主的样本。2026-11-11 核对。[Tomo 产品说明](https://www.tomo.ai/about) | P2 | 无 | planned | technologyHu | | | 预期在对比报告中交付产品记录。验证跨天目标跟进、提醒质量和日程写入边界。 | | 核对连接器权限和可执行操作，再选可比场景。 |
| T017 | product／16 款通用 Personal Agent 横向对比 | | | 研究能用授权账户和长期个人上下文发现需求、后台推进事务、在关键节点交回决定权的产品。判断组织拥有的形态时，核对团队记忆、任务能否跨人员交接、协作状态能否一致。<br>第 1 周查访问条件，准备人工基线，以 Today AI、Hark Pro、Fo 和有访问条件的 Muse 校准用例。第 2 周做同题测试和跨天复跑。第 3 周汇总，接入受限的产品保留公开资料记录。 | 两篇已核对的文章分别提供选样口径和团队边界，均为讨论与判断依据。产品级能力可信度和实际采用按 T001–T016 的来源单独核对。统一场景可减少任务难度和授权差异对判断的影响。2026-11-11 核对。[Personal Agent 定义与场景](https://mp.weixin.qq.com/s/0Lu-FYVKN6d9u7n7pz3RmQ) · [Team Agent 边界](https://mp.weixin.qq.com/s/2O_NVmkSAy0yhoe59RETXw) | P1 | T001、T002、T003、T004、T005、T006、T007、T008、T009、T010、T011、T012、T013、T014、T015、T016（hard，汇总需有 16 款可追溯的产品记录。未获访问的产品接受核实过的开放条件和公开能力记录，实测格留待验证。当前待满足） | planned | technologyHu | | | 预期 `product/compare-personal-agents__YYYYMMDD-HHmmss/report.md`，含 16 款产品矩阵、产品记录、同题实测和场景结论。<br>① 订阅续费。注入续费通知、促销和重复通知，检查触发、误报、重复提醒及取消或改套餐能推进到哪一步。<br>② 周期购物。第二轮加入涨价或缺货，检查偏好复用、含运费总价、确认及购物车或订单状态。<br>③ 预约改期。注入服务商通知，检查是否接续、消解日程冲突、联系服务方并核对最终状态。<br>记录版本、地区、套餐、权限、触发类型、完成状态、人工操作时间、介入次数、可核实费用及失败原因。对照人工流程，关键场景跨天复跑并修改一次偏好。单列厂商声明、实际观察与访问缺口。 | | 准备三套脱敏测试资料，固定验收条件和测试账号。补查服务接入、订阅或交易收费、实际采用和持续使用证据。 |
