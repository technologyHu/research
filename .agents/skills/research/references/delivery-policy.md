# 调研产物保存与清理规范

本文件是所有 research 技能的保存与清理规则唯一来源。用户明确指定的路径、文件格式或保留要求优先；类型技能只规定内容，不另设一套目录规则。

## 最终目录

默认按“对象类型／分类主题／对象或对比专题”保存到 `<type>/<theme>/<target>/`。沿用用户指定路径或已存在报告的位置，不自动迁移。一个叶子目录对应一份明确调研，不因组织名自动生成调研对象。主报告名默认 report.md，用户明确指定时通过 outline.delivery.report 记录其他根目录 Markdown 文件名。

```text
<type>/<theme>/<target>/
├── report.md
├── references/
│   ├── sources.md           # 来源链接、日期、版本、访问限制
│   └── <article>.md         # 本次实际使用且允许保留的参考文章
└── assets/
    └── <image>              # 报告实际引用的图片
```

这是通用报告目录模板，只在有内容时创建子目录，不用空文件占位。短报告可将来源索引写入 report.md；复杂报告可有被主报告链接的 Markdown 补充报告或术语表。来源文章的名称可使用可读标题，项目与对象 id 则使用稳定 slug。

### 类型与主题归类

- type 使用 `paper`（论文）、`open-source`（开源项目）、`product`（产品）、`benchmark`（评测）、`topic`（技术专题）。按本次研究的主要对象选类型，不按资料文件格式分类。
- theme 是领域或问题分类，例如 `agent-memory`、`agent-orchestration`、`coding-agent`。优先沿用已有主题名，避免同义目录；通过 create 的 `--theme` 传入。上下文无法确定时用 `general`，不为目录分类阻断已明确的研究任务。
- 单对象 target 优先使用明确提供的对象 id；未提供对象时使用调研标题的 slug。同类型比较仍归入该类型，target 为 `compare-<调研标题slug>`；跨类型比较归入 `topic`。分类主题不替代研究问题，`--topic` 仍是调研标题。
- 对比报告包含多个对象的分析，不自动复制成多份单对象报告。已有独立报告可互相引用；同一对象跨主题研究时保留各自范围，避免复制同一内容。
- 用户指定 `--output` 时以其路径为准；新增分类不意味着迁移已有报告。调整分类目录不表示原证据已重新核实。

```text
项目根目录/
├── paper/agent-memory/<paper-id>/report.md
├── open-source/agent-orchestration/<project-id>/report.md
├── product/coding-agent/<product-id>/report.md
├── benchmark/agent-evaluation/<benchmark-id>/report.md
└── topic/agent-memory/compare-<title>/report.md
```

文档、配置和命令输出使用相对路径，命令默认从项目根执行。项目文件路径相对于项目根，报告中的文章和图片链接相对于当前 Markdown 文件。脚本执行时解析路径以检查范围，不把机器盘符或用户目录写入新任务配置。

## 允许交付的内容

- Markdown 主报告和确有阅读价值的补充报告。
- 被报告链接的参考文章、来源索引；原始 URL 保留在文中。
- 被主报告或其 Markdown 补充报告实际嵌入的本地图片，使用相对路径。
- 默认图片格式为 PNG、JPEG、WebP、GIF、SVG、AVIF、BMP、TIFF；格式仍需与用户阅读器相容。

参考文章中的装饰图、作者头像、推广图及未被报告引用的图片不复制进最终目录。参考文章如仍需显示这些图片，可保留原始网络链接或省去图片，不留下本地断链。只给图片放一个下载链接不算正文使用，应实际嵌入。

## 中间资料

本次主动创建的中间文件统一放在对应调研目录的 `.tmp/<run-id>/`；即 `<type>/<theme>/<target>/.tmp/<run-id>/`。每次调研独立一个任务目录，不集中到项目根，也不散落在报告正文旁、桌面或系统临时目录。完整目录模板如下：

```text
.
├── <type>/
│   └── <theme>/
│       └── <target>/
│           ├── report.md
│           ├── references/
│           ├── assets/
│           └── .tmp/
│               └── <run-id>/
│                   ├── owner.json
│                   ├── outline.json
│                   ├── articles.json # 文章获取、核对及归档清单
│                   ├── fields.json # full 模式
│                   ├── notes.md    # light 模式，full 按需
│                   ├── results/
│                   ├── sources/
│                   ├── code/
│                   ├── scratch/
│                   ├── baseline/
│                   ├── progress.json
│                   └── verified.json
└── .gitignore              # 包含 .tmp/，忽略所有层级临时目录
```

