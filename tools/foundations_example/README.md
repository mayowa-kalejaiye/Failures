# Foundations Example

This folder contains a tiny FastAPI example used by the `docs/FOUNDATIONS.md` first API lab.

Run the server from the repository root:

```bash
pip install -r requirements.txt
uvicorn tools.foundations_example.app:app --reload --port 9000
```

Then try the example requests in the `docs/FOUNDATIONS.md` file.
