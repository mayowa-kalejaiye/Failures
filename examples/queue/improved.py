"""Improved queue worker — idempotent + ack after success + DLQ."""
import queue

def consume():
    while True:
        msg = queue.get()
        try:
            if is_duplicate(msg["id"]):
                queue.ack(msg)
                continue
            process_idempotently(msg)
            queue.ack(msg)  # ack AFTER success
        except Exception as e:
            if should_dlq(msg):
                queue.move_to_dlq(msg)
                queue.ack(msg)
            else:
                queue.nack(msg)

def is_duplicate(msg_id: str) -> bool:
    # dedup table with unique constraint
    try:
        db.execute("INSERT INTO dedup (msg_id) VALUES (%s)", (msg_id,))
        return False
    except:
        return True

def process_idempotently(msg):
    # idempotent insert
    db.execute("INSERT INTO jobs (id) VALUES (%s) ON CONFLICT DO NOTHING", (msg["id"],))
