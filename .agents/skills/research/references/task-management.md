# 临时任务管理与完整流程

使用 [research_task.py](../scripts/research_task.py) 创建和恢复任务。它默认写 JSON，除可选的旧 YAML 配置外只依赖 Python 标准库。以下命令从项目根执行，使用相对路径；`<skills_root>` 在本项目为 `.agents/skills`。

Windows 调用 Python 可加 `-X utf8 -B`，读写文档使用 UTF-8。用 subprocess 捕获脚本输出时显式指定 `text=True, encoding="utf-8"`，不要让系统默认 GBK 解码中文或数学符号。脚本的 JSON／Markdown 输出采用 UTF-8。

## 创建与定位

长期主题计划先按 [主题计划维护](theme-planning.md) 定位；单次任务的 outline／fields 继续留在本节创建的临时目录。只维护主题计划时直接编辑长期 Markdown，不必执行 create。现有命令不会自动同步或归档主题计划，也没有主题归档命令；由当前代理按规范维护。

从主题计划进入执行、回写成果及清理前同步，使用 [流程交接表](theme-planning.md#流程接入与交接)。创建／维护主题计划本身不调用本节 list/show 代替查找计划，也不以缺少旧 .tmp 为由中断纯计划编辑。

创建新任务前按 [已有成果核对](routing.md#已有成果核对与复用) 明确可采用内容与实际缺口。对象调研交给 research-deep，analysis 判断交给 research-analysis；两者共用本任务格式和公共报告流程。补查只为实际缺口创建／恢复任务，不能因输入跨类型或提出新判断重复创建全部基础调研。

```text
python <skills_root>/research/scripts/research_task.py create --workspace . --topic "研究主题" --theme agent-memory --type paper --target memory-method --depth standard --field "method=方法怎样解决问题？" --field "limitations=主要适用边界是什么？"
python <skills_root>/research/scripts/research_task.py list --workspace .
python <skills_root>/research/scripts/research_task.py show --work-dir <work_dir>
```

返回 run_id 和相对于项目根的任务、计划与报告路径。所有中间资料集中在对应报告目录的 `<theme>/<type>/<target>/.tmp/<run-id>/`，包含 owner.json 标记；同名主题产生独立 run，不覆盖旧任务。完整目录模板见 [交付规范](delivery-policy.md)。list 查找当前项目各调研目录内的任务，跳过临时目录内部的源码、下载资料及其他项目任务，可用 `--topic` 筛选。多个任务匹配时明确选择 run_id／work_dir，不自动采用第一项。

后续命令和编辑使用返回的 outline、fields 相对路径，例如 `agent-memory/paper/example-paper/.tmp/<run-id>/outline.json`。受管任务默认 outline.json、fields.json；已有 fields.yaml／fields.yml 由 show 返回实际路径。自动发现时若同时存在多个 fields 配置就报错，不静默选择一份；手工校验可明确传 --fields，但不要为追加对象或字段另建同名配置。受管 outline 始终为 outline.json，旧手工 YAML 计划用检查脚本明确传路径，不伪造 owner。

create 创建调研目录及其 .tmp/ 任务目录，但不创建或覆盖 report.md。按 [目录归类规则](delivery-policy.md#类型与主题归类) 输出到 `<theme>/<type>/<target>/`；`--theme agent-memory` 指定英文主题，省略时为 general。单对象 target 优先取明确给定的英文对象 id；`--target` 可另行指定英文目录名，同类型对比任务按需加 compare-。跨类型对象分别创建任务；基于已有成果的判断单独使用 analysis。中文正式名称通过 `--native-target-name 扣子` 明确声明例外，内部仍可使用 `--item coze:product=扣子`。`--topic` 是中文或英文调研标题，不能因此把一般中文描述用作目录；无英文对象 id 时传 --target。`--output` 相对于 `--workspace`，新建位置必须匹配主题优先结构，已有报告可原地复用。

默认只有一个对象，名称取调研标题；可重复 `--item id[:type]=名称` 明确对象，两个以上自动使用 comparison。同一任务中的 items 使用同一实际类型。分析判断例如 `--type analysis --theme agent-memory --target memory-selection --item selection:analysis=记忆方案取舍`，输入报告记录为来源；不把论文、项目、产品混合为分析对象。create／show 返回 classification，便于核对分类，不代表证据已更新。

向已有任务追加内容时先按 [增加对象](../../research-add-items/SKILL.md) 分流：同类型对象可扩充原 items，跨类型对象复用或建立独立任务；analysis 仅新增报告或观点时更新来源／采用关系，不增加来源对象到 items、不修改 mode。只有实际增加比较对象才转 comparison，并按需要 promote。

字段可重复 `--field id=问题`，默认 overview 仅是规划起点。执行前根据所选类型模板调整 fields.json，必要时增加 applies_to、item_ids 和 core。指定版本、时间范围和来源种子也在 outline.json 中完善。详细结构见 [配置约定](research-config.md)。

已关联主题计划时，选取本次授权任务，将问题落实到 goal／fields，在主题表回填实际 run_id，并按 [本次范围快照与对照](theme-planning.md#本次执行范围快照与回写前对照) 在本 run 的 scope/ 保存目标、版本／时间、相关问题及验收原文。复用主题标识传入 --theme，不用 --topic 代替整个主题计划；恢复执行、成稿和回写前与当前计划对照，清理前把结论、报告及缺口记入长期计划。scope/ 由代理填写，报告工具不会自动读取或核对主题 Markdown。

范围快照同时记录本次依赖 ID、hard／soft、所需成果及接受条件，notes.md／证据记录补记实际采用的前置版本与主张；按 [依赖规则](theme-planning.md#依赖的满足失效与复核) 核对并回写。依赖判定和主题任务状态由代理维护，不等同于 progress.json 的字段状态，也不由任务 verify 自动判断。

用户指定文章用重复的 `--reference URL` 登记；已有任务可用 add-article。fetch-articles、import-article、review-article 和 archive-article 负责获取、核对和归档；fetch-articles 可按 --id 筛选，download-article-images 独立补图，不重抓正文。完整命令及状态规则见 [文章获取流程](article-acquisition.md)。light／full 都会检查必获取项，不能把退出码 0 或 HTTP 成功当作正文已核对、调研已完成。

show／list 中 verification_receipt_present 只表示有历史检查记录，不保证后续修改后的文件仍有效；最终使用 verify 或 cleanup-plan 重新核对。

## 完整与轻量工作流

`--workflow auto` 是默认值：单对象且 brief 时选择 light；其他情况选择 full。可显式指定 full。强制 light 但不是单对象 brief 时会失败。

### full：逐字段调研与增量续查

保留 outline.json、fields.json、results/ 和按需的 progress.json。按类型定义问题，生成输入指纹，阅读来源并写结构化结果，再运行结果检查。继续新增对象、字段或版本时，只复查受影响字段。

### light：单对象简短分析

只保留 outline.json、owner.json 和执行阶段写入的 notes.md，无需 fields.json、逐对象 JSON 或 progress.json。

1. show 输出的 input_fingerprint 代表开始分析时的范围。
2. 阅读实际来源，notes.md 记录核心结论、证据位置、采用版本和缺口。不能以标题或模板代替分析。
3. 在 outline.json 添加 assessment，保留分析开始时的指纹：

```json
{
  "input_fingerprint": "show 给出的当前范围指纹",
  "status": "complete",
  "version": "实际采用版本或 null",
  "core_gaps": [],
  "non_core_gaps": [],
  "sources": [
    {
      "title": "实际阅读的原始资料",
      "url": "https://example.org/source",
      "kind": "primary",
      "accessed_at": "2026-11-05",
      "locator": "实际核对的章节或代码位置"
    }
  ]
}
```

例子仅示意结构，日期填实际访问日期。status 可为 complete／partial／blocked；核心缺口非空会得到 partial，没有来源会得到 blocked。可选 non_core_gaps 也为描述数组，自动带入可见报告说明，但单独存在不会降低完成度；不能为通过检查而将核心问题移入该数组。轻量模式的证据和结论由人工审核，检查器不会仅凭这些字段就证明内容真实。notes.md 必须包含实质分析，不能只放状态或来源列表。

```text
python <skills_root>/research/scripts/validate_results.py --outline <work_dir>/outline.json
```

问题或版本改变后，轻量笔记应整体复查；增加对象、复杂维度或需要逐字段复用时先升级：

```text
python <skills_root>/research/scripts/research_task.py promote --work-dir <work_dir> --field "method=需要深入核实的问题"
```

升级保留原笔记，建立 fields.json 和空 results/。旧笔记作为待核对证据，不自动变为 confirmed 结果。若增加对象，再按增加对象技能更新计划。

遇到影响结论的来源冲突也先升级，按 [证据规范](evidence-policy.md) 逐字段保存各方说法与处理理由。

## 已有报告的局部更新

仅复查指定章节时，按 [局部更新流程](report-updates.md) 新建任务并指向已有报告，在改动前用 begin-update 保存基线和章节范围，再用 apply-update 写入选定章节。最终状态只描述本次更新，未复核部分的旧版本、日期与缺口继续保留。普通错字或措辞更正不强制走调研任务。

### 基于既有证据追加对象或维度

```text
python <skills_root>/research/scripts/research_task.py derive --work-dir <previous_work_dir>
```

适用于旧 full 任务仍存在且证据检查为 report_ready 的情况。它建立新 run，复制原问题、对象、字段、结果和进度，记录 derived_from 的原任务路径、run_id 与文件散列；不改旧任务或最终报告，不继承旧基线及验证回执。源任务有过期／pending 记录时先在源任务复核；light 笔记需先 promote 并核对逐字段证据，不能自动升级为已核实结果。

使用返回的新任务路径，先 begin-update 登记比较表、结论和新增章节等实际受影响范围，再按增加对象／维度技能扩展计划。仅查询新增对象或受影响问题；未改变的问题与版本复用旧结果，来源 accessed_at 保持实际旧日期。若用户目标转为“当前版本／最新状态”，重新确定时间范围并复核受影响旧判断，不能凭派生动作宣称来源已更新。

派生结果按相同问题计算证据指纹，旧版包含 update 的指纹会在校验有效后做等价格式转换并记录数量，不改变结论、理由或来源日期。报告说明列出仍沿用的来源原访问日期；新增内容不能冒充旧证据，修改来源访问日期必须确实重新读取。旧任务已被清理时不能从散列恢复资料，应从报告与来源重建证据。

## 从证据到报告

```text
python <skills_root>/research/scripts/research_task.py report-note --work-dir <work_dir>
```

仅在本次证据可以交付完整或部分报告时输出状态说明。将输出原样放在主报告标题下：包含隐藏摘要及可见的完成度、版本、核心缺口、存在的非核心缺口和无实质结果对象。缺口注明对应对象、问题与理由；非核心 unknown 不会因状态为完整就消失，not_applicable 不自动视为未知。隐藏摘要不算正文引用来源；仍需在正文和来源索引给出原始链接。

按类型模板撰写草稿后，按 [润色快照与对照](writing-policy.md#保存快照并对照) 保存副本，执行 humanizer 并检查 diff。局部更新只处理 scratch/sections.json，通过后才 apply-update；随后完成归档、链接及 report-note 同步，再检查：

```text
python <skills_root>/research/scripts/research_task.py verify --work-dir <work_dir>
```

成稿后先按 [报告语言润色](writing-policy.md#报告语言润色) 执行 humanizer 并对照证据复核，再运行 verify。verify 同时检查结果有效性、报告与本次结果的一致性、来源引用、图片、本地链接和交付文件；通过后把报告文件散列及研究摘要记录在当前任务的 verified.json。它不修改报告，也不验证论证的语义、润色是否完成或自动访问远程 URL。完整／部分报告都能通过，但可见状态必须准确；之后改动正文须重新 verify。

不带 --outline 的 validate_report.py 仍可做独立的文件检查，但不会检查研究一致性，不能替代任务最终 verify。

## 用户明确要求的附加交付

规则唯一来源为 [delivery-policy.md](delivery-policy.md)。create 可用 `--report 分析.md` 改主报告文件名，用重复的 `--extra "exports/report.pdf=用户要求附带 PDF"` 登记精确附加文件。也可编辑 outline.delivery，不能按泛化扩展名放行所有文件。

## 清理前核对

```text
python <skills_root>/research/scripts/research_task.py cleanup-plan --work-dir <work_dir>
```

该命令验证目录归属、当前结果、报告及历史检查记录，任何一方变化均需重新 verify。返回待删任务相对路径、保留的报告相对路径、文件数、字节数、plan_id 和 requires_confirmation，不执行删除。eligible 仅表示技术条件满足，不能代替用户确认。

向用户展示具体清理范围并取得确认后，重新运行该命令；plan_id 未变即可立即按 [交付规范](delivery-policy.md) 用原生文件操作删除精确任务目录并检查结果。同范围已有明确确认时不重复询问；计划变化、用户仍需补查或要求保留时不直接删除。不要为保存预览而向任务目录写入新文件，否则清单变化会使 plan_id 改变。检查被拒绝时不得换工具规避。
