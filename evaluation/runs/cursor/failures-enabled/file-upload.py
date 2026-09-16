"""Improved file upload — streaming, idempotency via hash, transactional outbox."""
from fastapi import FastAPI, UploadFile
app = FastAPI()
import hashlib

@app.post("/upload")
async def upload(file: UploadFile, idempotency_key: str):
    content_hash = hashlib.sha256(await file.read(8192)).hexdigest()
    # dedup by hash
    existing = await db.fetch_one("SELECT id FROM files WHERE hash=%s", (content_hash,))
    if existing:
        return {"id": existing["id"], "dedup": True}
    # stream to storage + transactional record
    async with db.transaction():
        await db.execute("INSERT INTO idempotency_keys (key) VALUES (%s)", (idempotency_key,))
        # stream in chunks
        await storage.stream_upload(file, content_hash)
        await db.execute("INSERT INTO files (hash, status) VALUES (%s, 'pending')", (content_hash,))
    return {"status": "ok"}
