# SkillOpt-Sleep 😴：部署阶段的学习助手（预览版）

> 原始资料：[SkillOpt-Sleep 官方文档](https://github.com/microsoft/SkillOpt/blob/79124b37e9a6371e13b753f8bcd7adb1e493ade1/docs/sleep/README.md)
> 本文为已存档官方文档的中文翻译；命令、配置键、模型名、实验数据及资料链接保留原样。

**SkillOpt-Sleep** 将 SkillOpt 的方法应用到你自己的日常使用中。它为本地编码 Agent 提供每晚执行的**睡眠周期**：回顾过去的会话，在你设定的 API 预算内回放经常出现的任务，再将学到的内容整合成**经过验证**的长期记忆和技能。更新需要通过留出任务的验证门控，并暂存供你审核。这个过程**不需要训练模型权重**，也不会给普通 Agent 请求增加额外的优化循环。

> **预览版。** 这是一个仍在积极迭代的早期预览版本，接口和默认配置可能变化。引擎位于顶层 [`skillopt_sleep/`](https://github.com/microsoft/SkillOpt/tree/main/skillopt_sleep) 包中，**完全不依赖**论文中的 `skillopt/` 代码；验证门控代码以独立副本的形式内置。

## 工作原理

一“夜”的流程如下：

```text
采集 Claude Code / Codex / VS Code Copilot / Cursor / Pi / OpenCode 会话记录
  → 挖掘重复出现的任务
  → 通过配置的后端回放（隔离程度因后端而异；mock/handoff 不发起网络调用）
  → 整合（反思 → 有限幅度编辑 → 在真实留出任务上执行验证门控）
  → 暂存提案 → 由你采纳
```

它结合了 **SkillOpt**（由验证门控约束的有限文本编辑）、**Claude Dreams**（离线整合、先审核后采纳）和 **agent-sleep** 的理念（将短期经验转化为长期能力）。

可选配置项 `gate_no_regression` 可以加强聚合门控。为保持兼容性，其默认值是 `false`；设为 `true` 后，每个验证任务在所配置的 `gate_metric` 下都必须保持原分数或提高分数。该检查适用于中间技能候选、记忆候选，以及重新执行的最终回放。如果缺少任务结果，或任务分数不是有限数值，候选更新也会被阻止；缺少数值型分数则会中止评估。任务级变化会记录在 `report.md`、`report.json`、`diagnostics.json`、CLI 的 `--json` 输出以及证据日志中。

基于规则的标题检查刻意采用增量扩展方式。对现有任务集，`section_present` 保留原有的严格行为：ATX 标题不能在要求的名称后追加文字。如果带编号、双语或注释的 ATX Markdown 标题也应通过检查，可使用 `section_contains`。它仅在 ATX 标题内对要求的文本进行不区分大小写的字面匹配，不会匹配加粗行、标签或普通正文。这两个操作符都只检查形式，应搭配结果检查或有实质内容的评分标准。

> **数据边界。** 采集在本地进行，且只读取数据。`mock` 后端不会调用模型服务商。但真实后端会将采集会话的截断片段及其衍生任务发送给你选定的服务商，用于挖掘、回放、评分和反思。目前不能保证发出的提示词不包含秘密信息；在敏感项目上运行前，应检查会话来源和服务商的数据政策。若需要可审核的流程，可先将采集结果写入任务文件，检查并脱敏，将其标记为 `"reviewed": true`，然后再通过真实后端回放该文件。
>
> Cursor 数据源读取本地用户／助手消息文本、明确的回合错误和工具名称，但排除工具参数、工具输出及非消息记录。已知的疑似秘密字符串会被脱敏，这只是纵深防御。Cursor 后端通过 `cursor-agent` 发送提示词；普通调用在空临时工作区中使用只读 Ask 模式，并禁止访问项目文件。Cursor 的工具感知回放暂时禁用，等待真实环境中的权限边界验证。因此，Cursor 及其选择的模型服务商可能接收到会话衍生内容。
>
> VS Code Copilot 数据源从已确认的 GitHub Copilot Chat 请求中读取本地用户输入的提示词、可见的助手 Markdown 和工具名称。它排除系统通知、推理内容、工具输入／输出、渲染后的上下文以及账户／模型元数据。已知的疑似秘密字符串会被脱敏，但这仍属于纵深防御，不能作为保证。
>
> Pi 数据源读取 `~/.pi/agent/sessions` 下的本地会话，保留用户／助手文本、工具名称，以及用户文本中的词语层面反馈。它排除思考内容、工具参数、工具输出、图片和无关元数据。会话头中的项目绝对路径 `cwd` 会被保留以进行范围筛选，也可能出现在发送给真实后端及其服务商的挖掘提示词中。对保留消息文本中的已知疑似秘密字符串进行脱敏，也仅是一项纵深防御措施。
> Pi 后端使用本机已安装并完成身份验证的 Pi CLI 联系用户选定的模型服务商。调用会禁用工具、技能、上下文文件、扩展、提示词模板、主题和会话写入，但保留 Pi 的身份验证与模型配置。Pi 的离线启动模式还会阻止已配置的 npm/git 包安装、包更新和模型目录刷新，但不会阻止对选定服务商的调用。这不构成永久或完整隔离的保证。在发送来自敏感会话的衍生提示词前，应检查服务商的数据保留和隐私政策。
>
> 默认情况下，每次有状态的夜间运行还会在项目暂存目录树下写入本地 `evidence.jsonl`；若已暂存报告，则放在报告旁边。试运行会将证据写入配置的 Sleep 状态目录。日志包含挖掘、回放、评分和反思过程中提示词与回复的副本，采用尽力而为的脱敏，并按字段截断。应将其视为敏感本地数据，采用适当的保留策略。设置 `"evidence_log": false` 可禁用日志；设置 `"redact_secrets": false` 则会主动关闭这层纵深防御脱敏。

## 使用方式

### 最快捷的方式：通过 pip 安装 `skillopt-sleep` CLI

```bash
pip install skillopt        # installs the engine + the `skillopt-sleep` command
skillopt-sleep dry-run      # harvest + mine + replay, report only; stages nothing
skillopt-sleep run          # a full nightly cycle; the proposal is staged for review
skillopt-sleep status       # show state + the latest staged proposal
skillopt-sleep adopt --legacy       # apply a reviewed managed proposal
skillopt-sleep adopt --skill NAME   # adopt one staged skill (repeatable)
skillopt-sleep adopt --all-skills   # adopt every still-pending fan-out skill
skillopt-sleep schedule     # install a nightly cron entry for this project
```

上述命令依次用于：安装引擎和 CLI；只生成报告的试运行；完整夜间循环并暂存提案；查看状态与最新提案；应用已审核的托管提案；采纳一个暂存技能；采纳全部待处理的扇出技能；为当前项目安装夜间 cron 定时项。

> **版本说明。** 本页跟随 `main` 分支。PyPI 0.2.0 提供上述基础命令。Cursor 数据源／后端／插件支持、VS Code Copilot 会话采集、Pi 数据源／后端支持、Sleep 交接、非 Azure 的 OpenAI 兼容端点、OpenCode Sleep 数据源／后端支持，以及 `--preferences`、多技能扇出和审核后按子集采纳等功能，是后续加入的；在下一版发布前，需要从 `main` 分支源码安装。

下面各 Agent 的集成仍来自仓库；上面的 CLI 则是只需 pip 即可独立运行周期的方式。Claude Code、Codex、Cursor、Copilot 和 Devin 都封装了共享引擎。OpenClaw 是单独的参考适配，使用自己的配置方式。

一个共享引擎，各 Agent 使用轻量封装，见 [`plugins/`](https://github.com/microsoft/SkillOpt/tree/main/plugins)：

| 平台 | 目录 | 安装方式 |
|---|---|---|
| **Claude Code** | [`plugins/claude-code`](https://github.com/microsoft/SkillOpt/tree/main/plugins/claude-code) | `/plugin marketplace add ./plugins/claude-code` → `/skillopt-sleep` |
| **Codex** | [`plugins/codex`](https://github.com/microsoft/SkillOpt/tree/main/plugins/codex) | `bash plugins/codex/install.sh` → `skillopt-sleep` 技能 |
| **Cursor** | [`plugins/cursor`](https://github.com/microsoft/SkillOpt/tree/main/plugins/cursor) | `bash plugins/cursor/install.sh` → `/skillopt-sleep` |
| **Copilot** | [`plugins/copilot`](https://github.com/microsoft/SkillOpt/tree/main/plugins/copilot) | 将 `plugins/copilot/mcp_server.py` 注册为 MCP 服务器 |
| **Devin** | [`plugins/devin`](https://github.com/microsoft/SkillOpt/tree/main/plugins/devin) | 将 `plugins/devin/mcp_server.py` 注册为 MCP 服务器 |
| **OpenClaw** | [`plugins/openclaw`](https://github.com/microsoft/SkillOpt/tree/main/plugins/openclaw) | 根据安装环境调整参考封装及路径 |

### VS Code GitHub Copilot Chat

使用 `--source copilot` 采集本地 VS Code GitHub Copilot Chat 会话。SkillOpt 会自动检测稳定版和 Insiders 版 VS Code 的 `User/workspaceStorage` 根目录；如果存在 `VSCODE_PORTABLE`，也会检测便携版根目录。可通过 `--vscode-workspace-storage PATH` 覆盖自动发现。项目范围根据各存储项旁的 `workspace.json` 确定，无法安全映射到本地项目的项会被跳过。`--source auto` 仍优先选择 Codex，再选择 Claude，不会选择 Copilot。

```bash
skillopt-sleep harvest --project "$(pwd)" --source copilot --progress
skillopt-sleep dry-run --project "$(pwd)" --source copilot --backend copilot
```

数据源和后端相互独立：`--source copilot` 读取 VS Code 的本地历史，而 `--backend copilot` 使用另行安装并完成身份验证的 GitHub Copilot CLI 执行挖掘、回放、评分和反思。在敏感项目中使用真实后端前，应先检查采集到的任务。

托管调度器不会保留 `--source` 或 `--vscode-workspace-storage`。安排该数据源的定时任务前，应在 `~/.skillopt-sleep/config.json` 中设置 `"transcript_source": "copilot"`；若使用非标准根目录，还应设置 `"vscode_workspace_storage": "/absolute/path/to/workspaceStorage"`。

### Pi

Pi 会话采集与模型执行相互独立。使用 `--source pi` 读取 `~/.pi/agent/sessions` 下的本地 JSONL 会话文件，或通过 `--pi-home` 指定包含 `agent/sessions` 的父目录，默认是 `~/.pi`。单独使用该数据源不需要安装 Pi CLI，也不需要完成服务商身份验证。Pi 从不会被隐式选中：`--source auto` 仍优先选择 Codex，再选择 Claude。

`--backend pi` 使用本地已安装并完成身份验证的 Pi CLI，在挖掘、回放、评分和反思阶段发起真实的模型服务商调用。可用 `--pi-path` 选择可执行文件，用 `--model` 覆盖已配置模型：

```bash
skillopt-sleep run --project "$(pwd)" \
  --source pi --backend pi --pi-path /absolute/path/to/pi \
  --model provider/model --max-sessions 5 --max-tasks 3 --progress
```

这些调用会禁用工具、技能、上下文文件、扩展、提示词模板、主题和会话写入，但仍使用用户的 Pi 身份验证和模型配置。它们还会启用 Pi 的离线启动模式，阻止已配置的 npm/git 包安装、包更新和模型目录刷新；仍会联系选定的模型服务商。这些控制只约束本次调用的启动配置，不代表永久或完整隔离。真实的 Pi 后端会将会话衍生提示词发送给 Pi 中配置的服务商，应先检查其数据保留和隐私政策。`mock` 和 `handoff` 后端不会发起网络调用。

托管调度器会记录后端，但不会保留 `--source`、`--pi-home`、`--pi-path` 或 `--model`。为 Pi 设置定时任务前，应在 `~/.skillopt-sleep/config.json` 中设置 `transcript_source`、`pi_home`、`pi_path` 和 `model`。`pi_path` 应使用绝对路径，并确认定时任务所用账户已完成 Pi 身份验证。

### OpenCode

使用 `--source opencode` 读取本地 OpenCode SQLite 历史，无需启动 CLI、登录或访问模型服务商。`--source auto` 不会选择它。数据库选择及数据保留边界见 [CLI 参考](https://github.com/microsoft/SkillOpt/blob/79124b37e9a6371e13b753f8bcd7adb1e493ade1/docs/reference/cli.md#opencode-source-and-backend)。

若要发起模型调用，请按[官方文档](https://opencode.ai/docs/)安装并配置 OpenCode，再使用 `opencode --version` 确认 CLI 可用。

`--backend opencode` 通过已安装的 OpenCode CLI 发送 SkillOpt 的模型调用，执行挖掘、普通任务回放、评分和反思。它沿用用户现有的登录状态、服务商环境变量及文件形式的全局配置。仅在 OpenCode 默认设置不合适时，才需要指定可执行文件和模型：

```bash
skillopt-sleep run --project "$(pwd)" \
  --source opencode --backend opencode \
  --opencode-path /absolute/path/to/opencode --model provider/model
```

普通调用会禁用项目配置、模型发起的工具调用、外部插件及已配置的 MCP 服务器。如果无法确认所有解析出的 MCP 服务器均已禁用，SkillOpt 会在模型调用前停止。

工具感知回放默认关闭。对于规则评分器包含 `tool_called` 检查的任务，可通过 `--opencode-tool-replay` 或 `"opencode_tool_replay": true` 启用。该模式会提供名称随机、结果固定的临时合成工具，核实 OpenCode 实际调用了哪些工具，并拒绝所有其他工具。历史工具参数和结果不会被保留或回放。

两种模式都会继续使用 OpenCode 的常规数据目录和文件形式的全局配置。因此，这些调用可能出现在会话历史中，全局自定义 JS/TS 工具也可能初始化，不过 SkillOpt 不允许模型调用它们。完整的配置、历史记录和隔离细节见 [CLI 参考](https://github.com/microsoft/SkillOpt/blob/79124b37e9a6371e13b753f8bcd7adb1e493ade1/docs/reference/cli.md#opencode-source-and-backend)。

定时运行时，请按需在 `~/.skillopt-sleep/config.json` 中配置数据源、数据库、可执行文件和模型。将其中的 `opencode_tool_replay` 设为 `true`，即可启用工具感知回放。

### Cursor

Cursor 会话采集与模型执行相互独立。使用 `--source cursor` 读取 `~/.cursor/projects/<workspace>/agent-transcripts/*/*.jsonl`。`--scope invoked` 使用 Cursor 记录的工作区路径，必要时回退到经过净化处理的存储目录；`--scope all` 则扫描所有 Cursor 工作区。可用 `--cursor-home` 指定不同的 Cursor 主目录。`--source auto` 仍优先选择 Codex，再选择 Claude，不会选择 Cursor。

`--backend cursor` 需要已安装并完成身份验证的 `cursor-agent`。如果它不在 `PATH` 中，可通过 `--cursor-path`、`SKILLOPT_SLEEP_CURSOR_PATH` 或配置项 `cursor_path` 指定。可通过 `--model` 或 `SKILLOPT_SLEEP_CURSOR_MODEL` 选择模型。采纳目标应是项目中的 Cursor 技能，而不是插件本身的工作流技能：

```bash
skillopt-sleep run --project "$(pwd)" \
  --source cursor --backend cursor \
  --target-skill-path .cursor/skills/skillopt-sleep-learned/SKILL.md \
  --max-sessions 5 --max-tasks 3 --progress
```

目标技能以提示词文本形式提供给 Cursor，不会作为原生技能调用。`--project` 决定会话范围、目标文件、状态和暂存位置，但普通 Cursor 调用无法检查该项目的文件。因此，当前后端评估的是文本指导，而不是端到端的仓库、CLI、浏览器或服务工作流。

Cursor 的工具感知回放暂时禁用，等待真实 Cursor 环境中的权限边界验证。如果任务包含 `tool_called` 检查，Cursor 后端会在启动 Agent 模式前以非零状态退出，不会暂存、采纳或推进状态。此类任务应使用其他后端。

初始采集窗口为 72 小时。若需要考虑更早的会话，请显式设置 `--lookback-hours N`；设为 `0` 会在会话数量限制内扫描全部历史。即使没有挖掘出任务，有状态的 `run` 也会推进采集检查点。可先使用 `harvest` 或 `dry-run` 查看数量。使用真实后端的 `dry-run` 仍会发起服务商调用并产生费用；会话／任务数量限制不是严格的调用次数、token、时间或金额预算。

托管调度器只记录项目、后端、时间及可选的自动采纳设置。它不会保留 Cursor 数据源、主目录、CLI 路径、模型或目标技能等命令行选项。运行 `skillopt-sleep schedule --backend cursor` 前，应在 `~/.skillopt-sleep/config.json` 中设置 `transcript_source`、`cursor_home`、`cursor_path`、`model` 和 `target_skill_path`。目标可以继续使用项目相对路径 `.cursor/skills/skillopt-sleep-learned/SKILL.md`。`cursor_path` 应使用绝对路径，并确认定时任务账户已完成身份验证，因为 cron 和任务计划程序运行时的环境可能非常精简。

若要使用 DeepSeek、vLLM、Ollama 或其他 Chat Completions 服务器，请参阅 **[OpenAI 兼容端点](https://github.com/microsoft/SkillOpt/blob/79124b37e9a6371e13b753f8bcd7adb1e493ade1/docs/sleep/openai-compatible-endpoints.md)**。该指南还说明了 Azure 托管身份凭据单独适用的“仅限 HTTPS”边界。

确定性验证，无需 API 密钥：
`python -m skillopt_sleep.experiments.run_experiment --persona researcher --assert-improves`。

### 可选功能：按技能扇出

在 `~/.skillopt-sleep/config.json` 中设置 `"multi_skill_fanout": true`，可为当晚挖掘到的每个显式技能提示分别生成门控结果和可审核提案。`multi_skill_report` 仍作为兼容别名保留：

```json
{"multi_skill_fanout": true}
```

这会为每个分组额外执行一次整合；当带技能提示和不带提示的证据混合出现时，还会包含一个兜底分组。因此，后端调用和 token 用量会成倍增加；配置的梦境轨迹执行和合成变体也会进一步增加每组工作量。每组继承所配置的编辑预算、门控模式／指标、`gate_no_regression`、`dream_rollouts`、`dream_factor`、`recall_k` 和 `evolve_skill`。从归档召回的任务必须具有相同的技能提示；扇出运行中的共享记忆是只读的。因此，将 `evolve_skill` 设为 `false`，会同时禁用按技能提案和托管技能提案。

每个带显式技能提示的分组，都会在整合前解析并读取自己的现用 `SKILL.md`，使暂存提案保留该技能原有的基线。对于缺失、有歧义、不可读、存在别名或冲突的技能，会跳过并报告，而不会回退到托管文档。采纳仍由审核驱动：用 `adopt --skill NAME` 或 `--all-skills` 选择扇出提案，用 `adopt --legacy` 处理同时暂存的托管技能／记忆对。`auto_adopt` 从不会自动采纳按技能生成的扇出提案。当某晚只有托管兜底组时，仍保持原有的单次整合行为。

解析过程先搜索现有的项目原生目录 `.agents/skills`、`.claude/skills`、`.cursor/skills` 和 `.devin/skills`，再搜索既定的 Claude 主目录及插件缓存根目录。如果某个集成将技能存放在其他位置，可重复添加 `--skill-root PATH`。相对根路径以 `--project` 为基准解析。

### 可选功能：经验回放与梦境轨迹执行

这两种整合机制默认都**关闭**；除非主动启用，否则不会改变行为。当任务具有清晰的正确性信号时，它们可以加强夜间更新；最终交付哪些更新，仍由验证门控决定。

| 配置项 | 默认值 | 作用 |
|---|---|---|
| `dream_rollouts` | `1` | 每个任务执行 K 次，通过好坏结果对比进行学习，即对比式反思。 |
| `recall_k` | `0` | 联想召回：从持久化归档中取出 K 个最相似的历史任务，加入当晚的梦境过程。 |
| `dream_factor` | `0` | 为每个任务增加 N 个轻量合成变体。 |

### 配对 A/B 评估工具包

声称“B 优于 A”的报告和 PR，应使用共享评估工具包，而不是引用单次运行结果。一个命令即可在同一份固定任务清单上配对比较两种条件，运行 McNemar 检验，并报告成功率差值的 bootstrap 置信区间。夜间门控保持不变。

```text
python -m skillopt_sleep.evalkit --manifest tasks.json --a cond_a.json --b cond_b.json
```

ID 集合约定、对按位置重复的随机种子进行任务簇层面推断、A/A 检查，以及仅复现公开 RESULTS 结果单元点估计的方法，见 [`evalkit.md`](https://github.com/microsoft/SkillOpt/blob/79124b37e9a6371e13b753f8bcd7adb1e493ade1/docs/sleep/evalkit.md)。

## 实验结果

> 📊 **更多结果与分析，包括门控安全压力测试、经验回放扩展实验和梦境多样性消融，见 [`docs/sleep/RESULTS.md`](https://github.com/microsoft/SkillOpt/blob/79124b37e9a6371e13b753f8bcd7adb1e493ade1/docs/sleep/RESULTS.md)。** 主要结果如下。

**受控实验配置，不是已发布 CLI 的默认配置。** 共 5 夜，每夜新增 10 个真实的“当天”任务；完整留出**测试集**分别在第 1 夜之前（基线）和第 5 夜之后（更新后）评分；优化器为 GPT-5.5；使用单个随机种子（42）。实验采用随项目提供的整合与门控组件，但夜间 CLI 与基准测试框架是不同入口。数值表示留出集上的绝对准确率；**Δ** = `after − baseline`，单位为百分点。

**（a）真实 Agent 上的端到端实验：[gbrain-evals](https://github.com/garrytan/gbrain-evals) `skillopt-v1`。** 当目标 Agent 分别为 **Claude Code 和 Codex** 时，存在缺陷的种子技能在留出集上的分数均从 **0.00 → 1.00**，覆盖全部 4 个种子技能，其中包含真实工具使用循环。

**（b）经验回放扩大收益：SearchQA**。留出测试集包含 1,400 个样本，采用 SQuAD 精确匹配；目标模型为 GPT-5.5，**启用验证门控**：

| 回放配置（`dream_rollouts=5`） | 基线 → 更新后 | Δ（百分点） |
|---|---|---|
| `recall_k=10` | 0.802 → 0.834 | +3.1 |
| `recall_k=20` | 0.803 → 0.848 | **+4.5** |
| 全历史回放，作为参考而非发布默认值 | 0.796 → 0.851 | +5.6 |
| `recall_k=10`、`dream_rollouts=8`，增加梦境次数、召回数量不变 | 0.798 → 0.835 | +3.7 |

随着相关历史经验召回量增加，收益单调上升。相同 SearchQA 配置在**关闭**门控时，`recall_k=10` 的结果为 0.808 → 0.839（+3.1）。

**（c）第二个基准：SpreadsheetBench**。留出测试集包含 280 个样本；执行 Agent 生成的 openpyxl 代码，并与标准工作簿逐单元格比较；目标模型为 GPT-5.4-nano；不启用门控，但保留输出契约护栏：0.279 → 0.314（**+3.6**）。

**（d）适用范围说明。** 这些收益出现在任务重复发生、且正确性可以检查的场景。在接近饱和或噪声较大的基准上，例如强模型已接近上限时，效果在**运行间噪声范围内基本持平**。这里单个随机种子的基线波动为 ±1–2 个百分点，因此应将低于约 1.5 个百分点的差异视为噪声。验证门控能限制最坏情形，默认应保持**开启**。

## 更多资料

为每个技能暂存一份提案并采纳已审核子集的**底层** API，包括 `staged_skills`／`adopt_skills`，以及 `status` 和 `adopt --skill`，见 [`docs/sleep/multi-skill-staging.md`](https://github.com/microsoft/SkillOpt/blob/79124b37e9a6371e13b753f8bcd7adb1e493ade1/docs/sleep/multi-skill-staging.md)。该页还介绍了可选的夜间扇出机制：每个带技能提示的分组都根据各自解析出的现用 `SKILL.md` 生成提案，但是否采纳仍由人明确决定。

另请参阅 [SkillOpt 文档索引](https://github.com/microsoft/SkillOpt/blob/79124b37e9a6371e13b753f8bcd7adb1e493ade1/docs/index.md)、[CLI 参考](https://github.com/microsoft/SkillOpt/blob/79124b37e9a6371e13b753f8bcd7adb1e493ade1/docs/reference/cli.md)，以及 [`plugins/`](https://github.com/microsoft/SkillOpt/tree/main/plugins) 下各集成的 README。
