# 调研总览首次完整发布验收

- 验收日期：2026-11-06（Asia/Shanghai）。
- 发布分支：`openjiuwen-harness`。
- [线上交互页面](https://technologyhu.github.io/research/)。
- [完整验收成功的发布流水线](https://github.com/technologyHu/research/actions/runs/42186435418)。
- 源提交：`36d5209d6ee12d358ebdabf4b6afe19adc629dac`。
- 本轮发布制品对应提交：`36d5209d6ee12d358ebdabf4b6afe19adc629dac`。
- 首次 Linux 预览自动回写提交：`6b2db8b84242e27bfb923833827b50f1c675f440`。
- 数据指纹：`50b76c64bfbe03a4`。
- [线上发布版本与资源清单](https://technologyhu.github.io/research/publication.json)。

| 验证内容 | 结果与依据 |
| --- | --- |
| 数据、提取及失败恢复测试 | 43 项通过 |
| 发布前浏览器检查 | 本地文件、HTTP、桌面／移动端布局及隔离数据下的搜索、筛选、详情、拖动缩放和动画暂停检查通过 |
| Git 自动回写 | 首次 CI 使用 Linux 字体重建预览，生成产物提交并推送成功；本轮内容未变，无需额外回写 |
| GitHub Pages 部署 | 同一流水线内部署步骤成功 |
| 真实页面版本 | CI 线上验收核对源提交、产物提交、仓库、分支及数据指纹通过；另有本地独立线上验收 |
| 真实静态资源 | `index.html`、`app.js`、`style.css`、`graph.json`、`graph-data.js`、`preview.gif`、`preview.png` 共 7 项 SHA-256 与发布清单一致 |
| 真实页面浏览器检查 | 桌面页面检查与移动端布局、数据指纹检查通过；未发现横向溢出 |
| CI 发布后验收 | 通过；整条流水线为 success，结果 JSON 和桌面／移动端截图已保存为 research-graph-publication-checks 制品 |
| 数据范围 | 0 个主题、0 种类型、0 项调研工作、0 份报告，页面显示真实空状态；测试夹具未进入发布数据 |

本记录针对上述源提交及发布制品，不表示所有历史或未来版本均已验证。日常更新由工作流重复执行发布前后检查，线上版本清单也随新部署更新。CI 验收结果和截图位于工作流制品，本地副本位于 `.tmp/research-graph/ci-publication/`；独立验收结果与截图位于 `.tmp/research-graph/publication/`。
