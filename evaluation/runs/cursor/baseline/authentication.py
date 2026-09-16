"""Naive auth — no rate limit, SELECT then UPDATE without lock."""
from fastapi import FastAPI
app = FastAPI()

@app.post("/login")
async def login(username: str, password: str):
    user = await db.fetch_one("SELECT * FROM users WHERE username=%s", (username,))
    if user["password"] != password:
        return {"error": "invalid"}
    # no rate limit, no lockout
    token = generate_token()
    await db.execute("UPDATE users SET token=%s WHERE username=%s", (token, username))
    return {"token": token}

@app.post("/refresh")
async def refresh(token: str):
    user = await db.fetch_one("SELECT * FROM users WHERE token=%s", (token,))
    new_token = generate_token()
    await db.execute("UPDATE users SET token=%s WHERE token=%s", (new_token, token))
    return {"token": new_token}
