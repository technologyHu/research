---
name: research-report
description: 把已有调研证据组织成中文 Markdown 单对象报告或对比综述，检查来源、引用图片并整理最终交付。用于生成、更新调研报告及按约定清理本次中间产物。
---

# Research Report：成稿与交付

1. 通过 [任务管理](../research/references/task-management.md) 定位计划。full 读取 fields 和结果，light 读取 notes 与 assessment；结合所选类型模板与清单成稿。更新已有报告的证据或结论时先读 [局部更新流程](../research/references/report-updates.md)，在改动前保存基线；普通文字更正直接编辑。
2. 遵循 [写作规范](../research/references/writing-policy.md)、[证据规范](../research/references/evidence-policy.md) 和 [交付规范](../research/references/delivery-policy.md)。先检查本次全部对象，不带 --item；valid 与 completion 分开处理，缺乏证据时不按模板编造结论。
3. 按 outline.delivery.report 起草主 Markdown，默认 report.md；局部更新先把选定章节草稿写到当前任务 scratch/sections.json，暂不 apply-update。partial 明确为部分报告，保留核心缺口及其影响；blocked 继续补查或说明阻碍，不宣称完成。正文真正引用证据，冲突各方保留条件、依据与处理理由。
4. 按 [报告语言润色](../research/references/writing-policy.md#报告语言润色) 用 research_polish.py snapshot 保存润色前副本，读取项目内 [humanizer](../humanizer/SKILL.md) 并以 embedded 模式润色草稿，再用 check 检查受保护内容并人工阅读 diff。保持技术报告的客观语气、事实和引用；发现误改先修复，不覆盖快照来接受差异。只保存最终文本，中间资料留在任务 scratch/。
5. 局部更新在润色对照通过后才 apply-update；不再对整份报告执行一轮润色，保留未复核章节的原文、版本、日期和缺口。随后完成文章和图片归档、同步报告链接。仅保存允许保留的参考文章与实际引用的本地图片；源码、实验、配置和原始 JSON 默认不随报告交付。用户明确要求的额外交付逐个登记到 delivery.extra_files，写明理由。
   按 [文章归档流程](../research/references/article-acquisition.md#实际引用后归档) 将实际引用且已核对的原文转入 references/，保留来源 URL，并链接本地原文；报告实际嵌入的图片转入 assets/，其他图片恢复网络链接。未引用文章仍留临时目录。候选来源索引不代替正文引用，获取缺口和归档限制须可见。
6. 用 research_task.py report-note 生成当前说明，原样放在主报告标题下；包含可见完成度、版本、核心及存在的非核心缺口和隐藏摘要，沿用来源保留原日期。apply-update 自动生成的说明在归档记录变化后也须同步；隐藏摘要不算引用，不用更新说明掩盖过期结论。核对事实、限定条件和引用位置，再运行 `python <skills_root>/research/scripts/research_task.py verify --work-dir <work_dir>`；后续再改正文需重新 verify。它只在临时目录保存回执，不修改报告、不验证远程可访问性、论证真实性或语言润色是否完成。
7. 按类型清单人工复核。准备交付且无需保留工作资料时，运行 cleanup-plan，向用户展示待删目录、文件数／大小和保留目录并取得明确确认。确认后复核 plan_id 未变，及时用原生操作清理精确任务目录并检查结果；同范围不重复询问。用户尚未确认、仍需补查或要求保留时保留临时资料。不要删除技能、其他任务、用户既有资料或项目根索引。汇报产物、缺口及实际清理状态。

独立 validate_report.py 不带 outline 只做文件检查，不能替代最终任务 verify。生成报告不默认执行 Git 提交、推送或发布。
