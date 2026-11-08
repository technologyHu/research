# 分析洞察报告

本目录保存基于已有调研成果、围绕主题或问题形成的分析／洞察报告，由 [research-analysis](../.agents/skills/research-analysis/SKILL.md) 独立处理。

- 报告：`<主题名>[__<专题>]__YYYYMMDD-HHmmss/report.md`，根目录下只有一层报告目录，内部类型保留 analysis。
- 主题可有多级，层级由共用的 [themes.yaml](../themes.yaml) 推导，用 `__` 连接；主题与专题之间也用 `__`，每级 slug 内的单词用 `-`。例如 `agent__memory__architecture__mechanisms__tradeoffs__YYYYMMDD-HHmmss/report.md`，不另建 theme 或 analysis 目录。每个独立专题保留稳定报告 ID，分类记录使用原有主题 ID。
- 可选专题 target 的片段间用 `__` 分隔，片段内用 `-` 连接单词，片段数量不固定；旧单连字符及双连字符名称原样维护，修订不自动改变原主题拼接格式。
- 持续分析主题的当前计划：`<主题名>.plan.md`，新文件名按层级用 `__` 连接，如 `agent__memory__architecture.plan.md`；先复用旧位置计划，每个主题只维护一份，不给计划追加时间或另存快照。
- 时间后缀采用北京时间，用 `__` 与前面的名称连接，日期与时间之间用 `-`；真实修订后通过 stamp-report 更新目录和引用，保留最初创建时间及旧名称的日期分隔符。
- 输入报告作为来源引用，通常位于 [research-reports](../research-reports/README.md)；保留实际版本、散列和适用边界，不复制基础报告。

本目录报告产出后，用户可独立选择 [research-commit](../.agents/skills/research-commit/SKILL.md) 提交已有分析报告，无需重新分析。目录命名、附件和清理遵循共用的[交付规范](../.agents/skills/research-common/references/delivery-policy.md)。基础事实有缺口时，可按已授权范围使用对象证据子技能取得必要资料，再继续当前分析。
