# 可迁移的 GitNexus 技能运行环境

三个 GitNexus 技能共用这里的入口。路径由脚本位置计算，不依赖维护者的磁盘、用户目录、全局 GitNexus 或全局 MCP 配置。

在仓库根目录运行：

```sh
node .agents/skills/gitnexus-cli/scripts/gitnexus.mjs doctor
```

首次调用会用 `npm ci` 安装锁定的依赖，校验并解压仓库自带的 FTS / VECTOR 扩展，然后实际创建索引并执行全文查询和最近邻查询。后续调用复用本机缓存；损坏的扩展会从仓库副本恢复。初始化日志写入 stderr，MCP 的 stdout 保留给协议。

前提是安装 Git、带 npm 的 Node.js 22.18+（22.x）或 24.11+，首次使用可访问配置的 npm registry。扩展文件本身无需联网下载，也不需要 GitHub Token、API Key、管理员权限或固定代理。可使用自己的 npm mirror / proxy 配置；仓库不保存任何个人代理地址。

## 分析与检索

```sh
# 首次分析：FTS 默认建立；--embeddings 另外生成代码向量
node .agents/skills/gitnexus-cli/scripts/gitnexus.mjs analyze /path/to/project --embeddings --skip-agents-md --skip-skills

# 为已有索引补充向量，不必重建结构图
node .agents/skills/gitnexus-cli/scripts/gitnexus.mjs embeddings --help

node .agents/skills/gitnexus-cli/scripts/gitnexus.mjs query "authentication token validation"
node .agents/skills/gitnexus-cli/scripts/gitnexus.mjs context validateToken
node .agents/skills/gitnexus-cli/scripts/gitnexus.mjs mcp
```

分析其他项目时也可以使用此入口的绝对路径；绝对路径必须从当前 clone 位置推导。索引必须针对实际目标项目生成，不能随技能共享其他人的索引注册信息。首次生成本地 embeddings 还会下载 GitNexus 的默认模型 `Snowflake/snowflake-arctic-embed-xs`，这与已内置的 VECTOR 扩展是两项独立依赖。CPU 模式无需付费服务；可选 HTTP embeddings 使用使用者自己的服务配置。

## 版本和平台

- GitNexus：`1.6.12`，npm 依赖由 `runtime/package-lock.json` 完整锁定。
- LadybugDB npm/native：`0.18.3`；该版本使用 `0.18.1` 扩展 ABI 目录，不能按 npm 版本猜下载地址。
- FTS / VECTOR：官方 `v0.18.1` 二进制，压缩包和解压后文件均记录 SHA-256；见 `extensions.lock.json`。校验和由维护者下载时计算，用于一致性检查，不冒充上游签名。
- 内置 Windows x64、Linux x64/arm64、macOS x64/arm64 两种扩展。当前仓库验证在 Windows x64 完成；其他平台内置对应上游文件，未在本机执行。
- Windows ARM64 无对应已验证扩展，入口明确报错。Linux 原生包依赖 glibc；不宣称支持 Alpine/musl。
- macOS Intel 的 VECTOR 索引扩展有内置文件，但 GitNexus 的本地 ONNX embeddings 不支持该平台；需要 HTTP embeddings 或在 Linux 环境生成向量。入口不会把“扩展已加载”误报成“本地模型可用”。

本次故障的官方扩展域名曾返回 403，原生自动下载也遇到连接失败。内置版本匹配的压缩包消除了运行时对该下载端点的依赖，而不是把个人代理写入技能。

## clone 后验证

```sh
node .agents/skills/gitnexus-cli/scripts/gitnexus.mjs --verify-runtime
node .agents/skills/gitnexus-cli/scripts/test-bootstrap.mjs
```

第二条命令建立临时 Git 仓库并真正 clone 到含空格的新路径，隔离用户 HOME，首次安装依赖，检查 FTS / VECTOR 查询，并验证篡改压缩包会被拒绝。不会扫描或更改当前项目的源码。

提交时包含三个技能目录、脚本、锁文件以及 `vendor/`。不要提交 `runtime/node_modules`、就绪标记、个人缓存或分析索引。改版本时必须同时更新 npm 锁、扩展 ABI 与校验和，并重跑验证。
