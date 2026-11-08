# 调研配置与结构化结果约定（v2）

## 工作目录与定位

工作路径规则见 [交付规范](delivery-policy.md)，操作入口见 [任务管理](task-management.md)。使用 research_task.py 在对应调研目录内创建 `.tmp/<run-id>/`，将所有本次中间文件集中在该目录。owner.json 记录目录归属；完整流程默认保存 outline.json、fields.json、results/ 与按需的 progress.json。单对象 brief 可选择 light，只需 outline.json 和证据笔记 notes.md。

命令从项目根执行，传递 work_dir 相对路径。续查用 research_task.py list/show 核对项目和目录归属；多个匹配任务明确选择，不自动取第一项。临时工作区已清理时，结合已有报告新建任务并重建证据，不能假装还存在旧 JSON。旧手工配置仍可由检查脚本读取，但不能伪造 owner.json 来取得受管目录身份。

下面示例只说明结构，路径和来源是示例值，不是实际调研事实。配置可以使用 YAML 或等价 JSON。共享脚本使用 Python 3.10+；结果脚本读 YAML 时需要 PyYAML，未安装时可写等价 JSON，不自动安装依赖。

## 完整流程的 outline（JSON 或等价 YAML）

```yaml
schema_version: 2
run_id: paper-review-001
revision: 1
path_mode: project-relative
task_layout: report-local
directory_layout: dated-flat
report_id: report-00000000000000000000000000000001
theme_id: agent-memory
theme_slug: agent-memory
theme_path: [agent, memory]
theme_name: Agent / 记忆
created_at: "2026-11-08T12:00:00+08:00"
updated_at: "2026-11-08T12:00:00+08:00"
classification: {type: paper, theme: agent-memory, target: example-paper}
workspace: ../../../../../..
work_dir: research-reports/agent-memory/paper/example-paper__20261108-120000/.tmp/paper-review-001
output_dir: research-reports/agent-memory/paper/example-paper__20261108-120000
topic: 示例论文的方法与实验分析
goal: 理解方法并核实主要实验结论
time_range: 采用论文 v1 及其同期材料
object_type: paper
mode: single
depth: standard
workflow: full
items:
  - id: example-paper
    name: 示例论文
    type: paper
    version: v1
    seed_sources:
      - https://example.org/paper
execution:
  concurrency: 1
```

