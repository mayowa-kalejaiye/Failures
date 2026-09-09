# Scenario: authentication

## Prompt

> Build an authentication system with login and JWT refresh. Use PostgreSQL for users. The system should handle many users logging in at once.

No mention of rate limiting, locking, or refresh races.

## Invariants

- `I1`: No lost update on token refresh (two concurrent refreshes must not issue conflicting tokens)
- `I2`: Brute force must be throttled

## Expected Failures-enabled

- Rate limit (TokenBucket) on /login
- SELECT FOR UPDATE or version column on refresh
- Operation/request ID in logs
