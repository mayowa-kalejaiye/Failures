import json, pathlib

ROOT = pathlib.Path(__file__).parent.parent
KNOWLEDGE = ROOT / "knowledge"

def load_json(name: str):
    p = KNOWLEDGE / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8"))

def load_principles():
    return load_json("principles")

def load_rules():
    return load_json("rules")

def load_dimensions():
    return load_json("dimensions")
