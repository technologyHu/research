# Claude Code 事件详解与完整触发关系

> 核对日期：2026-10-13。覆盖 128 个固定公开类型事件和 13 个当前文档补充名称，共 141 个已确认名称。本文给出公开契约能支持的触发关系，不冒充闭源宿主的全部内部调用栈，也不是某次真实任务的运行 trace。

## 1. 阅读方式与版本边界

先读第 2 节，理解事件如何触发；再读第 3 节，沿前端、回合、工具和 UI 的关系理解整个过程；第 4 节按用途逐项解释全部事件，第 5 节保留可检索的类型索引。

- **宿主**：协调模型请求、工具、上下文、UI 和会话的 Claude Code 运行程序。
- **事件**：一个具名的操作或通知入口，例如 `tool.call`。同名事件可以发生多次。
- **handler（处理函数）**：mod 登记的函数，接收能力接口、事件数据与 next，并返回该事件规定的结果。
- **处理链**：某一次事件分发中，匹配的 handler 用 `next` 组合成的调用关系。
- **执行循环**：宿主获取模型响应、执行工具、加入结果并再次请求模型的整体控制流程。
- **回合 / 步骤**：一次提示词的响应过程是 turn，其中一次模型请求是 step。
- **绘制位置**：`Pane`、`ToolResult` 等 UI 扩展位置，是 `ui.render` 的 component 值，不是新事件名。
- **namespace（命名空间）**：API 的方法分组，例如 `$.fs` 中的 read、write。插件也可增加自己的分组。
- **schema（结构规则）**：声明对象有哪些字段、哪些必填、各字段允许什么值；工具输入与输出按相应规则检查。
- **envelope（外围字段）**：事件输入中用于定位和描述本次操作的字段；不能把它与工具自身参数或任意自由 JSON 混同。

字段名后的 `?` 表示可选。`NoArgs` 表示没有业务参数，handler 仍然有 `$`、`e`、`next`。`void` 表示 API 没有业务返回值，不代表拦截 handler 可以忽略事件结果契约。`Promise` 是等待一次结果；异步生成器则可以逐段产生流块，最后再返回完成结果。

固定来源为提交 `3deb873687379f0c199a69fdaccc65f0865f7a29` 的 v2.1.277 类型文件：40 个 `EngineEventOf`、55 个 `OpEventOf`、33 个 `classic.*`，合计 128 个。第 4 节每条均标明属于固定快照还是当前文档补充。部分补充 API 在旧 `CoreEngineInterface` 中已存在，但旧 `OpEventOf` 没有列出其独立事件；不把这种差异冒称为已验证的新宿主实现。

当前文档可能晚于公开 GitHub 类型；精确开发契约应使用目标安装版本生成的声明。本文没有升级旧 CLI、加载官方 mod 或伪造宿主 trace。

## 2. 一次事件是如何触发、执行和返回的

### 2.1 输入由谁构造

宿主触发时，原始事实可能来自模型工具请求、用户编辑、前端绘制请求或生命周期变化。mod 调 API 时，原始参数由 mod 提供。宿主根据事件契约准备 handler 的输入、能力和继续执行函数；上游 handler 还可以通过 `next(副本)` 改写允许的数据。

```text
模型 / 用户 / 界面 / 生命周期 / mod API 调用
                     ↓
          宿主准备事件名与规范化输入
                     ↓
       按层级、匹配条件和重入规则选择 handler
                     ↓
           handler($, 深度冻结的 e, next)
```

`$` 和 `next` 含函数，不能把整个 handler 输入理解为单个 JSON 对象。`e` 是按事件定义的普通数据；输入不是任意自由 JSON。直接改 `e` 会违反冻结契约，改写应复制，并遵守受保护字段和 schema 校验。

### 2.2 next 推进当前事件，宿主推进整体回合

```text
宿主分发事件 → handler A → next(e) → handler B → next(e) → 当前事件的核心行为
           ←   A 得结果  ←           B 得结果  ←           核心结果
```

handler 在调用 `next` 前做的是当前操作的前置处理，在 `await next` 后做的是后置处理；不调用 `next` 而返回有效结果，会接管本次事件。接管工具调用时，核心工具不一定执行；执行后改写结果不会撤销已经发生的副作用。

某事件的核心实现还可能分发其他事件，所以流程会嵌套。例如 `tool.call` 的核心路径可以进入 `tool.check`；handler 自己调用 `$.fs.read` 又会产生 API 事件。API 是否被某个 handler 观察还受来源、层级、重入与策略约束，不是全部 handler 无条件再次运行。

### 2.3 普通结果、API 结果与流式结果

| 类型 | handler 返回什么 | 不要混淆什么 |
|---|---|---|
| 宿主事件 | 该事件的专门结果，例如 ToolCallResult、RenderElement | 没有统一的 success/data envelope |
| 固定 OpEventOf API 事件 | ValueOrDeny<V>，即 value 或 deny 分支 | $.fs.read 的调用者得到内容；拦截 handler 得到事件封装 |
| classic.* | ClassicResultOf 中该事件可用的字段 | 不等于直接返回传统命令 hook 的 stdout JSON |
| 流式事件 | async generator 输出流块，最后返回最终结果 | chunk 不是又一个 EventName；普通 async handler 不适用 |

`turn.step` 是固定快照中的流式事件；当前参考还列出 `process.spawn`。普通函数的返回值、Promise、异步生成器必须分别按契约处理。

### 2.4 传统 Hooks 与 Mods 的衔接

传统 Hooks 常见于 settings 或 hooks.json，通过命令、HTTP 等处理传统输入；同一事件下匹配的传统 handler 可以并行。Mods 则使用函数与 `next` 组合。Mods 以 `classic.<传统事件名>` 介入这类操作，但不能把所有传统 handler 都画成串行的 next 链。

固定类型中还有一个重要例外：`classic.PreToolUse` 的 mod 输入是扁平 `ToolCallEnvelope`；传统命令 hook 的输入则包含 `tool_name`、`tool_input` 等字段。二者用途相关，参数形状不同。

### 2.5 失败、取消与返回后的推进

普通 hook 在调用 next 前失败时，宿主可跳过它继续下层；next 已完成后失败时，已有结果保留，核心操作不会因此重复执行。注册的 `.catch` 可按失败类型处理。`engine.create` 等构造事件有更特殊的失败后果，不能把普通跳过规则机械套到所有事件。

`next.signal` 表示关联操作被放弃；中断回合或上层提前返回可以影响下层等待。取消不是回滚。某次事件完成后，宿主根据结果、取消状态和模型响应决定下一步，而不是该事件最后一个 mod 自动启动下一回合。

## 3. 从前端到智能体：完整公开触发关系

### 3.1 加载与会话准备

以下显示逻辑职责与明确约束，不宣称宿主内部扫描、候选注册、准入与批量构建只有一种函数调用顺序。

```text
启动或恢复会话
├─ 指定初始化/维护模式：classic.Setup
├─ 传统会话生命周期：classic.SessionStart
├─ 指令文件真正加载：classic.InstructionsLoaded
├─ 发现并准备候选 mod 模块
│    ├─ register(on, options)：登记候选 handler
│    ├─ plugin.register：决定能否加入运行环境
│    ├─ engine.create：形成普通 hooks 使用的 $
│    └─ session.start：该 mod 加载后的初始化
└─ 描述与绘制准备（在各自需要的位置）
     ├─ tool.describe / agent.offer
     ├─ command.describe / config.describe
     └─ ui.resolve → 需要绘制时 ui.render
```

可确认的约束是：register 登记处理器；engine.create 构造普通 hooks 使用的能力；session.start 的必要初始化在首次提示词使用注册命令/工具前完成。不同插件的候选加载、热重载和内部批次未公开，不给它们编造严格全局顺序。

### 3.2 输入分流与提示词准备

```text
主提示词编辑框
├─ 用户编辑：prompt.edit
├─ 需要补全：prompt.autocomplete
├─ 程序填草稿：prompt.fill
└─ 程序提出建议：prompt.suggest

输入的处理入口
├─ /command → command.run
│    ├─ 返回文字或打开面板：可直接完成
│    └─ 需要展开为模型提示词：classic.UserPromptExpansion / skill.prompt
├─ 外部消息 → session.receive → 按会话规则排队或消费
└─ 提交任务 → prompt.submit
     ├─ drop：此次提交停止
     └─ 核心路径包含 classic.UserPromptSubmit → 接受后进入回合
```

消息保存处有 `session.append`，系统提示词与初始上下文装配处有 `prompt.section`、`prompt.compose`、`prompt.context`；文件提及、技能和提醒又各有事件。这些操作会按需要发生、缓存或重新读取，不是每次提交都从头无条件执行一遍完整清单。

### 3.3 回合与模型请求循环

```text
turn.start
    ↓
准备当前请求的上下文（相应装配事件按需要触发）
    ↓
turn.step：请求和流式响应 ◄─────────────────────────────┐
    ├─ 文字显示：classic.MessageDisplay                │
    ├─ 可扩展位置需要绘制：ui.render                    │
    ├─ API 错误结束：classic.StopFailure → 失败收尾      │
    ├─ 模型提出工具调用 → 单次工具路径（第 3.4 节）      │
    │    └─ 一批调用完成 → classic.PostToolBatch ────────┤
    └─ 模型准备结束 → classic.Stop                     │
         ├─ 要求继续 ──────────────────────────────────┘
         └─ 允许结束 → 回合收尾

收尾触发点：turn.complete；主循环指标变化处：session.measure
```

文字流展示、消息保存、UI 更新可能交错；这里不为 `turn.complete` 与测量、最终消息落盘等全部内部操作承诺精确相对顺序。用户中断走取消语义，也不能一律冒称为 API 错误的 StopFailure。

### 3.4 工具、权限与并行批次

```text
模型提出一个工具调用
    ↓
宿主校验和准备（某些无效调用可在 hooks 前直接拒绝）
    ↓
受管理的 PreToolUse hooks
    ├─ 拒绝 → 不进入 tool.call mods
    └─ 放行 → tool.call 的 mods 链
                  ├─ handler 回答 deny/result → 不进入核心工具执行
                  └─ next 进入核心
                       ├─ 其他 PreToolUse hooks 与规则、模式等权限处理
                       ├─ tool.check → 得到受政策约束的最终权限判断
                       ├─ 需要决定：PermissionRequest → 可能等待用户
                       ├─ 自动模式拒绝：PermissionDenied（条件路径）
                       └─ 获准后执行实际工具
                            ├─ 成功：PostToolUse
                            └─ 执行失败：PostToolUseFailure
    ↓
结果返回；相关消息行保存时经过 session.append
    ↓
整批调用形成结果：PostToolBatch → 下一次模型请求
```

图中传统名称在 Mods 中使用 `classic.` 前缀。工具执行还可嵌套 MCP 补充输入、子智能体或任务管理事件。权限拒绝不是执行失败；工具的每次成功通知与整批通知也不同。并行工具的逐工具事件可并发，批次完成事件发生在整批结果就绪后。

### 3.5 子智能体、团队与 MCP 子流程

```text
模型可选类型：agent.offer
    ↓（模型选择类型，或 mod 显式请求启动）
启动路径：agent.spawn
    ↓
classic.SubagentStart → 子智能体的模型请求 / 工具循环
    ↓
classic.SubagentStop
    ├─ 需要继续 → 回到子执行循环
    └─ 完成 → 按前台/后台/消息模式交回结果

团队与任务：TaskCreated / TaskCompleted / TeammateIdle 在相应操作处触发

MCP 工具运行中
    → 服务请求补充输入 → Elicitation
    → 形成响应 → ElicitationResult
    → 响应交回服务 → 原 MCP 工具继续
```

子智能体请求与工具调用用相应身份字段区分。恢复已有子智能体不等于再次创建实例；团队成员空闲不等于整个会话结束。

### 3.6 UI 与执行循环如何交错

```text
执行产生状态或内容                     界面处理（按需要）
mod 加载                         →    ui.resolve
用户消息、工作状态、回复、工具行变化 →    ui.render(component)
mod 更新计数并调用 ui.invalidate   →    失效/合并/调度 → 后续 ui.render

用户按 mod 的 Button
    → 前端报告控件身份
    → ui.press 链
    → next 到核心
    → 所属 mod 环境中的 onPress
    → 状态或其他 API 操作
    → 按需要再次绘制

mod 的 Input / Select：ui.input / ui.select → 相应回调
区域移动：ui.focus / ui.scroll → 核心移动或 handler 接管
Client：surface.post → ui.message → 可返回该实例新 props
Client 失败：ui.fault；面板关闭：ui.close
```

`ui.render` 没有固定的“在 tool.call 后执行一次”位置。普通 repaint 可复用已有结果，模型每个 token 也不等于每次调用渲染 hook。`ui.press` 对应 mod 控件，不是用户按 Enter 提交主提示词的通用前置事件。若工具 handler 等待 `$.ui.ask`，界面答案才成为推进这次工具调用的条件。

### 3.7 压缩、切换、环境与收尾

```text
需要压缩 → session.compact 包装压缩操作
              └─ 核心压缩路径：PreCompact → 压缩 → PostCompact
                   └─ 相应 SessionStart(source=compact)、指令重读按契约发生

用户/客户端请求切换 → PreModelSwitch → 应用切换 → PostModelSwitch
宿主自行恢复模型时，后置通知仍可发生，但前置请求事件不一定相同

环境变化：ConfigChange / CwdChanged / DirectoryAdded / FileChanged
隔离目录：WorktreeCreate / WorktreeRemove
会话通信：session.send / session.receive
界面连接：session.attach / session.detach

会话真正结束 → classic.SessionEnd → session.end → 相应插件/客户端清理
```

### 3.8 所有 API 事件的共同流程

```text
mod 调用 $.namespace.method(...)
    ↓
宿主按声明把参数变成事件输入（函数回调不等于可序列化数据）
    ↓
按调用来源、层级、重入和策略选取可介入的 handler
    ↓
handler 改写 / 拒绝 / 回答，或者 next 到核心 API
    ↓
结果返回该调用；原 handler 或定时回调继续
```

读取 API 不必改变状态；写入 API 不必请求模型；调用查询不是订阅通知。`$.plugin.name`、`$.plugin.root` 是身份元数据，不是可调用方法，也不列为事件。

## 4. 全部事件逐项详解

以下按用途组织。同名事件只列一次，即使既有宿主触发也有 API 入口。每条提供用途、触发条件、处理流程、输入输出、易混淆点和类型来源。字段概览是帮助阅读的索引；联合类型的字段不一定在所有分支同时存在，完整必填/可选与 schema 约束请看来源。


| 分组 | 条目数 |
|---|---|
| 加载与初始化 | 5 |
| 输入与命令 | 12 |
| 上下文与消息装配 | 8 |
| 回合与执行控制 | 7 |
| 工具与权限 | 10 |
| 智能体与任务 | 9 |
| UI 绘制与交互 | 23 |
| 会话与通信 | 23 |
| 直接模型调用 | 3 |
| 文件与工作区 | 11 |
| 进程执行 | 2 |
| 网络与 MCP | 5 |
| 配置与运行环境 | 9 |
| 状态与存储 | 6 |
| 定时器与时间 | 4 |
| 音频 | 2 |
| 遥测 | 2 |

