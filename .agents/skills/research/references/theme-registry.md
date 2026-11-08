# 统一主题注册表

项目根目录的 [themes.yaml](../../../../themes.yaml) 是 research、research-analysis 和图谱共用的主题词表。主题名与子主题名不在各技能内分别维护；目录格式及时间规则以 [交付规范](delivery-policy.md) 为准。

每项包含稳定 id、英文 slug、中文或英文显示名 name、父主题 parent，以及可选 aliases。id 在改显示名时保留；parent 引用父主题 ID。父链的 slug 从大到小用连字符拼接，得到一个目录名，显示时按父链名称组成面包屑。

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

以上主题完整目录名为 agent-memory。分类字段持久保存 agent-memory，而不是用户输入的别名。主题 ID、完整目录名及别名必须无歧义，parent 必须存在且不能形成环；完整主题名不超过 96 字符。兄弟同 slug、不同路径压平后重名、Windows 保留名称均不能进入新报告目录。

从项目根执行：

```text
python .agents/skills/research/scripts/research_task.py themes --workspace .
python .agents/skills/research/scripts/research_task.py add-theme --workspace . --id agent-memory-lifecycle --slug lifecycle --name 生命周期 --parent agent-memory --alias 记忆生命周期
```

首次在没有注册表的新工作区使用时可运行 init-themes --workspace .，只建立 general 条目；已有文件不会被覆盖。注册工具保留条目数据，以 JSON 兼容的 YAML 写回；读取普通 YAML 需要 PyYAML，不自动安装环境依赖。新增条目与计划、报告一起按授权纳入版本管理，命令不会自行暂存或提交。

新报告只能引用已注册主题。旧报告的未登记主题可兼容读取，不能将其静默映射为另一个主题；需要统一时先登记、核对范围和引用。修改 name 只影响展示；修改 slug 或 parent 会影响完整目录名，需要明确迁移范围、修订报告路径并更新引用，不能只改注册表后宣称目录已同步。

分析洞察采用同一词表，但报告目录保持扁平；同主题多个独立问题可加不同专题标识。各类报告按规范主题 ID 聚合，显示名或修订日期变化不会创建新的主题或工作身份。
