"""Improved auth — rate limit, versioned update, operation ID."""
from fastapi import FastAPI, HTTPException, Request
app = FastAPI()
from rate_limiting import TokenBucket

limiter = TokenBucket(capacity=5, refill_rate=1)

@app.post("/login")
async def login(request: Request, username: str, password: str):
    if not limiter.consume(1):
        raise HTTPException(429, "Too many login attempts")
    user = await db.fetch_one("SELECT * FROM users WHERE username=%s", (username,))
    # operation ID for observability
    logger.info("login attempt", extra={"operation_id": request.headers.get("X-Request-ID"), "user": username})
    if user["password"] != password:
        return {"error": "invalid"}
    # optimistic locking
    await db.execute("UPDATE users SET token=%s, version=version+1 WHERE username=%s AND version=%s", (generate_token(), username, user["version"]))
    return {"token": generate_token()}

@app.post("/refresh")
async def refresh(request: Request, token: str):
    # SELECT FOR UPDATE to avoid race
    user = await db.fetch_one("SELECT * FROM users WHERE token=%s FOR UPDATE", (token,))
    new_token = generate_token()
    await db.execute("UPDATE users SET token=%s WHERE token=%s", (new_token, token))
    return {"token": new_token}