## 4.1 加载与初始化

### `plugin.register`

**作用。** 决定 hooks 模块能否加入运行环境；用于准入策略。

**何时触发。** 宿主准备让一个模块加入处理链，包括加载与重载。

**处理流程。** 宿主收集模块身份与 uses → 已有的准入 handler 判断 → 允许则模块加入，refuse 则不加入。

**输入。** `PluginRegisterInput`。字段概览：`name`、`tier`、`root`、`version?`、`provenance`、`uses`。

**返回与效果。** `PluginRegisterResult`。可返回 refuse 阻止加入；核心允许分支按类型声明。

**易混淆点。** 不能把它当成 register 函数自身；refuse 会阻止该模块的 hooks、namespace 和工具生效。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3652)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3864)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6232)。

### `engine.create`

**作用。** 组合并建立某个 mod 能使用的能力接口 $。

**何时触发。** 该 mod 加载或重载期间，在它的普通 hooks 使用 $ 之前。

**处理流程。** 处理器拿到空的 $ → await next(e) 得到下层已构造接口 → 添加自己的 namespace 或按层级限制能力 → 返回能力接口。

**输入。** `EngineCreateInput`。字段概览：`plugins`。

**返回与效果。** `EngineCreateResult`。返回能力接口；不能把它当成普通 value/deny API 结果。

**易混淆点。** 它不创建智能体；不能覆盖另一个步骤已加入的 namespace，失败可能导致插件卸载并重建接口。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3684)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3881)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3224)。

### `classic.Setup`

**作用。** 执行一次性的初始化或维护脚本。

**何时触发。** 指定 --init、--init-only、--maintenance 等对应启动模式。

**处理流程。** 启动参数命中 → 宿主构造 Setup 输入 → 运行支持的 hooks → 继续启动或按模式退出。

**输入。** `SetupHookInput`；事件特有字段概览：`trigger`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.Setup"]`。快照映射的事件特有结果字段包括：`additionalContext`。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 不是普通每次启动都必须发生；当前文档明确它不能靠普通输出阻止启动，部分旧类型字段不代表运行时读取。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9529)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9528)。

### `classic.SessionStart`

**作用。** 在会话开始、恢复、清空或压缩等生命周期边界准备环境与上下文。

**何时触发。** 相应生命周期发生；source 区分 startup、resume、clear、compact、fork 等。

**处理流程。** 宿主建立会话上下文 → 执行匹配 SessionStart hooks → 按契约应用环境或附加上下文 → 后续模型请求使用它们。

**输入。** `SessionStartHookInput`；事件特有字段概览：`source`、`agent_type?`、`model?`、`session_title?`、`seconds_since_last_response?`、`context_tokens?`、`prompt_cache_likely_expired?`、`estimated_cache_write_usd?`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.SessionStart"]`。快照映射的事件特有结果字段包括：`additionalContext`、`initialUserMessage`、`sessionTitle`、`watchPaths`、`reloadSkills`。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 与每个 mod 加载后的 session.start 不同；后台执行不代表首个模型请求完全不等待相关上下文。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9369)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9368)。

### `classic.InstructionsLoaded`

**作用。** 观察 CLAUDE.md 或 rules 文件真正进入上下文。

**何时触发。** 启动时主动加载，或访问子目录、条件路径规则等引起延迟加载。

**处理流程。** 宿主加载指令文件 → 提供 file_path、load_reason 等事实 → 通知 hooks → 保持加载行为。

**输入。** `InstructionsLoadedHookInput`；事件特有字段概览：`file_path`、`memory_type`、`load_reason`、`globs?`、`trigger_file_path?`、`parent_file_path?`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.InstructionsLoaded"]`。没有在快照中额外列出的事件特有结果字段。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 属于观察事件；不应把直接读取任何 AGENTS.md 都算作这次通知，是否触发取决于加载路径。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L4682)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L4681)。


## 4.2 输入与命令

### `prompt.submit`

**作用。** 改写、补充或阻止将要进入回合的提示词。

**何时触发。** 输入被提交；运行中的提示词也可能在按 Enter 时先触发此事件。

**处理流程。** 宿主整理提交输入 → mods 链 → 核心执行相应 UserPromptSubmit hooks → 接受并推进，或 drop 停止。

**输入。** `PromptSubmitInput`。字段概览：`text`、`attachments?`、`context?`、`turnId?`、`wait`、`origin`。

**返回与效果。** `PromptSubmitResult`。返回 text、可选 context，或 drop 拒绝提交。

**易混淆点。** 改写 text 会改变用户消息；context 用于附加模型上下文；放行后再返回 drop 不能撤销已经开始的回合。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3383)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3771)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L7217)。

### `prompt.edit`

**作用。** 观察或处理主提示词输入框的一次编辑。

**何时触发。** 用户键入、粘贴等编辑发生时；一串键入可合并成一次编辑。

**处理流程。** 宿主提供原草稿和编辑区间 → handler 可改 inputText → 核心应用编辑 → 返回新的 text、cursor。

**输入。** `PromptEditInput`。字段概览：`origin`、`key?`、`text`、`cursor`、`start`、`end`、`inputText`。

**返回与效果。** `PromptEditResult`。text、cursor 描述输入框编辑后的状态。

**易混淆点。** 它处理主输入框；ui.input 处理 mod 画的 Input，二者不是同一事件。高频编辑 hook 的预算更短。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3419)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3783)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6870)。

### `prompt.fill`

**作用。** 让草稿填入输入框前可被检查或改写。

**何时触发。** 例如 mod 调用 $.prompt.fill，准备替换、追加或插入草稿。

**处理流程。** 提供 text 与 mode → handler 改写或拒绝 → 核心更新草稿 → 返回是否填入。

**输入。** `PromptFillInput`。字段概览：`text`、`mode`、`origin`。

**返回与效果。** `PromptFillResult`。isFilled 表示草稿是否实际填入。

**易混淆点。** 填草稿不等于提交任务；replace、append、insert 是不同编辑方式，无可用输入框时可能不填入。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3395)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3775)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6979)。

### `prompt.suggest`

**作用。** 处理输入框中可用 Tab 接受的建议文字。

**何时触发。** 宿主提出下一步建议，或 mod 调用 $.prompt.suggest。

**处理流程。** 提供建议与来源 → handler 修改文字或返回不展示 → 核心按界面状态决定是否显示。

**输入。** `PromptSuggestInput`。字段概览：`text`、`origin`。

**返回与效果。** `PromptSuggestResult`。isShown 表示建议是否实际显示。

**易混淆点。** 建议不是已提交输入；有草稿或任务进行中时核心也可能不显示。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3407)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3779)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L7316)。

### `prompt.read`

**作用。** 读取主输入框的当前草稿与光标位置。

**何时触发。** mod 调用 $.prompt.read()。

**处理流程。** 调用进入 prompt.read 链 → 核心读取当前输入框 → 返回 PromptBox。

**输入。** `NoArgs`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** handler 的结果是 `ValueOrDeny<PromptBox>`；核心 API 的值类型是 `PromptBox`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 它是读取 API，不是输入框每次变化的通知；没有输入框时返回契约规定的空状态。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5634)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5872)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5380)。

### `command.run`

**作用。** 执行内置或 mod 注册的斜杠命令。

**何时触发。** 用户运行 /name，或 mod 调用 $.command.run。

**处理流程。** 宿主解析名称和 args → 匹配 command.run handler → handler 返回输出，或 next 到内置命令实现。

**输入。** `CommandRunInput`。字段概览：`command`、`args`、`origin`、`presentation`。

**返回与效果。** `CommandRunResult`。text 可省略，例如命令只打开面板；某些版本还允许模型上下文等字段。

**易混淆点。** 命令可以只打开面板而不请求模型；执行后改写文字不会撤销已经打开的面板或触发的操作。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3493)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3808)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1483)。

### `command.describe`

**作用。** 改变命令列表中的描述、参数提示或可见性。

**何时触发。** 宿主为输入补全或帮助列表准备某个命令的展示信息时。

**处理流程。** 宿主提供命令描述 → handler 改写 → 核心得到展示条目 → 列表使用缓存结果。

**输入。** `CommandDescribeInput`。字段概览：`command`、`description`、`argumentHint?`、`isHidden`、`immediate`、`provider`。

**返回与效果。** `CommandDescribeResult`。description、argumentHint、isHidden 控制命令条目的展示。

**易混淆点。** 它不执行命令；描述缓存直到相应失效条件发生。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3505)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3812)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1380)。

### `classic.UserPromptSubmit`

**作用。** 在模型处理提示词前检查或补充提交内容。

**何时触发。** 用户提交提示词，以及当前版本规定的宿主自行启动回合。

**处理流程。** 宿主提供 prompt 等传统输入 → 执行匹配 hooks → 接受、附加上下文或阻止 → 后续回合处理。

**输入。** `UserPromptSubmitHookInput`；事件特有字段概览：`prompt`、`source?`、`session_title?`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.UserPromptSubmit"]`。快照映射的事件特有结果字段包括：`additionalContext`、`sessionTitle`、`suppressOriginalPrompt`。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** Mods prompt.submit 与它有关但不是同一个 handler；普通命令 hook 用 JSON 输出，mod 用 ClassicResultOf 对应结果。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L11516)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L11515)。

### `classic.UserPromptExpansion`

**作用。** 检查斜杠命令展开为模型提示词的内容。

**何时触发。** 用户输入的命令准备展开成提示词并发送给模型。

**处理流程。** 宿主展开命令 → 提供展开事实 → hooks 补上下文或阻止展开 → 放行文字进入后续处理。

**输入。** `UserPromptExpansionHookInput`；事件特有字段概览：`expansion_type`、`command_name`、`command_args`、`command_source?`、`prompt`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.UserPromptExpansion"]`。快照映射的事件特有结果字段包括：`additionalContext`、`suppressOriginalPrompt`。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 不是所有 command.run 都发生；只显示文本或打开面板的命令可没有模型提示词展开。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L11507)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L11506)。

### `command.list`

**作用。** 读取可用斜杠命令列表。

**何时触发。** mod 调用 $.command.list()。

**处理流程。** 进入查询事件 → 核心取得命令条目及相关描述 → 返回 CommandInfo 数组。

**输入。** `NoArgs`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** handler 的结果是 `ValueOrDeny<CommandInfo[]>`；核心 API 的值类型是 `CommandInfo[]`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 读取列表不执行命令；command.describe 处理展示描述，command.run 处理执行。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5646)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5877)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5380)。

### `command.register`

**作用。** 登记 mod 提供的斜杠命令。

**何时触发。** mod 调用 $.command.register(spec)，常在 session.start。

**处理流程。** 注册输入进入事件链 → 校验名称与声明 → 核心登记 → 返回命令标识。

**输入。** `CommandSpec`。字段概览：`name`、`description`、`argumentHint?`、`immediate?`。

**返回与效果。** handler 的结果是 `ValueOrDeny<{ command: string; }>`；核心 API 的值类型是 `{ command: string; }`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 名称冲突可被拒绝；仍需要 command.run handler 来实现命令行为。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5650)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5878)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1565)。

### `prompt.autocomplete`

**作用。** 为主提示词编辑框补充候选词。

**何时触发。** 用户输入后，光标处形成可补全的 token。

**处理流程。** 宿主提供 token → 异步取得 mod 的 suggestions → 本身补全先显示 → mod 候选补入 → 用户选中后替换相应词。

**输入。** 当前参考确认 e.token；完整 envelope 按安装声明。

**返回与效果。** { suggestions: [{ text, label, description }] }

**易混淆点。** 不是阻塞每次键入等模型回应；当前参考给出 suggestions 条目 text、label、description，完整输入以安装声明为准。

**依据。** 当前文档补充；未冒用旧 EventOf 为新版完整字段背书。 [当前 Mods reference](https://code.claude.com/docs/en/plugins/mods/reference)。


## 4.3 上下文与消息装配

### `prompt.section`

**作用。** 处理系统提示词中的一个命名部分。

**何时触发。** 宿主装配某个 section；首次计算或相应缓存失效后。

**处理流程。** 按 name 分发 → 核心计算该部分文字 → handler 观察或改写返回 text → 参与提示词装配。

**输入。** `PromptSectionInput`。字段概览：`name`、`text`。

**返回与效果。** `PromptSectionResult`。text 是该 section 的内容，null 可表示省略。

**易混淆点。** text 为 null 可省略该部分；不是每个模型请求都无条件重新计算。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3431)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3787)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L7165)。

### `prompt.context`

**作用。** 处理对话初始上下文，例如项目指令。

**何时触发。** 宿主计算首个用户消息携带的上下文，或压缩、清空、失效后重读时。

**处理流程。** 宿主整理 blocks、instructionFiles 等 → handler 增删或重排 → 核心渲染最终上下文。

**输入。** `PromptContextInput`。字段概览：`blocks`、`instructionFiles?`。

**返回与效果。** `PromptContextResult`。blocks 是最终上下文块集合。

**易混淆点。** 它不等于完整对话历史；缓存与重读条件决定是否再次触发。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3443)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3791)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6831)。

### `prompt.compose`

**作用。** 处理完整系统提示词的 section 组合。

**何时触发。** 宿主准备渲染系统提示词时。

**处理流程。** 取得核心 sections → handler 按 id 添加、替换、重排或删除 → 宿主组装并处理缓存标记。

**输入。** `PromptComposeInput`。字段概览：`model`、`promptModel`、`surfaces`、`tools`、`outputStyle`、`traits`。

**返回与效果。** `PromptComposeResult`。sections 是按发送顺序排列的系统提示词各部分。

**易混淆点。** section 的局部处理与 compose 的整体处理是两个层次；不能据名称推导所有内部函数的固定先后。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3455)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3796)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6694)。

### `prompt.attachment`

**作用。** 处理宿主自行注入给模型的提醒、模式变化或文件提示文字。

**何时触发。** 对应 attachment 需要随请求提供给模型时。

**处理流程。** 宿主提供 type 及相应事实 → handler 或核心生成 text → 请求使用结果。

**输入。** `PromptAttachmentInput`。字段概览：`type`、`text`、`origin`、`agentId?`。

**返回与效果。** `PromptAttachmentResult`。text 是该提醒或注入内容的文字，null 可表示省略。

**易混淆点。** text 为 null 可省略模型看到的文字；不等于删除宿主记录，已有结果可能缓存。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3467)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3800)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6581)。

### `skill.prompt`

**作用。** 处理展开给模型的技能提示词。

**何时触发。** 斜杠技能、Skill 工具或预加载等路径展开技能时。

**处理流程。** 找到技能并展开变量 → skill.prompt 链处理文字 → 结果进入模型上下文。

**输入。** `SkillPromptInput`。字段概览：`skill`、`text`。

**返回与效果。** `SkillPromptResult`。text 是模型实际读取的技能展开文字。

**易混淆点。** 处理的是技能内容，不是整个智能体循环；不需要把每个技能调用都解释成新回合。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3540)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3824)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9573)。

### `attribution.text`

**作用。** 处理要求模型写入提交、PR 等文本的归属说明。

**何时触发。** 宿主为相应 kind 生成归属文字时。

**处理流程。** 宿主提供用途 → 核心生成 text → handler 可替换 → 结果供后续模型或文本生成使用。

