"""Naive queue worker — flawed."""
import queue

def consume():
    while True:
        msg = queue.get()  # no ack, no dedup
        process(msg)
        # no ack, no idempotency -> redelivery duplicates

def process(msg):
    db.execute("INSERT INTO jobs (id) VALUES (%s)", (msg["id"],))
    send_email(msg["email"])
