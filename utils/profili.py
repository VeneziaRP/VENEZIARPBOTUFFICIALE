# utils/profili.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict

DB_FILE = Path("data/profili.json")
DB_FILE.parent.mkdir(parents=True, exist_ok=True)

# ---------- Helpers I/O ----------
def _load_db() -> Dict[str, Any]:
    if DB_FILE.exists():
        try:
            return json.loads(DB_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"profiles": {}}

def _save_db(db: Dict[str, Any]) -> None:
    DB_FILE.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------- Merge profilo ----------
def _deep_merge(base: Any, new: Any) -> Any:
    """
    Merge ricorsivo:
    - dict: merge key-by-key
    - list/tuple: sovrascrivi con 'new' (non fa union per evitare duplicati strani)
    - il resto: sovrascrivi
    """
    if isinstance(base, dict) and isinstance(new, dict):
        out = dict(base)
        for k, v in new.items():
            out[k] = _deep_merge(out.get(k), v)
        return out
    # se il campo non esiste, restituisci 'new' direttamente
    return new if new is not None else base

# ---------- API principali ----------
def get_profile(user_id: int) -> Dict[str, Any]:
    """Ritorna il profilo utente con default sensati."""
    db = _load_db()
    ukey = str(user_id)
    prof = (db.get("profiles") or {}).get(ukey) or {}

    # default consigliati (usati nei tuoi embed)
    defaults = {
        "wallet": 0.0,
        "bank": {
            "iban": "",
            "saldo": 0.0,
        },
        "nome_rp": "",
        "cognome_rp": "",
        "data_nascita": "",
        "stato_civile": "",
        "famiglia": "",
        "cittadinanza": "",
        "identity_card": "",
        "docs": {
            "cittadinanza": {
                "stato": False,
                "numero": "",
                "rilasciata_il": "",
                "rilasciata_da": "",
                "note": ""
            },
            "patenti": {
                "A": {"stato": False, "numero": "", "rilasciata_il": "", "scadenza": ""},
                "B": {"stato": False, "numero": "", "rilasciata_il": "", "scadenza": ""},
                "C": {"stato": False, "numero": "", "rilasciata_il": "", "scadenza": ""},
                "NAUTICA": {"stato": False, "numero": "", "rilasciata_il": "", "scadenza": ""}
            },
            # ✅ porto d’armi va qui, non dentro "patenti"
            "porto_armi": {
                "stato": False,
                "numero": "",
                "rilasciata_il": "",
                "scadenza": "",
                "rilasciata_da": "",
                "tipo": "",
                "note": ""
            }
        },
        "fazioni": [],
        "patenti_extra": [],
        "proprieta": {
            "case": [],
            "veicoli": [],   # es. [{"modello":"...", "targa":"..."}, ...]
            "aziende": []
        },
        "lavoro": "",      # o "lavoro_rp" se preferisci, nei tuoi embed leggi "lavoro"
        "riconoscimenti": [],
        "bio": "",
        "roblox": "",
        "social": "",
    }

    return _deep_merge(defaults, prof)

def set_profile(user_id: int, **patch: Any) -> Dict[str, Any]:
    """
    Applica un patch al profilo (merge ricorsivo) e salva.
    Uso: set_profile(uid, bank={"saldo": 123}, wallet=50)
    """
    db = _load_db()
    ukey = str(user_id)
    cur = (db.get("profiles") or {}).get(ukey) or {}
    new_prof = _deep_merge(cur, patch)
    db.setdefault("profiles", {})[ukey] = new_prof
    _save_db(db)
    return new_prof

# Alias comodo se preferisci passare un dict già pronto
def upsert_profile(user_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    return set_profile(user_id, **payload)

# ---------- Utility di formattazione ----------
def money_fmt(value: Any) -> str:
    try:
        n = float(value or 0)
    except Exception:
        n = 0.0
    # Stile europeo con separatore migliaia e 2 decimali
    return f"€{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def mask_iban(iban: Any) -> str:
    s = str(iban or "").replace(" ", "")
    if len(s) <= 6:
        return s or "—"
    return f"{s[:4]}{'*'*(len(s)-7)}{s[-3:]}"