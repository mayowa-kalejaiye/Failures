# Foundations for Newcomers

This short guide covers the absolute basics you need before tackling retry strategies, exponential backoff, and other resilience patterns.

Read this first if you are new to APIs, HTTP, or running small Python services.

1. What is an API?

- An API (Application Programming Interface) is a programmatic way for one piece of software to talk to another over a network.
- Most web APIs use HTTP and exchange data in JSON format.

2. HTTP methods (very short)

- `GET` - read data (safe, idempotent)
- `POST` - create or send data (may change server state)
- `PUT` - replace a resource
- `PATCH` - change part of a resource
- `DELETE` - remove a resource
@- `DELETE` - remove a resource

3. JSON basics

- JSON is a plain-text format for structured data. Example:

```json
{
  "email": "alice@example.com",
  "password": "safepassword123"
}
```

4. Sending requests with `curl` (quick examples)

- Simple GET:

```bash
curl http://localhost:8000/health
```

- POST with JSON:

```bash
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"MyPassw0rd!"}'
```

Notes:
- Use `-v` to show verbose output and headers.
- If a command fails, read the error and try one small fix.

5. Running a FastAPI app locally

- Install dependencies once:

```bash
pip install -r requirements.txt
```

- Run a FastAPI app (example for the auth starter):

```bash
uvicorn components.auth_system.api:app --reload --port 8001
```

- If a file or module name differs, adapt the path after `uvicorn` accordingly.

6. Using Postman or Insomnia

- GUI tools make it easier to build and re-run requests.
- Import a request, set method and JSON body, then send.

7. First tiny exercise (hands-on)

1. Start the auth app (see command above). If you do not have it running, try the exercises server instead:

```bash
uvicorn exercises.ex1_db_starter:app --reload --port 8000
```

2. Try a health check:

```bash
curl http://localhost:8001/auth/health
```

3. Try the example `curl` POST to register (it will return a TODO if the endpoint is not implemented yet).

---

8. First API lab (step-by-step)

This guided mini-lab walks you through creating and running a tiny API so you can see how requests, responses, and endpoints work.

1) Create a new file at `tools/foundations_example/app.py` with this content:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
  name: str

items = []

@app.get("/health")
def health():
  return {"status": "ok"}

@app.post("/items")
def create_item(item: Item):
  items.append(item.dict())
  return {"id": len(items), "item": item}

@app.get("/items")
def list_items():
  return items
```

2) Run it locally (in your project root):

```bash
pip install -r requirements.txt
uvicorn tools.foundations_example.app:app --reload --port 9000
```

3) In another terminal, try these requests:

```bash
curl http://localhost:9000/health
curl -X POST http://localhost:9000/items -H "Content-Type: application/json" \
  -d '{"name":"test item"}'
curl http://localhost:9000/items
```

4) Try editing the code (change the response shape or add validation) and watch the server reload.

5) What to try next:

- Add an endpoint that returns a single item by id.
- Add a small test script that calls the endpoints and asserts expected JSON.
- Experiment with error responses (raise HTTPException) and see how clients receive them.

---

- If `curl` says connection refused, check the server is running and the port matches.
- If you get a JSON error, ensure your data is valid JSON (use double quotes).
- If you see a 4xx or 5xx error, read the response body for details.

9. Where to go next

- After this short primer, return to `docs/START_HERE.md` and the exercises. Foundations gives you the minimal comfort to follow the exercises that introduce retries and backoff.

Good luck - take small steps and test often.
