"""Improved webhook — dedup via event_id UNIQUE, ordering via version, idempotent."""
from fastapi import FastAPI
app = FastAPI()
@app.post("/webhook/paystack")
async def webhook(event: dict):
    event_id = event["event_id"]
    # dedup with UNIQUE
    try:
        await db.execute("INSERT INTO webhook_events (event_id) VALUES (%s)", (event_id,))
    except:
        return {"already_processed": True}
    # ordering guard
    await db.execute("UPDATE payments SET status='completed', version=version+1 WHERE reference=%s AND version < %s", (event["data"]["reference"], event["version"]))
    # idempotent enrollment
    await db.execute("INSERT INTO enrollments (user_id, course_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (event["data"]["user_id"], event["data"]["course_id"]))
    return {"ok": True}
