---
name: research-deep
description: 基于已有调研计划执行证据搜集、论文或源码分析，记录结构化结果并支持续查。用于开始深度调研、继续未完成调研或补查新增对象和维度。
---

# Research Deep：执行调研

1. 按 [任务管理](../research/references/task-management.md) list/show 定位任务，没有计划时先执行 [research](../research/SKILL.md) 的规划。多个匹配任务不要自动取第一项。
   已关联长期主题计划时，先核对当前状态、本次任务的问题、依赖与验收，按 [主题计划维护](../research/references/theme-planning.md) 回填开始、实际 run_id、阻碍及阶段进展。暂停／归档主题仅在用户要求继续时按规范恢复，不展开本次授权范围以外的待办；旧成果不充分时回退对应状态并保留历史。
   首次执行保存 [本次范围快照](../research/references/theme-planning.md#本次执行范围快照与回写前对照)，恢复时与当前计划对照；只复核本次问题、对象／版本／时间及验收实质改变涉及的范围，不因无关计划修订全部重查，不覆盖旧快照接受变化。
   按 [依赖规则](../research/references/theme-planning.md#依赖的满足失效与复核) 核对所需成果及接受条件，记录实际采用版本／片段；hard 未满足的部分暂停，已授权的独立工作可继续。前置变化后定位实际使用的主张，必要时逐层复核下游，不能只看前置任务状态。
2. 读取所选类型的模板与清单，以及 [证据规范](../research/references/evidence-policy.md)、[执行规范](../research/references/execution-policy.md) 和 [交付规范](../research/references/delivery-policy.md)。
   指定参考文章必须按 [文章获取流程](../research/references/article-acquisition.md) 获取；按需调用 [web-article-fetcher](../web-article-fetcher/SKILL.md)。全部先存当前任务，人工阅读并接受正文，保留获取失败与未核对缺口；不得只看搜索摘要。新发现的补充文章按需登记 optional。
   optional 不免除实际引用时的正文核对与归档。按文章 id 重查正文，补图使用独立图片命令；刷新失败可沿用旧有效版本并说明缺口，不把旧快照宣称为最新内容。
   正文变化后按检查器的 stale_article_fields／stale_articles 复核相关结论，复核后才更新实际依赖的 article_fingerprints；接受正文和归档原文不解除结论过期。
   本次问题需要源码证据时，按 [源码理解接入](../research/references/code-understanding.md) 将当前任务、对象／问题、版本、指定代码及已有选择记录交给 [code-understanding](../code-understanding/SKILL.md)。由它统一完成必要的选仓、目标复核和源码分析；接收按问题映射的证据与缺口后，统一写回步骤 3／4 的 light/full 记录，再继续步骤 5—6。没有合格实现的部分保留缺口，独立资料研究继续；不重复选仓，不另建对象或报告。
3. **light**：开始时保存范围指纹，读取实际原始资料，将结论、证据位置、版本与缺口写入 notes.md，并按任务管理文档填写 outline.assessment。无需 fields、逐对象 JSON 或 progress；问题变化时整份复查，扩大范围时先 promote。
4. **full**：按 [配置约定](../research/references/research-config.md) 确定 fields，先用结果脚本 --fingerprints 获取输入指纹；逐字段搜集、分析并保存 results/<item_id>.json。记录 confirmed／inferred／unknown／not_applicable 与理由、来源和 locator；复查后才更新指纹并将进度改为 done。
   关键主张对应直接证据及其条件；出现冲突时按证据规范记录各方说法和处理理由。light 先 promote，未解决的事实矛盾不能写成 confirmed，也不能用并列观点掩盖。
5. 检查命令：light 使用 `python <skills_root>/research/scripts/validate_results.py --outline <outline.json>`；full 另传 `--fields <fields.json>`。full 可用 --item 检查本批次，成稿前检查全部对象。
6. 分开读取 valid 与 completion。常规退出码 0／2／3 分别表示完整／部分／阻塞，1 为结构或时效失败。过期／pending 先复查；partial 带明确缺口交付；blocked 不宣称完成也不清理工作资料。自动检查不能代替对来源和论证的审核。
7. 用户要求完整调研时衔接 [research-report](../research-report/SKILL.md)，只要计划或证据时停在相应阶段。不要从被拦截页面、标题或搜索摘要编写未读正文。

并行按当前用户授权和工具能力选择，不是每个对象都必须创建子代理。默认只读分析；运行下载项目、登录、部署或发布需在用户任务范围内。
