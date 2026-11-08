# 调研与分析洞察产物保存与清理规范

本文件是 research 和 research-analysis 及其共用技能的保存与清理规则唯一来源。两个入口独立选择工作、维护计划并决定交付，按需共用证据、任务、成稿、绘图和提交能力。用户明确的例外与保留要求优先。

## 最终目录

项目根目录分为两类正式成果；内部继续采用“主题／类型／对象或专题”的目录和命名要求：

| 成果与入口 | 正式报告 | 当前主题计划 |
| --- | --- | --- |
| 对象调研，research | `research-reports/<theme>/<type>/<target>/report.md` | `research-reports/<theme>/plan.md` |
| 分析洞察，research-analysis | `analysis-reports/<theme>/analysis/<subject>/report.md` | `analysis-reports/<theme>/plan.md` |

下文 `<report-root>` 按实际类型取 research-reports 或 analysis-reports。前者只创建 paper、open-source、product、benchmark 报告，后者只创建 analysis 报告。一个叶子目录对应一份独立交付，不因组织名自动生成对象；同类型比较仍是一份报告。主文件默认 report.md，自定义根目录 Markdown 文件名通过 outline.delivery.report 登记。

```text
<report-root>/<theme>/<type>/<target>/
├── report.md
├── references/
│   ├── sources.md           # 来源、日期、版本、访问限制
│   └── <article>.md         # 实际使用且允许保留的原文
└── assets/
    └── <image>              # 报告实际引用的图片
```

这是通用叶子目录模板。参考资料与图片按内容创建，不用空文件占位；两个报告根目录可保留说明用途的 README.md。短报告可将来源索引写入主文件；有需要时可附被主报告链接的 Markdown 补充报告或术语表。现有旧位置报告可原地更新与恢复任务，不因新规则重新核实证据；迁移必须在用户明确范围内处理报告、引用、计划和临时任务的实际路径，不能仅移动目录留下断链。

### 目录命名

- theme、target 和 subject 通常使用有含义的英文 slug：小写英文字母、数字、连字符，如 agent-memory、openjiuwen、compare-memory-methods；中文标题保留在正文。
- 正式名称本身为中文的产品或项目可声明对象目录例外，如 `research-reports/coding-agent/product/扣子/`。使用 `--native-target-name`，保留来源依据；内部 item.id 仍用稳定英文标识，不将例外扩大到一般中文研究标题。
- survey 论文属于 paper，单篇目录使用 `survey-<paper-id>`，如 `research-reports/agent-memory/paper/survey-agent-memory/report.md`；多篇比较使用 `compare-survey-<slug>`。
- 英文名称的空格和下划线由创建工具规范为连字符；目录名不含路径分隔符、系统保留名或任意标点，不超过 64 字符。
- 单对象使用 `--item <english-id>=<显示名称>` 或 `--target <english-slug>`。比较专题按需加 compare-；不自动把通用中文标题当作目录，也不臆造官方英文译名。

### 类型与主题归类

- research 的 type 为 paper（论文）、open-source（开源项目）、product（产品）、benchmark（评测）；research-analysis 独立使用内部类型 analysis（分析洞察）。输入报告保留原类型，是分析依据，不是混合 analysis items。
- theme 表示领域或问题分类，通过 `--theme` 传入，优先沿用已有名称；无法确定时用 general。两边可使用同一主题 slug，但计划与任务编号分别属于各自根目录。
- target／subject 优先使用明确的英文对象或主题标识。同类型多对象比较使用 compare-；跨类型对象分别复用成果或补查，综合分析交给独立分析入口。
- 用户指定的新 `--output` 必须匹配 `<report-root>/<theme>/<type>/<target>` 及类型对应根目录；旧报告位置可原地维护，新报告不能继续创建到项目根的旧主题目录。
- 分析洞察可跨目录采用既有报告，正文使用相对链接，来源登记使用项目根相对的 repo: 路径与实际散列。不得为分析复制整份基础调研或伪造新的验证日期。

