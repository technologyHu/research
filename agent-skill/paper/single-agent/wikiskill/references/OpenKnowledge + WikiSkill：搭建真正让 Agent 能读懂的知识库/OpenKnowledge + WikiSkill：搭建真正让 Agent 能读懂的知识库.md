# OpenKnowledge + WikiSkill：搭建真正让 Agent 能读懂的知识库

Source: https://mp.weixin.qq.com/s/_S2U3tQDKcZNtDJQ8Mi7xA

Mycelium
Mycelium

XStack18

![]()

在小说阅读器读本章

去阅读

![]()

在公众号小说中沉浸阅读

🍄 原文发布于 blog.mushroom.cv

上一篇文章我们深入拆解了谷歌 Research 的 **WikiSkill** 论文——一种让 Agent 把执行经验沉淀为持久知识的三层架构（Raw Layer / Wiki Layer / Skills Layer）。结论是：这套机制在工程上完全可以自己实现，但有一个现实问题——**你把知识写到哪里？谁来读？Agent 和人类怎么协作编辑？**

今天这篇，答案来了。

**inkeep/open-knowledge** 是一个开源的 AI-native Markdown IDE，3800+ stars，TypeScript 实现，GPL-3.0 协议。它定位自己为"Notion meets VS Code"——真正所见即所得的 Markdown 编辑器，同时内置对 Claude、Codex、OpenCode 等 Agent 的深度集成。

这两个项目放在一起，几乎是天作之合。

---

## OpenKnowledge 是什么

用一句话说：**一个让人和 Agent 都能顺畅读写的 Markdown 知识库 IDE。**

核心能力：

* \*\*真 WYSIWYG\*\*：编辑 Markdown 文件的手感接近 Google Doc / Notion，不需要在源码和预览之间反复切换
* \*\*跨平台桌面 + Web\*\*：macOS / Windows / Linux 桌面 App，也有 CLI 启动的 Web UI，Intel Mac 和服务器也能跑
* \*\*内置 MCP + Skills\*\*：开箱即用，安装时自动检测你电脑上的 Claude Code / Codex / Cursor / OpenCode，写好 MCP 配置和 Skills，让 Agent 能直接做富文档搜索和创作
* \*\*Git 同步\*\*：团队共享和版本控制底层是 git/GitHub，不是私有数据孤岛
* \*\*Embeddable HTML\*\*：工程 spec 和可视化报告里能嵌入富组件，不只是纯文本

topics 里有一个关键词：**`llm-wiki-karpathy`**——这个命名指向 Karpathy 提出的"LLM OS"概念里知识库应该是什么形状的讨论。OpenKnowledge 明确把自己定位为 LLM Wiki 的标准工具。

---

## 和 WikiSkill 的对接点在哪里

WikiSkill 定义了知识应该怎么组织：

|  |
| --- |
| workspace/ |
| ├── raw/ # 不可变执行轨迹 |
| ├── wiki/ |
| │ ├── patterns/ # 单个 Markdown 模式文件 |
| │ ├── logs.md # 时序演化日志 |
| │ ├── skill-impact.md # Accept/Reject 历史 + diff |
| │ └── index.md # 模式目录索引 |
| └── skills/ |
| └── <skill-name>/ |
| ├── SKILL.md |
| └── PURPOSE.md |

OpenKnowledge 能直接打开这个目录结构，提供：

1. \*\*人类可读的 WYSIWYG 视图\*\*：`wiki/patterns/\*.md` 每个模式文件在 OpenKnowledge 里渲染成漂亮的文档，不是裸 Markdown 源码
2. \*\*图谱视图\*\*：OpenKnowledge 内置 wiki link 图谱，`[[pattern-name]]` 跨文件链接自动可视化
3. \*\*Agent 写、人类审\*\*：WikiSkill 的 Wiki Maintainer Agent 往 `patterns/` 写文件，人类在 OpenKnowledge 里 review，侧边 AI 面板可以继续追问
4. \*\*Skills 管理\*\*：OpenKnowledge 的 Skills 系统可以把 `SKILL.md` 的内容直接挂载为 Agent 可调用的 skill，形成闭环

简单说：**WikiSkill 是知识演化的引擎，OpenKnowledge 是这个引擎的驾驶舱。**

---

## 快速上手：5 分钟搭一个 Agent Wiki

### 方式一：桌面 App（推荐）

从 openknowledge.ai/download 下载：

* \*\*macOS Apple Silicon\*\*：DMG 拖入 Applications
* \*\*Windows 10+\*\*：Setup installer，无需管理员权限
* \*\*Linux\*\*：.deb（Debian/Ubuntu）或 .rpm（Fedora/RHEL）

安装后直接 "Open Folder"，选一个包含 Markdown 文件的目录即可。

