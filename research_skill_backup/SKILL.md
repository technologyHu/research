---
name: research
user-invocable: true
allowed-tools: Read, Write, Glob, Grep, Bash, Agent, WebSearch, WebFetch, Task, AskUserQuestion
description: 对目标话题进行初步调研，生成调研outline或调研报告。支持三种模式：开源项目技术调研、多对象对比调研、单篇论文调研。当用户提到"开源项目调研"、"技术调研"、"项目分析"时使用开源项目模板；当用户提到"论文调研"、"分析论文"、"paper research"或提供论文标题/DOI/arXiv链接时，使用论文调研模板。也触发于：用户提供PDF文件路径要求分析论文、提到"调研一下"、"研究一下"某项技术时。
---

# Research Skill - 初步调研

## 触发方式
`/research <topic>`

## 调研模式识别

### 模式A: 开源项目技术调研
**识别条件**（满足任一即可）：
- 话题包含"开源项目"关键词
- 话题是具体的开源项目名称（如 React、TensorFlow、Kubernetes）
- 用户明确要求"技术调研"或"项目分析"
- 话题包含 GitHub 仓库地址

**特点**：单个项目的深度技术分析

### 模式B: 多对象对比调研
**识别条件**：
- 话题涉及多个对象的对比或列表
- 话题包含"对比"、"调研"、"分析"等词且对象是多个产品/项目

**特点**：多个对象的横向对比调研

### 模式C: 单篇论文调研
**识别条件**（满足任一即可）：
- 话题包含"论文调研"、"分析论文"、"paper research"
- 话题包含 arXiv 链接（如 arxiv.org/abs/XXXX.XXXXX）
- 话题包含 DOI
- 话题明显是一篇学术论文的标题
- 用户提供了论文 PDF 文件路径并要求分析

**特点**：单篇论文的深度分析与调研，支持论文分析和论文-代码对照两种子模式

---

## 模式A: 开源项目技术调研

### Step 1: 读取模板
读取 `~/.claude/skills/research/references/open-source-project-template.md` 获取完整的技术调研模板。

### Step 2: 项目信息收集
使用 WebSearch 收集项目基本信息：
- 项目名称、GitHub 地址
- Star 数、Contributor 数
- 最新版本、发布时间
- 项目简介

### Step 3: 确认调研范围
使用 AskUserQuestion 询问用户：
1. **项目类型**：库/SDK、框架、中间件、应用系统、工具类、算法库
2. **调研深度**：简要（核心章节）、标准（主要章节）、详细（全部章节）
3. **重点关注**：架构设计、核心实现、性能分析、使用方式等
4. **输出目录**：默认 `./{project_name}_research/`

根据用户选择，从模板中选择对应章节。

### Step 4: 生成调研目录结构
创建调研输出目录，包含以下结构：
```
{output_dir}/
├── report.md           # 调研报告（主输出文件）
├── outline.yaml        # 调研大纲（章节配置）
├── fields.yaml         # 字段定义（按模板章节）
├── templates/          # 模板文件（如有）
│   └── ...             # 项目相关的模板文件
├── assets/             # 图表等资源文件
│   └── diagrams/       # 架构图、流程图等
└── results/            # 调研结果（JSON）
```

**重要：templates 目录不能留空。** 调研过程中如果发现了项目的模版文件（设计文档模版、架构设计模版、spec 文件模版、PR 模版、Issue 模版等），必须将模版内容提取并写入 `templates/` 目录下的对应 `.md` 文件中。每个模版文件顶部应标注来源（如 `> Based on skills/brainstorming/SKILL.md from {repo}`）。如果项目确实没有模版文件，则在 `report.md` 中说明即可，无需创建 `templates/` 目录。

**重要：assets 目录管理。** 只在报告中实际使用了 Mermaid 图表或需要存放图片时才创建 `assets/` 目录。如果整个调研过程没有产出任何图表资源，不要创建 `assets/` 目录；如果已创建但确认为空，在调研完成时自动删除。

