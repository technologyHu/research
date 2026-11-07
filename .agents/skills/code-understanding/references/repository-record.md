# 仓库选择与记录

本文件统一规定源码仓库的发现、采用和选择记录，由 code-understanding 执行；research 传入已有范围与来源，接收结果，不再重复选仓。

## 确定源码仓库

1. **有用户指定代码**：采用明确 URL、路径或对话中已绑定的项目，即使不是官方也保留其真实身份，按指定范围分析。地址、权限、版本或实现范围有问题时如实说明，不自行换仓库。只有研究对象也无法确定时才询问；不能因技能位于 research 就默认分析 research。
2. **对象明确但未指定仓库**：从原论文、项目官网／文档、作者主页的代码链接开始，再结合准确名称、作者／机构和关键方法搜索代码平台。摘要只用于发现候选，必须打开原始来源与实际代码核实。
3. **自动采用门槛**：仅采用可核验的官方实现或可信第三方复现。官方需论文、官网／官方文档或可核实作者账号的关联证据，README 自称 official 不够。复现需明确原工作和复现范围、可读的相关实现、可辨识的维护主体，以及公开复现报告、独立核验或原作者认可等复现依据。维护者身份与 Star 本身都不能证明复现可靠。普通教程、无实质复现的 fork／镜像、仅同名或概念相似的项目不自动采用。

先按本次要求的论文／发布版本核对 tag／commit 映射，再按问题匹配实际实现角色，最后在合格候选中优先官方。不能拿当前 main 冒充历史方法；版本不符的材料可作为明确标注的背景，不能填补要求版本的实现证据。未指定历史版本时固定本次读取的快照，要求最新时重新核查远端。非 Git 源码可用内容快照定位，但不能凭内容哈希推断它对应的发布版本。

按问题分配核心算法、训练、推理、评测、SDK、数据处理等角色，允许多个仓库共同覆盖。SDK 或部分评测不能证明核心算法／服务端实现公开；跨仓库静态覆盖不证明已经组合运行。分别记录源码可读性和运行状态：缺权重、数据或 GPU 不排除可读实现，已有测试或外部复现报告也不等于本次跑通。

已有选择记录先复核当前问题、版本与源码状态；仍适用时直接使用，只补查改变或未覆盖部分，不从头搜索。搜索找到足够覆盖的合格实现后可停止；负面结论须完成相关官方／作者入口与代码平台检索，明确说明“未找到符合要求的相关代码实现”，然后结束源码分支。不能扩大为“实现不存在”，也不能编写示意代码充当真实实现。访问受阻、待核实与搜索未完成按下表分别处理。

## 何时使用完整记录

需要自动发现／比较候选、核对论文与代码等版本映射，或跨仓库覆盖问题时，填写 JSON 并运行选择检查。普通指定文件、函数或单仓库阅读，只需记录路径、实际版本、变更及证据，直接 preflight；身处 research 或恢复任务本身不要求新建完整选仓记录。

## 保存和执行

需要完整记录时，research 每个对象保存一份 `scratch/code/<item_id>/repository-selection.json`；多仓库放在同一份记录中，沿用当前对象与问题 ID。独立任务沿用用户指定的位置，未要求交付文件时使用本次临时位置，不为记录修改目标仓库。选择记录不新增 research 结果字段；路径隔离与证据回写见 research 的 [交接约定](../../research/references/code-understanding.md)。

从 [JSON 模板](repository-record.example.json) 开始，用实际检索和阅读结果替换示例，执行：

```sh
node <skill-dir>/scripts/repository-selection.mjs --input <facts.json> --output <task-dir>/scratch/code/<item_id>/repository-selection.json
node <skill-dir>/scripts/repository-selection.mjs --input <current-facts.json> --previous <previous-record.json> --output <current-record.json>
```

脚本仅用 Node 内置模块，clone 后即可运行，无须准备三种后端。退出码 0 表示记录格式和选择计算成功，仍须检查 `decision.status` 和 `gaps`；无合格仓库也可退出 0。格式错误退出 1。命令不会搜索网络、下载源码或运行被研究项目，也不能替代事实核查。

## 输入约定（schema_version: 1）

| 字段 | 填写要求 |
|---|---|
| `request.object` / `version` | 研究对象和要求版本；无特定历史版本时显式为 `null`，仍须固定实际源码快照。论文 v1、v2 与软件 tag 是不同标识，需有映射依据 |
| `request.questions` | `{id, roles}` 列表；full 复用 field_id，light 使用稳定问题 ID。roles 是该问题**全部需要**的实现角色，可用 core、training、inference、evaluation、sdk、data_processing 或明确的自定义角色。仅需任一实现时用 `any` |
| `request.specified_ids` | 用户已指定的候选 ID；自动发现用 `[]`。指定但无法取得的地址也必须登记，不能省略后换仓库 |
| `request.latest` / `refresh` | 要求最新／重新检索时填 true，强制复核旧记录 |
| `search` | 实际 `checked_at` 日期、是否检查相关官方入口、代码平台及本次搜索是否结束；可补充 `queries`、入口 URL、检索边界等。未检查不能标 true。成功找到合格实现可提前结束；负面结论要求两类入口都已检查 |
| `candidates` | 每个候选的 id、url、access、authority、relevance、version、components、runtime；保留被排除候选的原始依据，由输出生成排除理由 |

