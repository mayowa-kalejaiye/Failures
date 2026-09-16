"""Naive file upload — no streaming, no atomicity, no dedup."""
from fastapi import FastAPI
app = FastAPI()

@app.post("/upload")
async def upload(file: bytes):
    # loads entire file into memory, no limit
    open(f"/tmp/{file[:10]}", "wb").write(file)
    await db.execute("INSERT INTO files (name) VALUES (%s)", (file[:10],))
    return {"ok": True}
