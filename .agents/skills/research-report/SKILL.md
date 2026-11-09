---
name: research-report
description: 把已有证据组织成中文调研报告或分析洞察报告，检查来源、引用与最终交付，并按约定清理本次中间产物。作为成稿子技能，只处理调用方已明确的证据与交付范围。
---

# Research Report：成稿与交付

接收已核对的对象调研证据，或成果采用记录、综合过程、核心发现与可选贡献者观点，完成成稿与校验。发现缺口时向调用方返回具体问题与受影响范围，不调用顶层入口，也不在成稿阶段重做来源主体背景调查。

新格式报告完成创建或实际修订后，按 [修订时间与目录更新](../research-common/references/task-management.md#报告修订时间与目录更新) 执行 stamp-report；使用返回的新 work_dir 继续校验。仅复查不更新时间。工具同步本地引用，不替下游重新接受证据散列；受影响依据仍需实际复核。

沿用调用入口与当前任务的位置：对象报告属于 research-reports，分析洞察报告属于 analysis-reports。共用成稿不创建第二份报告、不合并两边计划。正式对象调研成稿时核对对应计划及实际任务映射，缺失则按 [补建规则](../research-common/references/theme-planning.md#单对象与已有报告补查) 补齐。用户明确免除计划时沿用该要求。报告完成后回写实际所属计划。

成稿时按 [值得纳入的图与演示类型](../research-common/references/writing-policy.md#值得纳入的图与演示类型) 核对取证阶段发现的素材，将有解释价值的架构、流程、界面、演示、交付物、评测和对比图放入对应章节，不为各类型凑图。形式、来源和实际核验范围准确，图文说明简短且互相补充。

1. 通过 [任务管理](../research-common/references/task-management.md) 定位计划。full 读取 fields 和结果，light 读取 notes 与 assessment；结合所选类型模板与清单成稿。更新已有报告的证据或结论时先读 [局部更新流程](../research-common/references/report-updates.md)，在改动前保存基线；普通文字更正直接编辑。
   组织章节时按 [图表与代码](../research-common/references/writing-policy.md#图表与代码) 判断哪里需要视觉解释，先检查来源资料和已有成果中的有用图片、产品／软件前端界面及演示 GIF，适用时直接插入。按 [已有图复用](../research-common/references/writing-policy.md#已有图复用) 和 [界面与演示](../research-common/references/writing-policy.md#界面截图与演示素材) 标注来源、演示任务和适用条件，核对 GIF 的关键状态与播放，不为统一风格重绘，不设数量。确需新绘时优先 Markdown 可渲染的代码图，必要时仍可生成静态图片或使用图片生成服务。
2. 遵循 [写作规范](../research-common/references/writing-policy.md)、[证据规范](../research-common/references/evidence-policy.md) 和 [交付规范](../research-common/references/delivery-policy.md)。先检查本次全部对象，不带 --item；valid 与 completion 分开处理，缺乏证据时不按模板编造结论。
   含源码证据时，按 [源码交接约定](../research-common/references/code-understanding.md) 从现有记录成稿：说明仓库身份／采用依据、研究与代码版本关系、各问题覆盖及运行限制，分别引用各仓库的固定原始源码。访问受阻、待核实和未找到分别披露，不以工具总结、临时 JSON 或示意代码填补证据。补查交回当前 research-deep，只复核受影响问题，不在成稿阶段重新选仓。
   关联主题时，成稿及正式回写前按 [范围快照对照](../research-common/references/theme-planning.md#本次执行范围快照与回写前对照) 核对当前问题和验收；实质变化先同步配置、复核受影响证据，旧范围 verify 不作为新目标完成依据。无关任务／排序变化不要求重查，正式回写保留起始／当前修订及对照结论。
   同时按 [依赖规则](../research-common/references/theme-planning.md#依赖的满足失效与复核) 核对 hard 条件及已接受的成果／版本；前置 done 不替代该检查，前置 partial 的片段仅在满足既定条件时采用。未解决的依赖在部分报告中明确披露，不回写 done；证据与部分报告仍按原完成度规则处理。
3. 按 outline.delivery.report 起草主 Markdown，默认 report.md；局部更新先把选定章节草稿写到当前任务 scratch/sections.json，暂不 apply-update。partial 明确为部分报告，保留核心缺口及其影响；blocked 继续补查或说明阻碍，不宣称完成。正文真正引用证据，冲突各方保留条件、依据与处理理由。
   先按 [配图能力条件与选型](../research-common/references/writing-policy.md#图表与代码) 判断能否新绘。满足条件时，简单关系可直接写 Mermaid 等内联代码图，需要静态技术图再调用 [draw-diagram](../draw-diagram/SKILL.md)，其他视觉表达按需使用图片生成；成本偏好不禁止必要出图。能力条件不满足时只复用现有图片。按 [配图规则](../research-common/references/writing-policy.md#自绘技术图) 完成语法、渲染和视觉复核，不以代码可解析代替可读性检查，也不对内联图强制静态导出。局部更新沿用章节范围；已有图片需按局部更新规则明确允许修改，新图按交付规范检查。复用图同时核对受影响章节，不把未复核内容视为已更新。
4. 按 [报告语言润色](../research-common/references/writing-policy.md#报告语言润色) 用 research_polish.py snapshot 保存润色前副本，读取项目内 [humanizer](../humanizer/SKILL.md) 并以 embedded 模式润色草稿，再用 check 检查受保护内容并人工阅读 diff。保持技术报告的客观语气、事实和引用；发现误改先修复，不覆盖快照来接受差异。只保存最终文本，中间资料留在任务 scratch/。
   按 [图文复核规则](../research-common/references/writing-policy.md#自绘技术图) 对照 diff 复核受影响的图；技术内容改变时返回成稿，不作为纯润色放行。
5. 局部更新在润色对照通过后才 apply-update；不再对整份报告执行一轮润色，保留未复核章节的原文、版本、日期和缺口。随后完成文章和图片归档、同步报告链接。仅保存允许保留的参考文章与实际引用的本地图片；源码、实验、配置和原始 JSON 默认不随报告交付。用户明确要求的额外交付逐个登记到 delivery.extra_files，写明理由。
   按 [文章归档流程](../research-common/references/article-acquisition.md#实际引用后归档) 将实际引用且已核对的原文转入 references/，保留来源 URL，并链接本地原文；报告实际嵌入的图片转入 assets/，其他图片恢复网络链接。未引用文章仍留临时目录。候选来源索引不代替正文引用，获取缺口和归档限制须可见。
   自绘图按 [保存规则](../research-common/references/delivery-policy.md#自绘图的保存) 归档并检查最终嵌入效果。
6. 按 [报告开头](../research-common/references/writing-policy.md#报告开头) 写一段简短说明。初稿可用 `report-note` 预览，落盘后运行 `research_task.py sync-report-note --work-dir <work_dir>`，由工具同步开头和同目录的 `.meta.json` 文件。沿用来源及原日期保留在元数据中，来源和证据限制在正文交代。核对事实、限定条件和引用位置，按修订规则执行 `stamp-report`，再用返回的工作目录运行 `verify`。后续改动需重新校验。`verify` 只写临时回执，检查报告与任务是否一致。
   报告 verify 不替代绘图检查和视觉复核；按 [配图验收规则](../research-common/references/writing-policy.md#自绘技术图) 核对必需图的交付情况，未完成时不得仅凭 verify 通过就宣称全部交付或回写任务 done。
7. 按类型清单人工复核。已关联主题计划时，先按 [主题计划维护](../research-common/references/theme-planning.md) 回填真实报告链接、版本／日期、问题覆盖、完整／部分结果及缺口；阶段收口或主题结束按交付规范直接更新当前计划的状态与收口记录。准备交付且无需保留工作资料时，再运行 cleanup-plan，向用户展示待删目录、文件数／大小和保留目录并取得明确确认。确认后复核 plan_id 未变，及时用原生操作清理精确任务目录并检查结果；同范围不重复询问。用户尚未确认、仍需补查或要求保留时保留临时资料。不要删除技能、其他任务、用户既有资料或项目根索引。汇报产物、缺口及实际清理状态。
   报告 verify 通过不自动表示主题任务或主题整体完成，长期计划始终保留；主题归档与执行目录清理分别处理。
   回写主题核心问题时只更新已确认问题的覆盖情况。本轮新增发现与证据缺口记入任务成果和范围。拟新增或实质改写主题问题须先 [取得用户确认](../research-common/references/theme-planning.md#核心问题的确认)。
   本次报告修订了已被其他任务采用的结论时，回写计划同时标出相关依赖与实际下游，按规则复核影响并保留旧接受记录；不自动执行所有后续研究，清理前将相关成果、接受版本及待复核事项写入长期计划。

独立 validate_report.py 不带 outline 只做文件检查，不能替代最终任务 verify。本技能在报告交付与计划回写后完成，不执行 Git 提交、推送或发布，也不回调顶层入口。
