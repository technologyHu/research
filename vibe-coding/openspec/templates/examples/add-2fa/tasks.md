# Tasks

## 1. Backend - TOTP Implementation

- [ ] 1.1 Install otplib package (`npm install otplib`)
- [ ] 1.2 Create `src/auth/totp.ts` with TOTP generation and validation
- [ ] 1.3 Implement TOTP secret encryption/decryption utilities
- [ ] 1.4 Create database migration for 2FA fields

## 2. Backend - Recovery Codes

- [ ] 2.1 Create `src/auth/recovery.ts` with recovery code generation
- [ ] 2.2 Implement recovery code hashing (using bcrypt)
- [ ] 2.3 Implement recovery code validation and invalidation

## 3. Backend - API Endpoints

- [ ] 3.1 Add `POST /auth/2fa/enable` endpoint
- [ ] 3.2 Add `POST /auth/2fa/disable` endpoint
- [ ] 3.3 Add `POST /auth/2fa/verify` endpoint
- [ ] 3.4 Add `GET /auth/2fa/recovery-codes` endpoint
- [ ] 3.5 Add `POST /auth/2fa/regenerate-recovery-codes` endpoint
- [ ] 3.6 Modify `POST /auth/login` to handle 2FA flow

## 4. Backend - Middleware & Security

- [ ] 4.1 Create 2FA verification middleware
- [ ] 4.2 Implement rate limiting for OTP attempts
- [ ] 4.3 Add account lockout after 5 failed attempts

## 5. Frontend - Login Flow

- [ ] 5.1 Create `TwoFactorChallenge.tsx` component
- [ ] 5.2 Modify `LoginForm.tsx` to handle 2FA redirect
- [ ] 5.3 Add "Use recovery code" option
- [ ] 5.4 Handle 2FA error states

## 6. Frontend - Settings Page

- [ ] 6.1 Create `TwoFactorSettings.tsx` component
- [ ] 6.2 Add QR code display for TOTP setup
- [ ] 6.3 Add recovery codes display with copy/download
- [ ] 6.4 Add 2FA enable/disable toggle
- [ ] 6.5 Add regenerate recovery codes button

## 7. Testing

- [ ] 7.1 Add unit tests for `totp.ts`
- [ ] 7.2 Add unit tests for `recovery.ts`
- [ ] 7.3 Add integration tests for 2FA login flow
- [ ] 7.4 Add E2E tests for complete 2FA setup flow
- [ ] 7.5 Test with Google Authenticator
- [ ] 7.6 Test with Authy
- [ ] 7.7 Test with 1Password

## 8. Documentation

- [ ] 8.1 Update API documentation with 2FA endpoints
- [ ] 8.2 Add user guide for enabling 2FA
- [ ] 8.3 Add admin guide for 2FA enforcement options
- [ ] 8.4 Update security documentation

## 9. Deployment

- [ ] 9.1 Run database migration in staging
- [ ] 9.2 Test 2FA flow in staging
- [ ] 9.3 Deploy to production
- [ ] 9.4 Monitor 2FA adoption metrics