**输入。** `AttributionTextInput`。字段概览：`kind`、`text`。

**返回与效果。** `AttributionTextResult`。text 是用于相应用途的归属说明。

**易混淆点。** kind 的具体可用值随版本变化；它不等于已经提交 git commit 或发布 PR。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3551)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3828)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L489)。

### `session.append`

**作用。** 处理对话中即将保存的一行消息。

**何时触发。** 提示词、回复块、工具结果、提醒等消息行即将存入会话。

**处理流程。** 宿主提供 message、door、origin、uuid → handler 改允许的 content → 核心恢复受保护字段并保存 → 返回保存结果。

**输入。** `SessionAppendInput`。字段概览：`message`、`door`、`origin`、`uuid`、`agentId?`。

**返回与效果。** `SessionAppendResult`。返回存下来的 message 与 uuid，或相应拒绝结果；受保护部分由宿主恢复。

**易混淆点。** 可影响后续模型上下文，不能任意伪造来源、角色、标识或工具调用身份；不是整个回复结束才执行一次。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3587)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3840)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L8677)。

### `prompt.mention`

**作用。** 在读取提示词 @ 提及的文件前检查或改变路径。

**何时触发。** 宿主准备读取这种提及文件。

**处理流程。** 宿主提供 path → handler 改路径、拒绝或 next → 核心按结果读取 → 内容参与相应上下文。

**输入。** 当前参考确认 path；完整 envelope 按安装声明。

**返回与效果。** next(改写 path 的副本)，或 { deny: reason }

**易混淆点。** 当前参考标注 v2.1.290+；不等于所有 Read 工具调用或任何文件系统读取。

**依据。** 当前文档补充；未冒用旧 EventOf 为新版完整字段背书。 [当前 Mods reference](https://code.claude.com/docs/en/plugins/mods/reference)。


## 4.4 回合与执行控制

### `turn.start`

**作用。** 标记一次模型回合开始，适合建立回合级统计。

**何时触发。** 一个回合开始，在首次模型调用之前。

**处理流程。** 宿主提供 text、turnId → handler 观察并 next → 核心返回 turnId。

**输入。** `TurnStartInput`。字段概览：`text`、`turnId`。

**返回与效果。** `TurnStartResult`。核心返回 turnId；主要用于观察和关联。

**易混淆点。** 它主要是通知；返回不同值不能任意改写已建立的回合身份。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3657)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3868)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L10603)。

### `turn.step`

**作用。** 包装回合中的一次模型请求与流式响应。

**何时触发。** 宿主即将发送一次主智能体或子智能体模型请求。

**处理流程。** handler 处理请求 → yield* next(e) 转发流块 → 得到最终响应 → 返回完整结果；也可按契约自己回答。

**输入。** `TurnStepInput`。字段概览：`turnId`、`index`、`model`、`effort?`、`messageCount`、`agentId?`。

**返回与效果。** `TurnStepResult`。输出流块，最后返回该次模型请求的完整响应及相应统计。

**易混淆点。** 一个回合可有多次 step；它是 async generator。turnId、index、messageCount 等受保护；流块本身不是独立事件名。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3666)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3872)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L10658)。

### `turn.complete`

**作用。** 处理回合结束时的汇总显示。

**何时触发。** 回合已结束，到报告耗时和结果的位置，包括相应的中断原因。

**处理流程。** 宿主提供完成信息 → next 获取核心汇总 → handler 可返回用于显示的 text 与契约结果。

**输入。** `TurnCompleteInput`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** `TurnCompleteResult`。text 用于回答下方的收尾显示；不是重写 transcript 中的原答复。

**易混淆点。** 不是 Stop 的继续执行决策点；改变显示文本不等于重写已经保存的回复记录。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3675)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3876)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L10553)。

### `turn.abort`

**作用。** 请求中断一个正在执行的回合。

**何时触发。** mod 调用 $.turn.abort({ turnId })，turnId 对应当前运行回合。

**处理流程。** 调用被分发 → 核心发出取消 → 关联事件的 signal 按执行状态中止 → 相应回合收尾。

**输入。** `{ turnId: string; }`。字段概览：`turnId`。

**返回与效果。** handler 的结果是 `ValueOrDeny<void>`；核心 API 的值类型是 `void`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 取消不是回滚；已产生的文件、进程或网络副作用不会因此自动撤销。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5628)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5868)。

### `classic.PostToolBatch`

**作用。** 在整批并行工具调用完成后统一处理结果。

**何时触发。** 这一批中的所有工具调用均已形成结果，下一次模型请求之前。

**处理流程。** 宿主收集 tool_calls → 一次 PostToolBatch 分发 → hooks 添加整批上下文 → 进入下一次模型请求。

**输入。** `PostToolBatchHookInput`；事件特有字段概览：`tool_calls`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.PostToolBatch"]`。快照映射的事件特有结果字段包括：`additionalContext`。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 每个工具各有自己的 PostToolUse/Failure；批次事件不是再执行一次工具，也不是每个工具触发一次。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6376)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6375)。

### `classic.Stop`

**作用。** 在主智能体准备结束回答时决定是否继续工作。

**何时触发。** 主智能体正常准备停止响应；具体异常或用户中断路径有其他语义。

**处理流程。** 宿主提供最后回复与停止状态 → hooks 判断 → 允许则结束，block 或相应上下文要求继续则再进入模型循环。

**输入。** `StopHookInput`；事件特有字段概览：`stop_hook_active`、`last_assistant_message?`、`background_tasks?`、`session_crons?`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.Stop"]`。快照映射的事件特有结果字段包括：`additionalContext`。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 它是可要求继续的停止决策点；注意 stop_hook_active 等避免重复要求继续，不能等同 turn.complete。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9664)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9663)。

### `classic.StopFailure`

**作用。** 观察由 API 错误引起的回合结束。

**何时触发。** 请求错误导致回合按相应失败原因结束。

**处理流程。** 宿主整理失败信息 → 调用匹配 hooks → 按失败路径收尾。

**输入。** `StopFailureHookInput`；事件特有字段概览：`error`、`error_details?`、`last_assistant_message?`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.StopFailure"]`。没有在快照中额外列出的事件特有结果字段。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 不同于正常 Stop；当前文档规定其通常不使用一般决策输出来恢复或阻止已发生的失败。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9657)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9656)。


## 4.5 工具与权限

### `tool.call`

**作用。** 包装一次工具调用，可观察、改参数、拒绝、替代执行或处理结果。

**何时触发。** 宿主准备执行模型工具，或相应 API 发起工具调用。

**处理流程。** 受管理 PreToolUse 可先拒绝 → tool.call mods 链 → 核心权限路径 → 获准后工具执行 → 结果逐层返回。

**输入。** `ToolCallInput`。字段概览：`tool`、`tool_use_id?`、`agentId?`、`各工具参数，例如 Bash.command、Read.file_path`。

**返回与效果。** `ToolCallResult`。拒绝分支使用 deny；成功分支包含 result，具体结构随工具变化；执行错误有 isError 等字段。

**易混淆点。** 工具参数在 e 顶层；返回 deny 若在执行后发生，只遮蔽结果，不撤销工具已做的事。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3264)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3720)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L10012)。

### `tool.check`

**作用。** 参与工具是否允许运行的权限决定。

**何时触发。** 权限处理形成基础判断后、询问用户等后续处理前；API 也可仅检查而不执行工具。

**处理流程。** 宿主准备工具与 input → next 获取基础 decision → handler 返回 allow、ask 或 deny → 宿主按约束处理决定。

**输入。** `ToolCheckInput`。字段概览：`tool`、`input`、`tool_use_id?`。

**返回与效果。** `ToolCheckResult`。decision 为 allow、ask 或 deny，可带 reason 等；这不是工具执行结果。

**易混淆点。** 它不能代替 tool.call 改工具请求；组织政策仍有约束。当前 agentId、ceiling 字段有版本要求。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3276)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3724)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L10139)。

### `tool.describe`

**作用。** 处理模型将要看到的工具描述和延迟加载属性。

**何时触发。** 工具描述首次准备；当前 MCP 工具经 ToolSearch 加载时可再次触发。

**处理流程。** 宿主提供描述 → handler 改 description 或延迟属性 → 描述与 schema 供模型使用并按条件缓存。

**输入。** `ToolDescribeInput`。字段概览：`tool`、`description`、`isDeferred?`、`provider`。

**返回与效果。** `ToolDescribeResult`。返回 description，按版本可包含 isDeferred。

**易混淆点。** 它不执行工具；isDeferred 控制工具是否放到搜索后再加载，含义不是禁止使用。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3481)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3804)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L10214)。

### `classic.PreToolUse`

**作用。** 工具执行前检查、更新输入或给出权限相关决定。

**何时触发。** 对应客户端工具调用尚未实际执行时。

**处理流程。** 受管理 hooks 可先拒绝 → 相关 mods/classic 链与其他 settings hooks 处理 → 宿主应用决策与 updatedInput → 后续权限或执行。

**输入。** `ToolCallEnvelope`；事件特有字段概览：`tool`、`tool_use_id?`、`具体工具参数`。

**返回与效果。** `PreToolUseResult`。快照映射的事件特有结果字段包括：`decision`、`reason?`、`updatedInput?`、`additionalContext?`。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** classic.PreToolUse 在固定 Mods 类型中使用扁平 ToolCallEnvelope；并非直接照搬传统 stdin 的 tool_input 嵌套。无效调用可能在 hook 前被校验拒绝。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6506)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L10002)。

### `classic.PermissionRequest`

**作用。** 在即将需要用户权限决定时由 hook 给出决定。

**何时触发。** 宿主准备请求权限，或在无法显示权限界面的路径中需要同类判断。

**处理流程。** 准备工具及请求信息 → 匹配 hooks → 若有有效决定则应用，否则进入通常的询问或拒绝路径。

**输入。** `PermissionRequestHookInput`；事件特有字段概览：`tool_name`、`tool_input`、`permission_suggestions?`、`mcp_server?`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.PermissionRequest"]`。快照映射的事件特有结果字段包括：`decision`。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 不是每个工具调用都触发；与每次执行前的 PreToolUse、Mods tool.check 各有不同触发条件。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6122)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6121)。

### `classic.PermissionDenied`

**作用。** 观察自动模式拒绝，并在支持情形提示可重试。

**何时触发。** 自动权限模式拒绝工具调用，含无分类器结论的某些拒绝。

**处理流程。** 拒绝形成 → 分发拒绝事实 → 读取契约允许的 retry → 将拒绝或可重试信息交回执行循环。

**输入。** `PermissionDeniedHookInput`；事件特有字段概览：`tool_name`、`tool_input`、`tool_use_id`、`reason`、`mcp_server?`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.PermissionDenied"]`。快照映射的事件特有结果字段包括：`retry`。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 不是所有失败的统称；retry 不等于直接授权，且无分类器结论时不一定生效。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6094)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6093)。

### `classic.PostToolUse`

**作用。** 处理已经成功执行的工具结果并补充上下文。

**何时触发。** 对应工具成功完成。

**处理流程。** 执行产生 tool_response → hooks 观察或按契约处理输出 → 附加内容进入下一次模型请求上下文。

**输入。** `PostToolUseHookInput`；事件特有字段概览：`tool_name`、`tool_input`、`tool_response`、`tool_use_id`、`duration_ms?`、`mcp_server?`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.PostToolUse"]`。快照映射的事件特有结果字段包括：`additionalContext`、`updatedToolOutput`、`updatedMCPToolOutput`。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 此时副作用已经发生，阻止或改输出不会撤销文件写入；并行工具的该事件也可并发发生。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6402)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6401)。

### `classic.PostToolUseFailure`

**作用。** 处理已经尝试执行但失败的工具调用。

**何时触发。** 实际执行产生错误，而不是执行前的权限拒绝或参数校验拒绝。

**处理流程。** 宿主整理 error、工具参数等 → hooks 记录或补充恢复建议 → 错误信息进入执行循环。

**输入。** `PostToolUseFailureHookInput`；事件特有字段概览：`tool_name`、`tool_input`、`tool_use_id`、`error`、`is_interrupt?`、`duration_ms?`、`mcp_server?`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.PostToolUseFailure"]`。快照映射的事件特有结果字段包括：`additionalContext`。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 不能把所有 deny 分支都画到这里；某些事件结果字段按版本读取，类型允许也不代表都能改变失败事实。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6388)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6387)。

### `tool.list`

**作用。** 读取宿主当前提供的工具列表。

**何时触发。** mod 调用 $.tool.list()。

**处理流程。** 进入事件链 → 核心收集工具条目 → 策略或 handler 可按契约组合结果 → 返回 ToolInfo 数组。

**输入。** `NoArgs`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** handler 的结果是 `ValueOrDeny<ToolInfo[]>`；核心 API 的值类型是 `ToolInfo[]`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 列表与模型已经缓存的描述不一定同时变化；列表查询不是工具执行。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5638)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5873)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5380)。

### `tool.register`

**作用。** 把 mod 提供的工具名称、描述和输入 schema 加入工具目录。

**何时触发。** mod 初始化等位置调用 $.tool.register(spec)。

**处理流程。** 参数进入注册事件 → 准入和名称校验 → 核心登记工具 → 返回最终工具名。

**输入。** `Required<ToolSpec>`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** handler 的结果是 `ValueOrDeny<{ tool: string; }>`；核心 API 的值类型是 `{ tool: string; }`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 登记不提供完整执行实现；通常还需要对应 tool.call handler。模型看到的名字常带插件前缀。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5642)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5874)。


## 4.6 智能体与任务

### `agent.offer`

**作用。** 决定某个子智能体类型是否向模型提供。

**何时触发。** 类型出现在模型可选列表，以及模型选择该类型后的派发检查。

**处理流程。** 宿主提供 agent 类型 → handler 返回 isOffered → 核心决定提供或拒绝该类型。

**输入。** `AgentOfferInput`。字段概览：`agent`、`description`、`source`、`provider`。

**返回与效果。** `AgentOfferResult`。isOffered 表示是否向模型提供该类型。

**易混淆点。** 不是每个 token 的决策通知；mod 自己调用 $.agent.spawn 不走同样的模型类型 offer 路径。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3365)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3763)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L184)。

### `agent.spawn`

**作用。** 处理子智能体或团队成员开始前的启动参数。

**何时触发。** 宿主准备启动相应智能体，参数确定而模型尚待解析时。

**处理流程。** 宿主提供启动事实 → handler 可调整 model 或拒绝 → 核心建立子执行环境 → 子智能体开始。

**输入。** `AgentSpawnInput`。字段概览：`tool_use_id`、`prompt`、`description`、`subagentType`、`provider`、`model?`、`parentModel`、`parentAgentId?`、`permissionMode?`、`background`、`fork`、`name?`、`cwd?`。

**返回与效果。** `AgentSpawnResult`。返回 model，或 deny；子智能体最终任务结果不是这一步模型选择结果。

**易混淆点。** 恢复现有子智能体不一定再次 spawn；当前文档中的团队字段与旧快照可能不同。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3374)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3767)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L231)。

### `classic.SubagentStart`

**作用。** 在子智能体启动时提供观察与附加上下文。

**何时触发。** 子智能体被启动，输入包含相应智能体标识。