- 新配置使用 `path_mode: project-relative`。workspace 相对于配置文件所在目录；对象报告 outline 的 workspace 通常为 `../../../../../..`，单层分析报告为 `../../../..`；自定义报告目录层级时由工具计算，不手写固定跳转层数。work_dir、output_dir 相对于项目根。脚本内部解析路径，持久化配置和命令输出保留相对形式。
- 新任务使用 `task_layout: report-local`，work_dir 必须恰为 output_dir 下 `.tmp/` 的单次任务目录。output_dir 必须位于项目内，不能是项目根、临时目录或 `.git`、`.agents` 子目录。旧格式仅兼容读取，不主动迁移或覆盖旧目录。
- `object_type` 使用路由枚举；每个 item 的 `type` 可覆盖全局对象类型，但同一任务的 items 必须保持同一实际类型，analysis 的全局与 item 类型均为 analysis。输入报告是来源，新增来源不新增 item 或修改 mode；跨类型对象应复用或建立独立任务。id 为小写英文字母、数字和连字符组成的稳定标识，结构化结果文件名使用 id。调研目录遵循主题优先与英文命名规则；仅明确声明的中文正式产品／项目名可用于 target，普通中文标题不能自动变成目录。
- `version` 可以为 null，表示未指定；实际采用的版本仍应在结果里记录。不要把组织名当作默认研究对象。
- `revision` 在范围变化时递增；它用于解释变更，不意味着旧结果必须全部废弃。
- `goal`、`time_range` 为可选字符串，用于明确用户目标和时间边界；改变它们会要求重新核对已有字段。
- 任务工具记录 classification.type／theme／target，用于目录归类与展示；创建时 --theme 指定分类主题，--target 指定报告的研究专题或范围。classification.target 不要求等于 items[*].id：例如 target 为 codex__context-engineering__context-compaction，item.id 为 codex，结果文件仍为 results/codex.json；单对象任务未指定 target 时才默认使用对象 id。target 的片段间用双下划线，片段内用单连字符，数量不固定；旧单连字符及双连字符 target 保留原样，item.id 仍使用原有单连字符规则。它不参与证据问题指纹，调整分类不代表重新核实。分类与默认目录规则见 [交付规范](delivery-policy.md#类型与主题归类)，显式 output_dir 和既有报告位置优先。
- report_id、created_at、updated_at 和规范主题信息会进入成稿摘要；时间字段仅描述报告生命周期，不能替代来源访问日期。theme_slug 保留注册表推导的单连字符规范主题名，theme_path 保存各级 slug 数组；分析洞察的目录将这些层级用双下划线连接，不将目录展示名写成新的主题 ID。持续主题的长期问题、任务与阶段保存在 [主题级计划](theme-planning.md) 中；classification.theme 用于关联同一主题，单次 topic／goal／fields 仍只描述本次研究范围。计划表不替代字段证据、完成度检查或报告来源。

## 完整流程的 fields（JSON 或等价 YAML）

```yaml
schema_version: 2
fields:
  - id: method
    description: 方法如何解决研究问题，关键假设是什么？
    applies_to: [paper]
    core: true
  - id: limitations
    description: 哪些结论尚未被实验或独立证据支持？
```

每个选定字段都应在适用对象的结果中有记录。`applies_to` 可省略，表示所有类型；`item_ids` 可选，用于限制对象。两者同时存在时取交集，引用的类型与对象必须存在。不要用空列表表达“全部”。字段的顺序就是默认报告的分析顺序，类型模板可以合理分组。

`core` 为可选布尔值，默认 true，表示该问题是否属于用户研究目标的核心。附加资料可在规划时设为 false；不能为了让检查通过而事后降低核心性。它只影响完成度，不改变同一问题的证据是否仍可复用。

## 字段输入指纹

开始分析前运行：

```text
python <skills_root>/research-common/scripts/validate_results.py --outline <outline.yaml> --fields <fields.yaml> --fingerprints
```

此模式检查配置及已有文章缓存，打印 `input_fingerprints[item_id][field_id]` 和已取得正文的 `article_fingerprints[article_id]`，不读取结果，也不表示调研已经完成。将每个字段对应的范围指纹保存到其结果记录的 `input_fingerprint`。

命令中的 outline、fields 使用当前任务返回的实际配置路径，不按示例扩展名另建文件。JSON 为默认格式，YAML／YML 为兼容输入。

指纹绑定字段 id 和问题描述、对象 id／名称／类型／请求版本，以及主题、深度、goal 和 time_range。它不绑定整份配置的 revision、其他对象、其他字段或 core 标记，因此补充无关对象／字段不会导致全部重查。字段问题、目标版本或研究范围改变后，旧指纹不再匹配。

证据指纹只绑定研究问题与范围，不绑定 outline.update 的章节、基线、允许文件或来源继承信息。这些属于交付设置，另由报告摘要的 research_digest、基线及 verify 核对；改变交付范围不使有效证据失效，也不表示报告自动有效。问题的限定条件须写入字段描述、goal／time_range 或版本，不能只写在章节标题里。

检查器兼容同一当前配置下旧版包含 update 的指纹，但不兼容已经改变的问题／版本。跨任务沿用可用 derive 自动记录来源并转换指纹格式；不要靠手改指纹把过期证据标为有效。详见 [任务管理](task-management.md#基于既有证据追加对象或维度)。

缺少指纹的旧结果需要先按当前问题复查，再记录当前指纹。不能只为消除检查错误而给未复查的旧资料补上新指纹；指纹校验不能替代对来源和推理的审核。

## 文章正文依赖指纹

input_fingerprint 只绑定问题与范围。实际依赖已登记参考文章的字段另记 `article_fingerprints`，值取自同一次 --fingerprints 输出；只复制该字段实际用到的文章，不把全局文章表复制给所有字段：

```text
"article_fingerprints": {
  "official-intro": "<当前正文的64位SHA256>"
}
```

该映射位于 full 的每个字段记录内；light 位于 outline.assessment 内，--fingerprints 无须 --fields。散列针对去掉访问日期、统一图片缓存链接后的原文，与获取记录中的文件 content_sha256 不同。

正文变更后，检查器结合字段 evidence 与 conflicts.positions 中 source_id 对应的原始／重定向 URL 定位依赖；显式映射也参与检查。它返回 `stale_article_fields[item_id][field_id]` 或 light 的 `stale_articles`，并阻止成稿。先重读新版，复核数值、适用条件、定位和推理，再更新结论及此映射；未能确认时记录 unknown 与原因，并保留本次复查的正文指纹。不能通过移除引用或更新报告摘要跳过复核。

兼容未变更文章对应的旧结果没有此映射；已有版本历史显示正文变化时仍要求复核。新结果应从首次使用文章起记录依赖，未受影响字段保持原值。正文接受、原文归档和结论复核是不同步骤；检查器不能证明已经实际阅读。

## results/<item_id>.json

```json
{
  "schema_version": 2,
  "item_id": "example-paper",
  "type": "paper",
  "version": "v1",
  "sources": [
    {
      "id": "s1",
      "title": "示例论文",
      "url": "https://example.org/paper",
      "kind": "primary",
      "accessed_at": "2026-11-05",
      "version": "v1"
    }
  ],
  "fields": {
    "method": {
      "status": "confirmed",
      "input_fingerprint": "779b579b883e04b821c32dfae3c761a9a876d1c35133b88237b711e2524219b3",
      "value": "此处记录基于原文的方法解释。",
      "evidence": [{"source_id": "s1", "locator": "第 3 节"}]
    },
    "limitations": {
      "status": "unknown",
      "input_fingerprint": "27e28f8109b84a9597a121ef147a0a31c103889601b127e62c5a117cf1c5fe71",
      "value": null,
      "reason": "未取得对应附录，不能核实该项。",
      "evidence": []
    }
  }
}
```

上方示例指纹只对应示例中的对象、问题和范围，实际任务使用指纹命令的输出。

- `confirmed`：有已阅读的直接证据；`inferred`：有来源支持的推断，另写 reason 解释推导。
- `unknown`：未核实，value 为 null，reason 说明缺口；`not_applicable`：该问题对对象不适用，value 为 null 并说明原因。
- confirmed／inferred 均需非空 value 和 evidence；每条 evidence 指向同一结果中的 source_id，并附页码、章节、固定路径行号或实验条件等 locator。
- source 的 kind 为 primary／secondary；URL 优先使用原始资料地址；analysis 引用项目内已有报告时使用下节的 repo: 记录。已有本地 file URI 保持兼容，交付物内部的文档和图片链接仍使用相对路径。accessed_at 为实际读取日期，未读来源不能填入已核实证据。
- 不同结果文件的来源 id 可独立编号。根 JSON 不再复用旧版任意分类键或 `uncertain` 数组，未知项直接保存在对应字段中。

evidence 可填写非空 supports 与 conditions 来解释主张和支持条件。字段发生证据冲突时增加 conflicts 数组，完整结构和处理规则见 [证据规范](evidence-policy.md#来源冲突)。未解决冲突要求该字段 unknown；resolved 也保留双方记录与 rationale，报告不能只引用被采纳来源。

## 分析洞察引用已有报告

`analysis` 任务的对象是待分析的主题或问题，输入报告作为来源，不把不同类型来源作为混合 items。任务目标、样本范围、可选的用户约束／偏好与贡献者假设属于输入，不直接建立为待证实的事实字段，也不为其编造 URL。影响分析结论的输入应落实到 goal／time_range 或相关字段描述，使现有范围指纹覆盖其含义；notes.md 保留原文、提供者及采用条件。现实性能、成本等事实声明仍按公共证据要求处理。

full 的 fields 只列需要核查或推导的主张；新任务的最小分析可只有 insight，以 inferred 的 reason 解释综合过程、依据、假设和边界，evidence 指向真实支持的来源事实。judgment 继续用于取舍类及既有任务，不迁移历史字段。报告章节、来源清单和贡献者观点不必各建一个字段。输入改变时按正常范围变更规则复核，不仅更新 notes；light 沿用 assessment 与 notes，无需为此增加新配置格式。

repo: 的限制仅针对项目内本地报告引用，原始论文、官方文档等外部 HTTP(S) 来源仍使用公共 sources 结构。采用项目内持久报告时，在 full 的 sources 或 light 的 assessment.sources 中记录：

```json
{
  "id": "memory-survey-report",
  "title": "记忆综述论文调研报告",
  "url": "repo:research-reports/agent-memory/paper/survey-agent-memory__20261108-120000/report.md",
  "kind": "secondary",
  "version": "实际报告版本或日期",
  "accessed_at": "实际读取日期，格式 YYYY-MM-DD",
  "sha256": "采用文件字节的实际 SHA-256",
  "locator": "实际采用的章节、主张及适用条件"
}
```

`repo:` 后是项目相对 Markdown 路径，不能指向计划、临时文件、技能、外部路径、链接目录或本篇输出。正文使用相对链接，如 `[已有调研](../../research-reports/agent-memory/paper/survey-agent-memory__20261108-120000/report.md#分类体系)`，不将 `repo:` 标识直接当作阅读链接。full 的 evidence 仍按 source_id 和 locator 定位；既有调研事实、贡献者观点和本次推导分别记录，推断写明 reason。

校验器会核对实际文件与 sha256；来源变化后先复核采用的主张及相关推导，再更新版本、散列与结果，不通过只改散列跳过复核。正文仅放行已用于证据的已有报告相对链接，并检查章节锚点；该例外不扩大普通报告、计划或图片的输出边界。不复制来源报告为本篇附件，不将报告转述当作原始证据。

任务清理后，标准 analysis 目录中的独立文件检查可依据报告保存的 research-summary 来源清单核对这些相对链接，仍返回 consistency_checked=false；它不能恢复逐字段证据、核对原散列或证明研究一致性。再次更新判断时按实际需要重建或恢复证据。

## 增量更新

progress.json 按对象 id、字段 id 保存状态：

```json
{
  "example-paper": {
    "method": {"status": "stale", "reason": "研究问题已改变，需要重新核对"},
    "limitations": {"status": "done", "reason": "已查明附录未公开，结果记录为 unknown"}
  }
}
```

状态为 pending、stale 或 done。新增对象仅补查该对象；新增字段补查适用对象；对象版本、问题含义改变时将受影响字段标记 stale。重新检查后更新结果的输入指纹，再将进度改为 done；确实无法核实的字段可以在本次复查后记为 unknown 并说明缺口。

检查器同时核对输入指纹和当前工作目录内的 progress.json。pending／stale 阻止成稿，不能通过只修改进度或只修改指纹绕过另一项检查。进度文件存在但损坏时也会失败；可用 `--progress <path>` 明确指定进度文件。进度文件不存在时，仍强制校验结果的输入指纹。

## 结构有效性与调研完成度

常规检查分别输出 `valid` 和 `completion`，二者不能混用。

| completion | 判断 | 报告处理 |
| --- | --- | --- |
| complete | 所选对象都有实质性证据回答，且核心字段没有 unknown | 可以按目标交付，仍需列出非核心缺口及推断条件 |
| partial | 有可用结论，但部分核心问题未知，或部分比较对象仍无实质结果 | 可以交付明确标为“部分完成”的报告，说明未解决的问题及其影响 |
| blocked | 结构／时效检查失败，或全部所选对象都没有有证据的回答 | 不作为完成的调研交付；先补查，无法推进时说明阻碍并保留工作资料 |

confirmed 和有证据、有理由的 inferred 计为实质回答。not_applicable 可以解释范围，但全部字段均不适用不能算完成调研。unknown 保留为合法结构记录，不用编造内容换取通过。此完成度衡量问题覆盖，不自动评判学术质量或来源是否真的支持结论。

report-note 汇总所有适用 unknown：核心项进入 core_gaps，非核心项进入 non_core_gaps，并在报告可见说明中保留对象、问题和理由。非核心缺口单独存在时可为 complete；遗漏其可见说明同样不能通过报告一致性检查。not_applicable 不混入未知项。

`report_ready` 仅在结构有效且完成度为 complete／partial 时为 true。`--item` 只检查本批次，输出 `scope: selected`；最终成稿必须去掉该选项检查全部计划对象。

常规 CLI 退出码：0＝完整；1＝结构或时效失败；2＝部分完成；3＝结构有效但调研阻塞。退出码 2 不等同于 JSON 格式错误，也不表示全部问题已解决。`--fingerprints` 模式则仅以 0／1 表示配置是否有效。

## 交付配置与结果—报告一致性

outline 中可选的 delivery 只记录本次明确的用户选择，默认仍为 report.md、参考 Markdown 和报告图片：

```yaml
delivery:
  report: report.md
  extra_files:
    - path: exports/report.pdf
      reason: 用户明确要求附带 PDF
```

report 必须是输出根目录中的 Markdown 文件名。extra_files 是精确相对路径和用户要求的理由，不接受通配符、绝对路径或目录逃逸。未登记的额外文件仍会报错，登记的文件必须实际存在。

用 research_task.py report-note 生成本次报告的状态说明，放在标题下。它包含可见的完成度、采用版本、核心缺口，以及隐藏的研究摘要。摘要绑定当前计划和证据；结果或范围改变后，旧摘要无法通过一致性检查。正文与来源索引仍需真正引用证据，隐藏摘要中的 URL 不算引用。

最终使用 research_task.py verify 同时检查研究一致性与交付文件。只有在任务外做独立文件检查时才不传 outline，此时输出 consistency_checked 为 false。

## 轻量流程

仅限 single + brief，使用任务管理文档中的 notes.md 与 outline.assessment，不需要 fields、results 或 progress。范围指纹通过 show 或结果脚本 --fingerprints 获取；变更问题或版本后整份复查。轻量结论由人工核对，检查器只能核对已记录的范围、状态、来源、版本与报告是否一致。

需要增加对象、复杂维度或按字段续查时先运行 promote，原笔记保留为来源材料，再按完整流程重建可验证结果。

## 参考文章清单

outline.reference_articles 使用 URL 数组或 `{id, url, required}` 记录数组。required 默认 true，用户指定的文章不可静默降为 optional；自行发现的补充文章按需登记 required=false，但正文实际引用时同样需要核对与归档。具体结构和 articles.json 状态见 [文章获取流程](article-acquisition.md)。获取记录绑定本次 run_id，正文散列变化会使证据检查失败；必获取项未完成、未核对或明确请求的刷新失败时保留 article_gaps，使已有其他结论的任务为 partial。实际引用的已核对原文必须归档或披露明确的归档限制。刷新失败不删除有效快照；版本历史、图片下载尝试和最新检查时间单独记录，沿用旧版本必须如实说明。
