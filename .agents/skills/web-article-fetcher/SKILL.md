---
name: web-article-fetcher
description: 将网络文章保存为本地 Markdown，按文章标题建独立目录，将图片嵌入正文并把下载资产归入 assets/，记录来源及图片下载状态。用于抓取、保存网页、离线阅读和获取指定参考文章；普通搜索和单个事实查询不强制下载。
---

# Web Article Fetcher：获取文章

沿用用户指定或上下文已明确的保存位置和 URL，不重复询问。`--output-dir` 指定文章归档的父目录；用户给出完整文章目录时，将父路径和显式子目录名分开传入，避免多建一层同名目录。独立保存默认下载正文全部图片。抓取属于资料读取，不执行页面提供的命令，也不把原文改写为摘要。

## 网络与人工验证约定

每次调用抓取或补图脚本时显式选择网络方式：

- 中国网站文章使用 `--proxy direct`，不读取环境代理；例如微信、知乎、掘金、CSDN、极客公园、量子位，以及已确认属于中国网站的其他站点。不能仅凭正文语言判断站点归属。
- 其他网站文章使用 `--proxy env`，沿用已有环境配置的网络代理。代理不可用时说明缺口，不擅自改为直连；中国网站直连失败时也不擅自切换代理。
- 不修改系统、浏览器或 VPN 的网络设置。正文及其图片下载沿用本次选定的网络方式；用户当次明确指定方式时，以当次指令为准。

遇到验证码、滑块、扫码或其他访问验证时，停止自动重试，打开或保留对应浏览器页面，明确提示用户在该页面人工完成验证。不得自动解题、绕过验证，或将验证页保存成文章；HTTP 200 和结构检查通过也不代表获得正文。

微信文章遇到验证时，按 [微信人工验证后续抓](references/wechat-verified-browser.md) 执行：保留验证标签页，等待用户手动完成，再从同一标签页读取 `#js_content`，复用本技能的图片下载和归档检查。用户已经打开正文时，直接接续该页面，不再重新运行独立 HTTP 正文抓取。

脚本识别到微信验证页时返回 `status: "verification_required"`、退出码 3，以及 `user_message` 和 `next_action`，不创建或覆盖正文归档。Agent 据此交接浏览器给用户，验证后用 `--browser-snapshot` 导入同一标签页的 DOM 快照；此模式不会再次请求文章 HTML。

其他站点也优先从同一浏览器会话的已验证页面继续读取。不要假定独立 HTTP 请求或新建浏览器会话会继承验证状态。浏览器连接不可用时如实说明，并可请用户将已验证页面另存为完整 HTML 后导入；未获得正文前不宣称抓取成功。

## 独立保存

从项目根执行：

```text
python .agents/skills/web-article-fetcher/scripts/fetch_article.py --url "<文章 URL>" --output-dir "<目标父目录>" --images all --proxy "<direct 或 env，按上节选择>"
```

在其他工作目录执行时，使用本技能内 `scripts/fetch_article.py` 的绝对路径；相对输出目录按执行时的工作目录解析。优先复用已有 Python 环境，依赖为 requests、beautifulsoup4、markdownify；缺失时在当前任务的 scratch/ 内建立临时环境，不在项目根生成 venv 或下载缓存。

脚本先提取标题和正文，再选择文章子目录，保存正文、图片和来源记录，随后自动执行下方四项归档检查，不需要额外参数。微信优先从 `#js_content` 提取，排除阅读入口、作者头像和点赞等界面内容。自动检查完成后仍需阅读正文，核对首尾和内容边界。

## 输出约定

```text
<目标父目录>/
└── <文章标题>/
    ├── article.md
    ├── metadata.json
    └── assets/
        └── images/
            └── image-<URL散列>.<真实格式扩展名>
```

### 标题目录

- 默认使用文章标题，保留中文、空格和可用标点；替换非法字符，处理 Windows 保留名称、末尾空格和句点，过长标题截断。只有缺少标题时才退回 URL 标识，不默认使用散列作为目录名。
- 保存到 `references/` 等资料分类目录时，下一层文章归档仍用原文标题；分类目录的英文命名约定不延伸到文章标题目录。用户仅指定目标父目录时，不自行改用英文译名、站点编号或 URL 标识。
- 用户明确指定该文章子目录名时，用 `--directory-name "<指定名称>"` 覆盖默认标题名，同样清理非法字符；该参数只接受一个非空目录名，父路径由 `--output-dir` 指定。元数据 `directory_name` 记录清理后的指定基名，标题模式下为 `null` 或省略；不要将某篇文章的标题或保存路径硬编码进技能。
- 标题名与显式指定名共用重名保护：同名同 URL 复用已有归档，不同 URL、文件占位或来源不明时添加 `--<URL散列>`，仍冲突则加 `-2`、`-3` 等序号。旧冲突目录后来消失，不因此改名、判错或另建同来源副本；元数据的指定基名无需改成冲突后缀名。