### Step 5: 图表规范说明

调研报告中推荐使用 **Mermaid** 图表，遵循以下规范：

#### 推荐使用的图表类型

| 图表类型 | Mermaid 语法 | 适用场景 | 兼容性 |
|---------|-------------|---------|--------|
| **架构图** | `graph TB` | 整体架构、模块关系、组件交互 | ⭐⭐⭐⭐⭐ |
| **流程图** | `flowchart TB/LR` | 工作流、命令流程、数据处理流程 | ⭐⭐⭐⭐⭐ |
| **时序图** | `sequenceDiagram` | 关键用例运行视图、组件交互时序 | ⭐⭐⭐⭐⭐ |
| **类图** | `classDiagram` | 数据模型、类结构 | ⭐⭐⭐⭐ |
| **ER图** | `erDiagram` | 实体关系、数据库模型 | ⭐⭐⭐⭐ |

#### 避免使用的图表类型

| 图表类型 | 问题 | 替代方案 |
|---------|------|---------|
| `stateDiagram-v2` | note 语法有兼容性问题 | 使用 `flowchart TB` |
| `quadrantChart` | 不是所有渲染器支持 | 使用表格 + flowchart |

#### 必要图表清单

根据项目类型，报告应包含以下图表：

| 项目类型 | 必要图表 | 可选图表 |
|---------|---------|---------|
| **框架/工具** | 整体架构图、CLI命令流程图、核心用例时序图 | 模块依赖图、状态流转图 |
| **库/SDK** | 整体架构图、API调用时序图 | 数据流图、模块依赖图 |
| **应用系统** | 整体架构图、部署架构图、核心用例时序图 | 数据流图、ER图 |
| **中间件** | 分层架构图、数据流图、部署架构图 | 性能流程图 |

#### 图表标题规范
图表标题直接使用描述性名称，**不要加"Mermaid:"前缀**。例如用"双循环架构总览"而非"Mermaid: 双循环架构总览"。

### Step 6: 输出并确认
展示给用户：
- 选定的章节列表
- 输出目录结构
- 下一步操作建议

**后续命令**：
- `/research-deep` - 开始深度调研

---

## 模式B: 多对象对比调研

### Step 1: 模型内部知识生成初步框架
基于topic，利用模型已有知识生成：
- 该领域的主要研究对象/items列表
- 建议的调研字段框架

输出{step1_output}，使用AskUserQuestion确认：
- items列表是否需要增减？
- 字段框架是否满足需求？

### Step 2: Web Search补充
使用AskUserQuestion询问时间范围（如：最近6个月、2024年至今、不限）。

**参数获取**：
- `{topic}`: 用户输入的调研话题
- `{YYYY-MM-DD}`: 当前日期
- `{step1_output}`: Step 1生成的完整输出内容
- `{time_range}`: 用户指定的时间范围

**硬约束**：以下prompt必须严格复述，仅替换{xxx}中的变量，禁止改写结构或措辞。

启动1个web-search-agent（后台），**Prompt模板**：
```python
prompt = f"""## 任务
调研话题: {topic}
当前日期: {YYYY-MM-DD}

基于以下初步框架，补充最新items和推荐调研字段。

## 已有框架
{step1_output}

## 目标
1. 验证已有items是否遗漏重要对象
2. 根据遗漏对象进行补充items
3. 继续搜索{topic}相关且{time_range}内的items并补充
4. 补充新fields

## 输出要求
直接返回结构化结果（不写文件）：

### 补充Items
- item_name: 简要说明（为什么应该加入）
...

### 推荐补充字段
- field_name: 字段描述（为什么需要这个维度）
...

### 信息来源
- [来源1](url1)
- [来源2](url2)
"""
```

### Step 3: 询问用户已有字段
使用AskUserQuestion询问用户是否有已定义的字段文件，如有则读取并合并。

