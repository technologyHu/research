# 调研报告

本目录保存对象调研，由 [research](../.agents/skills/research/SKILL.md) 作为入口。

- 报告：`<主题名>/<type>/<target>-YYYYMMDD-HHmmss/report.md`，type 为 paper、open-source、product 或 benchmark。
- 主题名由共用的 [themes.yaml](../themes.yaml) 沿父子关系压平成一个名称，不展开子主题目录；同主题的不同类型报告集中保存。
- survey 论文归 paper，对象目录使用 `survey-<paper-id>`；其他命名要求沿用[交付规范](../.agents/skills/research/references/delivery-policy.md)。
- 持续主题的当前计划：`<主题名>/plan.md`，每个主题只维护一份，不另存快照。
- 时间后缀为北京时间，创建时自动生成，修订后通过 stamp-report 更新目录与引用；报告 ID 和原创建时间保持稳定。

基于已有成果形成的主题或问题分析，使用独立的[分析洞察入口](../.agents/skills/research-analysis/SKILL.md)，成果保存到 [analysis-reports](../analysis-reports/README.md)。两个入口可共用证据、成稿和提交能力。