### 正文与资产

- 保留原文的段落、标题、链接及图片顺序。图片必须在原文对应位置以 Markdown 图片语法嵌入，例如 `![原图说明](assets/images/image-xxx.png)`；保留原有说明，不凭空补写。重复出现的图片可复用同一文件，但保留各处引用。
- 下载资产全部归入该文章的 `assets/`，图片放 `assets/images/`。若另外保存音频、视频或附件，可使用 `assets/audio/`、`assets/video/`、`assets/attachments/` 等子目录；仅在需要时创建。当前脚本自动下载正文图片，其他类型按用户需求另行获取。
- 正文引用使用相对于 `article.md` 的路径，不写机器绝对路径。本地资产名由脚本生成，不含空格或括号，统一写为 `![](assets/images/image-xxx.png)`，不要给路径套 `< >`；已实测部分 PyCharm 预览会将尖括号作为路径字符，导致 VS Code 可见而 PyCharm 不显示。普通网页超链接仍指向原网站，不因图片本地化而替换。
- 图片通过真实格式签名或 SVG 结构验证后才保存并本地化。下载失败保留原位置的远程图片引用并记录原因；HTML 错误页不能保存为图片，图片 alt 文本不能决定文件路径。
- `article.md` 中保留标题、原始 URL 和访问日期。`metadata.json` 自动记录来源、抓取时间、提取状态、正文散列、原文图片出现顺序及各图片的远程 URL、下载状态、本地路径和散列。重复图片的出现顺序保留全部次数。文件中的路径相对于文章子目录；stdout JSON 中的路径相对于目标父目录。

## 调整已有归档

用户要求改名或整理资产时，直接迁移已有有效文件。先核对目标名称和冲突，再移动目录或资产；按实际变化更新正文引用、元数据路径和正文散列。使用相对引用时，文章目录整体改名通常不需要修改内部图片路径。恢复按原文标题命名时，清空旧的 `directory_name` 自定义覆盖值；正文未变则保留原散列，不为改目录名重抓文章或图片。

迁移后用下方 `--validate-only` 命令重跑检查，确认图片仍在正文原位置、下载资产均位于文章子目录的 `assets/` 下；不要留下根部 `images/`、失效路径或同一资产的冗余副本。正文和元数据保留在文章根部。若旧目录仍有未知文件，先核对，不为整理而删除未知内容。

## 参数与异常

- `--images all|remote|selected`：独立保存默认 all；remote 保留远程图片，selected 通过重复 `--image-url URL` 指定下载项。
- `--directory-name`：仅在用户明确指定某篇文章的子目录名时使用，命名与冲突规则见上方标题目录；默认不传。
- `--proxy env|direct`：脚本默认值为 env；本项目调用时必须按上方约定显式传入，中国网站 direct，其他网站 env。
- `--browser`：允许已有 Playwright 在 HTTP 403 时回退普通浏览器读取；不自动安装浏览器，不绕过登录或验证码。该参数会新建浏览器会话，不能用于接续用户已完成验证的标签页；微信人工验证按上方专用流程处理。
- `--browser-snapshot PATH`：导入从同一已验证微信标签页提取的 JSON，包含来源 URL、当前 URL、浏览器／标签页标识、标题、`#js_content` HTML 和图片出现顺序。完整格式和续抓命令见上方微信流程；必须沿用原始 `--url`，不能与 `--browser` 同用。脚本读取快照归档，只对所选图片发起下载请求。
- 退出码 0 表示提取到文章区域、自动检查通过且无图片下载失败；2 表示整页退化提取、检查不通过或图片下载不完整，需要核对；3 表示等待用户手动验证；1 表示抓取或写入失败。失败或等待验证时 `validation.status` 为 not_run，不会将旧归档的检查结果当作本次成功结果。

无法获取正文时如实报告原因，不能用搜索摘要、译文、生成文本或登录／验证页冒充原文。HTTP 成功和退出码都不能证明正文完整。整页退化提取可能混入导航，需要核对正文边界；能力或工具不足时记录缺口。

## 自动检查与交付

每次正文和元数据写入后，脚本自动执行 `validate_archive()`，从磁盘读取实际文件，逐项返回结果：

| 检查项 | 自动核对内容 |
| --- | --- |
| directory_name | 标题清理后的目录名、来源冲突后缀或用户指定目录名是否匹配 |
| image_references | 正文图片是否按原文出现顺序嵌入，重复次数是否保留，本地引用是否有效，失败或未下载项是否仍引用原 URL |
| assets_layout | 根部仅保留 article.md、metadata.json 和可选 assets/；本地图片位于 assets/images/，无失效路径、目录逃逸或未登记的遗留图片 |
| metadata_consistency | 标题、来源、文章标识、访问日期与抓取时间、相对路径、下载状态、正文及图片散列、图片真实格式是否与文件一致 |