### Step 4: 生成Outline（分离文件）
合并{step1_output}、{step2_output}和用户已有字段，生成两个文件：

**outline.yaml**（items + 配置）：
- topic: 调研主题
- items: 调研对象列表
- execution:
  - batch_size: 并行agent数量（需AskUserQuestion确认）
  - items_per_agent: 每个agent调研项目数（需AskUserQuestion确认）
  - output_dir: 结果输出目录（默认./results）

**fields.yaml**（字段定义）：
- 字段分类和定义
- 每个字段的name、description、detail_level
- detail_level分层：极简 → 简要 → 详细
- uncertain: 不确定字段列表（保留字段，deep阶段自动填充）

### Step 5: 输出并确认
- 创建目录: `./{topic_slug}/`
- 保存: `outline.yaml` 和 `fields.yaml`
- 展示给用户确认

---

## 模式C: 单篇论文调研

### Step 1: 论文信息收集

信息收集有三个来源，按优先级依次执行：

**1. 本地 PDF 原文（最优先）**
如果用户提供了论文 PDF 文件路径，必须先提取全文内容：
- 检查可用 PDF 库（PyMuPDF/fitz > pdfplumber > PyPDF2），使用项目虚拟环境运行
- 提取策略：先提取全部页面文本（`PYTHONIOENCODING=utf-8` 避免编码问题），分页保存供后续引用
- 如果 PDF 超过 20MB 无法直接用 Read 工具读取，必须通过 Python 代码提取
- 提取后根据文本内容获取：标题、作者、摘要、章节结构、实验数据、参考文献

**2. WebSearch 在线补充**
- 如果用户提供 arXiv 链接，搜索 `arxiv 论文ID` 获取元数据
- 如果用户提供论文标题，搜索 `论文标题 arxiv` 或 `论文标题 paper`
- 如果用户提供 DOI，搜索 `doi:XXXXX`
- 补充信息：引用数、代码仓库、社区讨论

**3. 辅助参考资料（如有）**
用户可能提供辅助分析资料（微信公众号文章、博客解读、技术评论等）：
- 对于微信公众号文章：使用 `web-article-fetcher` 技能获取内容
- 对于普通网页：使用 WebFetch 获取
- 对于本地文件：直接 Read
- 辅助资料的价值在于提供论文之外的视角和解读，但注意与论文原文交叉验证

### Step 2: 确认调研子模式
使用 AskUserQuestion 询问用户选择调研子模式：

1. **C1: 论文调研** — 单篇论文的深度分析
   - 读取模板：`~/.claude/skills/research/references/paper-research-template.md`
   - 适用于：理解论文方法、分析实验、评估贡献
   - 输出：按模板结构撰写的论文调研报告

2. **C2: 论文代码分析** — 论文与代码的对照分析
   - 读取模板：`~/.claude/skills/research/references/paper-code-analysis-template.md`
   - 适用于：复现论文实验、验证论文-代码一致性、评估可复现性
   - 前提：论文必须有开源代码仓库
   - 如果选择了 C2 但未找到代码仓库，提醒用户并提供 C1 选项

3. **C3: 论文+代码综合调研** — 同时覆盖论文内容和代码实现
   - 同时读取两个模板，合并撰写一份综合报告
   - 适用于：用户既想理解论文方法，又想评估代码实现
   - 当用户说"论文和代码都要调研"时选择此模式

同时确认输出目录（默认 `./{paper_slug}_research/`）。

### Step 3: 读取对应模板
根据用户选择的子模式，读取对应模板文件：
- C1 → `~/.claude/skills/research/references/paper-research-template.md`
- C2 → `~/.claude/skills/research/references/paper-code-analysis-template.md`
- C3 → 两个模板都读取

### Step 4: 代码仓库分析（C2/C3 模式）

