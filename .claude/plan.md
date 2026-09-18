# agent-skill 方向整理计划

## 目标

把散落在仓库各处的 skill（技能）相关内容聚合为独立的一级调研方向 `agent-skill/`。核心主题报告物理迁入；涉及 skill 概念的报告保留原位，在新方向内做交叉引用。

> **调整记录**：Superpowers 保留在 `vibe-coding/open-source-project/superpowers/` 原位，**不迁移**，仅在新方向的交叉引用中索引。

---

## 一、新目录结构

```
agent-skill/                         # Agent Skill 技术方向（新建）
├── paper/                           # 学术论文 / 博客
│   ├── single-agent/               # 单 agent 技能（MOVE ← wikiskill）
│   │   └── wikiskill/              # WikiSkill: 编译经验为持久知识驱动技能进化
│   └── multi-agent/                # 多 agent 技能（MOVE ← skill-mas）
│       └── skill-mas/              # Skill-MAS: Meta-Skill 演化编排能力
├── open-source-project/             # 开源工具/框架（当前为空占位）
└── product/                         # 产品级系统（当前为空占位）
```

> 采用与其它方向一致的三类二级目录：`paper/`、`open-source-project/`、`product/`。单 agent / 多 agent 分组只在 paper/ 下细分（沿袭 harness-optimization 的分类经验）。superpowers 留在 vibe-coding 原位，open-source-project/ 暂为空占位。

---

## 二、物理迁移清单（共 2 个目录）

全用 `git mv` 迁移，保留完整 git history：

| # | 源路径 | 目标路径 | 说明 |
|---|--------|---------|------|
| 1 | `recursive-self-improvement/harness-optimization/paper/single-agent/wikiskill/` | `agent-skill/paper/single-agent/wikiskill/` | 核心：三层架构 + 非对称回滚 |
| 2 | `recursive-self-improvement/harness-optimization/paper/multi-agent/skill-mas/` | `agent-skill/paper/multi-agent/skill-mas/` | 核心：Meta-Skill 编排进化 |

---

## 三、源目录清理方案

迁移后对源目录做清理，避免内容残留：

- **recursive-self-improvement/harness-optimization/paper/single-agent/**: 删除 `wikiskill/` 目录（git rm）
- **recursive-self-improvement/harness-optimization/paper/multi-agent/**: 删除 `skill-mas/` 目录（git rm）
- **vibe-coding/**：**不做任何改动**，superpowers 完整保留（含 `templates/skill-template.md`）

---

## 四、README.md 更新

### 4.1 新增 `agent-skill/` 方向章节

在 README.md 的 `recursive-self-improvement/` 之后、`vibe-coding/` 之前插入新方向索引，列出迁入的 2 篇报告。

### 4.2 源位置占位更新

- **harness-optimization/paper/single-agent/**: 原 wikiskill 条目替换为一行简注「✱ WikiSkill 已迁移至 `agent-skill/paper/single-agent/wikiskill/`」
- **harness-optimization/paper/multi-agent/**: 原 skill-mas 条目替换为一行简注「✱ Skill-MAS 已迁移至 `agent-skill/paper/multi-agent/skill-mas/`」
- **vibe-coding/**: 无改动

### 4.3 交叉引用

在 agent-skill 方向索引末尾，增加「**相关报告（其它方向涉及 skill 概念）**」小节，列出以下报告中与 skill 相关的讨论：

| 方向 | 报告 | 与技能的关系 |
|------|------|-------------|
| vibe-coding / open-source-project | Superpowers | agentic skills 框架 + SKILL.md 模板（保留原位） |
| recursive-self-improvement / harness-optimization | RHO (retro-harness) | Harness 形式化 = 工具 + prompts + 技能 |
| 同上 | LIFE-HARNESS | 四层架构包含「技能层」 |
| 同上 | MemoHarness | Harness 六维空间中 D3 Generation/Skill 维度 |
| 同上 | AHE (Agentic Harness Engineering) | 技能作为可编辑组件槽位 |
| recursive-self-improvement / survey | A Taxonomy of Self-Evolving Agents | L2 2b Tool & Skill Creation 分类锚点 |
| agent-in-organization / product | Grok Bot | Teach a Task → Skill → Routine 产品化链路 |
| agent-in-organization / open-source-project | Multica | Skills 团队经验沉淀 (skills-lock.json) |
| multi-agent-framework / open-source-project | AgentSpace | 远程 daemon 物化技能/知识上下文 |
| context-engineering / paper | Self-GC | skill state 作为可索引上下文对象 |

---

## 五、执行步骤（order of operations）

```
Step 1: [mkdir -p] 新建 agent-skill/paper/single-agent/、paper/multi-agent/、open-source-project/
Step 2: [git mv] 依次迁移 2 个报告目录到目标位置
Step 3: [git rm] 删源目录（含 assets/、references/、report.md）
Step 4: 更新 README.md —— 新增 agent-skill 章节 + 源位置替换为迁移注 + 交叉引用表
Step 5: git commit（分两步：Step 1-3 为第一 commit，Step 4 为第二 commit）
```

---

## 六、不受影响的内容

- **Superpowers** 保留原位，`vibe-coding/` 下 openspec、spec-kit 及其 todo.md 不受影响。
- 所有其它 skill 仅作为组件提及的论文（RHO、MemoHarness 等）**保留原位**，只在交叉引用中关联。
- `recursive-self-improvement/harness-optimization/paper/multi-agent/autogenesis/`、`evo-mas/` 不受影响。
- `recursive-self-improvement/harness-optimization/paper/single-agent/` 下其余 10 篇报告不受影响。
- `agent-in-organization/` 下所有报告不受影响。

---

**所有操作基于 `git mv`，全程保留 git history。执行分两 commit：第一 commit 做物理迁移 + 源目录清理，第二 commit 做 README 索引更新。两 commit 均为独立原子操作，可按需分批 review。**