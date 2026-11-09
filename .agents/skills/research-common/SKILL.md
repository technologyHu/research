---
name: research-common
description: 为研究类任务和报告提交提供共用的主题注册、计划、任务配置、证据、写作、保存与校验规则。作为内部支持子技能，按调用方已确定的类型与范围提供资料和工具，不选择或调用顶层入口。
---

# 研究与报告共用支持

只处理调用方已经确定的任务类型与范围，返回规则、任务配置或校验结果，不启动另一种顶层工作流。按需读取下列资料，不要求一次加载全部文件。

- 目录、附件、当前计划和清理：[交付规范](references/delivery-policy.md)。
- 主题命名：[统一主题注册表](references/theme-registry.md)。
- 类型、已有成果复用与基础缺口：[类型与复用规则](references/routing.md)。
- 长期计划：[计划维护](references/theme-planning.md)、[模板](references/theme-plan-template.md) 与 [对象背景](references/object-background.md)。
- 执行与增量续查：[执行规范](references/execution-policy.md)、[任务管理](references/task-management.md)、[配置约定](references/research-config.md) 与 [局部更新](references/report-updates.md)。
- 证据和成稿：[证据规范](references/evidence-policy.md)、[写作规范](references/writing-policy.md) 与 [分析质量标准](references/analysis-criteria.md)。
- 指定文章与源码证据：[文章获取](references/article-acquisition.md) 与 [源码理解接入](references/code-understanding.md)。

公共任务、文章、校验和润色实现均位于本技能的 scripts/，调用方直接使用这些工具，不依赖顶层入口的私有目录。已有任务配置、报告位置和命令参数保持兼容。

读取 YAML 使用本技能的 [Python 依赖清单](requirements.txt)。任务需要抓取或处理参考文章时，还需准备 [文章抓取技能的依赖](../web-article-fetcher/requirements.txt)。

需要成稿时可使用 [research-report](../research-report/SKILL.md)；需要对象证据时可使用 [research-deep](../research-deep/SKILL.md)；配图可使用 [draw-diagram](../draw-diagram/SKILL.md)，仍遵守项目的图像能力条件。共用子技能只完成被请求的阶段，不回调顶层入口。
