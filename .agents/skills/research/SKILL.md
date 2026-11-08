---
name: research
description: 统筹论文、开源项目、产品和评测的对象调研与计划。先复用已有成果，再执行新调研、续查、增补或同类型比较，交付调研报告。基于已有成果的主题分析洞察使用独立入口 research-analysis；单个事实查询直接回答。
---

# Research：调研报告入口

负责 `paper`、`open-source`、`product`、`benchmark` 的对象调研，正式报告保存到 `research-reports/<主题名>/<type>/<target>-<时间>/report.md`。OpenJiuwen Harness 是组织归属，不限定研究对象。

[分析洞察](../research-analysis/SKILL.md) 是并列的独立入口，负责基于已有成果形成主题或问题的分析／洞察报告。收到此类请求时直接交接已有目标与资料，不先建立对象调研或重复计划；只有明确的基础事实缺口才进入本技能。

## 确定任务与复用成果

先读取项目根的 themes.yaml，按 [主题注册表](references/theme-registry.md) 复用规范主题 ID；新主题先登记。主题层次压成一个名称，具体报告目录由工具追加北京时间戳，不手工拼接子主题目录。

1. 提取目标、实际对象、深度、版本／时间范围和交付范围。按 [入口分工与路由](references/routing.md) 选择对象类型；仅需源码解释时使用代码理解入口。已有信息可推定时直接推进，只澄清会改变方向或位置的关键缺口。
2. 按 [已有成果核对](references/routing.md#已有成果核对与复用) 查找用户指定及相关主题的计划、报告与仍在的任务，逐问题判断可复用内容、失效部分和实际缺口。跨类型对象分别采用已有成果，只补查缺口。用户指定文章按 [文章获取流程](references/article-acquisition.md) 登记、获取并核对。
3. 持续主题、分阶段／多对象研究或明确要求计划时，按 [主题计划维护](references/theme-planning.md) 和 [模板](references/theme-plan-template.md) 维护 `research-reports/<主题名>/plan.md`。按实际类型核对候选、背景、优先级和依赖；只要求计划时保存后结束，不创建执行任务或空报告。
4. 需要执行或修订报告时，按 [任务管理](references/task-management.md) 创建／恢复任务，位置遵循 [交付规范](references/delivery-policy.md)。单对象 brief 可用 light，其余按复杂度用 full。结论更新先按 [局部更新](references/report-updates.md) 登记实际范围，保留未复核部分；一般文字更正直接编辑。追加对象或问题使用下列公共能力，不把跨类型对象塞入同一任务。
5. 简要说明采用成果、补查范围、类型、关联任务和保存位置。需要执行的部分交给 [research-deep](../research-deep/SKILL.md)，按对应类型规范研究，再用 [research-report](../research-report/SKILL.md) 成稿、校验及回写计划。已有结果足以回答且未要求新报告时直接引用回答；仅要计划或证据时停在该交付点。

## 类型规范

- 论文：[research-paper](../research-paper/SKILL.md)，包括 survey；单篇 survey 目录使用 `survey-<paper-id>`。
- 开源项目：[research-open-source](../research-open-source/SKILL.md)
- 产品：[research-product](../research-product/SKILL.md)
- 评测：[research-benchmark](../research-benchmark/SKILL.md)

需要源码实现证据时按 [源码理解接入](references/code-understanding.md) 调用统一入口；仅规划时不准备后端或建立索引。执行与回写前按 [流程交接](references/theme-planning.md#流程接入与交接) 核对范围和依赖。

## 共用能力与边界

本入口与 research-analysis 可共用计划模板、任务工具、证据规则、报告成稿和校验能力，共用工具不合并报告目录或计划。

- [增加对象](../research-add-items/SKILL.md)、[增加维度](../research-add-fields/SKILL.md)：增补所需对象或问题，只复核受影响部分。
- [报告绘图](../draw-diagram/SKILL.md)：按项目图像能力条件与 [配图规范](references/writing-policy.md#自绘技术图) 使用。
- [提交报告](../research-commit/SKILL.md)：用户明确要求提交时使用；支持两类报告，生成不自动提交或推送。

证据、执行与写作分别遵循 [证据规范](references/evidence-policy.md)、[执行规范](references/execution-policy.md) 和 [写作规范](references/writing-policy.md)。保存与清理只以 [交付规范](references/delivery-policy.md) 为详细来源，沿用已授权的精确清理范围。

命令从项目根执行；技能引用相对本技能目录，配置按其路径基准解析，正文链接相对当前 Markdown。持久配置不硬编码个人机器目录。
