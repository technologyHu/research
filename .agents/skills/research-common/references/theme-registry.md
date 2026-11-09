# 统一主题注册表

项目根目录的 [themes.yaml](../../../../themes.yaml) 是 对象调研、分析任务和图谱共用的主题词表。主题名与子主题名不在各技能内分别维护；目录格式及时间规则以 [交付规范](delivery-policy.md) 为准。

用户仅登记主题或子主题时，只维护主题词表。计划任务按 [计划纳入条件](theme-planning.md#计划纳入条件) 另行登记。

每项包含稳定 id、英文 slug、中文或英文显示名 name、父主题 parent，以及可选 aliases。id 在改显示名时保留；parent 引用父主题 ID。父链的 slug 从大到小压平：规范主题名及调研报告目录用单连字符连接，分析洞察的主题目录名及新计划文件名用双下划线连接；每级 slug 内的单词仍用单连字符。显示时按父链名称组成面包屑。

```yaml
schema_version: 1
themes:
  - id: agent
    slug: agent
    name: Agent
    parent: null
  - id: agent-memory
    slug: memory
    name: 记忆
    parent: agent
    aliases: [智能体记忆]
```

以上主题的规范主题名与调研目录名为 agent-memory，分析洞察中为 agent__memory。分类字段持久保存 agent-memory，而不是用户输入的别名或双下划线展示名。主题 ID、规范主题名及别名必须无歧义，parent 必须存在且不能形成环；规范主题名不超过 96 字符。兄弟同 slug、不同路径压平后重名、Windows 保留名称均不能进入新报告目录。

从项目根执行：

```text
python .agents/skills/research-common/scripts/research_task.py themes --workspace .
python .agents/skills/research-common/scripts/research_task.py add-theme --workspace . --id agent-memory-lifecycle --slug lifecycle --name 生命周期 --parent agent-memory --alias 记忆生命周期
```

首次在没有注册表的新工作区使用时可运行 init-themes --workspace .，建立 general 条目。注册工具保留条目数据，以 JSON 兼容的 YAML 写回。读取普通 YAML 需要 PyYAML。主题登记可独立交付，登记结果用 `themes --workspace .` 核对。Git 跟踪与提交按本轮实际授权处理。

新报告只能引用已注册主题。旧报告的未登记主题可兼容读取，不能将其静默映射为另一个主题；需要统一时先登记、核对范围和引用。修改 name 只影响展示；修改 slug 或 parent 会影响完整目录名，需要明确迁移范围、修订报告路径并更新引用，不能只改注册表后宣称目录已同步。

分析洞察采用同一词表，支持多级主题，报告目录仍保持扁平；例如 agent → memory → architecture 的主题名为 agent__memory__architecture。主题与专题之间也用双下划线连接，同主题多个独立问题可加不同专题标识。旧报告和计划继续使用原路径，修订不自动改变主题分隔符。各类报告按规范主题 ID 聚合，显示名或修订日期变化不会创建新的主题或工作身份。