**处理流程。** 宿主建立子运行环境 → SubagentStart hooks 提供上下文 → 子智能体执行请求与工具循环。

**输入。** `SubagentStartHookInput`；事件特有字段概览：`agent_id`、`agent_type`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.SubagentStart"]`。快照映射的事件特有结果字段包括：`additionalContext`。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 它与 agent.spawn 的启动参数拦截不同；子智能体工具事件使用身份字段区分来源。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9783)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9782)。

### `classic.SubagentStop`

**作用。** 决定子智能体准备结束时是否需要继续。

**何时触发。** 子智能体准备完成响应。

**处理流程。** 宿主提供子智能体完成信息 → hooks 判断 → block 或附加反馈可让子智能体继续，否则完成并按调用方式交回结果。

**输入。** `SubagentStopHookInput`；事件特有字段概览：`stop_hook_active`、`agent_id`、`agent_transcript_path`、`agent_type`、`last_assistant_message?`、`background_tasks?`、`session_crons?`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.SubagentStop"]`。快照映射的事件特有结果字段包括：`additionalContext`。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 不必触发主智能体的普通 Stop；不同版本的附加字段与后台模式需核对。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9789)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9788)。

### `classic.TeammateIdle`

**作用。** 在团队成员准备空闲时执行团队质量或任务检查。

**何时触发。** 相应 teammate 将进入 idle 状态。

**处理流程。** 宿主提供成员和团队信息 → 匹配 hooks → 按事件决定允许空闲或提供继续工作的反馈。

**输入。** `TeammateIdleHookInput`；事件特有字段概览：`teammate_name`、`team_name`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.TeammateIdle"]`。没有在快照中额外列出的事件特有结果字段。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 团队成员空闲不是整个会话结束；不要把 pending、waiting、idle 都混成 completed。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9884)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9883)。

### `classic.TaskCreated`

**作用。** 在任务管理工具创建任务时检查相关任务事实。

**何时触发。** TaskCreate 准备创建任务。

**处理流程。** 宿主整理任务输入 → hooks 判断或观察 → 按有效决策继续创建或阻止 → 工具返回结果。

**输入。** `TaskCreatedHookInput`；事件特有字段概览：`task_id`、`task_subject`、`task_description?`、`teammate_name?`、`team_name?`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.TaskCreated"]`。没有在快照中额外列出的事件特有结果字段。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 是任务管理事件，不是每条用户提示词的 turn.start；适用输出以该事件契约为准。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9872)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9871)。

### `classic.TaskCompleted`

**作用。** 在任务将标记完成时检查完成条件。

**何时触发。** 任务操作或团队相关路径准备完成某项任务。

**处理流程。** 宿主提供任务与可能的智能体信息 → hooks 检查 → 允许则标记完成，阻止则反馈到相应执行路径。

**输入。** `TaskCompletedHookInput`；事件特有字段概览：`task_id`、`task_subject`、`task_description?`、`teammate_name?`、`team_name?`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.TaskCompleted"]`。没有在快照中额外列出的事件特有结果字段。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 工具 TaskUpdate 与团队成员结束时，对 continue 等字段的读取不一定相同。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9860)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9859)。

### `agent.list`

**作用。** 查询当前会话中的子智能体或团队成员。

**何时触发。** mod 调用 $.agent.list()。

**处理流程。** 进入事件链 → 核心读取智能体记录 → 返回 AgentInfo 数组。

**输入。** `NoArgs`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** handler 的结果是 `ValueOrDeny<AgentInfo[]>`；核心 API 的值类型是 `AgentInfo[]`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 不是可选类型目录 agent.offer，也不表示列表中每个条目正在运行；状态值有版本差异。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5658)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5882)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5380)。

### `agent.register`

**作用。** 登记 mod 提供的智能体类型定义。

**何时触发。** mod 调用 $.agent.register(spec)。

**处理流程。** 定义进入注册事件 → 校验并登记类型 → 返回类型标识 → 后续模型 offer 或显式 spawn 使用它。

**输入。** `AgentSpec`。字段概览：`name`、`description`、`prompt`、`tools?`、`disallowedTools?`、`model?`、`effort?`、`permissionMode?`、`mcpServers?`、`hooks?`、`maxTurns?`、`skills?`、`initialPrompt?`、`memory?`。

**返回与效果。** handler 的结果是 `ValueOrDeny<{ agent: string; }>`；核心 API 的值类型是 `{ agent: string; }`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 登记类型不等于启动实例；实例由 agent.spawn 等路径建立。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5663)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5883)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L354)。


## 4.7 UI 绘制与交互

### `ui.resolve`

**作用。** 准备某个界面环境中可构造的元素表。

**何时触发。** mod 加载时，按 surface、component 和 mod 准备表。

**处理流程。** 宿主或下层提供 ElementTable → handler 返回组合后的表 → ui.render 中的 $.ui.resolve(e) 读取准备好的构造器。

**输入。** `ResolveInput`。字段概览：`surface`、`component`。

**返回与效果。** `ElementTable`。返回当前 surface 的元素构造器表，不是已经绘制的界面。

**易混淆点。** 不是每次 repaint 都重跑；读取元素表与初始表构造是两个动作。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3294)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3733)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L8476)。

### `ui.render`

**作用。** 生成某个可扩展绘制位置的元素树。

**何时触发。** 首次需要绘制、相关 props 或视口变化、插件变化或指定失效后。

**处理流程。** 宿主提供 surface、component、requestId、props → handler 返回或包装下层树 → 宿主校验 → 相应界面绘制。

**输入。** `RenderInput`。字段概览：`surface`、`component`、`requestId`、`viewport?`、`props（随 component 变化）`。

**返回与效果。** `RenderElement`。返回描述界面的元素树，或保留下层核心绘制引用；不是 DOM 节点或图片文件。

**易混淆点。** 普通 repaint 可复用缓存，不等于每个 token 都触发。无效树会按宿主契约回退。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3285)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3728)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L7811)。

### `ui.press`

**作用。** 处理 mod 绘制控件的一次按下操作。

**何时触发。** 用户激活对应 Button 等可按控件。

**处理流程。** 前端报告控件标识 → ui.press handler 链 → next 到核心 → 在所属 mod 环境执行 onPress → 返回结果。

**输入。** `UiPressArgument`。字段概览：`plugin`、`element`、`component`、`requestId`、`surface`、`link?`。

**返回与效果。** `UiPressResult`。结果标识被处理的 element；并不天然包含新的模型回复。

**易混淆点。** 点击不必启动模型回合；handler 接管时，原 onPress 不一定执行。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3303)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3737)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L11147)。

### `ui.input`

**作用。** 处理 mod 绘制 Input 的改变或提交。

**何时触发。** 对应 Input 产生 change 或 submit。

**处理流程。** 前端报告 element、kind、value → handler 可改 value → 核心调用 onInput 或 onSubmit → 返回处理结果。

**输入。** `UiInputArgument`。字段概览：`plugin`、`element`、`component`、`requestId`、`surface`、`kind`、`value`。

**返回与效果。** `UiInputResult`。结果包含 element 与最终处理的 value。

**易混淆点。** 主提示词输入框使用 prompt.edit；把两个输入路径混在一起会误判触发位置。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3312)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3742)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L10980)。

### `ui.select`

**作用。** 处理 mod 绘制 Select 的选项变化。

**何时触发。** 用户选择对应控件的某个值。

**处理流程。** 前端报告 value → handler 改写或接管 → 核心调用该控件 onSelect → 返回选中结果。

**输入。** `UiSelectArgument`。字段概览：`plugin`、`element`、`component`、`requestId`、`surface`、`value`。

**返回与效果。** `UiSelectResult`。结果包含 element 与最终选中的 value。

**易混淆点。** 选项值与显示文字不必相同；结果不自动成为新模型输入。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3321)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3747)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L11389)。

### `ui.message`

**作用。** 让 Client 组件向所属 mod 发送数据。

**何时触发。** 该 Client 调用 surface.post(data)。

**处理流程。** 前端 Client 发数据 → 宿主路由到所属 mod → handler 处理 → 可返回 props 更新该实例。

**输入。** `UiMessageArgument`。字段概览：`surface`、`component`、`requestId`、`element`、`module`、`data`。

**返回与效果。** `UiMessageResult`。可返回 props，交给发消息的 Client 实例作为下一份属性。

**易混淆点。** 不是任意插件间广播；data 来自界面代码，返回 props 可以不经整次重绘更新实例。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3330)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3751)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L11061)。

### `ui.focus`

**作用。** 在焦点即将移动时处理目标控件。

**何时触发。** 用户 Tab、方向键、点击、autoFocus 或 $.ui.focus 导致相应区域焦点变化。

**处理流程。** 宿主构造目标 → handler 可改 element 或拒绝 → 核心移动焦点并绘制。

**输入。** `UiFocusInput`。字段概览：`component`、`requestId`、`plugin?`、`element?`、`origin`。

**返回与效果。** `UiFocusResult`。移动完成的结果，或 deny；拒绝时不按正常路径移动焦点。

**易混淆点。** 仅适用于相应 Pane 或 AbovePrompt 等受支持位置；省略目标与指定插件控件不同。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3354)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3759)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L10902)。

### `ui.scroll`

**作用。** 在相应区域即将滚动时处理滚动位置。

**何时触发。** 用户滚轮、滚动键或 $.ui.scroll 请求发生时。

**处理流程。** 宿主提供 offset、by、区域高度 → handler 可改 offset 或接管 → 核心移动并绘制。

**输入。** `UiScrollInput`。字段概览：`component`、`requestId`、`offset`、`by`、`bodyRows`、`contentRows`、`origin`、`pointer?`。

**返回与效果。** `UiScrollResult`。移动完成的结果，或 deny；自绘列表可以接管并自己安排更新。

**易混淆点。** 自绘虚拟列表可能自己更新行与失效；它不等于模型执行步骤。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3342)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3755)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L11250)。

### `classic.Notification`

**作用。** 观察宿主准备发出的通知。

**何时触发。** 权限、等待输入或其他支持的通知类型产生时。

**处理流程。** 宿主形成通知内容与类型 → 匹配 hooks → 进行相应观察或外部提示 → 宿主继续通知流程。

**输入。** `NotificationHookInput`；事件特有字段概览：`message`、`title?`、`notification_type`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.Notification"]`。没有在快照中额外列出的事件特有结果字段。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 不是每次屏幕绘制都会发生；它也不等于 mod 调用 ui.toast。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5408)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5407)。

### `classic.MessageDisplay`

**作用。** 处理助手消息显示层的文本。

**何时触发。** 助手文字显示或流式显示更新时。

**处理流程。** 宿主提供待显示文字 → hooks 按契约返回 displayContent → 前端使用显示内容。

**输入。** `MessageDisplayHookInput`；事件特有字段概览：`turn_id`、`message_id`、`index`、`final`、`delta`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.MessageDisplay"]`。快照映射的事件特有结果字段包括：`displayContent`。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 显示改写不等于改模型上下文或 transcript；不能与 prompt.section 或 session.append 的内容作用混淆。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5083)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5082)。

### `ui.toast`

**作用。** 显示一条暂时性的界面提示。

**何时触发。** mod 调用 $.ui.toast(text, options)。

**处理流程。** text、timeout 等进入 UI API 事件 → 核心安排 toast → 相应界面展示并按超时消失。

**输入。** `{ text: string; timeoutMs?: number; }`。字段概览：`text`、`timeoutMs?`。

**返回与效果。** handler 的结果是 `ValueOrDeny<void>`；核心 API 的值类型是 `void`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 通常不进入模型上下文，也不启动回合；它与 classic.Notification 是不同入口。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5667)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5886)。

### `ui.status`

**作用。** 设置或清空 mod 的状态文字。

**何时触发。** mod 调用 $.ui.status(text)。

**处理流程。** 提供 text → 事件链 → 核心更新状态 → 界面按需要绘制。

**输入。** `{ text: string | undefined; }`。字段概览：`text`。

**返回与效果。** handler 的结果是 `ValueOrDeny<void>`；核心 API 的值类型是 `void`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** undefined 清空；状态文字不是工具结果，不必供模型读取。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5674)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5887)。

### `ui.log`

**作用。** 写入 mod 的显示日志或调试日志。

**何时触发。** mod 调用 $.ui.log(text, options)。

**处理流程。** text 和归一化 to 进入链 → handler 可改目标 → 核心将日志送到相应位置。

**输入。** `{ text: string; to: UiLogSink; }`。字段概览：`text`、`to`。

**返回与效果。** handler 的结果是 `ValueOrDeny<void>`；核心 API 的值类型是 `void`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 日志不等于对话消息；改成 debug 可不显示在用户 transcript 区域。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5681)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5888)。

### `ui.notice`

**作用。** 更新工具相关对话框下的说明文字。

**何时触发。** mod 调用 $.ui.notice(tool_use_id, text)。

**处理流程。** 提供调用标识和文字 → 事件链 → 核心更新对应说明 → 界面绘制。

**输入。** `{ tool_use_id: string; text: string | undefined; }`。字段概览：`tool_use_id`、`text`。

**返回与效果。** handler 的结果是 `ValueOrDeny<void>`；核心 API 的值类型是 `void`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** undefined 可清空；需要对应的交互位置，不是任意创建一条模型消息。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5688)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5889)。

### `ui.invalidate`

**作用。** 请求某个可失效结果重新计算。

**何时触发。** mod 调用 $.ui.invalidate(event)。

**处理流程。** 失效请求进入链 → 核心标记缓存或绘制结果失效 → 后续安排相应事件重新计算。

**输入。** `{ event: InvalidatableEventName; }`。字段概览：`event`。

**返回与效果。** handler 的结果是 `ValueOrDeny<void>`；核心 API 的值类型是 `void`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 不是同步执行 ui.render；相近请求会合并。它也可用于支持的 prompt 或 describe 缓存，而非只用于 UI。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5695)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5890)。

### `ui.open`

**作用。** 请求打开 mod 的面板。

**何时触发。** mod 调用 $.ui.open(pane)。

**处理流程。** pane 参数进入链 → 可被重命名显示标题或拒绝 → 核心打开 → Pane 需要绘制时进入 ui.render。

**输入。** `PaneOpenArgs`。字段概览：`id`、`title?`、`focus?`、`closeOnEscape?`、`holdToasts?`、`rows?`、`columns?`。

**返回与效果。** handler 的结果是 `ValueOrDeny<void>`；核心 API 的值类型是 `void`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 面板 id 是身份，不能随意被 handler 改成另一个；打开面板不等于启动智能体回合。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5702)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5891)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6006)。

### `ui.close`

**作用。** 处理面板即将关闭。

**何时触发。** 用户关闭、mod 调用 $.ui.close，或卸载引起关闭。

**处理流程。** 宿主提供 id 与 origin → 对应 handler 链 → 核心完成相应关闭。

**输入。** `PaneCloseInput`。字段概览：`id`、`origin`。

**返回与效果。** handler 的结果是 `ValueOrDeny<void>`；核心 API 的值类型是 `void`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 它既是 API 调用入口又有宿主触发来源；不要重复列成两个不同事件。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5707)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5892)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5971)。

### `ui.panes`

**作用。** 查询本 mod 已打开的面板。

