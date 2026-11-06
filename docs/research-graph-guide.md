# 调研工作图谱

总览只体现调研主题、类型和对象。这里的“对象”指一项具体调研工作，不是报告里提到的候选名称。图谱按实际关联自由布局，不规定“主题—类型—对象”三层结构。

## 展示口径

- 主题与具体调研工作是节点；类型以颜色、标签和筛选体现。
- 主题连接其关联工作；计划明确记录的工作依赖可以连接两项工作。
- 同一个工作编号在同一主题中保持稳定，不随标题变化而产生新节点。
- 报告作为工作的相关资料链接，不作为节点。报告中的项目、论文、工具候选名单不会被展开成额外节点。
- 技能目录、技能维护与技能选型资料不进入总览。
- 没有调研内容时显示真实空状态，统计为 0，不添加演示数据或演示节点；有数据后启用节点浮动等效果。

## 输入边界

默认通过 `git ls-files` 获取已纳入 Git 的文件，包括已暂存文件，忽略未跟踪的工作区材料。新增调研工作需要先将其计划或报告纳入 Git，再运行生成器；远程工作流只使用当前分支已经推送的内容。

[索引范围配置](../.research-graph.json) 的 `exclude_paths` 明确排除不属于总览的资料。当前配置排除了工作区中的绘图技能选型计划和两份技能相关分析；原始文件保留，排除规则在它们以后被纳入 Git 时仍生效。

输入限于：

| 来源 | 工作识别规则 |
| --- | --- |
| `plans/<theme>/plan.md` | 读取主题元数据；“对象与任务”表里的每一项具体工作对应一个对象节点，名称采用本次目标，并保留工作编号、对象描述和类型 |
| `<type>/<theme>/<target>/report.md` | 与计划中明确关联的工作对应；没有对应计划项时，一个独立交付目录对应一项工作，以报告标题命名 |
| 同一交付目录中的其他 Markdown 报告 | 需有有效的 `research-summary` 元数据；关联同一目录的工作，不因报告文件变多而增加工作数 |

支持的类型为 `paper`、`open-source`、`product`、`benchmark`、`topic`。计划中的工作类型由“类型／对象”字段确定；独立报告的工作类型来自其目录。类型作为工作属性，不单独插入一层分类节点。

计划与报告只按明确的交付声明关联：成果索引（含其子标题）中的报告链接，或“实际报告”“实际交付”“已交付报告”等明确字段。同一段／列表项需要标明工作编号；表格读取本行的工作编号列，不从前置任务或参考说明中猜编号。参考／预期报告列、参考资料子节和下一步中的引用不算交付；`run_id` 仅保留追溯，不单独证明交付。一份报告可以支撑多项工作，仍只计为一份报告；一项工作可以关联多份报告。关联只用于导航，不把报告的完整度自动当作整项工作的完成状态。

代码示例、`.agents`、`.tmp`、参考文章、图片、归档快照、符号链接均不作为新增调研工作。未识别的自定义目录或表格写法不会自动猜测；需要扩展输入规范时同步补充测试。

## 查看与本地生成

