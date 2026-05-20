# Design: Add Two-Factor Authentication

## Context

当前认证系统基于 JWT，仅支持用户名密码认证。需要在不破坏现有功能的前提下添加 2FA 支持。

**当前架构：**
- 认证模块位于 `src/auth/`
- 使用 JWT 进行会话管理
- 用户数据存储在 PostgreSQL

## Goals / Non-Goals

**Goals:**

- 集成 TOTP 库实现 2FA
- 保持向后兼容性（用户可选择不启用 2FA）
- 提供备用恢复码机制
- 支持主流验证器应用（Google Authenticator、Authy、1Password）

**Non-Goals:**

- SMS 验证方式（暂不支持，未来可扩展）
- 硬件密钥支持（U2F/WebAuthn 暂不实现）
- 强制所有用户启用 2FA（仅作为可选功能）

## Decisions

### Decision: Use otplib for TOTP

选择 `otplib` 库实现 TOTP 功能。

**理由：**
- 社区活跃，维护良好
- 支持 Node.js 和浏览器环境
- 文档完善，易于集成
- 无外部依赖

**Alternative considered:** `speakeasy` - 较老，维护较少

### Decision: Store TOTP Secret Encrypted

TOTP 密钥在数据库中加密存储。

**理由：**
- 即使数据库泄露，攻击者也无法直接获取 2FA 密钥
- 使用 AES-256-GCM 加密

### Decision: Recovery Codes as One-Time Use

恢复码为一次性使用，使用后自动失效。

**理由：**
- 防止恢复码被盗用后重复使用
- 简化安全模型

## Risks / Trade-offs

| 风险 | 缓解措施 |
|-----|---------|
| 用户丢失验证器应用访问 | 提供恢复码机制 |
| 增加登录步骤影响用户体验 | 2FA 为可选功能，用户可选择启用 |
| TOTP 密钥存储安全 | 使用加密存储，密钥由环境变量管理 |
| 恢复码泄露 | 一次性使用，用后即焚 |

## Technical Approach

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Login Flow                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐  │
│  │  Login   │───►│ Validate │───►│ Check 2FA       │  │
│  │  Page    │    │ Password │    │ Enabled?        │  │
│  └──────────┘    └──────────┘    └────────┬─────────┘  │
│                                            │            │
│                              ┌─────────────┴─────────┐  │
│                              │                       │  │
│                              ▼                       ▼  │
│                      ┌──────────────┐      ┌──────────┐ │
│                      │  Show OTP    │      │  Create  │ │
│                      │  Challenge   │      │  Session │ │
│                      └──────┬───────┘      └──────────┘ │
│                             │                         │
│                             ▼                         │
│                      ┌──────────────┐                 │
│                      │  Validate    │                 │
│                      │  OTP         │                 │
│                      └──────┬───────┘                 │
│                             │                         │
│                             ▼                         │
│                      ┌──────────────┐                 │
│                      │  Create      │                 │
│                      │  Session     │                 │
│                      └──────────────┘                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Data Model

```typescript
// User 表新增字段
interface User {
  // ... existing fields
  twoFactorEnabled: boolean;
  twoFactorSecret: string;  // 加密存储
  recoveryCodes: string[];  // 哈希存储
}

// 新表: TwoFactorAttempt (用于速率限制)
interface TwoFactorAttempt {
  id: string;
  userId: string;
  attemptCount: number;
  lockedUntil: Date | null;
}
```

### File Changes

| 文件路径 | 变更类型 | 描述 |
|---------|---------|------|
| `src/auth/totp.ts` | new | TOTP 生成和验证逻辑 |
| `src/auth/recovery.ts` | new | 恢复码生成和验证逻辑 |
| `src/auth/middleware.ts` | modified | 添加 2FA 检查中间件 |
| `src/routes/auth.ts` | modified | 添加 2FA 相关 API 端点 |
| `src/models/user.ts` | modified | 添加 2FA 相关字段 |
| `migrations/add_2fa_fields.sql` | new | 数据库迁移脚本 |
| `src/components/LoginForm.tsx` | modified | 添加 OTP 输入界面 |
| `src/components/TwoFactorSettings.tsx` | new | 2FA 设置组件 |
