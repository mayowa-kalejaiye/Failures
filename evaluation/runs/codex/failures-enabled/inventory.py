"""Improved inventory — optimistic locking + idempotency."""
from fastapi import FastAPI, HTTPException
app = FastAPI()

@app.post("/deduct")
async def deduct(item_id: str, qty: int, idempotency_key: str):
    # idempotency dedup
    try:
        await db.execute("INSERT INTO dedup (key) VALUES (%s)", (idempotency_key,))
    except:
        existing = await db.fetch_one("SELECT stock FROM inventory WHERE id=%s", (item_id,))
        return {"stock": existing["stock"], "dedup": True}
    # optimistic locking
    row = await db.fetch_one("SELECT stock, version FROM inventory WHERE id=%s", (item_id,))
    if row["stock"] < qty:
        raise HTTPException(400, "insufficient stock")
    updated = await db.execute("UPDATE inventory SET stock=stock-%s, version=version+1 WHERE id=%s AND version=%s", (qty, item_id, row["version"]))
    if updated.rowcount == 0:
        raise HTTPException(409, "concurrent modification, retry")
    return {"stock": row["stock"] - qty}