如果论文有开源代码仓库：
1. 浅克隆仓库（`git clone --depth 1`）到临时目录
2. 分析目录结构，识别核心模块
3. 阅读关键源文件，建立论文概念→代码实现的映射
4. 评估代码质量、论文-代码一致性、可复现性
5. 调研完成后清理临时克隆

### Step 5: 论文图片提取

从论文中提取关键图表到 `assets/` 目录。这是论文调研的重要环节，图表能让报告更直观。

**优先使用 arXiv 源文件提取（推荐）**：

如果论文来自 arXiv，应优先从源文件提取原始图片，而非从 PDF 截图。这种方法获取的是作者原始矢量图，清晰度和准确性远超截图。

**arXiv 源文件提取流程**：

1. **下载源文件**：
```bash
curl -L -o source.tar.gz "https://arxiv.org/e-print/{paper_id}"
# paper_id 从 arXiv URL 提取，如 https://arxiv.org/abs/2604.15034 → paper_id = 2604.15034
```

2. **解压源文件**：
```bash
mkdir -p source && tar -xzf source.tar.gz -C source
```

3. **查找原始图片**：
- 图片通常在 `source/figures/` 目录下
- 常见格式：PDF、PNG、SVG、EPS
- 文件名通常对应论文章节或图表编号

4. **转换为 PNG**（使用 PyMuPDF）：
```python
import fitz
import os

source_dir = 'source/figures'
output_dir = 'assets'

# 遍历figures目录下的PDF文件
for pdf_file in os.listdir(source_dir):
    if pdf_file.endswith('.pdf'):
        doc = fitz.open(os.path.join(source_dir, pdf_file))
        page = doc[0]  # 通常单页
        mat = fitz.Matrix(3, 3)  # 3x缩放
        pix = page.get_pixmap(matrix=mat)
        # 根据文件名映射到输出文件名
        pix.save(os.path.join(output_dir, f'{output_name}.png'))
        doc.close()
```

5. **清理临时文件**：
```bash
rm -rf source source.tar.gz
```

**常见文件名映射**：
| 源文件 | 输出文件 |
|-------|---------|
| architecture.pdf | fig1_architecture.png |
| overview.pdf | fig1_overview.png |
| comparison*.pdf | fig2_comparison.png |
| benchmark*.pdf | fig3_benchmark.png |

---

**备选方法：从 PDF 截图**：

如果无法获取 arXiv 源文件（如论文发表在期刊、会议），则从 PDF 截图：

1. 用 PyMuPDF 以 3x 缩放渲染包含图表的页面为高分辨率图片
2. 通过分析页面文本元素定位图表的精确边界坐标
3. 从渲染页面中裁剪出图表区域

**精确定位方法** — 用 PyMuPDF 的 `get_text('dict')` 分析页面元素：
```python
import fitz
doc = fitz.open('paper.pdf')
page = doc[page_index]
blocks = page.get_text('dict')['blocks']
for b in blocks:
    if b['type'] == 0:  # text block
        for line in b['lines']:
            text = ' '.join([span['text'] for span in line['spans']])
            y_top = line['bbox'][1]
            # 搜索 Figure 标题、坐标轴标签等定位元素
```

**裁剪原则**：
- 图表标题（如 "(a) Total nodes"）和 y 轴标签必须在裁剪范围内
- 图例（legend）必须完整包含，不能截断
- 图注（Figure N. ...）包含到裁剪范围，用于后续在报告中引用
- 底部坐标轴标签必须完整
- 不要包含图表范围外的正文文字
- 裁剪完成后用 Read 工具验证图片内容正确

**命名规范**：`fig{N}_{描述}.png`，N 与论文中 Figure 编号严格对应，不能跳号

**提取后立即验证**：每提取一张图片，用 Read 工具查看确认内容正确。常见问题：
- 截到文字区域而非图表
- 图例被截断
- 图表不完整
发现问题时重新调整坐标裁剪。

