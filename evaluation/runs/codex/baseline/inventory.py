"""Naive inventory — lost update."""
from fastapi import FastAPI
app = FastAPI()

@app.post("/deduct")
async def deduct(item_id: str, qty: int):
    row = await db.fetch_one("SELECT stock FROM inventory WHERE id=%s", (item_id,))
    new_stock = row["stock"] - qty
    await db.execute("UPDATE inventory SET stock=%s WHERE id=%s", (new_stock, item_id))
    return {"stock": new_stock}