### 方式二：CLI + Web（Intel Mac / 服务器）

需要 Node.js 24+：

|  |
| --- |
| npm install -g @inkeep/open-knowledge |
| cd your-wiki-directory |
| ok init # 检测本地 Agent 环境，自动配好 MCP 和 skills |
| ok start --open # 启动 Web 编辑器并打开浏览器 |

`ok init` 会扫描你电脑上的 Claude Code、Codex、Cursor 等，自动生成对应的配置。这一步省去了手动配 MCP 的麻烦。

### 配合 WikiSkill 工作流

按上一篇文章搭好 WikiSkill 的 `workspace/` 目录后：

|  |
| --- |
| cd workspace |
| ok init |
| ok start --open |

OpenKnowledge 会立刻识别 `wiki/patterns/` 里的所有 Markdown 文件，`skill-impact.md` 和 `logs.md` 也会正确渲染成时序文档。侧边 AI 面板直接让 Claude 或 Codex 查询 wiki 知识、提建议，或者让 WikiSkill 的 Skill Proposer 把新 proposal 写进 `skills/` 目录。

---

## 几个值得关注的细节

**关于 MCP 集成**：`ok init` 写入的 MCP 配置不只是简单的文件读写，还包含"富搜索"——Agent 能根据语义查询相关 pattern，而不只是关键词匹配。这对 WikiSkill 的推理阶段有直接价值。

**关于 Skills**：OpenKnowledge 的 Skills 机制和 WikiSkill 的 Skills Layer 命名相同，但层次不同——前者是 IDE 插件级别，后者是 Agent 记忆演化级别。两者可以叠加：用 WikiSkill 生成的 `SKILL.md` 文件，可以直接被 OpenKnowledge 挂载为可调用 skill。

**关于隐私**：所有数据本地存储，不上传任何云服务。git 同步是可选的，并且是你自己的 git 仓库。在企业知识库场景下这一点很重要。

**关于活跃度**：仓库创建于 2026-06-03，最后 push 在今天（2026-09-01），3838 stars，很活跃。不是停更的概念项目。

---

## 实际使用建议

如果你在用 WikiSkill 模式管理 Agent 知识：

1. 把 `workspace/wiki/` 用 OpenKnowledge 打开，配好 Claude Code 的 MCP，当你的主要查阅和编辑界面
2. WikiSkill 的自动化脚本（Wiki Maintainer、Skill Proposer）继续在后台跑，写入文件
3. 每隔几天在 OpenKnowledge 里 review `skill-impact.md`，看哪些 skill 被接受、哪些被 rollback，手动干预异常情况
4. 用 OpenKnowledge 的图谱视图检查 pattern 之间的 wiki link 是否合理，发现孤立节点及时补充连接

这套组合相当于：**Agent 持续学习，人类随时介入，知识以 Markdown 形式沉淀，git 保证可审计。**

---

## 相关链接

* GitHub：[inkeep/open-knowledge](https://github.com/inkeep/open-knowledge)
* 官网：[openknowledge.ai](https://openknowledge.ai)
* 文档：[openknowledge.ai/docs](https://openknowledge.ai/docs)
* 上一篇：WikiSkill——把 Agent 经验沉淀为持久知识
* Discord：[discord.gg/VRKk2EaGHN](https://discord.gg/VRKk2EaGHN)

关于本号 · 免责声明

🍄 Mushroom Research Blog 是非营利、免费公开的个人科技观察博客与公众号 XStack18，不接受商业合作、不代表任何企业或机构立场，也不谋求商业利益。我们以个人视角客观中立地记录和分析 AI、Web3 等领域的最新模型发布与技术动态，希望帮更多人获得有价值的一手科技认知，而非碎片化的信息噪音。

本文为作者基于公开信息的个人研究与观点整理，不代表文中提及公司/产品/模型的官方立场；文中引用的第三方商标、图片、数据等版权归原权利人所有，如有疏漏或侵权，请联系 hello@mushroom.cv，我们会尽快核实处理。内容仅为技术科普，不构成投资、法律等专业建议。

🍄

Mycelium Protocol

数字公共物品 · 开源免费无许可

🎵 表达者
|
🎨 创造者
|
🔨 建设者

🪵 Infras
|
🦠 Protocols
|
🕸️ Networks

📍 blog.mushroom.cv · Apache 2.0

预览时标签不可点

![]()

微信扫一扫  
关注该公众号

知道了



![]()
微信扫一扫  
使用小程序

取消
允许

取消
允许

取消
允许

×
分析

![跳转二维码]()


微信扫一扫可打开此内容，  
使用完整服务

：
，
，
，
，
，
，
，
，
，
，
，
，
。
 
视频
小程序
赞
，轻点两下取消赞
在看
，轻点两下取消在看
分享
留言
收藏
听过