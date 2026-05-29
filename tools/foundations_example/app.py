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
