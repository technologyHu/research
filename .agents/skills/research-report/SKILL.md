---
name: research-report
description: 把已有调研证据组织成中文 Markdown 单对象报告或对比综述，检查来源、引用图片并整理最终交付。用于生成、更新调研报告及按约定清理本次中间产物。
---

# Research Report：成稿与交付

接收 research-deep 的对象调研证据，或 research-analysis 的成果采用记录、综合过程、核心发现与可选贡献者观点，共用本流程成稿与校验。成稿发现缺口时返回原执行分支，只复核受影响范围；不把 analysis 再转成整轮对象调研，也不在成稿阶段重做来源主体背景调查。

1. 通过 [任务管理](../research/references/task-management.md) 定位计划。full 读取 fields 和结果，light 读取 notes 与 assessment；结合所选类型模板与清单成稿。更新已有报告的证据或结论时先读 [局部更新流程](../research/references/report-updates.md)，在改动前保存基线；普通文字更正直接编辑。
   组织章节时按 [自绘技术图](../research/references/writing-policy.md#自绘技术图) 在已有笔记或草稿中安排配图，证据稳定后再生成。
2. 遵循 [写作规范](../research/references/writing-policy.md)、[证据规范](../research/references/evidence-policy.md) 和 [交付规范](../research/references/delivery-policy.md)。先检查本次全部对象，不带 --item；valid 与 completion 分开处理，缺乏证据时不按模板编造结论。
   含源码证据时，按 [源码交接约定](../research/references/code-understanding.md) 从现有记录成稿：说明仓库身份／采用依据、研究与代码版本关系、各问题覆盖及运行限制，分别引用各仓库的固定原始源码。访问受阻、待核实和未找到分别披露，不以工具总结、临时 JSON 或示意代码填补证据。补查交回当前 research-deep，只复核受影响问题，不在成稿阶段重新选仓。
   关联主题时，成稿及正式回写前按 [范围快照对照](../research/references/theme-planning.md#本次执行范围快照与回写前对照) 核对当前问题和验收；实质变化先同步配置、复核受影响证据，旧范围 verify 不作为新目标完成依据。无关任务／排序变化不要求重查，正式回写保留起始／当前修订及对照结论。
   同时按 [依赖规则](../research/references/theme-planning.md#依赖的满足失效与复核) 核对 hard 条件及已接受的成果／版本；前置 done 不替代该检查，前置 partial 的片段仅在满足既定条件时采用。未解决的依赖在部分报告中明确披露，不回写 done；证据与部分报告仍按原完成度规则处理。
3. 按 outline.delivery.report 起草主 Markdown，默认 report.md；局部更新先把选定章节草稿写到当前任务 scratch/sections.json，暂不 apply-update。partial 明确为部分报告，保留核心缺口及其影响；blocked 继续补查或说明阻碍，不宣称完成。正文真正引用证据，冲突各方保留条件、依据与处理理由。
   先按 [配图能力条件](../research/references/writing-policy.md#图表与代码) 判断能否新绘，仅在允许时调用 [draw-diagram](../draw-diagram/SKILL.md)；否则只复用现有图片。按 [配图规则](../research/references/writing-policy.md#自绘技术图) 完成适用复核，无法目视检查时如实说明。局部更新沿用本次章节范围；已有图片需按局部更新规则明确允许修改，新图按交付规范检查。图被其他章节复用时，同时核对影响，不因图片文件可修改就将未复核章节视为已更新。
4. 按 [报告语言润色](../research/references/writing-policy.md#报告语言润色) 用 research_polish.py snapshot 保存润色前副本，读取项目内 [humanizer](../humanizer/SKILL.md) 并以 embedded 模式润色草稿，再用 check 检查受保护内容并人工阅读 diff。保持技术报告的客观语气、事实和引用；发现误改先修复，不覆盖快照来接受差异。只保存最终文本，中间资料留在任务 scratch/。
   按 [图文复核规则](../research/references/writing-policy.md#自绘技术图) 对照 diff 复核受影响的图；技术内容改变时返回成稿，不作为纯润色放行。
5. 局部更新在润色对照通过后才 apply-update；不再对整份报告执行一轮润色，保留未复核章节的原文、版本、日期和缺口。随后完成文章和图片归档、同步报告链接。仅保存允许保留的参考文章与实际引用的本地图片；源码、实验、配置和原始 JSON 默认不随报告交付。用户明确要求的额外交付逐个登记到 delivery.extra_files，写明理由。
   按 [文章归档流程](../research/references/article-acquisition.md#实际引用后归档) 将实际引用且已核对的原文转入 references/，保留来源 URL，并链接本地原文；报告实际嵌入的图片转入 assets/，其他图片恢复网络链接。未引用文章仍留临时目录。候选来源索引不代替正文引用，获取缺口和归档限制须可见。
   自绘图按 [保存规则](../research/references/delivery-policy.md#自绘图的保存) 归档并检查最终嵌入效果。
6. 用 research_task.py report-note 生成当前说明，原样放在主报告标题下；包含可见完成度、版本、核心及存在的非核心缺口和隐藏摘要，沿用来源保留原日期。apply-update 自动生成的说明在归档记录变化后也须同步；隐藏摘要不算引用，不用更新说明掩盖过期结论。核对事实、限定条件和引用位置，再运行 `python <skills_root>/research/scripts/research_task.py verify --work-dir <work_dir>`；后续再改正文需重新 verify。它只在临时目录保存回执，不修改报告、不验证远程可访问性、论证真实性或语言润色是否完成。
   报告 verify 不替代绘图检查和视觉复核；按 [配图验收规则](../research/references/writing-policy.md#自绘技术图) 核对必需图的交付情况，未完成时不得仅凭 verify 通过就宣称全部交付或回写任务 done。
7. 按类型清单人工复核。已关联主题计划时，先按 [主题计划维护](../research/references/theme-planning.md) 回填真实报告链接、版本／日期、问题覆盖、完整／部分结果及缺口；阶段收口或主题结束按交付规范直接更新当前计划的状态与收口记录。准备交付且无需保留工作资料时，再运行 cleanup-plan，向用户展示待删目录、文件数／大小和保留目录并取得明确确认。确认后复核 plan_id 未变，及时用原生操作清理精确任务目录并检查结果；同范围不重复询问。用户尚未确认、仍需补查或要求保留时保留临时资料。不要删除技能、其他任务、用户既有资料或项目根索引。汇报产物、缺口及实际清理状态。
   报告 verify 通过不自动表示主题任务或主题整体完成，长期计划始终保留；主题归档与执行目录清理分别处理。
   本次报告修订了已被其他任务采用的结论时，回写计划同时标出相关依赖与实际下游，按规则复核影响并保留旧接受记录；不自动执行所有后续研究，清理前将相关成果、接受版本及待复核事项写入长期计划。

独立 validate_report.py 不带 outline 只做文件检查，不能替代最终任务 verify。生成报告不默认执行 Git 提交、推送或发布。用户明确要求提交报告时，交给 [research-commit](../research-commit/SKILL.md)，按报告分别组织提交，同篇本轮修订尽量集中或合并。
