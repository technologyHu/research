# 后端运行与可迁移初始化

入口依赖同一 `skills/` 下已有的 GitNexus、Understand Anything 和 Graphify 技能。复制或提交时保留这些兄弟目录。路径由脚本所在位置推导，运行文件写到本技能已忽略的 `.runtime/`，无需复制维护者的个人目录或代理。

## 技能位置与源码位置

技能可以保留在本仓库，目标源码可以在其他仓库、磁盘或没有 Git 的目录。`--target` 相对调用时的 cwd 解析；省略它才使用调用时的当前目录。后端通过绝对入口启动，cwd 设为目标目录；单个文件目标使用其父目录。源码与 Git 元数据绑定目标项目，依赖与工具缓存归属技能运行环境。索引／分析输出默认位于目标项目；受管任务调用时按 [交接约定](../../research-common/references/code-understanding.md#源码与工具输出的位置) 隔离到本任务，显式设置后端输出路径或使用任务副本，不能把默认 cwd 当作输出隔离。

使用“绝对技能脚本路径 + 独立目标路径”即可跨项目调用。后端参数中的相对路径将相对目标 cwd 解析：进入目标后，分析该目录应传 `.` 或目标的绝对路径，避免再次拼接原来的相对目标路径。运行环境准备本身不移动源码，也不要求给目标项目复制 `.agents/skills`。

GitNexus 的 registry 可能包含其他项目，cwd 不能替代 registry 绑定。先用真实路径确认对应的注册项目，再为 query/context/trace 等命令显式选择 repo；不能因为只有一个注册项目就假定它与 `--target` 相同。

## 检查、准备、执行

```sh
# 只检查目标、Git 状态与索引位置，不安装或扫描
node <skill-dir>/scripts/preflight.mjs --target <project> --backend all

# 准备选中的运行环境，不建立项目索引
node <skill-dir>/scripts/preflight.mjs --target <project> --backend understand --prepare

# 准备并运行指定后端；--run 后全部内容传给后端
node <skill-dir>/scripts/preflight.mjs --target <project> --backend graphify --run -- --version
node <skill-dir>/scripts/preflight.mjs --target <project> --backend gitnexus --run -- status
```

默认 `--backend source`，目标默认当前目录；也支持单个文件，此时后端工作目录为文件所在目录。`--run` 只接受一个后端，不能配合 `source` 或 `all`。GitNexus/Graphify 的参数传给对应 CLI；Understand Anything 的参数传给 Node，用于运行选定技能自带的 `.mjs` 脚本。

检查输出为 JSON：`target` 包含真实项目路径、Git 版本、分支、worktree 和未提交内容摘要；`indexes` 只列出已有结果，`freshness` 始终要求后端进一步检查。外置 GitNexus 索引须通过其 registry/CLI 查询。大文件超出摘要读取限额时，`fingerprintComplete` 为 false，不能用该摘要证明没有变化。

准备后的 JSON 提供后端绝对路径，但这些路径仅属于本次环境，不能写死回技能。准备日志写入 stderr，`--run` 保留后端 stdout。

## GitNexus

复用兄弟技能的 `gitnexus-cli/scripts/gitnexus.mjs`。准备步骤实际验证 FTS 与 VECTOR；项目索引独立建立，保留用户选择的范围。首次生成语义向量才使用 `--embeddings`，并按 GitNexus 本地说明处理模型下载和平台限制。

## Graphify

固定 `graphifyy==0.9.103`，传递依赖和不同 Python 版本的条件分支固定在 `graphify.lock`，使用哈希验证安装文件。可用 uv 时创建隔离 venv；否则使用已有 Python 3.10+ 的 venv/pip。首次准备需要访问配置的 Python 包源，不会升级全局 Graphify。

运行上游图谱技能时，先读取其 `LOCAL_INSTALL.md`。上游编号流程里的 `PYTHON` 使用准备结果的 `paths.python`，CLI 使用 `paths.entry` 或本入口的 `--run`。普通代码和 Markdown 文档使用已锁定的核心依赖；PDF、媒体或远程服务等额外能力需要另行准备，不能静默安装未锁定 extras。

更新锁文件：在技能仓库根目录运行 `uv pip compile .agents/skills/code-understanding/references/graphify.in --universal --python-version 3.10 --generate-hashes --output-file .agents/skills/code-understanding/references/graphify.lock`，然后重新验证准备流程。

## Understand Anything

固定上游提交、插件版本及 pnpm 版本，见 `backends.lock.json`。`vendor/understand-plugin.json.gz` 包含该提交的完整插件源码和上游许可证，双重 SHA-256 校验后才会解包；运行时不依赖 GitHub 克隆或维护者的 `.agents/tools` 目录。依赖仍通过 npm registry 下载，pnpm 工作区使用上游冻结锁，核心构建后执行实际模块导入检查。

需要受支持的 Node.js（上游核心要求 22+）和 npm。pnpm 从这里的独立 npm 锁安装，无需全局 pnpm。源码分析使用 web-tree-sitter 和依赖包自带的 WASM 语法文件，初始化跳过无关的 node-gyp lifecycle，直接通过 Node 执行锁定 TypeScript 编译器构建 core，避免 Windows 长路径/含空格路径下的 pnpm lifecycle 问题。本机验证为 Windows x64。

`--backend understand --run` 会传递 `PLUGIN_ROOT`，并设置 `UNDERSTAND_NO_WORKTREE_REDIRECT=1`，保持当前 checkout。例如：

```sh
node <skill-dir>/scripts/preflight.mjs --target <project> --backend understand --run -- <understand-skill-dir>/scan-project.mjs <project> <temporary-scan.json>
```

需要 Dashboard 时，用 Node 直接运行 `<pluginRoot>/packages/dashboard/node_modules/vite/bin/vite.js`，工作目录设为 `<pluginRoot>/packages/dashboard`，环境 `GRAPH_DIR` 指向用户分析项目的数据目录；这样不依赖 pnpm 的 lifecycle shell。其他工作区脚本同样优先直接运行其已安装的 Node 入口。已有的 Understand Anything Node 脚本也会从兄弟 `code-understanding` 技能定位运行文件。不要把源码压缩包之外的 LLM 分析结果当作已生成：项目分析仍由对应技能执行。

## 失败与更新

检查阶段不会自动安装。准备失败返回非零状态及具体错误；入口可继续直接阅读源码，并明确哪些图谱能力缺失。`.runtime` 是可再生缓存，不提交到 Git。变更后端版本时，同时更新版本锁、源码包/依赖锁及校验和；不能只改版本字符串。后端升级或损坏不能使先前缓存结论自动变成有效证据。

## 验证入口

在技能仓库根目录运行 `node .agents/skills/code-understanding/scripts/test-preflight.mjs`。该测试在临时目录中真正创建 Git clone，使用空 HOME 和含空格路径，检查只读预检、同一提交下的内容变化、独立 worktree、三后端初始化、源码包篡改拒绝，以及 Understand Anything 对示例 Python 文件的定义与调用边提取。测试不会为当前项目建立索引。平台验证范围以实际运行结果为准。

仅验证外部项目绑定时，运行 `node <skill-dir>/scripts/test-external-target.mjs`。该测试使用安装目录之外的两个独立仓库，验证绝对目标、相对目标、缺省 cwd 和不存在目标的失败行为，不安装依赖或建立索引。
