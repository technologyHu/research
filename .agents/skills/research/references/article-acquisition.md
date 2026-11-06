# 参考文章获取、核对与归档

所有 research 类型及 light／full 都遵循本流程。抓取能力由项目内 [web-article-fetcher](../../web-article-fetcher/SKILL.md) 提供，来源判断仍遵循 [证据规范](evidence-policy.md)。下列命令从项目根执行，`<work_dir>` 使用任务返回的相对路径。

## 指定文章必须获取

用户明确指定的参考文章必须登记并执行获取，不再询问是否下载。只有标题时先定位对应 URL，存在实质歧义再澄清。网页文章走抓取脚本；PDF 等文档经论文／PDF 读取流程提取正文后导入。

创建任务可重复传 `--reference URL`；已有任务使用：

```text
python .agents/skills/research/scripts/research_task.py add-article --work-dir <work_dir> --url https://example.org/article
python .agents/skills/research/scripts/research_task.py fetch-articles --work-dir <work_dir>
```

自行发现的补充来源需要获取时，先用 `add-article --optional` 登记，再 fetch-articles。它会执行当前清单内的待获取项；可重复 `--id <文章ID>` 只处理选定文章，其他条目保持原样。相同 URL 去除 fragment 后去重，保留查询参数，不合并可能代表不同版本的 URL。已取得正文的缓存复用原日期，不假装重新访问；需要重查当前网页时用 `fetch-articles --id <文章ID> --refresh`。

optional 只表示未引用时不强制获取，不允许把未读文章用于结论。报告正文、表格或脚注直接引用某篇文章时，无论 required 为何，都必须核对正文并归档。待查或失败链接可列在来源索引／自动缺口说明中，正文不将其作为依据；手工复制未核对原文或只改变链接形式也不能代替核对与归档。

outline.reference_articles 支持 URL 字符串或记录：

```json
[
  {"id": "official-intro", "url": "https://example.org/article", "required": true}
]
```

省略 id 时工具生成稳定 URL 标识，required 默认 true。不要为让检查通过而把用户指定文章改成 optional 或从清单中删除。文章清单属于获取要求，追加清单不要求重查语义未变的研究字段，但会改变本次完成度和报告摘要。

## 所有获取结果先进入临时目录

```text
<调研目录>/.tmp/<任务ID>/
├── articles.json
└── sources/articles/
    └── <文章标识>/
        ├── versions/<版本ID>/article.md
        └── image-downloads/<下载ID>/images/
```

articles.json 记录本次 run_id、原始与最终 URL、标题、实际访问时间、提取方式、质量提示、正文散列、图片状态、人工核对及归档位置。访问时间与文章头部访问日期明确采用 UTC；报告可另列用户本地日期，不把两种日期混成同一口径。清单内文件路径相对于 work_dir，最终归档位置相对于报告目录，均使用相对路径。不同 URL 的同名文章不会覆盖。

fetch-articles 默认 `--images remote`，正文保留远程图片链接。补图使用独立命令，不重抓正文、不更改正文散列、原访问日期、核对记录或已有归档：

```text
python .agents/skills/research/scripts/research_task.py download-article-images --work-dir <work_dir> --id <文章ID> --image-url https://example.org/figure.png
```

可重复 --image-url，或用 --all 选择该文章列出的所有图片；--refresh 只刷新所选图片。图片失败明确返回 failures，已有有效图保留并记录失败尝试。成功下载的图仍需人工查看，实际引用后才归档到 assets/。不修改临时正文中的链接，归档阶段再选择图片并改写最终链接。

兼容的 fetch-articles --images all／selected 也可对已缓存文章补图，无须正文 --refresh；新流程优先使用独立图片命令。未列在所选文章中的图片 URL 会报错，不静默下载到其他文章。

正文刷新先保存候选副本，再比较去除访问日期和图片缓存路径差异后的内容。内容未变时保留原正文快照、核对和归档记录，仅登记 last_fetch_attempt 的最新检查时间；确实变化时生成待核对的新版本，previous_versions 保留旧快照和记录，旧归档文件不自动覆盖。刷新失败保留旧有效正文、核对和归档，显式记录 refresh_gap；报告仍可基于旧版本给出带刷新缺口的部分结果，不能声称已经取得最新内容。再次按篇刷新成功后消除该缺口。所有版本都留在本任务临时目录，等待确认后统一清理。