```text
项目根目录/
├── research-reports/
│   ├── agent-memory/paper/<paper-id>/report.md
│   ├── agent-orchestration/open-source/<project-id>/report.md
│   ├── coding-agent/product/<product-id>/report.md
│   └── agent-evaluation/benchmark/<benchmark-id>/report.md
└── analysis-reports/
    └── agent-memory/analysis/<subject>/report.md
```

命令默认从项目根执行，项目文件路径相对于项目根，正文链接相对于当前 Markdown；脚本解析后的机器绝对路径不写回持久配置。

## 主题计划的保存与收口

两个入口使用同一计划模板与维护规则，但分别维护 `research-reports/<theme>/plan.md` 和 `analysis-reports/<theme>/plan.md`。research 计划只列对象调研与补查，analysis 计划只列分析主题或问题；跨入口依赖登记对应计划／报告路径、版本、所需主张与接受条件，不复制为两份同范围计划。只有实际需要计划时才创建，单次任务不因 general 分类自动生成主题计划。旧位置计划继续维护，不复制出第二份当前计划。

```text
<report-root>/<theme>/
├── plan.md                  # 本入口本主题唯一当前计划
├── .tmp/<draft-id>/          # 确需计划编辑中间文件时使用
└── <type>/<target>/
    ├── report.md
    ├── references/
    ├── assets/
    └── .tmp/<run-id>/
```

计划不另存归档快照、不创建主题 archive/ 或日期／修订号副本。阶段收口、范围调整、结束与恢复直接更新当前 plan.md，记录 revision、日期、原因、成果及缺口；历史通过 Git 追溯，保存不自动提交或推送。

计划内链接相对于该计划；预期路径先用行内代码，文件存在后再转为链接。同根目录下论文用 `paper/<paper-id>/report.md`；分析计划引用同主题论文用 `../../research-reports/<theme>/paper/<paper-id>/report.md`（从 `analysis-reports/<theme>/plan.md` 出发）。计划不链接 .tmp 内容。

### 收口与恢复

1. 阶段收口或研究范围重大调整时，核对当前问题／任务 ID、实际成果、版本／日期、背景与评估、依赖接受条件及未解决问题，直接更新当前计划并保留必要的变更记录。不因一份报告交付就结束整轮主题。
2. 用户明确要求结束整轮主题时，在当前计划记录覆盖范围、实际完成／部分完成／取消的情况、重要成果、缺口及继续安排。按实际情况更新 revision、status 和日期；选择 archived 时填写 archived_at。归档仅表示主题状态，不生成计划副本，也不代表全部问题已解决。
3. 保留来源主体、团队及相关资源／治理关系的依据、实际核实日期，以及依赖 ID、hard／soft、实际采用的成果／版本、接受判定和下游影响。内容变化时在变更或执行记录中说明原判断、变化及影响，不能抹去缺口或把旧来源日期更新为本次核实。
4. 需要定位历史报告时记录已存在的 Git 提交号或报告版本／日期，不虚构提交，也不为收口擅自创建提交。恢复已归档主题时，直接更新当前计划，增加 revision、恢复 active、清空 archived_at，并记录恢复原因及沿用／新增范围。
5. 保存前核对实际链接、状态与变更记录一致，并保留并发修改；保存后重新读取确认。收口与恢复不授权清理，临时资料仍按精确范围确认规则处理。

主题计划不属于单次报告交付目录，不能交给 validate_report 或报告任务 cleanup-plan 当作报告／垃圾检查；现有报告校验范围不扩大。计划可链接各报告，报告中可纯文本记录主题／任务 ID，不能为反向链接计划而绕过输出目录边界。analysis 可引用已登记并核对散列的项目内已有报告，使用相对链接；该例外不包括计划、临时文件或外部图片，不将来源报告复制为本篇交付。计划草稿确需临时文件时放在该计划目录的 .tmp/<draft-id>/；它不属于受管报告任务，不能伪造 owner 或让 report cleanup-plan 删除，清理时仍先确认精确草稿范围。

