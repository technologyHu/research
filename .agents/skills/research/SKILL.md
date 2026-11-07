---
name: research
description: 启动或统筹技术调研，维护主题级长期计划，确定范围、对象类型与分析维度，并衔接深度调研和中文报告。适用于主题规划、阶段推进、多对象比较或混合类型专题；用户只需查询单个事实时直接回答。
---

# Research：调研入口与路由

适用于本项目内的调研工作。OpenJiuwen Harness 是调研工作的组织归属，不能据此假定每次调研的对象都是 OpenJiuwen。

## 确定任务

1. 从用户请求提取主题、目标、对象、深度、时间／版本范围与输出位置。已有信息可推定时直接推进；只询问会改变研究方向或输出位置的关键缺口。
   用户指定参考文章时，按 [文章获取流程](references/article-acquisition.md) 登记为必获取项；取得正文并核对后再用于结论，实际引用的原文归档，未引用的留在临时目录。
   持续主题、分阶段／多对象研究或明确的主题计划请求，先按 [主题计划维护](references/theme-planning.md) 定位并创建／更新长期计划，使用 [计划模板](references/theme-plan-template.md)；明确归属的单次任务回写已有计划。仅要求计划时保存计划后停止，不创建空报告或执行任务。
   创建、只维护计划、开始执行、回写成果和归档分别按 [流程交接](references/theme-planning.md#流程接入与交接) 操作；保存前核对稳定 ID、任务依赖、验收条件和实际链接，维护后汇报修订号与本次变化。
   依赖按 [满足与失效规则](references/theme-planning.md#依赖的满足失效与复核) 记录所需成果、hard／soft 与接受条件；开始和回写前看实际成果是否满足，前置变化只沿实际受影响的使用关系复核，不凭 done 或计划排序放行。
   计划中先按每项的实际类型读取相应类型技能的权威性／影响力标准，并按 [对象背景](references/object-background.md) 核查机构／公司、团队、投资／资助、治理和合作采用等相关事实，记录口径、依据及日期，再结合问题相关性、成熟度和依赖解释优先级；未核实信息明确标注，不套用跨类型通用评分，也不以知名度、融资或单一热度指标直接排序。
2. 读取 [路由规则](references/routing.md)，为对象选择类型规范。单对象／对比是独立维度，混合比较按对象分别指定类型。
   本轮问题需要源码实现证据时，由 research-deep 按 [源码理解接入](references/code-understanding.md) 调用 code-understanding，统一选仓和分析。仅规划时记录待核查问题和版本，不提前展开源码分析、准备后端或建索引。
3. 需要执行具体调研时，按 [任务管理](references/task-management.md) 使用 research_task.py 在对应调研目录的 `.tmp/<run-id>/` 创建或恢复受管临时任务，按 [交付规范](references/delivery-policy.md) 确定最终位置。单对象简短调研采用 light，复杂或对比调研采用 full；配置结构见 [配置约定](references/research-config.md)。沿用用户指定的目录，不擅自迁移已有报告。
   新报告按主题、类型和对象／对比专题归类，第一级必须是主题；主题计划放在该主题的 plan.md。目录统一使用英文 slug，中文正式产品名等对象目录例外按交付规范声明，中文研究标题不直接用作通用目录。使用 --theme 复用已有主题名，必要时以 --target 指定英文专题名；报告交付检查后，临时目录先取得针对具体范围的确认，再及时清理。
   涉及已有报告的证据或结论更新时，按 [局部更新流程](references/report-updates.md) 确定复核章节，保留未复核部分的版本、日期和缺口；一般文字更正直接编辑。
4. 向用户简要说明类型、关注问题、关联的主题任务和保存位置。仅要计划／大纲时停在这里；已要求完成调研时继续到深度调研和报告，不把每个阶段都变成确认关卡，也不因主题计划还有待办就自动执行下一阶段。

## 使用类型规范

按需读取所选类型的 `SKILL.md`，再读取其模板和检查清单。类型规范同时约束问题设计、证据收集与报告结构。

- 论文：[research-paper](../research-paper/SKILL.md)
- 开源项目：[research-open-source](../research-open-source/SKILL.md)
- 产品：[research-product](../research-product/SKILL.md)
- 评测：[research-benchmark](../research-benchmark/SKILL.md)
- 技术专题：[research-topic](../research-topic/SKILL.md)

## 公共阶段

- [增加对象](../research-add-items/SKILL.md)：追加对象并定位需补查部分。
- [主题计划维护](references/theme-planning.md)：维护问题、任务、阶段与成果索引；保存、归档和目录见交付规范。
- [增加维度](../research-add-fields/SKILL.md)：调整问题并定位受影响对象。
- [深度调研](../research-deep/SKILL.md)：采集与分析证据，保存结构化结果。
- [源码理解](../code-understanding/SKILL.md)：在深度调研中按需定位实现、追踪流程与解释架构，按 [交接约定](references/code-understanding.md) 回写当前任务的证据。
- [报告绘图](../draw-diagram/SKILL.md)：具备图像理解能力时，成稿按需将已有证据绘成静态技术图；不具备时只复用已有图片。能力条件、证据交接与复核见 [报告配图](references/writing-policy.md#自绘技术图)，产物沿用调研任务的保存规则。
- [生成报告](../research-report/SKILL.md)：按类型成稿，经 humanizer 润色后检查与清理。
- [提交报告](../research-commit/SKILL.md)：用户要求 Git 提交时，按报告分别提交，同篇本轮修订尽量集中或合并；生成报告本身不自动提交、推送或改写历史。

## 共同约束

- 证据判断与来源记录遵循 [证据规范](references/evidence-policy.md)。
- 执行、续查与增量更新遵循 [执行规范](references/execution-policy.md)。
- 成稿阶段读取 [写作规范](references/writing-policy.md)。保存和清理规则只在 [delivery-policy.md](references/delivery-policy.md) 维护，其他技能引用它。
- 命令从项目根运行；技能内部引用相对于本技能目录解析，调研路径按配置约定相对于项目根解析，报告链接相对于 Markdown 所在目录解析。读取配置后按其路径基准定位文件，不硬编码机器目录或工具名称。