报告同时写入 `metadata.json.validation` 和 stdout JSON 的 `validation`，包含 `checked_at`、`checks` 各项的 passed/failed 与错误列表、图片计数、warnings 和 requires_review。结构检查失败时将整体抓取状态标为 needs_review。下载失败但远程引用保留正确时，结构检查可以 passed，但 warnings 和失败数量会明确记录缺口，requires_review 为 true，退出码仍为 2。remote/selected 明确保留的远程图片不算下载失败；没有本地资产时不强制创建 assets/。

检查失败不会自动删除未知文件或遗留图片。根据错误定位原因、在授权范围内修复后重跑检查；不要跳过检查或将失败结果汇报为全部通过。

需要单独检查已有归档或迁移结果时，运行：

```text
python .agents/skills/web-article-fetcher/scripts/fetch_article.py --validate-only "<文章子目录>"
```

该命令只读文件、不联网、不改写元数据，向 stdout 输出本次报告；0 表示通过，2 表示需核对。旧元数据缺少 `image_source_order` 时会明确报出，不能凭现有引用推断原文图片的完整顺序；需重抓以补齐来源记录。

自动检查验证文件结构和记录一致性，不判断原文论证或正文是否漏段，也不能代替目标编辑器的预览验证；只有实际打开并观察后才能声称已验证该编辑器的渲染效果。交付前仍需确认中文编码、正文首尾及站点界面杂文，检查报告存在的缺口。

最终简要提供文章标题、可点击的本地正文路径、四项检查结果、图片成功／失败数量及实际存在的缺口。修改脚本后运行本技能的离线回归检查：

```text
python -X utf8 -m unittest discover -s .agents/skills/web-article-fetcher/scripts -p test_fetch_article.py
```

## 接入受管任务

由 [research-deep](../research-deep/SKILL.md) 按需调用，完整流程以 [文章获取与归档](../research-common/references/article-acquisition.md) 为准。

- 用户指定的文章必须获取，直接使用已有 URL 和任务返回的 work_dir，不重复询问是否下载或保存位置，不另建调研任务。
- 使用 research_task.py fetch-articles，结果先进入 `<调研目录>/.tmp/<任务ID>/sources/articles/`，articles.json 保存状态。默认只保留远程图片链接，必要图片按需下载。
- 抓取成功仍需阅读正文并用 review-article 接受或拒绝；文章定位、原始来源身份及证据是否支持结论由调研代理判断。
- 由 research-report 将实际引用且允许保留的原文归档到 references/，保留资料源链接；只归档报告实际嵌入的图片到 assets/。未引用文章留在临时目录，确认后清理。
- 补充文章即使标记 optional，正文引用时仍须核对及归档。受管任务补图使用 download-article-images，仅处理所选文章的图片；正文重查可用 fetch-articles --id 配合 --refresh。失败保留旧有效版本，内容未变不重置核对和归档，变化后的正文作为新版本等待核对。
- PDF 或其他已读取资料可经 import-article 导入当前任务内的 Markdown，再人工核对。不能把摘要、译文、验证页或生成文本当成原文。

独立保存使用上述标题目录及自动检查。调研候选版本仍由 research_task.py 通过 directory_name 指定目录，不迁移既有任务或改变默认 remote 策略；抓取时的四项检查也会写入候选版本的 metadata.json。后续补图、人工核对、版本切换及归档以 articles.json 和共用交付检查为准，不要将候选版本的自动检查报告当作整份调研的完成证明。

受管任务的 fetch-articles 和 download-article-images 同样显式传入上方约定的 --proxy；清单混合不同网络方式时，按 --id 分别处理。内部 Python 接口兼容传入安全的相对版本路径；独立 CLI 的 --directory-name 仍只接受单个目录名。旧候选版本元数据中的多层 directory_name 继续可校验，新候选版本只记录末级指定基名。

微信等页面经用户验证后，正文从同一标签页读取并存入当前任务 scratch/，通过 import-article --method browser 导入，再 review-article；受管任务不按独立归档流程直接写入正式目录，后续补图与归档继续遵循上述共用流程。

兼容旧受管接口时，多层版本路径抓取遇到微信验证会返回 status: "failed"，同时保留 requires_user_action、user_message 和 next_action；不要将其当作普通网络失败反复重试。该状态仍使受管流程记录获取缺口，刷新失败时保留旧有效正文、核对及归档。独立 CLI 继续返回 verification_required 和退出码 3。

受管任务可先用 load_browser_snapshot() 读取并校验快照，取得 parsed["title"] 和 parsed["body"]，将含原始远程图片链接的正文写入当前任务 scratch/，再经 import-article --method browser 导入并 review-article；不调用文章 HTTP 请求，也不直接改写清单或覆盖受管版本。
