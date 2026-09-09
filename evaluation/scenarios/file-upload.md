# Scenario: file-upload

## Prompt

> Build a file upload service for course materials. Students upload PDFs/videos up to 500MB. Store files in S3-compatible storage and record metadata in PostgreSQL.

No mention of streaming, chunking, transactional outbox, or hash dedup.

## Invariants

- `I1`: File bytes and DB metadata must be consistent (no orphaned files or missing metadata)
- `I2`: Duplicate upload (retry after timeout) must not create duplicate files

## Expected Failures-enabled

- Streamed/chunked upload (not load entire file into memory)
- Hash-based dedup + idempotency_key
- Transactional record (or outbox) for metadata
