# Delta for Auth

## ADDED Requirements

### Requirement: Two-Factor Authentication

The system SHALL support TOTP-based two-factor authentication. Users MAY enable this feature to enhance account security.

系统应支持基于 TOTP 的双因素认证。用户可选择启用此功能以增强账户安全。

#### Scenario: Enable 2FA

- **GIVEN** a user with valid credentials and 2FA not enabled
- **WHEN** the user navigates to security settings and clicks "Enable 2FA"
- **THEN** the system generates a TOTP secret and displays a QR code
- **AND** the user must scan the QR code with an authenticator app
- **AND** the user must verify with a valid code before activation

#### Scenario: Login with 2FA

- **GIVEN** a user with 2FA enabled
- **WHEN** the user submits valid username and password
- **THEN** an OTP challenge is presented
- **AND** login completes only after valid OTP is entered

#### Scenario: Use Recovery Code

- **GIVEN** a user with 2FA enabled who has lost access to authenticator app
- **WHEN** the user clicks "Use recovery code" and enters a valid recovery code
- **THEN** the user is authenticated
- **AND** the used recovery code is invalidated

### Requirement: Recovery Codes

The system SHALL generate a set of one-time recovery codes when 2FA is enabled.

系统应在启用 2FA 时生成一组一次性恢复码。

#### Scenario: Generate Recovery Codes

- **GIVEN** a user enabling 2FA
- **WHEN** the 2FA setup is complete
- **THEN** the system generates 8 unique recovery codes
- **AND** the codes are displayed to the user for safekeeping

## MODIFIED Requirements

### Requirement: Session Expiration

The system MUST expire sessions after 7 days of inactivity.

(Previously: 30 days of inactivity)

When 2FA is enabled, sessions SHALL expire after 30 days of inactivity.

#### Scenario: Session timeout with 2FA

- **GIVEN** an authenticated session with 2FA enabled
- **WHEN** 30 days pass without activity
- **THEN** the session is invalidated
- **AND** the user must re-authenticate with 2FA

#### Scenario: Session timeout without 2FA

- **GIVEN** an authenticated session without 2FA
- **WHEN** 7 days pass without activity
- **THEN** the session is invalidated
- **AND** the user must re-authenticate

## REMOVED Requirements

### Requirement: Remember Me

(Deprecated in favor of 2FA. Session length is now determined by 2FA status.)

移除"记住我"选项，由 2FA 状态决定会话长度。