清理任何单次报告的 .tmp/<run-id>/ 前，先把本次状态、已存在的报告链接、重要缺口及依赖接受／失效复核摘要同步回关联主题计划；下游需要继续复用的成果必须有持久来源，不能只留 .tmp 链接或临时笔记。清理精确任务目录时保留当前计划及报告，不删除主题目录或其他长期资料。用户只要求维护计划时，不创建受管执行任务，也不自动结束用户尚需继续维护的整轮计划。

## 允许交付的内容

- Markdown 主报告和确有阅读价值的补充报告。
- 主题计划按上述独立位置长期保留，不混入对象报告目录。
- 被报告链接的参考文章、来源索引；原始 URL 保留在文中。
- 被主报告或其 Markdown 补充报告实际嵌入的本地图片，使用相对路径。
- 默认图片格式为 PNG、JPEG、WebP、GIF、SVG、AVIF、BMP、TIFF；格式仍需与用户阅读器相容。

参考文章中的装饰图、作者头像、推广图及未被报告引用的图片不复制进最终目录。参考文章如仍需显示这些图片，可保留原始网络链接或省去图片，不留下本地断链。只给图片放一个下载链接不算正文使用，应实际嵌入。

### 自绘图的保存

仅在满足 [图像能力条件](writing-policy.md#图表与代码)、允许生成或重绘时执行下述流程；否则按现有图片归档规则保留实际引用的原图，不派生新的图片格式或重建生成源。

通过 draw-diagram 配图时，先确定报告 `assets/` 中的最终文件名，草稿直接以 `assets/<filename>` 引用，不链接临时文件；图片须在交付前实际落盘。生成和检查仍在当前任务的 `<work_dir>/scratch/diagrams/` 内进行，默认得到静态 SVG 与 PNG，随后把正文采用的成图复制到预定位置，不为归档重复更名或改写链接，不另建项目根的 `diagrams/`。

沿用绘图入口的同名和后端标识约定；同图通常选用一种格式嵌入。复制后在最终报告中确认链接、字体、背景及显示尺寸仍正确。更新图时先定位已保留的生成源；源已清理时，依据现存成图与已核实证据重建并说明，不假定原始输入仍可用。更新后同步生成源、最终成图与必要的正文引用，完成绘图复核后再运行报告 verify。

普通一次性配图未采用的格式、JSON／HTML 源文件及布局与检查记录留在任务临时目录。用户明确要求可编辑、可复现、持续维护该图，或要求同时交付其他格式时，按现有附加交付规则登记需保留的精确源文件及必要资源，持久保存并从报告给出相对链接，不只依赖 `.tmp`；不能仅因主题持续研究就自动扩大源文件交付范围。清理前核对所需生成源已保留，并在清理范围说明中交代哪些源会被删除；仅保留成图时，不承诺清理后仍能直接从原生成源续改。中间资料继续沿用本任务的确认后清理规则。

## 中间资料

本次主动创建的中间文件统一放在对应调研目录的 `.tmp/<run-id>/`；即 `<report-root>/<theme>/<type>/<target>/.tmp/<run-id>/`。每次调研独立一个任务目录，不集中到项目根，也不散落在报告正文旁、桌面或系统临时目录。完整目录模板如下：

```text
<report-root>/<theme>/<type>/<target>/
├── report.md
├── references/
├── assets/
└── .tmp/<run-id>/
    ├── owner.json
    ├── outline.json
    ├── articles.json          # 获取、核对及归档清单
    ├── fields.json            # full 模式
    ├── notes.md               # light 必需，full 按需
    ├── results/
    ├── sources/
    ├── code/
    ├── scratch/               # 含图片下载尝试，避免重复深层路径
    ├── baseline/
    ├── progress.json
    ├── scope/                 # 本轮执行范围
    └── verified.json
```

临时子目录同样按需创建。owner、outline 和必要的 fields／results 由工具建立，其余由执行调研的代理写到当前任务内。工作目录创建、归属验证和恢复使用 [任务管理](task-management.md)，配置见 [research-config.md](research-config.md)。不要把克隆仓库及其 `.git` 混进最终报告。系统已有缓存和用户原始资料不属于本次临时文件，不搬移或删除。原项目根临时目录和旧系统临时任务兼容读取，不自动迁移。报告检查、文件散列和更新基线都排除该报告根下的 .tmp/，不递归扫描或备份临时资料；最终报告不得链接其中的文件，以免清理后断链。

用户只要计划、任务尚未完成或正在修改时保留临时工作区；用户明确要求保留全部工作资料时沿用其要求，并说明与默认交付的差别。用户要求另外交付源码、PDF、HTML 等时，在 outline.delivery.extra_files 逐个登记精确路径与用户要求的理由；不能用通配符或按扩展名整体放行。任务检查器只放行本次登记文件，仍检查其他多余文件。未配置的独立默认检查器保持严格默认规则。

参考文章遵循 [获取与归档流程](article-acquisition.md)。指定文章必须获取，全部获取结果先存本次 sources/articles/；实际引用且允许保留的原文进入 references/，只复制报告实际嵌入的图片到 assets/，未引用材料随任务等待确认后清理。

## 最终检查与清理

1. 先完成文章和图片落盘，再更新报告中相对路径与目录清单；图片来源／署名放在图注或来源索引。
2. 先按 [写作规范](writing-policy.md#报告语言润色) 完成润色和对照复核，完成归档及链接同步后，用 research_task.py report-note 生成当前状态说明，再运行 research_task.py verify。它调用 [validate_report.py](../scripts/validate_report.py)，同时检查本次完成度、版本、核心缺口、证据引用和文件规范；通过后仅在临时目录记录校验回执。不带 outline 的文件检查不能替代任务 verify。
3. 手工复查来源、版本、论证与类型检查清单。结构有效与调研完成度分开检查：partial 可以带明确缺口交付，blocked 不宣称完成也不清理工作资料。脚本不访问远程 URL，也不能证明结论正确。
4. 最终副本检查通过并完成人工复核后，先同步关联主题计划的成果、状态和缺口，再运行 research_task.py cleanup-plan。向用户列出待删任务相对路径、文件数、占用空间、将保留的报告目录及长期主题计划，以及仍需续查的情况，取得针对该范围的明确确认。检查通过本身不代表批准删除；不以超时、无回复或一般调研授权代替确认。
5. 确认后及时执行：先重新运行 cleanup-plan，对照已确认的 plan_id，核对实际目标仍是同一受管任务目录。内容或范围变化时先解释变化并取得新确认；没有变化时直接按原确认清理，不再重复询问。Windows 使用原生 PowerShell 删除精确任务目录，随后检查该目录已不存在、报告仍保留；如被占用或操作失败，当轮说明实际残留原因，不把“计划清理”报告成“已清理”。
6. cleanup-plan 只做检查，不执行删除；eligible 表示满足技术检查条件，requires_confirmation 明确仍需用户确认。plan_id 绑定任务归属、报告回执及临时文件清单、大小和修改时间，不是授权凭据。实际删除限于核对过的 `<report-root>/<theme>/<type>/<target>/.tmp/<run-id>/`，不能递归删除其 `.tmp/` 父目录或整个调研目录，其他任务继续保留。旧布局任务仍按其已验证的精确目录处理。
7. 最终目录中意外多出的本次生成文件可按已授权规范清理。已有用户文件不因“不符合目录规则”就擅自删除；明确报告冲突，保留用户指定内容。
8. 保留用户可见的成果路径与重要资料缺口。不默认提交 Git、推送或发布。

清理时遵守当前系统和文件操作工具的边界。Windows 使用原生 PowerShell 路径操作，先核对删除目标，不跨 shell 拼接递归删除。检查被拒绝时说明实际阻碍，不换工具规避同一拒绝。
