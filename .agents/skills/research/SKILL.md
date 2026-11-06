---
name: research
description: 启动或统筹技术调研，确定范围、对象类型与分析维度，并衔接深度调研和中文报告。适用于目标尚需规划、多对象比较或混合类型专题；用户只需查询单个事实时直接回答。
---

# Research：调研入口与路由

适用于本项目内的调研工作。OpenJiuwen Harness 是调研工作的组织归属，不能据此假定每次调研的对象都是 OpenJiuwen。

## 确定任务

1. 从用户请求提取主题、目标、对象、深度、时间／版本范围与输出位置。已有信息可推定时直接推进；只询问会改变研究方向或输出位置的关键缺口。
   用户指定参考文章时，按 [文章获取流程](references/article-acquisition.md) 登记为必获取项；取得正文并核对后再用于结论，实际引用的原文归档，未引用的留在临时目录。
2. 读取 [路由规则](references/routing.md)，为对象选择类型规范。单对象／对比是独立维度，混合比较按对象分别指定类型。
3. 按 [任务管理](references/task-management.md) 使用 research_task.py 在对应调研目录的 `.tmp/<run-id>/` 创建或恢复受管临时任务，按 [交付规范](references/delivery-policy.md) 确定最终位置。单对象简短调研采用 light，复杂或对比调研采用 full；配置结构见 [配置约定](references/research-config.md)。沿用用户指定的目录，不擅自迁移已有报告。
   新报告按类型、分类主题和对象／对比专题归类，使用 --theme 复用已有主题名；报告交付检查后，临时目录先取得针对具体范围的确认，再及时清理。
   涉及已有报告的证据或结论更新时，按 [局部更新流程](references/report-updates.md) 确定复核章节，保留未复核部分的版本、日期和缺口；一般文字更正直接编辑。
4. 向用户简要说明类型、关注问题与保存位置。仅要计划／大纲时停在这里；已要求完成调研时继续到深度调研和报告，不把每个阶段都变成确认关卡。

## 使用类型规范

按需读取所选类型的 `SKILL.md`，再读取其模板和检查清单。类型规范同时约束问题设计、证据收集与报告结构。

- 论文：[research-paper](../research-paper/SKILL.md)
- 开源项目：[research-open-source](../research-open-source/SKILL.md)
- 产品：[research-product](../research-product/SKILL.md)
- 评测：[research-benchmark](../research-benchmark/SKILL.md)
- 技术专题：[research-topic](../research-topic/SKILL.md)

## 公共阶段

- [增加对象](../research-add-items/SKILL.md)：追加对象并定位需补查部分。
- [增加维度](../research-add-fields/SKILL.md)：调整问题并定位受影响对象。
- [深度调研](../research-deep/SKILL.md)：采集与分析证据，保存结构化结果。
- [生成报告](../research-report/SKILL.md)：按类型成稿，经 humanizer 润色后检查与清理。

## 共同约束

- 证据判断与来源记录遵循 [证据规范](references/evidence-policy.md)。
- 执行、续查与增量更新遵循 [执行规范](references/execution-policy.md)。
- 成稿阶段读取 [写作规范](references/writing-policy.md)。保存和清理规则只在 [delivery-policy.md](references/delivery-policy.md) 维护，其他技能引用它。
- 命令从项目根运行；技能内部引用相对于本技能目录解析，调研路径按配置约定相对于项目根解析，报告链接相对于 Markdown 所在目录解析。读取配置后按其路径基准定位文件，不硬编码机器目录或工具名称。
