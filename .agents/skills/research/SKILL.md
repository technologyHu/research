---
name: research
description: 统筹调研计划、对象调研与基于已有成果的主题分析洞察。先核对已有成果，再按目标选择类型、补查范围和执行路径，衔接中文报告。适用于新调研、续查、增补、比较和跨类型研究；单个事实查询直接回答。
---

# Research：调研入口与路由

适用于本项目内的调研工作。OpenJiuwen Harness 是组织归属，不限定研究对象。

## 确定任务与复用成果

1. 提取目标、对象、待分析主题或问题、深度、版本／时间范围和期望交付。先读 [路由规则](references/routing.md)，区分对象调研与分析洞察；仅需源码解释时交给代码理解入口。已有信息可推定时直接推进，只澄清会改变方向或位置的关键缺口。
2. 按 [已有成果核对与复用](references/routing.md#已有成果核对与复用) 定位用户指定或相关主题的计划、报告及仍在的任务，逐问题判断可复用内容、失效部分和实际缺口。跨类型来源分别采用其已有成果，只为缺口补查；不因类型不同或提出新的分析主题而重做全部调研。用户指定的文章仍按 [文章获取流程](references/article-acquisition.md) 登记、取得正文并核对，已有报告不免除本轮明确要求。
3. 持续主题、分阶段／多对象研究或明确要求计划时，按 [主题计划维护](references/theme-planning.md) 和 [模板](references/theme-plan-template.md) 创建或维护当前 plan.md；明确归属的单次任务回写已有计划。按已选类型评估候选与优先级：对象调研采用其类型标准；analysis 重点核对成果依据、分析目标、样本边界及可选观点归属，背景信息仅在影响分析时核查，见 [对象背景](references/object-background.md)。依赖按 [满足与失效规则](references/theme-planning.md#依赖的满足失效与复核) 检查实际成果与接受条件。只要求计划时保存并汇报后结束，不创建执行任务或空报告。
4. 需要新执行或报告修订时，按 [任务管理](references/task-management.md) 创建／恢复受管任务，按 [交付规范](references/delivery-policy.md) 选择位置；单对象 brief 可用 light，其余按复杂度使用 full，配置见 [配置约定](references/research-config.md)。涉及已有报告结论更新先按 [局部更新](references/report-updates.md) 登记实际范围，保留未复核部分。一般文字更正直接编辑。追加内容先区分同类型对象、其他类型对象与分析来源，按 [增加对象](../research-add-items/SKILL.md) 分流，不能直接修改成混合类型任务。
5. 简要说明本轮采用的成果、需要补查的范围、类型、关联任务和保存位置，然后进入下节相应路径。已有结果足以直接回答且用户未要求新报告时可直接回答并引用，不为流程另建重复成果。仅要大纲或证据时停在相应交付点，不自动推进主题中的其他待办。

## 执行与交接

| 本轮工作 | 执行路径 |
| --- | --- |
| 论文、开源项目、产品或评测的对象调研／补查 | 读取对应类型规范，交给 [research-deep](../research-deep/SKILL.md)；复用有效证据，只补查所需问题 |
| 基于已有成果开展主题／问题综合、机制解释或洞察提炼 | 交给 [research-analysis](../research-analysis/SKILL.md)，采用相关报告与可选思考，综合、对照并形成分析／洞察报告 |
| 分析中发现基础事实缺口 | 按路由规则界定问题、实际对象类型和接受条件；授权范围内的补查交给对象调研路径，结果返回原分析任务，不重建同一分析 |

两条执行路径共用 [research-report](../research-report/SKILL.md) 完成成稿、润色、状态说明、最终校验和计划回写。需要源码实现证据时按 [源码理解接入](references/code-understanding.md) 调用统一入口；仅规划时不准备后端或建立索引。正式执行和回写前仍按 [流程交接](references/theme-planning.md#流程接入与交接) 核对范围与依赖，不凭前置 done 或旧 verify 放行。

## 类型规范

按本轮类型和问题读取所需模板与检查清单。

- 论文：[research-paper](../research-paper/SKILL.md)，包括 survey；单篇 survey 目录使用 `survey-<paper-id>`。
- 开源项目：[research-open-source](../research-open-source/SKILL.md)
- 产品：[research-product](../research-product/SKILL.md)
- 评测：[research-benchmark](../research-benchmark/SKILL.md)
- 分析洞察：[research-analysis](../research-analysis/SKILL.md)，输入报告是依据，分析对象是主题／问题，选型与建议只是其中一种用途。

## 按需使用的公共能力

- [增加对象](../research-add-items/SKILL.md)：按对象类型或来源性质分流追加内容。
- [增加维度](../research-add-fields/SKILL.md)：增加问题、比较指标或分析维度，只复核受影响部分。
- [报告绘图](../draw-diagram/SKILL.md)：满足图像能力条件时按 [配图规范](references/writing-policy.md#自绘技术图) 使用；否则仅复用已有原图。
- [提交报告](../research-commit/SKILL.md)：用户明确要求提交时使用，生成报告不自动提交、推送或改写历史。

## 共同约束

证据与执行遵循 [证据规范](references/evidence-policy.md) 和 [执行规范](references/execution-policy.md)；成稿遵循 [写作规范](references/writing-policy.md)。保存与清理仅以 [交付规范](references/delivery-policy.md) 为详细来源，沿用已授权的精确清理范围。

命令从项目根执行；技能引用相对本技能目录，配置按其路径基准解析，正文链接相对当前 Markdown。持久配置不硬编码个人机器目录。
