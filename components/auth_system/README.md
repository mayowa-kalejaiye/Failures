# 🔐 Authentication System

A production-ready authentication system with proper failure handling.

## What You'll Build

A complete auth system with:
- ✅ User registration
- ✅ Login with JWT tokens
- ✅ Session management
- ✅ Password reset
- ✅ Rate limiting (prevent brute force)
- ✅ Connection pooling (handle DB load)
- ✅ Secure password hashing

## Failure Patterns Applied

| Pattern | Where Used | Why |
|---------|------------|-----|
| **Connection Pool** | Database access | Share connections efficiently |
| **Rate Limiting** | Login, registration | Prevent brute force attacks |
| **Retry Logic** | Email sending | Handle temporary email failures |
| **Circuit Breaker** | Email service | Stop trying if email is down |
| **Timeouts** | All operations | Prevent hanging requests |

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│     FastAPI Endpoints           │
│  - POST /register               │
│  - POST /login                  │
│  - POST /refresh                │
│  - POST /forgot-password        │
│  - POST /reset-password         │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│   Rate Limiter Middleware       │
│  (Token Bucket per IP/User)     │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│   AuthService (Business Logic)  │
│  - User validation              │
│  - Password hashing             │
│  - JWT token generation         │
└──────┬──────────────────────────┘
       │
       ├─────────────┐
       ▼             ▼
┌──────────────┐  ┌──────────────┐
│   Database   │  │Email Service │
│(via Pool)    │  │(via Circuit) │
└──────────────┘  └──────────────┘
```

## Database Schema

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_sessions_token ON sessions(token_hash);
CREATE INDEX idx_reset_tokens ON password_reset_tokens(token_hash);
```

## API Endpoints

### POST /auth/register
Register a new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Success Response (201):**
```json
{
  "user_id": 123,
  "email": "user@example.com",
  "message": "Registration successful"
}
```

**Failures:**
- `400`: Invalid email or weak password
- `409`: Email already exists
- `429`: Too many registration attempts
- `503`: Database unavailable

---

### POST /auth/login
Login and get JWT token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Failures:**
- `401`: Invalid credentials
- `429`: Too many login attempts (brute force protection)
- `503`: Database unavailable

---

### POST /auth/refresh
Refresh access token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 3600
}
```

---

### POST /auth/forgot-password
Request password reset.

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Success Response (200):**
```json
{
  "message": "If the email exists, a reset link has been sent"
}
```

**Note:** Always returns 200 to prevent email enumeration.

**Failures:**
- `429`: Too many reset requests
- `503`: Email service unavailable (circuit breaker open)

---

### GET /auth/health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "checks": {
    "database": "healthy",
    "email_service": "healthy"
  },
  "timestamp": "2026-02-07T10:30:00Z"
}
```

## Implementation Plan

### Phase 1: Setup (30 min)
- [ ] Create project structure
- [ ] Set up database with schema
- [ ] Configure environment variables
- [ ] Install dependencies

### Phase 2: Core Auth (2 hours)
- [ ] Implement user registration
- [ ] Implement password hashing (bcrypt)
- [ ] Implement JWT token generation
- [ ] Implement login logic

### Phase 3: Database Layer (1 hour)
- [ ] Create connection pool
- [ ] Implement user CRUD operations
- [ ] Handle connection errors
- [ ] Add query timeouts

### Phase 4: Failure Handling (2 hours)
- [ ] Add rate limiting to endpoints
- [ ] Add circuit breaker for email
- [ ] Add retry logic for transient failures
- [ ] Handle pool exhaustion

### Phase 5: Testing (1.5 hours)
- [ ] Test happy path for all endpoints
- [ ] Test rate limit enforcement
- [ ] Test DB connection failures
- [ ] Test email service failures
- [ ] Load test with concurrent requests

### Phase 6: Production (1 hour)
- [ ] Add comprehensive logging
- [ ] Add metrics/monitoring
- [ ] Add health check endpoint
- [ ] Write documentation
- [ ] Create Docker setup

## Setup Instructions

### 1. Install Dependencies
```bash
pip install fastapi uvicorn[standard] pydantic python-jose[cryptography] passlib[bcrypt] psycopg2-binary python-multipart aiosmtplib
```

### 2. Set Environment Variables
Create `.env` file:
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/auth_db
DB_POOL_SIZE=10
DB_POOL_TIMEOUT=30

JWT_SECRET_KEY=your-super-secret-key-change-this
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

RATE_LIMIT_REGISTER=5
RATE_LIMIT_LOGIN=10
RATE_LIMIT_WINDOW=60
```

### 3. Create Database
```bash
createdb auth_db
psql auth_db < schema.sql
```

### 4. Run
```bash
uvicorn api:app --reload --port 8001
```

## Testing

### Manual Testing
```bash
# Register a user
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePass123!"}'

# Login
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePass123!"}'

# Health check
curl http://localhost:8001/auth/health
```

### Automated Testing
```bash
pytest tests/
```

## Failure Scenarios to Test

1. **Database Connection Pool Exhaustion**
   - Send 50 concurrent requests
   - Should handle gracefully with 503

2. **Rate Limiting**
   - Send 20 login requests in 10 seconds
   - Should get 429 after limit reached

3. **Email Service Down**
   - Simulate email failure
   - Circuit breaker should open
   - Should return 503 for password reset

4. **Invalid Credentials**
   - Try wrong password
   - Should return 401 (not 503)

5. **Database Temporarily Down**
   - Restart database
   - Should retry and recover

## Security Considerations

✅ **Passwords**: Hashed with bcrypt (12 rounds)  
✅ **Tokens**: JWT with expiration  
✅ **Rate Limiting**: Prevent brute force  
✅ **SQL Injection**: Parameterized queries  
✅ **Email Enumeration**: Don't reveal if email exists  
✅ **HTTPS Only**: In production  
✅ **Secrets**: Never in code, use env vars

## Monitoring

Key metrics to track:
- Login success/failure rate
- Registration rate
- Rate limit hits
- Database pool utilization
- Email delivery success rate
- Circuit breaker state changes

## Common Issues

### Issue: "Database pool exhausted"
**Cause:** Too many concurrent requests  
**Fix:** Increase pool size or optimize queries  
**Monitor:** Pool utilization metric

### Issue: "Too many password reset emails"
**Cause:** Email bombing attack  
**Fix:** Rate limit per email address  
**Monitor:** Reset request rate

### Issue: "Tokens not refreshing"
**Cause:** Clock skew or expired refresh token  
**Fix:** Check token expiration logic  
**Monitor:** Token refresh failure rate

## Next Steps

After completing this:
1. Add OAuth2 providers (Google, GitHub)
2. Add 2FA (TOTP)
3. Add session management UI
4. Add audit logging
5. Add admin panel

## Resources

- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [OWASP Auth Cheatsheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

---

**Good luck building!** 🔐