候选的结构：

- `url` 为 http/https URL 或本地 `file:` URI。`access` 为 readable、blocked、missing 或 unverified，表示**代码可读性**。
- `authority.kind` 为 official、reproduction、other 或 unverified。自动选择 official 需已核实的 paper／official_page／author_profile 关联证据；reproduction 需可辨识的 `maintainer` 及 reproduction_report／independent_evaluation／author_endorsement 证据。仅 README 自称 official 不够。用户指定代码保留真实身份，不要求达到自动发现的身份门槛。
- `relevance.status` 为 matched、unrelated 或 unverified；matched 需要实际核对的相关性证据。
- `version` 记录 `requested`（须与 request.version 一致）、matched／mismatch／unverified 的 `status`、实际 `ref` 和完整 `commit`。非 Git 源码使用内容快照的 `snapshot_sha256`；存在本地修改时还需记录其摘要，并交给 preflight 核对。指定研究版本时附 tag_mapping／paper／official_page／reproduction_report 类型的版本映射证据；commit 固定本身不证明它对应某篇论文。
- `components` 为 `{role, paths, question_ids, evidence}` 列表。paths 使用仓库内相对路径，需已核实的 source_code 证据。空仓库为 `[]`；SDK 只能覆盖 SDK 问题。原论文与复现实现存在差异时在证据 note 中明确限制。
- `runtime.status` 为 not_run（默认）、blocked 或 verified。缺少权重、数据、GPU 等记入 `missing`，不会排除可读源码。verified 需实际 execution 证据；外部复现报告不能代替本次运行。运行行为仍遵循 research 的执行约定。

每条 evidence 包含 `kind`、`url`、精确 `locator`、说明支持关系与条件的 `note`、布尔值 `verified`。模板全部为 false；仅在实际打开原始来源、代码或执行记录核实后改为 true，不能为了让检查通过而填写。工具只能检查已记录的事实是否满足规则，不能证明填入的网页或代码事实真实。

## 输出和复用

`decision` 包含选中仓库、逐问题／角色的 `assignments`、未覆盖的 `gaps`、每个候选的 `assessments.reasons` 以及指纹。

| status | 后续处理 |
|---|---|
| selected | 问题要求的实现角色均有可读代码，进入源码分析；不代表研究字段已证实或运行通过 |
| partial | 分析已覆盖部分，保留 gaps，不能用一个仓库概括整个方法 |
| unavailable | 相关或指定地址访问受阻／无法取得，说明访问限制 |
| unverified | 身份、版本映射、固定快照或源码事实尚待核实，说明缺口 |
| specified_uncovered | 用户指定代码与版本／问题不符，说明边界，不自动替换 |
| search_incomplete | 继续完成必要检索，不能下“未找到”的结论 |
| not_found | 本次检索未找到符合条件且覆盖问题的实现，结束源码分支 |

相同身份优先级先覆盖更多角色，再沿候选顺序。用户指定多个仓库时按用户顺序分配角色。Star 不参与资格和排序。selected／partial 仅决定可以分析哪些源码，不自动设置研究字段 confirmed 或 done。

续查时可比较旧记录：同一冻结版本、相同问题和证据可提示复用；版本、问题、候选依据改变，或 latest／refresh 时须重新核对。负面结果不作为长期缓存。指纹只是**已登记事实**的变化检查，不检测远端新提交、伪造记录或工作树变化；仍需按任务要求检查实际 checkout、变更摘要和索引。旧记录中 `verified` 不等于本轮已核实最新事实。

选择记录保留在当前任务期间；清理前把报告需要的仓库身份、版本、范围、关键依据及日期写入已有笔记／证据和正式报告。报告引用原始固定源码，不引用将被清理的此 JSON；跨任务可从这些保留资料重新建立记录，不能声称临时文件永久可用。

## 行为测试

```sh
node --test <skill-dir>/scripts/tests/repository-selection.test.mjs
```

测试用离线候选和证据夹具调用真实选择函数，并验证 CLI 保存、重载与错误退出。覆盖用户指定优先、版本匹配、权威性／热度、空仓库、角色覆盖、运行缺件、访问受阻和复用失效；不依赖实时 Star 或网络响应，也不将这些夹具视为真实网页事实。