临时子目录同样按需创建。owner、outline 和必要的 fields／results 由工具建立，其余由执行调研的代理写到当前任务内。工作目录创建、归属验证和恢复使用 [任务管理](task-management.md)，配置见 [research-config.md](research-config.md)。不要把克隆仓库及其 `.git` 混进最终报告。系统已有缓存和用户原始资料不属于本次临时文件，不搬移或删除。原项目根临时目录和旧系统临时任务兼容读取，不自动迁移。报告检查、文件散列和更新基线都排除该报告根下的 .tmp/，不递归扫描或备份临时资料；最终报告不得链接其中的文件，以免清理后断链。

用户只要计划、任务尚未完成或正在修改时保留临时工作区；用户明确要求保留全部工作资料时沿用其要求，并说明与默认交付的差别。用户要求另外交付源码、PDF、HTML 等时，在 outline.delivery.extra_files 逐个登记精确路径与用户要求的理由；不能用通配符或按扩展名整体放行。任务检查器只放行本次登记文件，仍检查其他多余文件。未配置的独立默认检查器保持严格默认规则。

参考文章遵循 [获取与归档流程](article-acquisition.md)。指定文章必须获取，全部获取结果先存本次 sources/articles/；实际引用且允许保留的原文进入 references/，只复制报告实际嵌入的图片到 assets/，未引用材料随任务等待确认后清理。

## 最终检查与清理

1. 先完成文章和图片落盘，再更新报告中相对路径与目录清单；图片来源／署名放在图注或来源索引。
2. 先按 [写作规范](writing-policy.md#报告语言润色) 完成润色和对照复核，完成归档及链接同步后，用 research_task.py report-note 生成当前状态说明，再运行 research_task.py verify。它调用 [validate_report.py](../scripts/validate_report.py)，同时检查本次完成度、版本、核心缺口、证据引用和文件规范；通过后仅在临时目录记录校验回执。不带 outline 的文件检查不能替代任务 verify。
3. 手工复查来源、版本、论证与类型检查清单。结构有效与调研完成度分开检查：partial 可以带明确缺口交付，blocked 不宣称完成也不清理工作资料。脚本不访问远程 URL，也不能证明结论正确。
4. 最终副本检查通过并完成人工复核后，运行 research_task.py cleanup-plan。向用户列出待删任务相对路径、文件数、占用空间、将保留的报告目录，以及仍需续查的情况，取得针对该范围的明确确认。检查通过本身不代表批准删除；不以超时、无回复或一般调研授权代替确认。
5. 确认后及时执行：先重新运行 cleanup-plan，对照已确认的 plan_id，核对实际目标仍是同一受管任务目录。内容或范围变化时先解释变化并取得新确认；没有变化时直接按原确认清理，不再重复询问。Windows 使用原生 PowerShell 删除精确任务目录，随后检查该目录已不存在、报告仍保留；如被占用或操作失败，当轮说明实际残留原因，不把“计划清理”报告成“已清理”。
6. cleanup-plan 只做检查，不执行删除；eligible 表示满足技术检查条件，requires_confirmation 明确仍需用户确认。plan_id 绑定任务归属、报告回执及临时文件清单、大小和修改时间，不是授权凭据。实际删除限于核对过的 `<type>/<theme>/<target>/.tmp/<run-id>/`，不能递归删除其 `.tmp/` 父目录或整个调研目录，其他任务继续保留。旧布局任务仍按其已验证的精确目录处理。
7. 最终目录中意外多出的本次生成文件可按已授权规范清理。已有用户文件不因“不符合目录规则”就擅自删除；明确报告冲突，保留用户指定内容。
8. 保留用户可见的成果路径与重要资料缺口。不默认提交 Git、推送或发布。

清理时遵守当前系统和文件操作工具的边界。Windows 使用原生 PowerShell 路径操作，先核对删除目标，不跨 shell 拼接递归删除。检查被拒绝时说明实际阻碍，不换工具规避同一拒绝。