**何时触发。** mod 调用 $.ui.panes()。

**处理流程。** 进入查询事件 → 核心读取面板记录 → 返回 UiPane 列表。

**输入。** `NoArgs`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** handler 的结果是 `ValueOrDeny<readonly UiPane[]>`；核心 API 的值类型是 `readonly UiPane[]`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 这是 mod 自己的面板查询，不是所有插件面板的任意控制权。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5711)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5896)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5380)。

### `ui.blit`

**作用。** 对支持的 Raster 或 Image 实例更新局部绘制数据。

**何时触发。** mod 调用 $.ui.blit(args)。

**处理流程。** 提供目标及 cells 或 source → handler 按契约处理 → 核心更新对应绘制对象 → 返回 UiBlitResult。

**输入。** `UiBlitArgs`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** handler 的结果是 `ValueOrDeny<UiBlitResult>`；核心 API 的值类型是 `UiBlitResult`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 它是特定绘制更新能力，不是每次整棵 ui.render 元素树重新计算。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5716)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5897)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L10850)。

### `ui.fault`

**作用。** 报告 Client 组件加载、绘制或运行失败。

**何时触发。** Client 在相应 phase 失败。

**处理流程。** 前端或宿主形成 phase 与 reason → 分发到相关 mod → handler 记录或按能力做后续处理。

**输入。** 当前参考确认 phase、reason，及 Client 相关身份。

**返回与效果。** 当前参考未给完整返回类型；不要据观察用途猜测结果字段。

**易混淆点。** 当前参考标注 v2.1.289+；完整返回型未在本次固定快照中取得，不能假定返回一个值即可让失败组件重试。

**依据。** 当前文档补充；未冒用旧 EventOf 为新版完整字段背书。 [当前 Mods reference](https://code.claude.com/docs/en/plugins/mods/reference)。

### `ui.ask`

**作用。** 让 mod 请求用户选择并等待答案。

**何时触发。** mod 调用 $.ui.ask(question, options)。

**处理流程。** 请求进入宿主 → 按 UI API 事件规则处理 → 显示问题 → 等待选择或文字 → Promise 返回答案，原 handler 继续。

**输入。** 可确认 API 调用形式为 question 与 options；完整事件 envelope 未在旧 OpEventOf 中声明。

**返回与效果。** API Promise 返回用户选择/文字；拦截结果封装以安装声明为准。

**易混淆点。** Core API 在旧快照中已存在，但没有对应 OpEventOf 条目；这次列的是当前参考补充的事件映射。关闭或无交互环境可能拒绝 Promise。

**依据。** 当前文档补充；未冒用旧 EventOf 为新版完整字段背书。 [当前 Mods reference](https://code.claude.com/docs/en/plugins/mods/reference)。

### `ui.copy`

**作用。** 让 mod 请求复制内容。

**何时触发。** mod 调用当前版本支持的 $.ui.copy。

**处理流程。** 复制请求进入 UI API 分发 → 可介入的 handler 处理 → 核心执行支持的复制操作 → 返回调用者。

**输入。** 当前参考只枚举方法；完整事件输入需安装声明。

**返回与效果。** 当前参考未给完整返回类型。

**易混淆点。** 当前参考只枚举方法；本次没有该版本完整参数与返回声明，不编造 e 的字段或平台行为。

**依据。** 当前文档补充；未冒用旧 EventOf 为新版完整字段背书。 [当前 Mods reference](https://code.claude.com/docs/en/plugins/mods/reference)。

### `ui.selection`

**作用。** 让 mod 查询界面中当前可用的选择内容。

**何时触发。** mod 调用当前版本支持的 $.ui.selection。

**处理流程。** 查询进入 UI API 分发 → 核心读取支持的选择状态 → 返回该版本规定的结果。

**输入。** 当前参考只枚举方法；完整事件输入需安装声明。

**返回与效果。** 当前参考未给完整返回类型。

**易混淆点。** 它是主动查询，不是用户每次选中文字都必然发生的广播；精确参数、空值结构待目标版本类型确认。

**依据。** 当前文档补充；未冒用旧 EventOf 为新版完整字段背书。 [当前 Mods reference](https://code.claude.com/docs/en/plugins/mods/reference)。


## 4.8 会话与通信

### `session.start`

**作用。** 执行 mod 加载后的初始化，例如登记命令和工具。

**何时触发。** 每个 mod 首次加载后，以及该 mod 的重新加载后。

**处理流程。** 宿主提供加载信息 → handler 初始化 → next(e) 取得核心结果；首个提示词等待必要初始化完成。

**输入。** `SessionStartInput`。字段概览：`cwd`、`surface`、`isInteractive`。

**返回与效果。** `SessionStartResult`。核心返回 cwd；它不是新回合的 turnId。

**易混淆点。** 与 classic.SessionStart 不同；当前文档明确 /clear、/resume、/branch 不按 mod 重载再次触发它。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3563)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3832)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9396)。

### `session.receive`

**作用。** 处理外部送到会话的消息，决定排队或消费。

**何时触发。** 中继、其他会话或远程入口的消息送达并尚未排队。

**处理流程。** 宿主提供来源与正文 → handler 改 text 或返回 consumed → 放行内容排队、记录并按会话规则处理。

**输入。** `SessionReceiveInput`。字段概览：`origin`、`text`、`event?`。

**返回与效果。** `SessionReceiveResult`。放行返回 text；consumed 分支表示消息被消费，不再进入通常的队列路径。

**易混淆点。** 收到不等于立即开始模型回合；consumed 表示不再进入通常的排队与模型路径。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3575)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3836)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9257)。

### `session.compact`

**作用。** 包装会话上下文压缩。

**何时触发。** 手动 /compact、阈值、mod 请求或预计算压缩。

**处理流程。** 宿主提供 trigger、messages 等 → handler 可改输入 → 核心压缩 → handler 处理结果；skip 可保留原上下文。

**输入。** `SessionCompactInput`。字段概览：`trigger`、`agentId?`、`instructions?`、`messages`。

**返回与效果。** `SessionCompactResult`。返回 messages 及可选压缩统计，或 skip；预计算不一定立刻安装压缩结果。

**易混淆点。** 它和 classic.PreCompact/PostCompact 的通知层不同；不是普通的模型回复。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3599)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3844)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L8849)。

### `session.attach`

**作用。** 观察界面客户端加入会话。

**何时触发。** 客户端显式连接，或首次请求绘制而进入 attached roster。

**处理流程。** 宿主登记客户端 → 分发连接信息 → handler 观察 → 核心返回 clientId。

**输入。** `SessionAttachInput`。字段概览：`surface`、`clientId`、`viewport?`。

**返回与效果。** `SessionAttachResult`。核心回显 clientId，用于观察连接。

**易混淆点。** 主要是连接通知；修改返回值不等于伪造客户端。实际渲染仍看每次 e.surface。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3611)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3848)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L8583)。

### `session.detach`

**作用。** 观察界面客户端离开会话。

**何时触发。** 客户端断开，或会话结束而解除已有连接。

**处理流程。** 宿主准备解除记录 → handler 观察 reason → 核心返回 clientId 并完成相应收尾。

**输入。** `SessionDetachInput`。字段概览：`surface`、`clientId`、`reason`。

**返回与效果。** `SessionDetachResult`。核心回显 clientId，用于观察断开。

**易混淆点。** 客户端离开不必等同智能体回合结束。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3616)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3852)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9057)。

### `session.measure`

**作用。** 接收上下文、限额或成本指标变化。

**何时触发。** 主线程回合结束后，或相关限额指标改变到契约规定粒度时。

**处理流程。** 宿主测量并提供 changed、context、rateLimits、cost → handler 观察阈值 → next 返回测量结果。

**输入。** `SessionMeasureInput`。字段概览：`context`、`rateLimits`、`cost?`、`changed`。

**返回与效果。** `SessionMeasureResult`。核心回显 changed；测量事实不是 handler 任意改写的业务配置。

**易混淆点。** 它是推送通知，session.usage 是主动查询；缺失指标不是零，连续变化可合并。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3628)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3856)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9140)。

### `session.end`

**作用。** 执行 mod 的会话结束清理。

**何时触发。** 退出、clear、resume、logout、信号或相应运行结束。

**处理流程。** 传统 SessionEnd hooks 完成 → session.end 链 → mod 清理 → 宿主插件结束步骤与客户端收尾。

**输入。** `SessionEndInput`。字段概览：`reason`、`sessionId`、`resume`。

**返回与效果。** `SessionEndResult`。核心返回 sessionId；主要用于清理收尾。

**易混淆点。** 每次 turn.complete 不等于 session.end；强制终止不保证任何清理事件发生。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3640)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3860)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9097)。

### `classic.PreCompact`

**作用。** 在上下文压缩前执行记录或观察。

**何时触发。** 自动或手动压缩将开始。

**处理流程。** 宿主确定压缩触发原因 → 分发 PreCompact → 运行相应 hooks → 继续压缩核心路径。

**输入。** `PreCompactHookInput`；事件特有字段概览：`trigger`、`custom_instructions`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.PreCompact"]`。没有在快照中额外列出的事件特有结果字段。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 普通传统 hook 的输出不能等同 Mods session.compact 的 skip 或替换 messages 能力。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6415)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6414)。

### `classic.PostCompact`

**作用。** 观察已经完成的上下文压缩。

**何时触发。** 压缩完成，宿主具备压缩结果和相关信息时。

**处理流程。** 核心压缩完成 → 分发结果事实 → hooks 记录或做后续操作 → 按生命周期继续。

**输入。** `PostCompactHookInput`；事件特有字段概览：`trigger`、`compact_summary`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.PostCompact"]`。没有在快照中额外列出的事件特有结果字段。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 不能把执行后事件画成压缩前控制点；已有压缩结果不因普通观察输出自动撤销。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6326)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6325)。

### `classic.SessionEnd`

**作用。** 运行传统的会话结束处理。

**何时触发。** 会话终止或相应 clear、resume、退出等结束边界。

**处理流程。** 宿主确定 reason → 执行 SessionEnd hooks → 再进入 Mods session.end 的插件清理。

**输入。** `SessionEndHookInput`；事件特有字段概览：`reason`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.SessionEnd"]`。没有在快照中额外列出的事件特有结果字段。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 与 Stop/turn.complete 不同；无法把会话强杀解释为必定有清理通知。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9087)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9086)。

### `session.cwd`

**作用。** 查询当前操作上下文的工作目录。

**何时触发。** mod 调用 $.session.cwd()。

**处理流程。** 无参数调用进入 session.cwd 链 → 核心读取目录 → 返回字符串。

**输入。** `NoArgs`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** handler 的结果是 `ValueOrDeny<string>`；核心 API 的值类型是 `string`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 读取不是改变工作目录；不会因为查询本身就触发 classic.CwdChanged。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5578)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5849)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5380)。

### `session.root`

**作用。** 查询会话的根工作目录。

**何时触发。** mod 调用 $.session.root()。

**处理流程。** 进入 session.root 链 → 核心读取会话根 → 返回路径。

**输入。** `NoArgs`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** handler 的结果是 `ValueOrDeny<string>`；核心 API 的值类型是 `string`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 根目录与执行中变化的 cwd 不一定相同，路径相对解释要看具体 API 的上下文。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5582)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5850)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5380)。

### `session.model`

**作用。** 查询主执行循环当前模型。

**何时触发。** mod 调用 $.session.model()。

**处理流程。** 查询进入事件链 → 核心读取主循环模型 → 返回模型名。

**输入。** `NoArgs`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** handler 的结果是 `ValueOrDeny<string>`；核心 API 的值类型是 `string`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 它不是模型切换通知；子智能体请求实际模型仍应看对应事件的 model 或结果。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5586)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5851)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5380)。

### `session.turns`

**作用。** 查询会话中用户提示词回合数量。

**何时触发。** mod 调用 $.session.turns()。

**处理流程。** 进入事件链 → 核心统计会话中的用户 turns → 返回数字。

**输入。** `NoArgs`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** handler 的结果是 `ValueOrDeny<number>`；核心 API 的值类型是 `number`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 不是模型请求 step 数，也不是工具调用数。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5590)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5852)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5380)。

### `session.id`

**作用。** 查询当前会话标识。

**何时触发。** mod 调用 $.session.id()。

**处理流程。** 进入事件链 → 核心提供会话 id → 返回字符串。

**输入。** `NoArgs`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** handler 的结果是 `ValueOrDeny<string>`；核心 API 的值类型是 `string`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** session id、turnId、tool_use_id 是不同级别的身份，不应互换。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5594)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5853)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5380)。

### `session.messages`

**作用。** 读取宿主提供的会话消息。

**何时触发。** mod 调用 $.session.messages()；其他读取选项以安装版本为准。

**处理流程。** 进入 session.messages 链 → 核心取得消息列表 → 返回 SessionMessage 数组。

**输入。** `NoArgs`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** handler 的结果是 `ValueOrDeny<SessionMessage[]>`；核心 API 的值类型是 `SessionMessage[]`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 它是主动读取，session.append 是保存前事件；固定快照的 OpEventOf 这里声明 NoArgs，不应把新版选项硬塞进旧类型。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5598)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5854)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5380)。

### `session.repo`

**作用。** 查询会话工作目录所在 git 仓库的信息。

**何时触发。** mod 调用 $.session.repo()。

**处理流程。** 进入事件链 → 核心按当前工作副本读取仓库信息 → 返回对象或 null。

**输入。** `NoArgs`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** handler 的结果是 `ValueOrDeny<SessionRepo | null>`；核心 API 的值类型是 `SessionRepo | null`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 不在仓库内可为 null；查询不会创建仓库或工作树。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5602)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5855)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5380)。

### `session.surface`

**作用。** 读取会话第一个绘制环境，属于旧兼容 API。

**何时触发。** mod 调用 $.session.surface()。

**处理流程。** 进入事件链 → 核心读取 surfaces 的首项 → 无界面时返回 null。

**输入。** `NoArgs`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** handler 的结果是 `ValueOrDeny<RenderSurface | null>`；核心 API 的值类型是 `RenderSurface | null`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 固定类型已标记 deprecated；会话可能同时连多个界面，应优先使用 surfaces，不应拿它替代 render 的 e.surface。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5608)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5856)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5380)。

### `session.surfaces`

**作用。** 查询当前会话连接的绘制环境集合。

**何时触发。** mod 调用 $.session.surfaces()。

**处理流程。** 进入事件链 → 核心读连接记录 → 去重返回 surface 列表。

**输入。** `NoArgs`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** handler 的结果是 `ValueOrDeny<readonly RenderSurface[]>`；核心 API 的值类型是 `readonly RenderSurface[]`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 它是查询，不是 session.attach/detach 通知；无界面的运行可以返回空列表。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5612)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5857)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5380)。

### `session.authorize`

**作用。** 查询宿主支持的身份授权句柄。

**何时触发。** mod 调用 $.session.authorize()。

**处理流程。** 进入事件链 → 核心按运行环境和提供商取得句柄或空值 → 返回 SessionAuthorization。

**输入。** `NoArgs`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** handler 的结果是 `ValueOrDeny<SessionAuthorization>`；核心 API 的值类型是 `SessionAuthorization`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 句柄按契约用于支持的宿主请求，不是公开的明文密钥读取 API。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5616)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5862)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5380)。

