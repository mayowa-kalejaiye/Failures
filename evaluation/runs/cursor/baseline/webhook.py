"""Naive webhook — no dedup, no ordering, no idempotency."""
from fastapi import FastAPI
app = FastAPI()
@app.post("/webhook/paystack")
async def webhook(event: dict):
    # no dedup, no event_id check
    await db.execute("UPDATE payments SET status='completed' WHERE reference=%s", (event["data"]["reference"],))
    await db.execute("INSERT INTO enrollments (user_id, course_id) VALUES (%s, %s)", (event["data"]["user_id"], event["data"]["course_id"]))
    return {"ok": True}
