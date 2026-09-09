"""Naive payment — intentionally flawed (for benchmark)."""
from fastapi import FastAPI
import requests

app = FastAPI()

@app.post("/payments")
async def pay(payment: dict):
    # CRITICAL: external call before durable state, no idempotency, no transaction, no timeout
    result = requests.post("https://api.paystack.co/charge", json={"amount": payment["amount"]})
    # DB writes without transaction
    await db.execute("INSERT INTO payments VALUES (%s, %s, 'completed')", (payment["id"], payment["amount"]))
    await db.execute("UPDATE accounts SET balance = balance - %s WHERE user_id=%s", (payment["amount"], payment["user_id"]))
    # enrollment unconditional, no verification
    await db.execute("INSERT INTO enrollments (user_id, course_id) VALUES (%s, %s)", (payment["user_id"], payment["course_id"]))
    return result.json()