### `session.usage`

**作用。** 查询上下文、限额、成本及可选分类统计。

**何时触发。** mod 调用 $.session.usage(args)。

**处理流程。** 请求进入事件链 → 核心按 breakdown 等选项获取或计算统计 → 返回 SessionUsage。

**输入。** `SessionUsageArgs`。字段概览：`breakdown?`、`columns?`。

**返回与效果。** handler 的结果是 `ValueOrDeny<SessionUsage>`；核心 API 的值类型是 `SessionUsage`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 缺失指标不能当作零；summary 与 full 的计算方式不同。session.measure 是指标变化时的通知。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5620)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5863)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9449)。

### `session.version`

**作用。** 查询执行宿主的版本和构建信息。

**何时触发。** mod 调用 $.session.version()。

**处理流程。** 进入事件链 → 核心返回 version、base、builtAt 等契约字段。

**输入。** `NoArgs`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** handler 的结果是 `ValueOrDeny<SessionVersion>`；核心 API 的值类型是 `SessionVersion`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 某些构建字段可缺失；用版本信息核对声明，不能把研究快照版本当成安装版本。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5624)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5867)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5380)。

### `session.send`

**作用。** 处理向其他会话或智能体发送的消息。

**何时触发。** 对应发送 API 或宿主准备交付消息。

**处理流程。** 提供发送目标与内容 → handler 处理 → 核心尝试交付 → 返回交付结果；目标接收路径可进入 session.receive。

**输入。** 目标与发送内容等；完整字段需安装声明。

**返回与效果。** 当前参考确认可返回 { isDelivered: false, reason }。

**易混淆点。** 当前参考允许返回 isDelivered:false 与 reason；send 与 receive 不是保证同时完成的单个本地 handler 调用。

**依据。** 当前文档补充；未冒用旧 EventOf 为新版完整字段背书。 [当前 Mods reference](https://code.claude.com/docs/en/plugins/mods/reference)。


## 4.9 直接模型调用

### `model.complete`

**作用。** 让 mod 发起一次独立模型请求。

**何时触发。** mod 调用 $.model.complete(request)。

**处理流程。** 调用参数进入 model.complete 链 → 核心发送独立请求 → 获取响应 → 事件结果解包返回调用者。

**输入。** `ModelCompleteRequest`。字段概览：`model`、`prompt`、`system?`、`maxTokens?`。

**返回与效果。** handler 的结果是 `ValueOrDeny<string>`；核心 API 的值类型是 `string`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 它不是主智能体 turn.step；默认不带完整会话和工具。固定快照返回 string，当前指南使用结构化结果，不能混用示例。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5541)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5843)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5109)。

### `model.fork`

**作用。** 使用当前对话上下文做一次 mod 发起的模型请求。

**何时触发。** mod 调用 $.model.fork(request)。

**处理流程。** 宿主从当前请求上下文构造 fork → model.fork 链 → 请求模型 → 结果返回 mod。

**输入。** `ModelForkRequest`。字段概览：`prompt`。

**返回与效果。** handler 的结果是 `ValueOrDeny<ModelForkResult | null>`；核心 API 的值类型是 `ModelForkResult | null`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 名字里的 fork 不表示新建一个可持续执行工具的独立智能体或保存的新会话；当前指南说明模型不能在该请求中调用工具。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5553)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5845)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5138)。

### `model.classify`

**作用。** 把文字按给定标签分类。

**何时触发。** mod 调用 $.model.classify(text, labels, options)。

**处理流程。** text、labels、options 形成事件输入 → handler 链 → 核心请求相应分类 → 返回标签或契约规定的空结果。

**输入。** `{ text: string; labels: readonly string[]; options?: ClassifyOptions; }`。字段概览：`text`、`labels`、`options?`。

**返回与效果。** handler 的结果是 `ValueOrDeny<string | undefined>`；核心 API 的值类型是 `string | undefined`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 标签判断是辅助模型任务，不是决定主智能体下一步的通用事件；模型选项和返回结构按版本核对。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5545)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5844)。


## 4.10 文件与工作区

### `classic.CwdChanged`

**作用。** 在工作目录变化后调整环境或记录路径。

**何时触发。** 会话工作目录被改变，例如相关 cd 操作。

**处理流程。** 宿主确认 old_cwd、new_cwd → 运行相应 hooks → 后续操作使用新目录和环境。

**输入。** `CwdChangedHookInput`；事件特有字段概览：`old_cwd`、`new_cwd`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.CwdChanged"]`。没有在快照中额外列出的事件特有结果字段。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 不是读取 session.cwd 就触发的通知；查询与变化通知是两条路径。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3062)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3061)。

### `classic.DirectoryAdded`

**作用。** 观察运行中加入新的工作目录。

**何时触发。** /add-dir 或 SDK 对应控制请求添加目录。

**处理流程。** 宿主接收目录添加 → 提供目录事实 → hooks 处理 → 后续工作区使用新增范围。

**输入。** `DirectoryAddedHookInput`；事件特有字段概览：`directory`、`source`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.DirectoryAdded"]`。没有在快照中额外列出的事件特有结果字段。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 它不等于 fs.list 或发现磁盘上新建了子目录。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3068)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3067)。

### `classic.FileChanged`

**作用。** 响应被监视文件的磁盘变化。

**何时触发。** 配置的监视目标发生 change、add、unlink 等变化。

**处理流程。** 文件监视器发现变化 → 构造 file_path、event → 匹配 hooks → 观察或按契约更新动态监视目标。

**输入。** `FileChangedHookInput`；事件特有字段概览：`file_path`、`event`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.FileChanged"]`。没有在快照中额外列出的事件特有结果字段。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 它不等于每次 Write 工具必定触发；监视范围与事件合并取决于配置和宿主。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3992)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3991)。

### `classic.WorktreeCreate`

**作用。** 接管需要隔离工作树的创建。

**何时触发。** --worktree、对应 isolation 或后台会话等路径准备工作树。

**处理流程。** 宿主请求隔离目录 → hook 创建并提供 worktreePath → 宿主使用该路径继续执行。

**输入。** `WorktreeCreateHookInput`；事件特有字段概览：`name`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.WorktreeCreate"]`。快照映射的事件特有结果字段包括：`worktreePath`。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 这是可替代默认创建行为的事件，不能只写成创建后的通知。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L11538)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L11537)。

### `classic.WorktreeRemove`

**作用。** 清理由对应创建 hook 管理的工作树。

**何时触发。** 宿主准备清理由 WorktreeCreate hook 创建的工作树。

**处理流程。** 宿主提供待移除路径 → 匹配清理 hook → 按相应生命周期完成清理。

**输入。** `WorktreeRemoveHookInput`；事件特有字段概览：`worktree_path`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.WorktreeRemove"]`。没有在快照中额外列出的事件特有结果字段。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 不能把任何磁盘目录删除都看成此事件；清理对象由创建路径决定。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L11543)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L11542)。

### `fs.read`

**作用。** 读取 mod 自己请求的文件内容。

**何时触发。** mod 调用 $.fs.read(path, options)。

**处理流程。** 宿主把 path、as 归一化为事件输入 → fs.read 链 → 核心读文件 → 返回文本或字节表示。

**输入。** `{ path: string; as: FsReadAs; }`。字段概览：`path`、`as`。

**返回与效果。** handler 的结果是 `ValueOrDeny<string | FsBytes>`；核心 API 的值类型是 `string | FsBytes`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 与模型 Read 工具的 tool.call 是不同入口；不会仅因使用 fs.read 就自动走模型的 Read 权限规则。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5721)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5901)。

### `fs.write`

**作用。** 按 mod 请求写入文件内容。

**何时触发。** mod 调用 $.fs.write(path, text)。

**处理流程。** 参数进入 fs.write 链 → 核心写文件 → 事件结果返回调用者。

**输入。** `{ path: string; text: string; }`。字段概览：`path`、`text`。

**返回与效果。** handler 的结果是 `ValueOrDeny<void>`；核心 API 的值类型是 `void`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 当前文档说明写入不保证原子替换；不是模型 Write 工具执行后事件，也不自动保证触发文件监视通知。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5728)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5902)。

### `fs.list`

**作用。** 列出目录条目。

**何时触发。** mod 调用 $.fs.list(path)。

**处理流程。** path 进入事件链 → 核心列目录 → 返回 FsEntry 数组。

**输入。** `{ path: string; }`。字段概览：`path`。

**返回与效果。** handler 的结果是 `ValueOrDeny<FsEntry[]>`；核心 API 的值类型是 `FsEntry[]`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 它不是递归遍历全部工作区的隐含事件；是否进一步读取由调用者决定。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5735)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5903)。

### `fs.exists`

**作用。** 检查路径是否存在。

**何时触发。** mod 调用 $.fs.exists(path)。

**处理流程。** path 进入事件链 → 核心检查 → 返回布尔值。

**输入。** `{ path: string; }`。字段概览：`path`。

**返回与效果。** handler 的结果是 `ValueOrDeny<boolean>`；核心 API 的值类型是 `boolean`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 存在与可读取、目标真实路径或下一时刻仍存在不是同一事实。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5741)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5904)。

### `fs.stat`

**作用。** 读取路径元信息，并可解析实际目标。

**何时触发。** mod 调用 $.fs.stat(path, options)。

**处理流程。** 归一化 path、resolve → handler 链 → 核心获取 stat → 返回 FsStat 或拒绝/错误。

**输入。** `{ path: string; resolve: boolean; }`。字段概览：`path`、`resolve`。

**返回与效果。** handler 的结果是 `ValueOrDeny<FsStat>`；核心 API 的值类型是 `FsStat`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** resolve 为真时可取得 realPath；查询本身不执行文件读取工具。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5748)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5905)。

### `fs.ancestors`

**作用。** 沿祖先目录查找指定指令文件并取得内容。

**何时触发。** mod 调用 $.fs.ancestors(request)。

**处理流程。** 提供 names、of、below 等范围 → 链处理 → 核心按契约搜索和读取 → 返回 FsAncestor 数组。

**输入。** `FsAncestorsRequest`。字段概览：`names`、`of?`、`below?`。

**返回与效果。** handler 的结果是 `ValueOrDeny<readonly FsAncestor[]>`；核心 API 的值类型是 `readonly FsAncestor[]`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 结果包含指令文件的相关内容与导入部分；与只列目录的 fs.list 不同。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5755)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5906)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L4051)。


## 4.11 进程执行

### `process.run`

**作用。** 运行进程并收集结束后的输出。

**何时触发。** mod 调用 $.process.run(argv, init)。

**处理流程。** argv 与运行选项进入事件链 → 核心启动并等待进程 → 返回 ProcessRunResult。

**输入。** `{ argv: readonly string[]; init?: ProcessRunInit; }`。字段概览：`argv`、`init?`。

**返回与效果。** handler 的结果是 `ValueOrDeny<ProcessRunResult>`；核心 API 的值类型是 `ProcessRunResult`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 它与模型 Bash 工具入口不同；run 收集结果，当前补充的 spawn 使用流式契约。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5808)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5919)。

### `process.spawn`

**作用。** 以流式方式运行 mod 发起的子进程。

**何时触发。** mod 调用 $.process.spawn。

**处理流程。** 启动请求进入流式事件链 → 核心进程输出产生流块 → handler 转发或处理 → 结束时得到最终结果。

**输入。** 进程启动参数；具体字段需安装声明。

**返回与效果。** 异步生成器的流块和最终结果；不是 process.run 的单次结果。

**易混淆点。** 当前参考把它与 turn.step 一起列为 async-generator 事件；不能套用 process.run 的单次 Promise 结果格式。

**依据。** 当前文档补充；未冒用旧 EventOf 为新版完整字段背书。 [当前 Mods reference](https://code.claude.com/docs/en/plugins/mods/reference)。


## 4.12 网络与 MCP

### `classic.Elicitation`

**作用。** 处理 MCP 服务在工具执行期间向用户索取补充输入。

**何时触发。** MCP 服务发送支持的 elicitation 请求。

**处理流程。** MCP 工具运行 → 收到请求 → hooks 可按契约处理响应 → 必要时显示界面并等待用户。

**输入。** `ElicitationHookInput`；事件特有字段概览：`mcp_server_name`、`message`、`mode?`、`url?`、`elicitation_id?`、`requested_schema?`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.Elicitation"]`。没有在快照中额外列出的事件特有结果字段。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 嵌套在工具执行中，不是普通 prompt.submit；它与工具权限确认也不是同一问题。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3195)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3194)。

### `classic.ElicitationResult`

**作用。** 处理 MCP 补充输入的响应。

**何时触发。** 已经形成用户响应或相应 elicitation 结果，尚未发回 MCP 服务。

**处理流程。** 取得响应 → ElicitationResult hooks 按契约处理 → 结果返回 MCP 服务 → MCP 工具继续。

**输入。** `ElicitationResultHookInput`；事件特有字段概览：`mcp_server_name`、`elicitation_id?`、`mode?`、`action`、`content?`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.ElicitationResult"]`。没有在快照中额外列出的事件特有结果字段。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 发生在请求之后、响应回传之前；结果不能被当成主对话的新用户提示词。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3208)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3207)。

### `mcp.call`

**作用。** 让 mod 自己调用一个 MCP 服务工具。

**何时触发。** mod 调用 $.mcp.call(server, tool, args)。

**处理流程。** 宿主整理 server、tool、args → mcp.call 链 → MCP 调用 → 返回 McpToolResult。

**输入。** `{ server: string; tool: string; args: Record<string, unknown>; }`。字段概览：`server`、`tool`、`args`。

**返回与效果。** handler 的结果是 `ValueOrDeny<McpToolResult>`；核心 API 的值类型是 `McpToolResult`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** mod 的 MCP API 与模型的 tool.call 入口不同；不能据 API 名称假设复用了同一模型权限链。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5570)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5848)。

### `http.fetch`

**作用。** 让 mod 发出网络请求。

**何时触发。** mod 调用 $.http.fetch(url, init)。

**处理流程。** url、init 进入事件链 → 核心发请求 → 构造 HttpResponse → 返回调用者。

**输入。** `{ url: string; init?: HttpInit; }`。字段概览：`url`、`init?`。

**返回与效果。** handler 的结果是 `ValueOrDeny<HttpResponse>`；核心 API 的值类型是 `HttpResponse`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 不是模型的网页工具调用；请求、响应与身份句柄有宿主限制，输出按类型处理。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5801)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5918)。

### `mcp.connect`

**作用。** 连接当前插件声明的 MCP 服务。

**何时触发。** mod 调用 $.mcp.connect(server)。

**处理流程。** 连接请求进入事件链 → 宿主核对插件声明并建立支持的连接 → 返回该版本的连接结果。

**输入。** API 接收插件声明的 server；完整事件输入需安装声明。

**返回与效果。** 完整连接结果需安装声明。

**易混淆点。** 当前指南限制为插件 manifest 声明的服务；完整结果形状未由固定快照提供。

