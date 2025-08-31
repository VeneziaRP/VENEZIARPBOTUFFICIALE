import os, json

DATA_DIR = "data/annunci"
os.makedirs(DATA_DIR, exist_ok=True)

def _path(mid: int) -> str:
    return os.path.join(DATA_DIR, f"{mid}.json")

def save(mid: int, data: dict):
    data["message_id"] = mid
    with open(_path(mid), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load(mid: int) -> dict | None:
    try:
        with open(_path(mid), "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def all_states() -> list[dict]:
    states = []
    for fn in os.listdir(DATA_DIR):
        if fn.endswith(".json"):
            try:
                with open(os.path.join(DATA_DIR, fn), "r", encoding="utf-8") as f:
                    states.append(json.load(f))
            except Exception:
                pass
    return states