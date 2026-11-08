# 调研报告

本目录保存对象调研，由 [research](../.agents/skills/research/SKILL.md) 作为入口。

- 报告：`<主题名>/<type>/<target>__YYYYMMDD-HHmmss/report.md`，type 为 paper、open-source、product 或 benchmark。
- 主题名由共用的 [themes.yaml](../themes.yaml) 沿父子关系压平成一个名称，不展开子主题目录；同主题的不同类型报告集中保存。
- target 表示报告的研究专题，不必等于对象 ID；片段间用 `__` 分隔，片段内用 `-` 连接单词，片段数量不固定。例如 `harness/product/codex__context-engineering__YYYYMMDD-HHmmss/report.md`，更细的范围可用 codex__context-engineering__context-compaction（harness 主题需先登记）。旧单连字符及双连字符名称原样维护。
- survey 论文归 paper，target 使用 `survey-<专题标识>`；其他命名要求沿用[交付规范](../.agents/skills/research-common/references/delivery-policy.md)。
- 持续主题的当前计划：`<主题名>/plan.md`，每个主题只维护一份，不另存快照。
- 时间后缀为北京时间，用 `__` 与专题连接，日期与时间之间用 `-`；创建时自动生成，修订后通过 stamp-report 更新目录与引用，旧日期分隔符保持原样。报告 ID 和原创建时间保持稳定。

本目录报告产出后，提交单独使用 [提交调研报告](../.agents/skills/research-commit/SKILL.md)，也可直接提交已有成果。基于已有成果形成的主题或问题分析，使用独立的[分析洞察入口](../.agents/skills/research-analysis/SKILL.md)，成果保存到 [analysis-reports](../analysis-reports/README.md)。两类报告使用同一提交技能，生成报告不自动提交。