**依据。** 当前文档补充；未冒用旧 EventOf 为新版完整字段背书。 [当前 Mods reference](https://code.claude.com/docs/en/plugins/mods/reference)。


## 4.13 配置与运行环境

### `config.set`

**作用。** 处理配置菜单行将要写入的新值。

**何时触发。** 用户菜单修改，或 mod 调用 $.config.set。

**处理流程。** 宿主提供 key、value → handler 改值或 deny → 核心按类型与来源约束写入 → 返回 value。

**输入。** `ConfigSetInput`。字段概览：`key`、`value`、`previous`、`provider`、`origin`。

**返回与效果。** `ConfigSetResult`。成功返回 value；拒绝有相应 deny 分支。

**易混淆点。** 不是外部配置文件变化通知；后者是 classic.ConfigChange。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3517)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3816)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1719)。

### `config.describe`

**作用。** 处理配置菜单的行说明与可见性。

**何时触发。** 菜单或 config.list 准备某个行的描述。

**处理流程。** 核心或下层提供 label、description、isHidden → handler 改写 → 菜单使用结果并按条件缓存。

**输入。** `ConfigDescribeInput`。字段概览：`key`、`label`、`description?`、`isHidden`、`provider`。

**返回与效果。** `ConfigDescribeResult`。label、description、isHidden 控制配置行的展示。

**易混淆点。** 隐藏菜单条目不是删除真实配置，也不改变已生效的值。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3529)、[事件返回类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L3820)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1600)。

### `classic.ConfigChange`

**作用。** 观察或按契约处理配置文件在运行中的变化。

**何时触发。** 相关用户、项目或受管理配置源被修改。

**处理流程。** 宿主发现配置变化 → 提供 source、文件事实 → hooks 处理 → 按来源与决策规则更新配置。

**输入。** `ConfigChangeHookInput`；事件特有字段概览：`source`、`file_path?`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.ConfigChange"]`。没有在快照中额外列出的事件特有结果字段。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 与 config.set 的菜单/API 写入事件不同；不同来源的阻止能力需要按当前契约判断。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1591)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1590)。

### `classic.PreModelSwitch`

**作用。** 在用户或客户端请求的模型切换前检查切换。

**何时触发。** 宿主即将应用这种请求切换。

**处理流程。** 提供 from_model、to_model 与来源 → hooks 允许或拒绝 → 放行后宿主切换模型。

**输入。** `PreModelSwitchHookInput`；事件特有字段概览：`from_model`、`to_model`、`requested_model`、`source`、`context_tokens`、`prompt_cache_warm`、`cache_ttl`、`estimated_cache_write_usd`、`pricing`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.PreModelSwitch"]`。快照映射的事件特有结果字段包括：`permissionDecision`、`permissionDecisionReason`。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 不是每次模型请求的 turn.step；宿主自动恢复模型不一定走同样的前置事件。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6421)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6420)。

### `classic.PostModelSwitch`

**作用。** 观察会话模型实际变化后的状态。

**何时触发。** 请求切换完成或宿主按生命周期自行恢复模型。

**处理流程。** 宿主更新模型 → 分发前后模型信息 → hooks 观察或提供相应下一请求上下文。

**输入。** `PostModelSwitchHookInput`；事件特有字段概览：`from_model`、`to_model`、`requested_model`、`source`、`context_tokens`、`prompt_cache_warm`、`cache_ttl`、`estimated_cache_write_usd`、`pricing`。
传统输入还包含适用的 BaseHookInput 通用字段，例如 session_id、cwd、transcript_path。

**返回与效果。** `ClassicResultOf["classic.PostModelSwitch"]`。快照映射的事件特有结果字段包括：`additionalContext`。类型可表达的字段与运行时实际读取的决策不同；观察类事件不能仅凭通用结果字段变成前置阻止。

**易混淆点。** 切换后观察不能撤销已经发生的切换；附加上下文何时使用取决于后续请求。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6335)、[classic 结果映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1086)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L6334)。

### `config.list`

**作用。** 查询配置菜单行及其值。

**何时触发。** mod 调用 $.config.list()。

**处理流程。** 进入事件链 → 核心收集配置行并取得相关描述 → 返回 ConfigRow 数组。

**输入。** `NoArgs`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** handler 的结果是 `ValueOrDeny<ConfigRow[]>`；核心 API 的值类型是 `ConfigRow[]`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 读取配置菜单不等于解析所有原始 settings 文件；读取完整来源使用相应 settings API。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5654)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5881)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5380)。

### `settings.read`

**作用。** 读取指定来源的设置。

**何时触发。** mod 调用 $.settings.read(args)。

**处理流程。** source 等参数进入事件链 → 核心按来源读取设置 → 返回 Settings。

**输入。** `SettingsReadArgs`。字段概览：`source?`。

**返回与效果。** handler 的结果是 `ValueOrDeny<Settings>`；核心 API 的值类型是 `Settings`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 读取用户设置与读取组织 policy 不可混同；源码中的安全 mod 会按指定来源判断。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5815)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5920)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9509)。

### `env.get`

**作用。** 读取 mod 环境中的一个变量。

**何时触发。** mod 调用 $.env.get(name)。

**处理流程。** 变量名进入事件链 → 核心读取 → 返回字符串或 undefined。

**输入。** `{ name: string; }`。字段概览：`name`。

**返回与效果。** handler 的结果是 `ValueOrDeny<string | undefined>`；核心 API 的值类型是 `string | undefined`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** name 是受保护身份字段；事件不是操作系统任意环境变化的广播。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5819)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5921)。

### `env.set`

**作用。** 设置或移除 mod 环境中的变量。

**何时触发。** mod 调用 $.env.set(name, value)。

**处理流程。** 提供受保护 name 和 value → handler 链 → 核心写入或移除 → 后续相应操作使用环境。

**输入。** `{ name: string; value?: string; }`。字段概览：`name`、`value?`。

**返回与效果。** handler 的结果是 `ValueOrDeny<void>`；核心 API 的值类型是 `void`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** value 为 undefined 表示移除；不应把它理解为永久更改整个系统的环境变量。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5826)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5922)。


## 4.14 状态与存储

### `store.get`

**作用。** 读取跨会话键值存储的一项。

**何时触发。** mod 调用 $.store.get(key)。

**处理流程。** key 进入事件链 → 核心读取相应值 → 返回 value。

**输入。** `{ key: string; }`。字段概览：`key`。

**返回与效果。** handler 的结果是 `ValueOrDeny<unknown>`；核心 API 的值类型是 `unknown`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 读取的是 store，不是本模块局部变量；是否存在与值的类型应由调用者按契约判断。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5759)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5907)。

### `store.set`

**作用。** 写入跨会话键值存储。

**何时触发。** mod 调用 $.store.set(key, value)。

**处理流程。** key、value 进入链 → 宿主按存储契约写入 → 返回写入完成。

**输入。** `{ key: string; value: unknown; }`。字段概览：`key`、`value`。

**返回与效果。** handler 的结果是 `ValueOrDeny<void>`；核心 API 的值类型是 `void`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** store 与响应式 state 不同；写 store 不代表所有 UI 自动重绘。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5765)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5908)。

### `store.delete`

**作用。** 删除键值存储中的一项。

**何时触发。** mod 调用 $.store.delete(key)。

**处理流程。** 进入事件链 → 核心删除对应键 → 返回完成。

**输入。** `{ key: string; }`。字段概览：`key`。

**返回与效果。** handler 的结果是 `ValueOrDeny<void>`；核心 API 的值类型是 `void`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 它不删除文件，也不自动清空当前模块中保存的副本。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5772)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5909)。

### `store.keys`

**作用。** 查询存储中可见的键集合。

**何时触发。** mod 调用 $.store.keys()。

**处理流程。** 进入查询事件 → 核心列键 → 返回字符串数组。

**输入。** `NoArgs`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** handler 的结果是 `ValueOrDeny<string[]>`；核心 API 的值类型是 `string[]`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 它只返回键，不是把所有值也一并返回；存储作用域按宿主版本契约。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5778)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5910)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5380)。

### `state.get`

**作用。** 读取声明的响应式状态。

**何时触发。** mod 或相应状态辅助方法调用 $.state.get。

**处理流程。** 状态读取请求 → 宿主按插件状态声明取得值 → 返回调用上下文。

**输入。** 声明的状态访问参数；完整字段需安装声明。

**返回与效果。** 对应状态值；事件封装需安装声明。

**易混淆点。** 不是跨会话 store 的同义词；响应式依赖规则和完整事件字段以目标版本的 state 类型为准。

**依据。** 当前文档补充；未冒用旧 EventOf 为新版完整字段背书。 [当前 Mods reference](https://code.claude.com/docs/en/plugins/mods/reference)。

### `state.set`

**作用。** 写入声明的响应式状态。

**何时触发。** mod 或相应状态辅助方法调用 $.state.set。

**处理流程。** 写请求进入宿主状态处理 → 更新状态 → 按响应式依赖规则安排相关计算或界面更新。

**输入。** 声明的状态写入参数；完整字段需安装声明。

**返回与效果。** 状态写入的契约结果；具体类型需安装声明。

**易混淆点。** 不能简单宣称每次 set 都同步重跑所有 ui.render；原子、派生状态等属于状态机制。

**依据。** 当前文档补充；未冒用旧 EventOf 为新版完整字段背书。 [当前 Mods reference](https://code.claude.com/docs/en/plugins/mods/reference)。


## 4.15 定时器与时间

### `clock.now`

**作用。** 读取宿主提供的当前时间数值。

**何时触发。** mod 调用 $.clock.now()。

**处理流程。** 进入事件链 → 核心读取时间 → 返回毫秒时间值。

**输入。** `NoArgs`。无字段参数或复合类型的完整约束见来源。

**返回与效果。** handler 的结果是 `ValueOrDeny<number>`；核心 API 的值类型是 `number`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 这是主动查询，不是时钟每走一毫秒就自动发出的事件。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5782)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5914)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5380)。

### `clock.sleep`

**作用。** 等待指定时长。

**何时触发。** mod 调用 $.clock.sleep(ms, options)。

**处理流程。** ms 形成 ClockWait → handler 链 → 核心等待或取消 → Promise 结束，原 handler 继续。

**输入。** `ClockWait`。字段概览：`ms`。

**返回与效果。** handler 的结果是 `ValueOrDeny<void>`；核心 API 的值类型是 `void`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** signal 不作为普通序列化字段跨界；等待仍可能计入 hook 预算，不应假设无限等待都被豁免。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5787)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5915)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1311)。

### `clock.after`

**作用。** 安排一次定时回调。

**何时触发。** mod 调用 $.clock.after(ms, fn)。

**处理流程。** 等待时间进入事件链 → 相应等待分发结束 → 留在 mod 环境的 fn 运行一次。

**输入。** `ClockWait`。字段概览：`ms`。

**返回与效果。** handler 的结果是 `ValueOrDeny<void>`；核心 API 的值类型是 `void`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** fn 不是 ClockWait 中的字段，也不是被序列化交给其他 handler 的源码。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5792)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5916)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1311)。

### `clock.every`

**作用。** 安排周期性的定时回调。

**何时触发。** mod 调用 $.clock.every(ms, fn)，随后每个周期按契约产生分发。

**处理流程。** 每期等待进入事件链 → 该期分发完成 → mod 环境运行 fn → 安排下一期。

**输入。** `ClockWait`。字段概览：`ms`。

**返回与效果。** handler 的结果是 `ValueOrDeny<void>`；核心 API 的值类型是 `void`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 不是只在登记时产生一次事件；周期控制和回调仍与主智能体 step 不同。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5797)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5917)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L1311)。


## 4.16 音频

### `audio.play`

**作用。** 请求播放给定音频片段。

**何时触发。** mod 调用 $.audio.play(clip, options)。

**处理流程。** 参数进入 audio.play 链 → 核心处理片段与播放参数 → 完成相应播放操作 → 返回调用者。

**输入。** `{ clip: AudioClip; shouldLoop: boolean; gain?: number; }`。字段概览：`clip`、`shouldLoop`、`gain?`。

**返回与效果。** handler 的结果是 `ValueOrDeny<void>`；核心 API 的值类型是 `void`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** signal 不作为普通数据字段跨宿主边界；停止与循环行为以具体播放参数为准。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5558)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5846)。

### `audio.speak`

**作用。** 请求把文字转换为语音并播放或按契约处理。

**何时触发。** mod 调用 $.audio.speak(text, options)。

**处理流程。** 生成 SpeakRequest → 事件链 → 核心执行语音操作 → 返回 SpeakResult。

**输入。** `SpeakRequest`。字段概览：`text`。

**返回与效果。** handler 的结果是 `ValueOrDeny<SpeakResult>`；核心 API 的值类型是 `SpeakResult`。成功的 value 分支与 deny 分支分开处理。

**易混淆点。** 这不是每次助手回复自动触发的事件；只有相应调用或宿主支持路径发生才有这次分发。

