import json
from typing import Any, List, Dict

def load_recipes(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Validation minimale
    for r in data:
        assert "id" in r and "name" in r and "ingredients" in r
        assert isinstance(r["ingredients"], list)
    return data

def save_json(obj, path: str | None = None):
    s = json.dumps(obj, ensure_ascii=False, indent=2)
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(s)
    else:
        print(s)