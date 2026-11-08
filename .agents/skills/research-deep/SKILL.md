---
name: research-deep
description: 执行 research 入口规划的论文、开源项目、产品或评测对象调研与针对性补查，先复用有效证据再补缺口，交付到 research-reports。分析洞察由独立入口 research-analysis 负责。
---

# Research Deep：执行调研

本技能执行 `paper`、`open-source`、`product`、`benchmark` 的对象调研。收到 analysis 主题／问题分析任务时，沿用目标与上下文交给 [research-analysis](../research-analysis/SKILL.md)，不把它转成一轮资料搜集。来自分析的基础补查只执行已说明的问题与接受条件，结果返回原分析任务；需要时按 [执行交接](../research/references/routing.md#执行交接与基础补查) 补齐范围。

1. 按 [任务管理](../research/references/task-management.md) list/show 定位任务，没有计划时先执行 [research](../research/SKILL.md) 的规划。多个匹配任务不要自动取第一项。
   先按 [已有成果核对](../research/references/routing.md#已有成果核对与复用) 确定本轮仍有效的证据与实际缺口，保留原来源和日期，仅补查未覆盖或已失效部分。
   已关联长期主题计划时，先核对当前状态、本次任务的问题、依赖与验收，按 [主题计划维护](../research/references/theme-planning.md) 回填开始、实际 run_id、阻碍及阶段进展。暂停／归档主题仅在用户要求继续时按规范恢复，不展开本次授权范围以外的待办；旧成果不充分时回退对应状态并保留历史。
   首次执行保存 [本次范围快照](../research/references/theme-planning.md#本次执行范围快照与回写前对照)，恢复时与当前计划对照；只复核本次问题、对象／版本／时间及验收实质改变涉及的范围，不因无关计划修订全部重查，不覆盖旧快照接受变化。
   按 [依赖规则](../research/references/theme-planning.md#依赖的满足失效与复核) 核对所需成果及接受条件，记录实际采用版本／片段；hard 未满足的部分暂停，已授权的独立工作可继续。前置变化后定位实际使用的主张，必要时逐层复核下游，不能只看前置任务状态。
2. 读取所选类型的模板与清单，以及 [证据规范](../research/references/evidence-policy.md)、[执行规范](../research/references/execution-policy.md) 和 [交付规范](../research/references/delivery-policy.md)。
   指定参考文章必须按 [文章获取流程](../research/references/article-acquisition.md) 获取；按需调用 [web-article-fetcher](../web-article-fetcher/SKILL.md)。全部先存当前任务，人工阅读并接受正文，保留获取失败与未核对缺口；不得只看搜索摘要。新发现的补充文章按需登记 optional。
   optional 不免除实际引用时的正文核对与归档。按文章 id 重查正文，补图使用独立图片命令；刷新失败可沿用旧有效版本并说明缺口，不把旧快照宣称为最新内容。
   正文变化后按检查器的 stale_article_fields／stale_articles 复核相关结论，复核后才更新实际依赖的 article_fingerprints；接受正文和归档原文不解除结论过期。
   本次问题需要源码证据时，按 [源码理解接入](../research/references/code-understanding.md) 将当前任务、对象／问题、版本、指定代码及已有选择记录交给 [code-understanding](../code-understanding/SKILL.md)。由它统一完成必要的选仓、目标复核和源码分析；接收按问题映射的证据与缺口后，统一写回步骤 3／4 的 light/full 记录，再继续步骤 5—6。没有合格实现的部分保留缺口，独立资料研究继续；不重复选仓，不另建对象或报告。
3. **light**：开始时保存范围指纹，复用已核对且符合本轮范围的资料，并读取缺口所需的原始资料，将结论、证据位置、版本与缺口写入 notes.md，按任务管理文档填写 outline.assessment。无需 fields、逐对象 JSON 或 progress；问题变化时整份复查，扩大范围时先 promote。
4. **full**：按 [配置约定](../research/references/research-config.md) 确定 fields，先用结果脚本 --fingerprints 获取输入指纹；逐字段复用有效证据、补查实际缺口，保存 results/<item_id>.json。记录 confirmed／inferred／unknown／not_applicable 与理由、来源和 locator；复查后才更新指纹并将进度改为 done。
   关键主张对应直接证据及其条件；出现冲突时按证据规范记录各方说法和处理理由。light 先 promote，未解决的事实矛盾不能写成 confirmed，也不能用并列观点掩盖。
5. 检查命令：light 使用 `python <skills_root>/research/scripts/validate_results.py --outline <outline.json>`；full 另传 `--fields <fields.json>`。full 可用 --item 检查本批次，成稿前检查全部对象。
6. 分开读取 valid 与 completion。常规退出码 0／2／3 分别表示完整／部分／阻塞，1 为结构或时效失败。过期／pending 先复查；partial 带明确缺口交付；blocked 不宣称完成也不清理工作资料。自动检查不能代替对来源和论证的审核。
7. 用户要求对象报告时衔接 [research-report](../research-report/SKILL.md)；分析的针对性补查将证据、版本、实际覆盖与缺口返回原 analysis，由其复核判断，再走公共成稿流程，不为每个补查重复创建同一分析或无要求的报告。只要计划或证据时停在相应阶段。不要从被拦截页面、标题或搜索摘要编写未读正文。

并行按当前用户授权和工具能力选择，不是每个对象都必须创建子代理。默认只读分析；运行下载项目、登录、部署或发布需在用户任务范围内。