- [README](../README.md)：动态图预览、主题总览与具体调研工作索引。主题总览逐项汇总主题、计划状态、计划链接、全部关联报告及计划中记录的下一步；报告单独标明自身完整度。暂无数据时保留完整表头和空状态。
- [交互页面](research-graph/index.html)：可直接在浏览器打开本地 HTML，支持搜索、主题／类型筛选、拖动、缩放和相关资料跳转。
- [静态预览](research-graph/preview.png)：便于关闭动画或离线查看。
- [远程页面](https://technologyhu.github.io/research/)：首次推送并部署成功后可用。

在项目根目录执行（Python 3.13）：

```powershell
python -m pip install -r scripts/research-graph-requirements.txt
python scripts/research_graph.py
```

生成器默认使用当前检出的 Git 分支。所有生成的仓库资料链接都指向该分支。Linux 需安装 `fonts-noto-cjk`；Windows 默认使用微软雅黑，也可用 `GRAPH_FONT` 指定本地中文字体。交互页不依赖 CDN、接口或在线字体，遵循系统减少动态效果设置，并提供暂停按钮。

README 的 `research-graph:start` 与 `research-graph:end` 之间由脚本维护，其他内容保留。预览最多展示 85 个真实节点并标注抽样数量，统计与交互页保留完整数据。工作标签优先显示简短工作名称，编号在下方辅助显示；密集图按空间预算减少标签，可进入交互页面查看全称。输入不变时布局和生成数据不变；不同操作系统字体可能导致首次远程重建图片时发生变化。

主题状态直接读取计划元数据，不用报告完整度推断。下一步读取“缺口与下一步”等含“下一步”标题及其子标题下的表格行动列、正文和列表，按原文顺序汇总去重，到同级或更高一级的新标题结束该范围；未记录时标为“未记录”。无计划的主题标为“尚未建立”，不把报告链接冒充计划链接。同一主题中共用的报告只列一次。归档快照不重复计为主题，但当前计划声明为已归档的主题仍保留在总览中。

## 生成与失败恢复

数据、README 和预览图片先在 `.tmp/research-graph/build-<id>/new/` 中生成。README 标记、JSON 与本地数据脚本的一致性、GIF／PNG 格式和尺寸全部通过校验后，才更新正式文件。准备或校验失败时，正式文件保持原样；人工维护的 README 内容也一并保留。

更新采用逐文件原子替换，不是跨文件系统事务。替换中途失败时，恢复已替换文件的原始内容，并移除本次新建的文件；内容没有变化的文件不替换。生成期间如果检测到正式文件被另外修改，会停止更新，避免覆盖外部修改。

如果恢复也因文件锁定等原因失败，程序将明确报错，保留 `.tmp/research-graph/build-<id>/backup/` 以及 `transaction.json`，不宣称回滚成功。解除锁定后可根据清单与备份恢复。正常完成或成功回滚后，仅清理本次创建的暂存目录。`--no-preview` 只用于开发调试，其更新集合不包括图片；正常自动化始终生成和校验完整产物。

## 自动更新

[GitHub Actions 工作流](../.github/workflows/research-graph.yml) 只监听 `openjiuwen-harness` 分支。该分支的报告、计划、索引范围配置、生成器和页面代码发生变化并推送后，工作流将：

1. 检出指定分支的最新内容，安装固定版本依赖和中文字体。
2. 执行提取测试与 JavaScript 语法检查，安装固定版本 Playwright 和 Chromium。
3. 重建图谱数据、README 索引和 GIF／PNG。
4. 对本地 HTML、HTTP、桌面和移动端执行浏览器检查，失败时停止发布。
5. 仅在生成内容变化时，以中文提交说明回写生成文件。
6. 为发布制品写入 `publication.json`，记录源提交、生成文件所在提交、数据指纹和 7 个静态资源的 SHA-256。
7. 将 `docs/research-graph` 发布到 GitHub Pages，再对真实 URL 执行版本、资源哈希和桌面／移动端验收。对页面传播延迟进行有限重试，最终失败则将工作流标为失败。

发布前和发布后的截图、线上验收结果保存在工作流制品中，保留 7 天。线上 `publication.json` 属于发布制品，不参与自动回写 Git，避免提交哈希自引用。发布后的验证失败表示本轮验收未通过，不会把部署状态冒充验证成功；该检查不自动回滚 GitHub Pages。

工作流串行执行，不 force-push；如果有人在构建期间推送新提交，旧构建的普通推送失败后停止发布，后续构建再使用最新内容。回写使用 `GITHUB_TOKEN`，不会递归触发构建。GitHub Pages 已设置为 Actions 发布，`github-pages` 环境仅允许 `openjiuwen-harness` 分支部署。

本地修改需要推送后才能更新远程展示；已打开页面需刷新获取新快照，不持续轮询。GitHub 图片缓存可能稍晚更新。更换分支时，需要同步调整工作流触发、checkout、生成参数、回写目标与发布环境分支规则。

平台规则见 [Pages 自定义工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)和 [Actions 触发规则](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)。

## 验证

```powershell
python -m unittest discover -s tests -p test_research_graph.py -v
node --check docs/research-graph/app.js
```

本地浏览器检查（CI 发布前必跑）：

```powershell
python -m pip install -r scripts/research-graph-browser-requirements.txt
python -m playwright install chromium
python tests/research_graph_browser.py
```

检查包含当前空状态、本地文件、HTTP、移动端，以及隔离测试数据下的交互行为。测试夹具仅供测试浏览器读取，不进入生成数据、README 或发布内容。截图位于 `.tmp/research-graph/`。

发布后验证由 CI 自动传入真实 URL、源提交和预期指纹，执行 `tests/research_graph_publication.py`。结果与截图位于 `.tmp/research-graph/publication/`。浏览器安装方式参阅 [Playwright CI 文档](https://playwright.dev/python/docs/ci)。