正文变化还会使依赖该文章的旧结论待复核。full 检查器依据 evidence、冲突各方的来源 URL 及显式文章指纹定位字段，返回 stale_article_fields；light 使用 assessment.sources，返回 stale_articles 并要求复核整份笔记。其他文章和无关字段不受影响。重新接受正文、归档原文或刷新报告摘要，都不能代替结论复核。重读变化部分，检查原结论与条件，更新结果或记录 unknown 后，才记录当前 article_fingerprints；具体结构见 [配置约定](research-config.md#文章正文依赖指纹)。内容未变、仅补图或刷新失败不使原有效结论过期，刷新失败仍保留资料时效缺口。

默认沿用环境代理，确需直连时传 --proxy direct。已有 Playwright 可通过 --browser 允许普通浏览器读取回退；登录页、验证页不能冒充正文。不自动创建项目根 venv 或安装浏览器。先复用现有环境，确需临时环境时放在本任务 scratch/ 下，并按当前任务授权处理依赖。

## 人工核对正文

HTTP 成功不等于已读、正文完整或结论正确。阅读 article.md，核对标题、正文边界、原始来源及缺失部分，再标记：

```text
python .agents/skills/research/scripts/research_task.py review-article --work-dir <work_dir> --id <文章ID> --decision accept --reason "已对照原页面核对正文与相关章节"
```

无法确认时用 --decision reject 并写明原因。工具对正文退化为整页提取会给 needs_review；明确人工核对后才可接受。验证页或抓取失败没有可接受的正文，不能仅修改状态。

其他读取方式取得的正文先存到当前任务 scratch/，再导入并核对：

```text
python .agents/skills/research/scripts/research_task.py import-article --work-dir <work_dir> --url https://example.org/article --file <work_dir>/scratch/extracted.md --title "文章标题" --method browser
```

method 可选 browser／pdf／provided，仅说明实际获取方式，不代表已验证。保留原文，不能用搜索摘要、译文、总结或生成内容冒充文章全文；图片链接需可解析，不把临时文件路径带进最终原文。

导入与网页抓取共用版本提交逻辑：先校验 URL、方式、标题、现有清单和输入文件，再写独立候选版本，最后原子替换清单。参数错误不改旧正文；保存或清单提交失败也不覆盖现用正文及其记录。失败留下的候选副本仍只位于本任务临时目录。相同正文复用原核对及归档，变化正文保留历史并触发结论复核。

required 文章未获取、获取失败或未接受正文时，检查器保留 article_gaps；已有其他实质结论时为 partial，无实质结论时仍为 blocked。缺口会出现在可见报告说明中，必须告知用户。取得部分报告不等于允许忽略指定文章。获取命令退出码 0 只表示命令执行完毕，应继续读取 JSON 状态与 gaps；正文散列变化、清单损坏等会阻止校验。

## 实际引用后归档

实际引用指文章在正文、表格、脚注或主报告链接的补充报告中支持具体分析。候选列表、sources.md 中的普通条目及隐藏元数据不单独算实际引用。人工确认引用关系，工具核对可见链接和位置。

先写报告草稿，再对实际引用且允许保留的文章执行：

```text
python .agents/skills/research/scripts/research_task.py archive-article --work-dir <work_dir> --id <文章ID> --citation report.md#分析
```

生成 `references/<文章ID>.md`，保留原文内容、来源 URL 和访问日期。在报告中链接本地原文，也可同时就近链接原始 URL；归档原文必须从主报告可达。--citation 可重复，指定根目录中的报告 Markdown 与可选标题锚点，不能用来源索引代替正文引用。

声明 `report.md#分析` 时，原始／最终来源链接或该文章的本地归档链接必须实际出现在“分析”章节及其子章节内，范围截止到下一个同级或更高层标题；其他章节的链接不能代替。重复标题按生成的锚点区分，例如 `#分析-1`；支持 URL 编码锚点。引用式链接的定义可以位于文末，按正文使用位置判断；脚注按正文调用位置判断，未调用的脚注和链接定义不算引用。代码示例、注释和图片链接也不算文章引用。不带锚点的 `report.md` 按整份文档判断；需要指定章节时填写准确锚点。

多次 --citation 声明的每个位置都必须符合要求。archive-article 在写归档或清单前检查，verify 在交付时重新检查；报告调整章节或移动引用后，应同步更新引用位置。检查只确认链接与章节对应，不自动证明相应论断获得了原文支持。

报告实际嵌入的图片用重复 `--image <图片ID>` 一并归档到 assets/，图片 ID 来自 articles.json；更新主报告的图片链接，并保留来源说明。其他已下载图片不随原文复制，归档文章恢复对应远程链接。最终不得依赖 .tmp/；未引用文章保留在临时目录。

已有同名归档内容不同会停止，确实需要更新时用 --replace；局部更新还须把该精确文件列入 begin-update 的 --allow-file。不要覆盖其他用户资料。确实不能保留全文时可用 --exception 记录具体归档限制，并在报告可见处披露同一原因，保留原始链接；这不免除文章获取与正文核对要求。

归档状态改变后，重新生成 report-note 再 verify。verify 检查已用文章是否获取并接受、可见引用、归档文件与散列、图片、临时目录依赖及已声明例外；不自动证明正文完整或论证真实。derive 保留已取得的正文、核对记录与原访问日期，不默认重新访问网页。

确认后清理的规则仍以 [交付规范](delivery-policy.md) 为准：先交付检查、展示精确范围，取得确认后及时清理当前任务；原文归档和实际引用图片保留。
