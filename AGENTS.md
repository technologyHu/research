# 项目约定

本文件适用于本仓库的调研、技能维护、图谱维护和文件整理。按本轮授权开展工作，保留用户已有改动。

## 入口技能

入口技能可直接承接用户请求，也可由其他流程按需调用。单个事实查询直接回答。

| 本轮目标 | 技能 | 适用范围 |
| --- | --- | --- |
| 登记主题、制定调研计划、调研或续查 | [research](.agents/skills/research/SKILL.md) | 论文、开源项目、产品和评测。 |
| 基于已有成果分析主题或问题 | [research-analysis](.agents/skills/research-analysis/SKILL.md) | 综合已有调研，贡献者的思考可作为补充材料。 |
| 提交已有调研或分析洞察报告 | [research-commit](.agents/skills/research-commit/SKILL.md) | 直接校验已有成果，再按篇提交。 |
| 保存指定网页文章 | [web-article-fetcher](.agents/skills/web-article-fetcher/SKILL.md) | 归档为 Markdown，保留来源。 |
| 理解代码库、模块或调用链 | [code-understanding](.agents/skills/code-understanding/SKILL.md) | 按问题选择源码阅读或图谱工具。 |
| 绘制架构图、流程图等技术图 | [draw-diagram](.agents/skills/draw-diagram/SKILL.md) | 按用途选择图的形式和后端，遵守[图片使用与生成](#图片使用与生成)约束。 |
| 润色已有正文 | [humanizer](.agents/skills/humanizer/SKILL.md) | 保留事实、技术术语和引用。 |
| 创建或更新仓库技能 | [skill-creator](.agents/skills/skill-creator/SKILL.md) | 使用仓库内的版本，按[技能维护](#技能维护)约定执行。 |

用户或外层任务按已授权目标分别选择 `research`、`research-analysis` 和 `research-commit`。这三个入口互不引用、调用或经由子技能回调。

共用规则见 [research-common](.agents/skills/research-common/SKILL.md)。对象调研与补查可调用 [research-deep](.agents/skills/research-deep/SKILL.md)，成稿与校验可调用 [research-report](.agents/skills/research-report/SKILL.md)。绘图等子技能也可共用，各自只返回当前阶段的结果。

### 可独立使用的专项技能

| 本轮目标 | 可直接使用的技能 |
| --- | --- |
| 调研已明确类型的对象 | 论文用 [research-paper](.agents/skills/research-paper/SKILL.md)，开源项目用 [research-open-source](.agents/skills/research-open-source/SKILL.md)，产品用 [research-product](.agents/skills/research-product/SKILL.md)，评测用 [research-benchmark](.agents/skills/research-benchmark/SKILL.md)。 |
| 增补调研对象或分析来源 | [research-add-items](.agents/skills/research-add-items/SKILL.md) |
| 补充问题或比较维度 | [research-add-fields](.agents/skills/research-add-fields/SKILL.md) |
| 使用 GitNexus | 索引管理用 [gitnexus-cli](.agents/skills/gitnexus-cli/SKILL.md)，代码探索用 [gitnexus-exploring](.agents/skills/gitnexus-exploring/SKILL.md)，工具用法见 [gitnexus-guide](.agents/skills/gitnexus-guide/SKILL.md)。 |
| 使用 Understand Anything | 图谱分析用 [understand](.agents/skills/understand/SKILL.md)，专项用法见 [code-understanding 的后端说明](.agents/skills/code-understanding/SKILL.md#绑定项目与准备后端)。 |
| 构建或查询 Graphify 图谱 | [graphify](.agents/skills/graphify/SKILL.md) |
| 使用指定绘图后端 | [fireworks-tech-graph](.agents/skills/fireworks-tech-graph/SKILL.md) 或 [diagram-design](.agents/skills/diagram-design/SKILL.md)，同样遵守[图片使用与生成](#图片使用与生成)约束。 |

## 调研资料布局

### 主题与计划

- 主题 ID、名称和父子关系统一登记在根目录的 [themes.yaml](themes.yaml)。本轮只登记主题时，仅更新注册表。
- 计划只收录有具体调研目标的任务、明确纳入的既有报告和用户指定加入的对象。符合条件的正式对象调研复用对应计划，缺失时自动创建。[计划纳入条件](.agents/skills/research-common/references/theme-planning.md#计划纳入条件)
- 计划用「核心问题」记录主题共同关注的问题，用「对象与任务」记录验收、成果、缺口和下一步。[共用计划模板](.agents/skills/research-common/references/theme-plan-template.md)
- 新增或实质改写核心问题前须经用户确认。暂无已确认的问题时留空。单个对象或本轮任务的问题记在执行范围中。[核心问题的确认](.agents/skills/research-common/references/theme-planning.md#核心问题的确认)
- 每个入口在同一主题下只维护一份当前计划，修订沿用原文件。跨入口计划用链接关联，共用范围只维护一处。

### 报告与交付

| 成果类型 | 报告目录 | 当前计划 |
| --- | --- | --- |
| 调研报告 | `research-reports/<主题名>/<type>/<target>__YYYYMMDD-HHmmss/` | `research-reports/<主题名>/plan.md` |
| 分析洞察 | `analysis-reports/<主题名>[__<专题>]__YYYYMMDD-HHmmss/` | `analysis-reports/<主题名>.plan.md` |

- 对象调研按实际类型归类，使用 `paper`、`open-source`、`product` 或 `benchmark`。综述论文归 `paper`，报告专题以 `survey-` 开头。分析洞察的内部类型为 `analysis`。
- 两类成果都将各级主题合写为一个目录名，主报告文件默认为 `report.md`。调研报告用 `-` 连接各级主题。分析洞察在成果根目录下只建一层报告目录，主题各级及主题与专题之间用 `__` 分隔。新分析计划文件名沿用该主题名。
- `target` 表示本篇报告的研究专题，可以独立于对象 ID。新专题的命名片段数量不限，片段之间用 `__` 分隔，片段内用 `-` 连接单词。主题 ID、各级 slug 和对象 ID 沿用原有规则。正式中文对象名称等例外按交付规范处理。
- 报告目录的时间后缀使用创建或最近修订的北京时间。修订时保留报告 ID 和最初创建时间，用 `stamp-report` 更新目录及引用。旧报告、旧计划和旧名称原地维护。需要迁移时，按用户明确的范围执行并同步链接。
- 正式目录只保存交付的报告、引用资料、图片和已登记的附加文件。单次任务的中间文件放在对应报告目录的 `.tmp/<run-id>/`。
- 报告中的本地链接使用相对于当前 Markdown 的路径。持久配置使用可移植路径，避免写入个人机器的绝对路径。
- 交付时分别说明文件校验结果、研究完整度和实际执行的验证。部分成果按已验证的范围陈述。

保存与清理的详细规则统一维护在[交付规范](.agents/skills/research-common/references/delivery-policy.md)中。变更规则时同步维护相关技能引用。

## 图片使用与生成

按解释需要配图。来源明确且有助于理解的原图、产品或软件界面和演示 GIF 可直接引用。需要新绘且满足图像能力条件时，优先使用 Markdown 可渲染的代码图。需要精确布局、原貌证据或其他视觉表达时，按需复用原图、绘制静态图或使用图片生成工具。[图表与代码](.agents/skills/research-common/references/writing-policy.md#图表与代码)

生成、重绘、修改、渲染或导出新图片前，必须确认当前执行模型能实际接收并理解图片。已有源文件、可用渲染器、导出请求和“跳过视觉复核”均不能证明模型具备该能力。

缺少图像理解能力或无法确认时，按以下规则处理。

- 只能下载、复制和引用用户提供或来源明确的现有原图。没有合适图片时使用文字或表格。
- 可以进行不生成图片的文件、链接和来源核对，不推断看不到的图内细节，也不宣称完成视觉复核。
- 明确要求的新图无法交付时说明限制，不把原图复用称为新图生成。

该条件覆盖调研、绘图入口、`diagram-design`、`fireworks-tech-graph`、全局旧版技能和直接调用脚本。SVG、HTML、Mermaid、定量绘图库、格式转换、截图、动画和测试样图同样适用。委派给其他技能、子代理、外部模型或服务也须遵守。更新绘图技能时保留本项目约束。

## 图谱与 README

- README 中 `research-graph:start` 与 `research-graph:end` 之间的内容由[生成脚本](scripts/research_graph.py)维护。更新数据时修改对应的计划、报告或其他输入。调整展示时修改生成脚本。修改后重新生成，人工说明写在标记区外。
- 本地图谱索引 Git 已跟踪的文件和已暂存的新文件。远程图谱使用已推送的分支内容。[图谱维护指南](docs/research-graph-guide.md)
- 生成预览、截图或运行会生成图片的测试前，按[图片使用与生成](#图片使用与生成)确认图像能力。

## 技能维护

- 优化或更新仓库技能前，必须先读取并使用仓库内的 [skill-creator](.agents/skills/skill-creator/SKILL.md)，按适用于本次改动的流程执行和验证。
- 修改技能入口、引用或脚本接口时，核对相关调用方，并按改动范围选择验证项。[仓库贡献指南](docs/repository-guide.md#按改动选择检查)

## 目录保留与清理

- 按需创建目录。清理前核对具体路径、实际用途、依赖和明确的保留要求。未跟踪、目录为空或暂时没有报告，均不能作为删除依据。
- 清理 `.agents/skills/` 前，区分旧安装副本、可再生缓存和当前运行依赖。锁文件、初始化脚本、固定版本源码包和被 Git 忽略的运行环境均按实际依赖处理。
- `docs/`、`scripts/`、`tests/` 和 `.github/workflows/` 包含图谱展示、生成、测试与发布设施，暂时没有报告时仍有用途。删除报告时默认保留这些设施。
- 只在用户已明确授权的范围内清理。受管任务的临时文件按交付规范处理，检查通过不代表取得删除授权。同一已授权范围无需重复询问。
- 在 Windows 上删除或移动前，核对解析后的绝对目标路径和链接属性，并在同一原生 shell 中操作。工具策略拒绝时，说明被拒绝的操作和返回原因，不换工具或改写路径绕过拒绝。

## Git 跟踪与提交

- `AGENTS.md` 纳入版本管理。用户只要求纳入跟踪时，仅暂存指定文件，保留其他暂存内容。
- 调研和分析入口负责产出、校验和计划回写。提交、推送和发布分别按当前会话的授权执行。改写已发布历史须有明确授权。
- 报告及必要附件按篇提交，同篇报告在本轮的修订集中提交。符合条件时合并未发布的本地修订。项目规则、技能和图谱工具的维护与报告分别提交。
- 精确指定文件时使用 `git --literal-pathspecs`。用户要求只提交已暂存内容时，以索引中的版本为准。保留与本次提交无关的工作区修改。
