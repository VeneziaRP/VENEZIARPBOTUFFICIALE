# utils/ferie_db.py
import os, json
from datetime import datetime, date
from typing import Dict, Any, List

DATA_DIR = "data"
FERIE_PATH = os.path.join(DATA_DIR, "ferie.json")

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(FERIE_PATH):
        with open(FERIE_PATH, "w", encoding="utf-8") as f:
            json.dump({"ferie": []}, f, ensure_ascii=False, indent=2)

def _load() -> Dict[str, Any]:
    _ensure()
    with open(FERIE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("ferie", [])
    return data

def _save(data: Dict[str, Any]):
    with open(FERIE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _to_date(s: str) -> date | None:
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s.replace("/", "-"), fmt.replace("/", "-")).date()
        except Exception:
            continue
    return None

def aggiungi_ferie(user_id: int, username: str, ruolo: str,
                   data_inizio: str, data_fine: str,
                   motivazione: str = "", approvato_da: str = ""):
    """Aggiunge/aggiorna il record ferie dell’utente (sovrascrive eventuale intervallo)."""
    db = _load()
    # rimuovi eventuali record preesistenti sovrapposti per quello user
    db["ferie"] = [r for r in db["ferie"] if r.get("user_id") != user_id]
    rec = {
        "user_id": user_id,
        "username": username,
        "ruolo": ruolo,
        "data_inizio": data_inizio,  # ISO preferito
        "data_fine": data_fine,      # ISO preferito
        "motivazione": motivazione or "",
        "approvato_da": approvato_da or "",
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    db["ferie"].append(rec)
    _save(db)

def rimuovi_ferie(user_id: int):
    db = _load()
    before = len(db["ferie"])
    db["ferie"] = [r for r in db["ferie"] if r.get("user_id") != user_id]
    if len(db["ferie"]) != before:
        _save(db)
        return True
    return False

def tutte_le_ferie() -> List[Dict[str, Any]]:
    return _load()["ferie"]

def ferie_attive_oggi() -> List[Dict[str, Any]]:
    oggi = date.today()
    out = []
    for r in tutte_le_ferie():
        d1 = _to_date(r.get("data_inizio"))
        d2 = _to_date(r.get("data_fine"))
        if d1 and d2 and d1 <= oggi <= d2:
            out.append(r)
    # ordina per fine crescente
    out.sort(key=lambda x: _to_date(x.get("data_fine")) or date.max)
    return out

def ferie_future(limit_giorni: int = 30) -> List[Dict[str, Any]]:
    """Ferie che devono ancora iniziare, entro N giorni (default 30)."""
    oggi = date.today()
    deadline = oggi.toordinal() + limit_giorni
    out = []
    for r in tutte_le_ferie():
        d1 = _to_date(r.get("data_inizio"))
        if d1 and d1 > oggi and d1.toordinal() <= deadline:
            out.append(r)
    out.sort(key=lambda x: _to_date(x.get("data_inizio")) or date.max)
    return out

def ferie_scadute() -> List[Dict[str, Any]]:
    oggi = date.today()
    return [r for r in tutte_le_ferie() if (_to_date(r.get("data_fine")) or oggi) < oggi]

def rimuovi_scadute() -> int:
    """Rimuove dal DB le ferie già terminate (opzionale se vuoi mantenere storico)."""
    db = _load()
    oggi = date.today()
    before = len(db["ferie"])
    db["ferie"] = [r for r in db["ferie"] if (_to_date(r.get("data_fine")) or oggi) >= oggi]
    _save(db)
    return before - len(db["ferie"])