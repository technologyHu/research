 # research 仓库使用、贡献与维护指南

## 从哪里开始

主题登记维护分类和父子关系。计划记录该主题下的具体任务、验收条件和成果链接。报告保存实际查到的证据、结论和待查事项。[主题注册表](../themes.yaml) · [项目约定](../AGENTS.md)

| 你现在要做什么 | 从这里开始 |
| --- | --- |
| 找到已有计划和报告 | [调研报告总览](../README.md#调研报告总览) · [分析洞察报告总览](../README.md#分析洞察报告总览) · [调研与分析计划总览](../README.md#调研与分析计划总览) |
| 登记主题、制定计划、新做调研或续查 | [开展调研与维护计划](#开展调研与维护计划) |
| 从已有报告得出新的认识 | [基于已有成果做分析](#基于已有成果做分析) |
| 处理文章、源码、配图或报告文字 | [查资料、读源码、配图和润色](#查资料读源码配图和润色) |
| 交付报告、回写计划或准备提交 | [交付与提交](#交付与提交) |
| 修改技能、图谱或仓库文档 | [维护与排查](#维护与排查) |

在对话中说明要用的技能和本轮目标。示例中的路径相对于仓库根目录，尖括号内换成实际信息。阅读现有成果用 Markdown 阅读器或浏览器即可，执行任务时按所选技能准备环境。单个事实可以直接提问。

`research`、`research-analysis` 和 `research-commit` 分别处理对象调研、分析洞察和报告提交。按本轮目标选择入口，提交时直接使用已有报告。

## 开展调研与维护计划

使用 `research` 处理主题登记和对象调研，支持论文、开源项目、产品和评测。先选本轮要交付什么，再给出与该任务有关的资料。需要同类型比较或增补对象和问题时，可查看技能文档。[research 技能文档](../.agents/skills/research/SKILL.md)

| 用法 | 何时选 | 需要提供 | 会改哪些文件 |
| --- | --- | --- | --- |
| [1. 仅登记主题](#1-仅登记主题) | 只需要建立分类 | 主题名称。登记子主题时给出父主题，有指定 ID 时一并提供 | 只更新 `themes.yaml` |
| [2. 只制定计划](#2-只制定计划) | 本轮只安排具体调研工作或登记已有成果 | 主题，以及调研目标、明确纳入的已有报告或指定加入计划的对象 | 创建或更新当前计划 `plan.md`。需要新主题时先登记 |
| [3. 新做一篇调研](#3-新做一篇调研) | 有明确对象和研究问题，需要交付报告 | 主题、对象、问题、版本或资料范围 | 新报告、必要附件和计划回写 |
| [4. 续查已有报告](#4-续查已有报告) | 已有报告，本轮有具体事项要补查 | 报告路径或计划路径与任务编号、本轮要查的问题 | 原报告及相关资料的修订、计划回写 |

新做调研和续查都先查对应的主题计划。正式调研默认复用已有计划，缺失时自动创建。交付后把实际成果和待查事项回写到计划。

### 1. 仅登记主题

```text
使用 research，在 Harness 下登记子主题 <子主题名称>，主题 ID 为 <主题 ID>。
本轮只在 themes.yaml 登记名称和父子关系。
```

只有主题名称或宽泛方向时，先明确具体目标，再决定是否安排调研任务。

### 2. 只制定计划

```text
使用 research，为 Harness 制定调研计划，目标是比较 <产品 A> 和 <产品 B> 恢复长任务上下文的方式。
先检查已有成果，按产品评估证据并确定优先级。写明要查的版本、预期成果和验收条件。
如有候选的主题共同问题，请先发给我确认再填表。本轮只交付计划。
```

本轮只维护计划。正文使用「核心问题」和「对象与任务」两张表，旧计划可沿用「调研任务」标题。核心问题记录主题下共同关注的问题，经用户确认后再填写，暂无确认时保留表头。单项任务的问题写在该任务的目标中。同一入口、同一主题只维护一份当前计划。

先按类型核对证据，在「类型评估与证据」写明调研价值和排序依据，再在「优先级」填级别。「缺口与下一步」只列要继续调研或确认的事项。五类证据填写示例见 [计划模板](../.agents/skills/research-common/references/theme-plan-template.md#按类型填写示例)，详细要求见 [主题计划维护](../.agents/skills/research-common/references/theme-planning.md)。

### 3. 新做一篇调研

```text
使用 research，调研开源项目 <项目名>，仓库为 <仓库 URL>，采用 <版本标签或提交号>。
归入 <已注册主题>。重点回答记忆如何写入、检索和更新，说明实现依据、扩展方式与限制。
交付中文报告，写明源码或文档能确认的结论和仍待核实的问题。如有实测，单独列出结果。
```

### 4. 续查已有报告

```text
使用 research，续查 research-reports/team-agent/plan.md 中 T001 对应的 Claude Tag 报告。
本轮只核对 Claude Tag 是否公开核心源码，以及现有公开资料能确认哪些服务端实现。
复用仍有效的证据，更新原报告和计划中的成果链接与待查事项。
```

修订同一篇报告时沿用报告 ID 和专题标识，保留未复核部分原有的版本、日期与缺口。由工具更新目录时间和相关引用。

## 基于已有成果做分析

**适用场景** · 从已有调研中解释一个问题、归纳共性或比较方案取舍。

**需要提供** · 分析问题、参考报告、样本范围和期望交付。也可以给出自己的初步观点或判断标准。

**交付结果** · 分析计划或独立的分析洞察报告，写明主要发现、依据、适用范围和待核实的判断。详见 [research-analysis 技能文档](../.agents/skills/research-analysis/SKILL.md)。

```text
使用 research-analysis，以 research-reports/team-agent/plan.md 中 T001 链接的 Claude Tag 报告为依据。
分析团队试点时权限范围和验收标准之间的取舍。
把已有证据、由证据推导的判断和还要实测的事项分开写，交付一份分析洞察报告。
```

## 查资料、读源码、配图和润色

### web-article-fetcher

**适用场景** · 将指定网页文章保存下来，供离线阅读或引用。

**需要提供** · 文章 URL、保存目录、图片需求和已知的网络访问条件。

**交付结果** · 保留原始标题和来源的 Markdown、抓取元数据和已保存的图片。需要人工验证或图片获取失败时说明实际情况。详见 [web-article-fetcher 技能文档](../.agents/skills/web-article-fetcher/SKILL.md)。

```text
使用 web-article-fetcher，直连获取 <中国网站文章 URL>，保存到 <本次调研资料目录> 下。
按文章标题建立归档目录，保留正文原始标题、来源链接和访问日期，只下载 <要引用的原图 URL>。
```

### code-understanding

**适用场景** · 阅读陌生代码、追踪调用与数据流，或对照设计文档核实实现。

**需要提供** · 源码位置、版本，以及想追踪的入口、模块或行为。

**交付结果** · 源码位置、调用路径、建议的阅读顺序，以及需要运行才能确认的行为。详见 [code-understanding 技能文档](../.agents/skills/code-understanding/SKILL.md)。

```text
使用 code-understanding 阅读 <本地源码目录> 的 <版本标签或提交号>。
从 <告警处理入口> 追到权限检查和工具调用，列出关键函数、代码位置与阅读顺序。
```

### draw-diagram

**适用场景** · 用架构图、流程图或方案对比图解释关系和过程。

**需要提供** · 图要回答的问题、可核对的资料、使用位置和格式要求。

**交付结果** · 有助理解的已有图及来源、Markdown 代码图或所需的静态图。报告中简单的新图优先使用 Markdown 代码图。独立静态图默认交付 SVG 和 PNG。新绘须满足图像能力条件。[图像能力条件](../.agents/skills/draw-diagram/SKILL.md#图像能力条件) · [draw-diagram 技能文档](../.agents/skills/draw-diagram/SKILL.md)

```text
使用 draw-diagram，依据 Claude Tag 报告中已核实的持续集成案例，说明告警、Claude 初步排查和人工复核之间的关系。
放在报告的案例说明旁。已有图能讲清流程时复用并注明来源。需要新绘且满足图像能力条件时，优先用 Markdown 代码图。写清读图重点。
```

### humanizer

**适用场景** · 润色已有正文，让表达自然、直接。

**需要提供** · 要润色的文件或段落、目标读者和要保留的内容。

**交付结果** · 润色后的文字，保留事实、数字、术语、引用和适用条件。详见 [humanizer 技能文档](../.agents/skills/humanizer/SKILL.md)。

```text
使用 humanizer，润色 <报告路径> 的主要结论，读者是准备接入的工程团队。
用短句写清发现和适用条件，保留事实、数字、引用和技术术语。
```

## 交付与提交

### 核对报告与计划

- **报告开头**写清调研状态、采用版本、调研人、调研或最近修订的北京时间，以及仍待确认的具体事项。署名用用户指定的名称，或当前 Git 远程平台上已确认的用户账号。没有可确认的署名时请用户提供。详见[调研人署名](../.agents/skills/research-common/references/task-management.md#调研人署名)。
- **报告目录**保留正文、同名元数据（例如 `report.meta.json`）、实际引用的资料与图片，以及已登记的附加交付。历史修订和证据记录保存在元数据中，源码副本、实验输出和原始结果放在任务临时目录。正文和计划中的本地链接使用相对路径。详见[交付规范](../.agents/skills/research-common/references/delivery-policy.md)。
- **计划回写**核对两张表，填写实际成果链接、验收结果、调研人和北京时间，写清下一步要查什么。计划任务状态取决于该任务的目标与验收。以 Claude Tag 为例，计划任务 `T001` 已完成其验收目标，报告显示「局部复查完成」，服务端实现仍有待查事项。[Team Agent 计划](../research-reports/team-agent/plan.md) · [Claude Tag 报告](../research-reports/team-agent/product/claude-tag__20261109-154839/report.md)

报告提交时，按实际将要提交的版本校验文件和链接。[报告提交检查](../.agents/skills/research-commit/references/pre-commit-checks.md) · [计划核对规则](../.agents/skills/research-common/references/theme-planning.md#收口与核对)

### 使用 research-commit 提交已有报告

**适用场景** · 已有调研或分析洞察报告，需要做提交前校验并按篇提交。

**需要提供** · 报告路径、获准提交的文件范围，以及对暂存版本、推送和临时资料保留的要求。

**交付结果** · 文件和链接的检查结论。校验通过后给出每篇报告的本地提交哈希。仍有待确认的临时资料或其他阻塞时，说明具体范围和原因。[research-commit 技能文档](../.agents/skills/research-commit/SKILL.md)

```text
使用 research-commit，校验并提交 research-reports/team-agent/plan.md 中 T001 链接的 Claude Tag 报告。
本轮提交范围是报告正文、同名元数据和必要附件。检查通过后只创建该篇报告的一笔本地提交。
```

### Git 范围与提交

修改前后先检查工作区与索引，保留其他人的暂存、未暂存和未跟踪资料：

```powershell
git status --short
git diff --stat
git diff --cached --stat
```

用户要求纳入跟踪时，只暂存明确文件；使用 `git --literal-pathspecs add -- <精确文件路径>`，不要用无范围的 `git add .` 或 `git add -A`。暂存不等于创建提交，生成报告或保存计划也不自动授权提交、推送或发布。

报告、项目规则、技能和图谱维护分开组织提交。只提交已暂存内容时以索引版本为准，保留同文件未暂存的修改。

建议在提交说明或评审说明中写清变更解决的问题、影响范围、实际执行的检查和剩余缺口。文档与工具维护使用相应检查，不把它们当成调研报告套用报告交付校验。

## 维护与排查

### 目录速查

| 路径 | 用途与维护边界 |
| --- | --- |
| `README.md` | 仓库入口，图谱标记区之外可以人工维护 |
| `AGENTS.md` | 项目约定 |
| `.agents/skills/` | 技能、支持文件和依赖清单 |
| `.agents/skills/research-common/` | 主题、计划、证据、任务、写作和交付的共用规则 |
| [themes.yaml](../themes.yaml) | 主题的稳定 ID、名称、父子关系与别名 |
| [research-reports/](../research-reports/README.md) | 对象调研报告，路径为 `<主题名>/<类型>/<专题>__YYYYMMDD-HHmmss/report.md` |
| [analysis-reports/](../analysis-reports/README.md) | 分析洞察报告，路径为 `<主题名>[__<专题>]__YYYYMMDD-HHmmss/report.md` |
| `research-reports/<主题名>/plan.md` | 对象调研的当前计划 |
| `analysis-reports/<主题名>.plan.md` | 分析洞察的当前计划 |
| `<报告目录>/.tmp/<run-id>/` | 一轮调研的配置、证据、源码副本和检查记录 |
| `docs/`、`scripts/`、`tests/`、`.github/workflows/` | 文档、图谱、工具、测试及工作流 |
| `.research-graph.json` | 图谱索引范围 |

两类报告都将主题层次压成一个目录名。例如 Agent → Memory → Architecture 在对象调研中写成 `agent-memory-architecture`，在分析洞察中写成 `agent__memory__architecture`。报告专题可以由多个片段组成，例如 `codex__context-engineering__context-compaction`。日期与时间采用北京时间。专题命名、目录改名和旧位置兼容见[交付规范](../.agents/skills/research-common/references/delivery-policy.md#目录命名)。

### 技能与工具

优化或更新技能前，先按[技能维护规则](../AGENTS.md#技能维护)执行。

技能维护直接修改 `.agents/skills/` 中对应技能及支持文件；新增或修改流程时同步核对入口、相对链接、脚本参数和相关测试。公共规则集中在 research-common，其他技能按需引用，避免复制出不同版本。子技能返回结果给调用方，不回调三个顶层入口。

修改技能关系后运行 `python -B -m unittest discover -s tests -p test_skill_dependencies.py -v`，检查链接、正文、元数据、脚本路径及本地导入形成的直接和间接依赖。`test_research_compat.py` 检查仅安装共用子技能时的实际流程及旧入口兼容。技能独立性工作流使用 [共用调研依赖](../.agents/skills/research-common/requirements.txt)、[文章抓取依赖](../.agents/skills/web-article-fetcher/requirements.txt) 和 [仓库技能测试依赖](../tests/skill-dependencies-requirements.txt)，执行这两项检查、公共任务回归及 Git 流程测试。抓取回归另在只安装文章抓取依赖的作业中运行。需要 HTTP 403 浏览器回退时使用 [抓取技能的浏览器清单](../.agents/skills/web-article-fetcher/requirements-browser.txt) 并准备 Chromium。图谱生成和浏览器测试依赖由 `scripts/` 下的图谱清单维护。

公共工具的正式实现位于 `.agents/skills/research-common/scripts/`，内部调用与新文档统一使用该路径；旧 `.agents/skills/research/scripts/` 仅保留兼容转发，不承载独立实现。新旧命令均接受原有参数，已有任务与报告无需迁移。

修改保存与清理规则时，更新 `research-common/references/delivery-policy.md` 并检查相关引用；修改脚本接口时，同步调整调用示例与测试；更新第三方后端时，同步维护版本锁、依赖锁、源码包或扩展包及校验和。

保留固定版本源码包、锁文件、初始化脚本和必要的兄弟技能目录。被 Git 忽略的运行环境仍可能是当前依赖，不能仅凭忽略状态删除。

### 图谱与 README 总览

图谱从 Git 已跟踪文件和已暂存的新文件读取数据。主题和具体调研工作是节点，报告通过计划的任务编号和「实际成果」链接关联到工作。远程图谱使用已推送的分支内容。[图谱输入与关联规则](research-graph-guide.md#输入边界)

README 中 `research-graph:start` 与 `research-graph:end` 之间由生成器维护。人工说明放在标记区外，总览有变化时先更新计划、报告或其他输入，再由工具生成。

在 `openjiuwen-harness` 上推送命中路径规则的改动后，工作流构建图谱、检查页面、回写生成文件并部署 Pages。核对线上结果时同时看验收状态与 `publication.json` 中的源提交和资源校验值。生成命令、预览、发布及失败恢复集中见图谱维护指南。[图谱维护指南](research-graph-guide.md) · [工作流配置](../.github/workflows/research-graph.yml)

本地生成预览、截图和运行会生成图片的测试时，沿用项目的图像能力条件。[项目图片规则](../AGENTS.md#图片使用与生成)

### 按改动选择检查

| 修改范围 | 检查入口 |
| --- | --- |
| 技能、技能脚本或后端依赖 | 按上文的技能维护要求运行相关检查 |
| 图谱提取、生成与恢复 | `python -X utf8 -B -m unittest discover -s tests -p test_research_graph.py -v` |
| 图谱前端 JavaScript | `node --check docs/research-graph/app.js` |
| 图谱交互与桌面、移动端布局 | `python -X utf8 -B tests/research_graph_browser.py`，需先安装浏览器依赖与 Chromium |
| 使用指南或 README | 核对本地链接、章节锚点、命令和 `git diff --check`。编辑 README 时检查自动生成区 |

浏览器依赖安装、线上验收和截图位置见[图谱验证说明](research-graph-guide.md#验证)。

### 临时任务与长期资料

临时资料清理以[交付规范](../.agents/skills/research-common/references/delivery-policy.md)为准，核对精确范围并沿用用户明确授权。同范围已有明确确认时不重复询问。Windows 删除或移动前核对解析后的绝对目标及链接属性，使用原生 PowerShell 的精确路径操作；受拒时说明返回原因，不换工具绕过。

只清理获准的任务目录，保留报告和当前主题计划。技能运行依赖以及 `docs/`、`scripts/`、`tests/`、工作流设施不因当前没有报告就失去用途。用户已有文件、其他任务、系统缓存或源码原项目不属于默认清理范围。

### 常见问题

| 现象 | 检查与处理 |
| --- | --- |
| 报告已存在，图谱中没有 | 核对是否已跟踪、路径与元数据是否受支持、排除配置、是否已重建；远程还需推送和成功发布 |
| 显示“工作待关联” | 在对应任务行的「实际成果」列填入报告链接。旧计划可在成果索引中按稳定工作 ID 登记。 |
| 调研未完成或需要补查 | 使用 research，说明已有计划或报告路径，以及本轮需要继续、补查或调整的范围 |
| 新机器上的技能不可用 | 查阅对应技能的环境要求与本地运行说明，不复制维护者绝对路径或擅自升级全局工具 |
| 图谱已部署，但发布验收失败 | 查看工作流制品中的版本、哈希与浏览器结果，按实际失败环节处理，不将部署状态写成验收通过 |
| 没有报告，目录是否可删 | 先核对保留约定、真实用途与明确授权，不能按空目录或未跟踪状态推断可删除 |
