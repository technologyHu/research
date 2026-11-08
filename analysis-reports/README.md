# 分析洞察报告

本目录保存基于已有调研成果、围绕主题或问题形成的分析／洞察报告，由 [research-analysis](../.agents/skills/research-analysis/SKILL.md) 独立处理。

- 报告：`<主题名>[-<专题>]-YYYYMMDD-HHmmss/report.md`，根目录下只有一层报告目录，内部类型保留 analysis。
- 主题层次通过完整目录名体现，名称由共用的 [themes.yaml](../themes.yaml) 推导，不另建 theme 或 analysis 目录。每个独立专题保留稳定报告 ID。
- 持续分析主题的当前计划：`<主题名>.plan.md`，每个主题只维护一份，不给计划追加时间或另存快照。
- 时间后缀采用北京时间；真实修订后通过 stamp-report 更新目录和引用，保留最初创建时间。
- 输入报告作为来源引用，通常位于 [research-reports](../research-reports/README.md)；保留实际版本、散列和适用边界，不复制基础报告。

目录命名、附件和清理遵循共用的[交付规范](../.agents/skills/research/references/delivery-policy.md)。基础事实需要补查时，由独立的 research 入口执行所需范围后返回本分析。
