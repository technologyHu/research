# 来源与验证记录

## 用户提供的资料

采用 OpenJiuwen 的 `features/agent_os/refs/muse-gadget-sdk/report.md`《Muse Gadget SDK 调研》，标注日期 2026-11-18，源码基线为 `6a44074`。本轮保留七个主题及两个 Linux 示例代码块，复用原始 PNG 和 SVG 场景图。参考 Markdown 的 SHA-256 为 `9c545c5febd6fc0e9554267b7402e0aab9b81043e4f6b0afa43e0a4ad609293e`。

| 参考内容 | 本报告对应位置 |
| --- | --- |
| 1. 背景与价值，含运行位置和职责 | 第 1 节 |
| 2. 三类交互、场景图、Home Link、Pebble 两条路径 | 第 2 节 |
| 3. 能力与适用条件 | 第 3 节 |
| 4. 首次配对、凭证、Noise 连接、注册、调用、对话及上报 | 第 4 节，附配对时序、Link 调用时序和消息确认流程，并补充 VM 文件和媒体链路 |
| 5. 源码阅读顺序、Linux 自定义只读命令、ESP32 两种扩展层级 | 第 5 节 |
| 6. 权限、可靠性、资源、许可及 Agent OS 设计启示 | 第 6 节 |
| 7. 参考报告验证与限制 | 第 7 节，按链路列出参考报告、初版复跑和本次补跑结果 |

## 一手资料

公开页面核对日期为 2026-11-18。设备端代码采用本地干净 checkout，其 Git 远端和官方产品页均对应 `facebookincubator/muse-gadget-sdk`。提交时间为北京时间 2026-11-18 10:39:29，提交说明为 `Add Sony Bravia TVs skill (#434)`。Linux 包定义的版本号是 `0.1.0`，报告以完整 Git 提交定位 ESP32 和 Linux 的共同源码快照。 [固定提交](https://github.com/facebookincubator/muse-gadget-sdk/commit/6a44074014daad1a623f54e62a169f514741836b) · [Linux 包定义](https://github.com/facebookincubator/muse-gadget-sdk/blob/6a44074014daad1a623f54e62a169f514741836b/linux/pyproject.toml)

| 来源 | 核对范围 |
| --- | --- |
| [Meta 发布公告](https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent/) · [Muse 安全架构](https://muse.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse) · [模型更新](https://research.meta.ai/blog/specialized-models-for-muse-and-metaai) | 产品发布日期，专属 VM、Hatch 隔离、凭证、推理代理和 Sentinel 的职责 |
| [Muse Gadgets](https://gadgets.muse.ai/) · [Home Link](https://gadgets.muse.ai/home-link) · [SDK Token 条款](https://gadgets.muse.ai/sdk-terms) · [Web Flasher](https://facebookincubator.github.io/muse-gadget-sdk/) | 官方接入方式、网关产品范围、固件及令牌条件 |
| [Linux SDK](https://github.com/facebookincubator/muse-gadget-sdk/blob/6a44074014daad1a623f54e62a169f514741836b/linux/README.md) · [ESP32 SDK](https://github.com/facebookincubator/muse-gadget-sdk/blob/6a44074014daad1a623f54e62a169f514741836b/esp32/README.md) · [设备协议](https://github.com/facebookincubator/muse-gadget-sdk/blob/6a44074014daad1a623f54e62a169f514741836b/protocols/DEVICE.md) | 部署、设备描述、扩展约定与公开接口。关键分支的固定源码位置见正文 |
| [Pebble Index 01](https://developer.repebble.com/index-01/) · [Webhook](https://developer.repebble.com/index-01/webhooks/) · [Core Devices Muse 插件](https://github.com/coredevices/pebble-apps/blob/5bc9f0394921692a5d69b2bb4d0ae4d9b7a0ffed/muse/README.md#library-and-host-integration) | 手机与戒指的分工、转写事件格式、插件使用的 Web 会话和版本限制 |

## 内联图

第 4 节三张图以固定提交 `6a44074` 的设备端实现为依据，直接写在 Markdown 的 Mermaid 代码块中。在 Mermaid 11.12.0 与 Chromium 环境检查了图的语法、渲染和标签边界。阅读器若显示为纯文本，可按同节的文字步骤阅读。 [GitHub Markdown 的 Mermaid 支持](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams#creating-mermaid-diagrams)

## 主机验证命令

在 Windows PowerShell、Python 3.13.12、pytest 9.1.1 下，从固定提交 `6a44074` 的 Muse Gadget SDK 仓库根执行。初版 Linux 子集的 HTTP 和 BLE 使用替身。ESP32 四组测试只读取源码。

```powershell
$env:PYTHONPATH = (Resolve-Path -LiteralPath 'linux/src').Path
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
python -B -X utf8 -m pytest -q -p no:cacheprovider linux/tests/test_pairing.py linux/tests/test_ble_framing.py linux/tests/test_ble_setup.py linux/tests/test_muse_api.py

python -B -X utf8 -m unittest discover -s esp32/tests -p test_link_transport_contract.py
python -B -X utf8 -m unittest discover -s esp32/tests -p test_link_encrypted_pairing_contract.py
python -B -X utf8 -m unittest discover -s esp32/tests -p test_link_pairing_state_contract.py
python -B -X utf8 -m unittest discover -s esp32/tests -p test_muse_app_boot_order.py
```

初版 Linux 子集 103 项通过。ESP32 四组分别通过 7、17、11、2 项。参考报告的 229 项 Linux 测试属于另一次筛选执行，精确选用列表未随参考资料提供。

2026-11-18 的局部修订沿用上述环境，补跑两项 Linux Link 测试。两项均通过。测试用内存 WebSocket 建立模拟 VM 会话，覆盖调用结果与请求 ID 的匹配、解绑事件，以及新旧会话共享的执行槽。

```powershell
$env:PYTHONPATH = (Resolve-Path -LiteralPath 'linux/src').Path
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
python -B -X utf8 -m pytest -q -p no:cacheprovider linux/tests/test_link_client.py::test_register_invoke_result_and_unpair linux/tests/test_link_client.py::test_reconnect_waits_for_disconnected_commands_to_finish
```
