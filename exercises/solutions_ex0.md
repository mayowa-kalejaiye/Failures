# Exercise 0 — Hints & Short Solution

Hints (work through in order):

- Validate email: a simple check is `if '@' not in email: raise ValueError` — keep this minimal for the exercise.
- Prevent duplicates: check the in-memory `_users` list for the same email and return HTTP 409 if found.
- Assign IDs: use `len(_users) + 1` when appending a new user.
- Use `pydantic` models for input validation (already in the starter).
- For list pagination: accept `limit` as a query param and slice the `_users` list.
- For `GET /users/{id}` return 404 when user is not present.

Short solution (conceptual):

1. `create_user` — check duplicates, append user dict with `id`, return the dict.
2. `list_users` — return `_users[:limit]`.
3. `get_user` — loop `_users` for `id` and return or raise 404.

Optional full reference (copy only when stuck):

```python
def create_user(payload):
    for u in _users:
        if u['email'] == payload.email:
            raise HTTPException(status_code=409, detail='Email already registered')
    user = {'id': len(_users) + 1, 'email': payload.email, 'name': payload.name}
    _users.append(user)
    return user

def list_users(limit=10):
    return _users[:limit]

def get_user(user_id):
    for u in _users:
        if u['id'] == user_id:
            return u
    raise HTTPException(status_code=404, detail='User not found')
```

Use these hints to implement and test; the full reference is deliberately small so you still learn by coding.