**依据。** 固定公开快照。 [事件映射](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5566)、[核心 API 值类型](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L5847)、[输入字段声明](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts#L9616)。


## 4.17 遥测

### `telemetry.log`

**作用。** 处理一条运行遥测记录。

**何时触发。** 宿主、内置 mod 或支持的 collector 路径产生记录。

**处理流程。** 记录进入 telemetry.log → gate 校验来源与格式 → 内置实现排队或转交 → sender 按条件批量发送。

**输入。** 遥测记录，按内置 namespace 的类型和来源校验。

**返回与效果。** 按 namespace 契约处理记录；不是网络发送成功的保证。

**易混淆点。** 该 namespace 也由公开内置 mod 扩展提供；用户观察 collector 需要相应 matcher，普通 * 不覆盖这些记录。

**依据。** 当前文档补充；未冒用旧 EventOf 为新版完整字段背书。 [当前 Mods reference](https://code.claude.com/docs/en/plugins/mods/reference)、[公开内置 namespace](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/telemetry/types/index.d.ts)。

### `telemetry.mark`

**作用。** 处理一个功能使用标记。

**何时触发。** 宿主或内置 mod 产生支持的功能标记。

**处理流程。** 标记进入 telemetry.mark → 来源与格式处理 → 排队 → 批次条件或会话结束时按策略发送。

**输入。** 功能标记，按内置 namespace 的类型和来源校验。

**返回与效果。** 按 namespace 契约处理标记；不是网络发送成功的保证。

**易混淆点。** 标记一次功能不等于马上发送一次网络请求；不能把它当成第三方 mod 任意复用的遥测通道。

**依据。** 当前文档补充；未冒用旧 EventOf 为新版完整字段背书。 [当前 Mods reference](https://code.claude.com/docs/en/plugins/mods/reference)、[公开内置 namespace](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/telemetry/types/index.d.ts)。

## 5. 固定类型索引与补充范围

| 事件 | 分组 | 输入定义 | 来源 |
|---|---|---|---|
| `agent.list` | 智能体与任务 | `NoArgs` | OpEventOf |
| `agent.offer` | 智能体与任务 | `AgentOfferInput` | EngineEventOf |
| `agent.register` | 智能体与任务 | `AgentSpec` | OpEventOf |
| `agent.spawn` | 智能体与任务 | `AgentSpawnInput` | EngineEventOf |
| `attribution.text` | 上下文与消息装配 | `AttributionTextInput` | EngineEventOf |
| `audio.play` | 音频 | `{ clip: AudioClip; shouldLoop: boolean; gain?: number; }` | OpEventOf |
| `audio.speak` | 音频 | `SpeakRequest` | OpEventOf |
| `classic.ConfigChange` | 配置与运行环境 | `ConfigChangeHookInput` | ClassicEventOf |
| `classic.CwdChanged` | 文件与工作区 | `CwdChangedHookInput` | ClassicEventOf |
| `classic.DirectoryAdded` | 文件与工作区 | `DirectoryAddedHookInput` | ClassicEventOf |
| `classic.Elicitation` | 网络与 MCP | `ElicitationHookInput` | ClassicEventOf |
| `classic.ElicitationResult` | 网络与 MCP | `ElicitationResultHookInput` | ClassicEventOf |
| `classic.FileChanged` | 文件与工作区 | `FileChangedHookInput` | ClassicEventOf |
| `classic.InstructionsLoaded` | 加载与初始化 | `InstructionsLoadedHookInput` | ClassicEventOf |
| `classic.MessageDisplay` | UI 绘制与交互 | `MessageDisplayHookInput` | ClassicEventOf |
| `classic.Notification` | UI 绘制与交互 | `NotificationHookInput` | ClassicEventOf |
| `classic.PermissionDenied` | 工具与权限 | `PermissionDeniedHookInput` | ClassicEventOf |
| `classic.PermissionRequest` | 工具与权限 | `PermissionRequestHookInput` | ClassicEventOf |
| `classic.PostCompact` | 会话与通信 | `PostCompactHookInput` | ClassicEventOf |
| `classic.PostModelSwitch` | 配置与运行环境 | `PostModelSwitchHookInput` | ClassicEventOf |
| `classic.PostToolBatch` | 回合与执行控制 | `PostToolBatchHookInput` | ClassicEventOf |
| `classic.PostToolUse` | 工具与权限 | `PostToolUseHookInput` | ClassicEventOf |
| `classic.PostToolUseFailure` | 工具与权限 | `PostToolUseFailureHookInput` | ClassicEventOf |
| `classic.PreCompact` | 会话与通信 | `PreCompactHookInput` | ClassicEventOf |
| `classic.PreModelSwitch` | 配置与运行环境 | `PreModelSwitchHookInput` | ClassicEventOf |
| `classic.PreToolUse` | 工具与权限 | `ToolCallEnvelope` | ClassicEventOf |
| `classic.SessionEnd` | 会话与通信 | `SessionEndHookInput` | ClassicEventOf |
| `classic.SessionStart` | 加载与初始化 | `SessionStartHookInput` | ClassicEventOf |
| `classic.Setup` | 加载与初始化 | `SetupHookInput` | ClassicEventOf |
| `classic.Stop` | 回合与执行控制 | `StopHookInput` | ClassicEventOf |
| `classic.StopFailure` | 回合与执行控制 | `StopFailureHookInput` | ClassicEventOf |
| `classic.SubagentStart` | 智能体与任务 | `SubagentStartHookInput` | ClassicEventOf |
| `classic.SubagentStop` | 智能体与任务 | `SubagentStopHookInput` | ClassicEventOf |
| `classic.TaskCompleted` | 智能体与任务 | `TaskCompletedHookInput` | ClassicEventOf |
| `classic.TaskCreated` | 智能体与任务 | `TaskCreatedHookInput` | ClassicEventOf |
| `classic.TeammateIdle` | 智能体与任务 | `TeammateIdleHookInput` | ClassicEventOf |
| `classic.UserPromptExpansion` | 输入与命令 | `UserPromptExpansionHookInput` | ClassicEventOf |
| `classic.UserPromptSubmit` | 输入与命令 | `UserPromptSubmitHookInput` | ClassicEventOf |
| `classic.WorktreeCreate` | 文件与工作区 | `WorktreeCreateHookInput` | ClassicEventOf |
| `classic.WorktreeRemove` | 文件与工作区 | `WorktreeRemoveHookInput` | ClassicEventOf |
| `clock.after` | 定时器与时间 | `ClockWait` | OpEventOf |
| `clock.every` | 定时器与时间 | `ClockWait` | OpEventOf |
| `clock.now` | 定时器与时间 | `NoArgs` | OpEventOf |
| `clock.sleep` | 定时器与时间 | `ClockWait` | OpEventOf |
| `command.describe` | 输入与命令 | `CommandDescribeInput` | EngineEventOf |
| `command.list` | 输入与命令 | `NoArgs` | OpEventOf |
| `command.register` | 输入与命令 | `CommandSpec` | OpEventOf |
| `command.run` | 输入与命令 | `CommandRunInput` | EngineEventOf |
| `config.describe` | 配置与运行环境 | `ConfigDescribeInput` | EngineEventOf |
| `config.list` | 配置与运行环境 | `NoArgs` | OpEventOf |
| `config.set` | 配置与运行环境 | `ConfigSetInput` | EngineEventOf |
| `engine.create` | 加载与初始化 | `EngineCreateInput` | EngineEventOf |
| `env.get` | 配置与运行环境 | `{ name: string; }` | OpEventOf |
| `env.set` | 配置与运行环境 | `{ name: string; value?: string; }` | OpEventOf |
| `fs.ancestors` | 文件与工作区 | `FsAncestorsRequest` | OpEventOf |
| `fs.exists` | 文件与工作区 | `{ path: string; }` | OpEventOf |
| `fs.list` | 文件与工作区 | `{ path: string; }` | OpEventOf |
| `fs.read` | 文件与工作区 | `{ path: string; as: FsReadAs; }` | OpEventOf |
| `fs.stat` | 文件与工作区 | `{ path: string; resolve: boolean; }` | OpEventOf |
| `fs.write` | 文件与工作区 | `{ path: string; text: string; }` | OpEventOf |
| `http.fetch` | 网络与 MCP | `{ url: string; init?: HttpInit; }` | OpEventOf |
| `mcp.call` | 网络与 MCP | `{ server: string; tool: string; args: Record<string, unknown>; }` | OpEventOf |
| `mcp.connect` | 网络与 MCP | `API 接收插件声明的 server；完整事件输入需安装声明。` | 当前文档补充 |
| `model.classify` | 直接模型调用 | `{ text: string; labels: readonly string[]; options?: ClassifyOptions; }` | OpEventOf |
| `model.complete` | 直接模型调用 | `ModelCompleteRequest` | OpEventOf |
| `model.fork` | 直接模型调用 | `ModelForkRequest` | OpEventOf |
| `plugin.register` | 加载与初始化 | `PluginRegisterInput` | EngineEventOf |
| `process.run` | 进程执行 | `{ argv: readonly string[]; init?: ProcessRunInit; }` | OpEventOf |
| `process.spawn` | 进程执行 | `进程启动参数；具体字段需安装声明。` | 当前文档补充 |
| `prompt.attachment` | 上下文与消息装配 | `PromptAttachmentInput` | EngineEventOf |
| `prompt.autocomplete` | 输入与命令 | `当前参考确认 e.token；完整 envelope 按安装声明。` | 当前文档补充 |
| `prompt.compose` | 上下文与消息装配 | `PromptComposeInput` | EngineEventOf |
| `prompt.context` | 上下文与消息装配 | `PromptContextInput` | EngineEventOf |
| `prompt.edit` | 输入与命令 | `PromptEditInput` | EngineEventOf |
| `prompt.fill` | 输入与命令 | `PromptFillInput` | EngineEventOf |
| `prompt.mention` | 上下文与消息装配 | `当前参考确认 path；完整 envelope 按安装声明。` | 当前文档补充 |
| `prompt.read` | 输入与命令 | `NoArgs` | OpEventOf |
| `prompt.section` | 上下文与消息装配 | `PromptSectionInput` | EngineEventOf |
| `prompt.submit` | 输入与命令 | `PromptSubmitInput` | EngineEventOf |
| `prompt.suggest` | 输入与命令 | `PromptSuggestInput` | EngineEventOf |
| `session.append` | 上下文与消息装配 | `SessionAppendInput` | EngineEventOf |
| `session.attach` | 会话与通信 | `SessionAttachInput` | EngineEventOf |
| `session.authorize` | 会话与通信 | `NoArgs` | OpEventOf |
| `session.compact` | 会话与通信 | `SessionCompactInput` | EngineEventOf |
| `session.cwd` | 会话与通信 | `NoArgs` | OpEventOf |
| `session.detach` | 会话与通信 | `SessionDetachInput` | EngineEventOf |
| `session.end` | 会话与通信 | `SessionEndInput` | EngineEventOf |
| `session.id` | 会话与通信 | `NoArgs` | OpEventOf |
| `session.measure` | 会话与通信 | `SessionMeasureInput` | EngineEventOf |
| `session.messages` | 会话与通信 | `NoArgs` | OpEventOf |
| `session.model` | 会话与通信 | `NoArgs` | OpEventOf |
| `session.receive` | 会话与通信 | `SessionReceiveInput` | EngineEventOf |
| `session.repo` | 会话与通信 | `NoArgs` | OpEventOf |
| `session.root` | 会话与通信 | `NoArgs` | OpEventOf |
| `session.send` | 会话与通信 | `目标与发送内容等；完整字段需安装声明。` | 当前文档补充 |
| `session.start` | 会话与通信 | `SessionStartInput` | EngineEventOf |
| `session.surface` | 会话与通信 | `NoArgs` | OpEventOf |
| `session.surfaces` | 会话与通信 | `NoArgs` | OpEventOf |
| `session.turns` | 会话与通信 | `NoArgs` | OpEventOf |
| `session.usage` | 会话与通信 | `SessionUsageArgs` | OpEventOf |
| `session.version` | 会话与通信 | `NoArgs` | OpEventOf |
| `settings.read` | 配置与运行环境 | `SettingsReadArgs` | OpEventOf |
| `skill.prompt` | 上下文与消息装配 | `SkillPromptInput` | EngineEventOf |
| `state.get` | 状态与存储 | `声明的状态访问参数；完整字段需安装声明。` | 当前文档补充 |
| `state.set` | 状态与存储 | `声明的状态写入参数；完整字段需安装声明。` | 当前文档补充 |
| `store.delete` | 状态与存储 | `{ key: string; }` | OpEventOf |
| `store.get` | 状态与存储 | `{ key: string; }` | OpEventOf |
| `store.keys` | 状态与存储 | `NoArgs` | OpEventOf |
| `store.set` | 状态与存储 | `{ key: string; value: unknown; }` | OpEventOf |
| `telemetry.log` | 遥测 | `遥测记录，按内置 namespace 的类型和来源校验。` | 当前文档补充 |
| `telemetry.mark` | 遥测 | `功能标记，按内置 namespace 的类型和来源校验。` | 当前文档补充 |
| `tool.call` | 工具与权限 | `ToolCallInput` | EngineEventOf |
| `tool.check` | 工具与权限 | `ToolCheckInput` | EngineEventOf |
| `tool.describe` | 工具与权限 | `ToolDescribeInput` | EngineEventOf |
| `tool.list` | 工具与权限 | `NoArgs` | OpEventOf |
| `tool.register` | 工具与权限 | `Required<ToolSpec>` | OpEventOf |
| `turn.abort` | 回合与执行控制 | `{ turnId: string; }` | OpEventOf |
| `turn.complete` | 回合与执行控制 | `TurnCompleteInput` | EngineEventOf |
| `turn.start` | 回合与执行控制 | `TurnStartInput` | EngineEventOf |
| `turn.step` | 回合与执行控制 | `TurnStepInput` | EngineEventOf |
| `ui.ask` | UI 绘制与交互 | `可确认 API 调用形式为 question 与 options；完整事件 envelope 未在旧 OpEventOf 中声明。` | 当前文档补充 |
| `ui.blit` | UI 绘制与交互 | `UiBlitArgs` | OpEventOf |
| `ui.close` | UI 绘制与交互 | `PaneCloseInput` | OpEventOf |
| `ui.copy` | UI 绘制与交互 | `当前参考只枚举方法；完整事件输入需安装声明。` | 当前文档补充 |
| `ui.fault` | UI 绘制与交互 | `当前参考确认 phase、reason，及 Client 相关身份。` | 当前文档补充 |
| `ui.focus` | UI 绘制与交互 | `UiFocusInput` | EngineEventOf |
| `ui.input` | UI 绘制与交互 | `UiInputArgument` | EngineEventOf |
| `ui.invalidate` | UI 绘制与交互 | `{ event: InvalidatableEventName; }` | OpEventOf |
| `ui.log` | UI 绘制与交互 | `{ text: string; to: UiLogSink; }` | OpEventOf |
| `ui.message` | UI 绘制与交互 | `UiMessageArgument` | EngineEventOf |
| `ui.notice` | UI 绘制与交互 | `{ tool_use_id: string; text: string &#124; undefined; }` | OpEventOf |
| `ui.open` | UI 绘制与交互 | `PaneOpenArgs` | OpEventOf |
| `ui.panes` | UI 绘制与交互 | `NoArgs` | OpEventOf |
| `ui.press` | UI 绘制与交互 | `UiPressArgument` | EngineEventOf |
| `ui.render` | UI 绘制与交互 | `RenderInput` | EngineEventOf |
| `ui.resolve` | UI 绘制与交互 | `ResolveInput` | EngineEventOf |
| `ui.scroll` | UI 绘制与交互 | `UiScrollInput` | EngineEventOf |
| `ui.select` | UI 绘制与交互 | `UiSelectArgument` | EngineEventOf |
| `ui.selection` | UI 绘制与交互 | `当前参考只枚举方法；完整事件输入需安装声明。` | 当前文档补充 |
| `ui.status` | UI 绘制与交互 | `{ text: string &#124; undefined; }` | OpEventOf |
| `ui.toast` | UI 绘制与交互 | `{ text: string; timeoutMs?: number; }` | OpEventOf |

## 6. 不能由本清单推出的结论

- 不存在适用于所有安装与任务的固定全局直线。插件扩展 namespace 还会增加事件。
- 公开 EventOf 不包含已证明的全部宿主内部调度、网络重试、缓存和取消实现。
- on("*") 不是全内部 trace：还受层级、匹配、重入、遥测过滤等约束。
- 141 是本次已确认名称的覆盖计数；不是宣称已获取最新安装的完整生成类型。
- 精确的一次任务先后关系需要目标版本的运行证据；本文没有冒称进行过宿主执行验证。

## 7. 来源与维护

- [固定公开 TypeScript 契约](https://github.com/anthropics/claude-code/blob/3deb873687379f0c199a69fdaccc65f0865f7a29/mods/types/claude-code.d.ts)：逐条输入、结果、事件/API 语义。
- [Mods reference](https://code.claude.com/docs/en/plugins/mods/reference)：当前事件与方法目录、版本补充。
- [Mods 事件处理](https://code.claude.com/docs/en/plugins/mods/events)：中间件、策略顺序、失败与暂停。
- [Hooks reference](https://code.claude.com/docs/en/hooks)：传统生命周期与每类事件决策。
- [Mods API 指南](https://code.claude.com/docs/en/plugins/mods/api)：直接模型请求、工具注册与会话通信。
- [智能体执行原理](https://code.claude.com/docs/en/how-claude-code-works)：宿主、模型、工具与上下文职责。
- 本地仅保留 Markdown 版本 event-catalog.md；编写阶段的中间数据及生成脚本已清理。