### Step 6: 生成调研目录与报告
创建输出目录：
```
{output_dir}/
├── report.md    # 调研报告（主输出文件，按模板结构直接撰写）
├── assets/      # 从论文提取的图表 + Mermaid图
└── references/  # 辅助资料（可选，如有微信文章等）
```

与模式A/B不同，模式C不需要 outline.yaml 和 fields.yaml，直接按照模板结构撰写完整的调研报告到 report.md。

**撰写报告的关键要求**：

1. **整体架构章节必须图文并茂**：每个架构/流程图都必须配合文字说明。仅放图是不够的——要解释图的每个组成部分、数据流向、交互关系，让不看图也能理解架构。图的标题用斜体描述图的内容要点。

2. **实验分析必须有总体总结**：在逐个实验结果之后，增加"实验结果总体分析"章节，从全局视角综合解读所有实验，说明各实验之间的逻辑关系，归纳核心结论和边界条件。

3. **图片引用**：从 PDF 提取的图片用相对路径引用（`assets/fig{N}_xxx.png`），图片下方用斜体说明图的内容要点。图片编号必须与论文一致且连续，不能跳过任何 Figure。

4. **Mermaid 流程图**：用 Mermaid 补充论文中没有但报告中需要的流程图（如代码架构图、运行时序图、与现有方法对比等）。图表标题直接用描述性名称，不加"Mermaid:"前缀。

5. **内容填充**：
   - 基于 PDF 全文提取的内容填充论文细节，而非仅依赖 WebSearch
   - 实验数据尽量从论文原文中提取，无法获取的标注"待补充"
   - 辅助参考资料（微信文章等）的观点标注来源，与论文原文交叉验证
   - 相关工作部分列出论文中提到的关键参考文献

### Step 7: 输出并确认
展示给用户：
- 调研报告的章节概要
- 提取的论文图片清单
- 添加的 Mermaid 流程图清单
- 输出目录位置
- 下一步操作建议

---

## 通用图表规范

### 图片提取与裁剪
- 从 PDF 提取图片时使用 3x 缩放渲染，保证清晰度
- 裁剪必须包含完整图表（标题、图例、坐标轴标签）
- 裁剪后立即用 Read 工具验证内容正确
- 命名与论文编号严格对应，不能跳号
- 清理原始渲染文件，只保留最终裁剪结果

### Mermaid 流程图
- 标题直接用描述性名称，不加"Mermaid:"前缀
- 推荐类型：flowchart、sequenceDiagram、classDiagram、erDiagram
- 避免使用：stateDiagram-v2（兼容性问题）、quadrantChart

---

## 输出路径

### 开源项目调研输出
```
{当前工作目录}/{project_name}_research/
├── report.md           # 调研报告（主文件）
├── outline.yaml        # 调研大纲
├── fields.yaml         # 字段定义
├── templates/          # 项目模版文件（如有）
└── results/            # 调研结果JSON
```

### 多对象对比调研输出
```
{当前工作目录}/{topic_slug}/
├── outline.yaml        # items列表 + execution配置
└── fields.yaml         # 字段定义
```

### 单篇论文调研输出
```
{当前工作目录}/{paper_slug}_research/
├── report.md           # 调研报告（按模板结构撰写）
├── assets/             # 论文图片 + 流程图
└── references/         # 辅助资料（可选）
```

---

## 完成确认

调研文件全部写入后，必须主动向用户确认是否满意。展示：
- 输出目录位置
- 报告包含的核心章节概要
- 提取的图片和流程图清单（论文调研时）
- templates 目录下写入了哪些模版文件（如有）
- 询问用户是否需要补充、修改或调整

**不要静默结束。** 即使用户之前已确认过范围，最终产出物仍需用户审阅。

## 后续命令
- `/research-add-items` - 补充items
- `/research-add-fields` - 补充字段
- `/research-deep` - 开始深度调研
