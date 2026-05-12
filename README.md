# Research

个人研究调研仓库，用于记录和整理各类技术调研报告。

## 目录结构

```
agent/
└── auto_harness/
    └── langchain_better_harness.md  # LangChain Better Harness 调研报告
```

## 调研报告

### LangChain Better Harness

**文件**: [agent/auto_harness/langchain_better_harness.md](agent/auto_harness/langchain_better_harness.md)

**简介**: 调研LangChain发布的Better Harness工作，这是一套eval驱动的agent harness自动优化系统。核心思想是让一个"外部Deep Agent"通过阅读评估反馈来自动改进另一个"目标Agent"的harness配置。

**主要内容**:
- Better Harness核心概念和定义
- Harness Hill Climbing方法论
- Harness Engineering for Deep Agents实践
- 技术实现和代码示例
- 最佳实践指南
