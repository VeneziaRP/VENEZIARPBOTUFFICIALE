from __future__ import annotations
import json, time
from pathlib import Path
from typing import Optional

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

ECON_FILE = DATA_DIR / "economy.json"          # conti per gilda
AUDIT_FILE = DATA_DIR / "economy_audit.jsonl"  # audit append-only

def _load() -> dict:
    if ECON_FILE.exists():
        try: return json.loads(ECON_FILE.read_text(encoding="utf-8"))
        except: pass
    return {}

def _save(d: dict) -> None:
    ECON_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

def _now() -> float: return time.time()

def _ensure_guild(d: dict, gid: int) -> dict:
    g = d.setdefault(str(gid), {})
    g.setdefault("accounts", {})
    return g

def _ensure_acct(d: dict, gid: int, uid: int) -> dict:
    g = _ensure_guild(d, gid)
    a = g["accounts"].setdefault(str(uid), {"wallet": 0, "bank": {"iban": None, "balance": 0}, "updated_at": _now()})
    return a

def get_account(guild_id: int, user_id: int) -> dict:
    d = _load()
    return _ensure_acct(d, guild_id, user_id)

def set_iban(guild_id: int, user_id: int, iban: Optional[str]) -> dict:
    d = _load(); a = _ensure_acct(d, guild_id, user_id)
    a["bank"]["iban"] = iban; a["updated_at"] = _now(); _save(d); _audit(guild_id, user_id, 0, "SET_IBAN", meta={"iban": iban})
    return a

def deposit_wallet(guild_id: int, user_id: int, amount: int | float, reason: str="") -> dict:
    d = _load(); a = _ensure_acct(d, guild_id, user_id)
    a["wallet"] = float(a.get("wallet", 0)) + float(amount); a["updated_at"] = _now(); _save(d)
    _audit(guild_id, user_id, amount, "WALLET_DEPOSIT", reason)
    return a

def withdraw_wallet(guild_id: int, user_id: int, amount: int | float, reason: str="") -> dict:
    d = _load(); a = _ensure_acct(d, guild_id, user_id)
    if float(a.get("wallet",0)) < amount: raise ValueError("Fondi insufficienti in portafoglio")
    a["wallet"] = float(a["wallet"]) - float(amount); a["updated_at"] = _now(); _save(d)
    _audit(guild_id, user_id, -amount, "WALLET_WITHDRAW", reason)
    return a

def deposit_bank(guild_id: int, user_id: int, amount: int | float, reason: str="") -> dict:
    d = _load(); a = _ensure_acct(d, guild_id, user_id)
    a["bank"]["balance"] = float(a["bank"].get("balance",0)) + float(amount); a["updated_at"] = _now(); _save(d)
    _audit(guild_id, user_id, amount, "BANK_DEPOSIT", reason)
    return a

def withdraw_bank(guild_id: int, user_id: int, amount: int | float, reason: str="") -> dict:
    d = _load(); a = _ensure_acct(d, guild_id, user_id)
    if float(a["bank"].get("balance",0)) < amount: raise ValueError("Fondi insufficienti in banca")
    a["bank"]["balance"] = float(a["bank"]["balance"]) - float(amount); a["updated_at"] = _now(); _save(d)
    _audit(guild_id, user_id, -amount, "BANK_WITHDRAW", reason)
    return a

def transfer_bank(guild_id: int, from_uid: int, to_uid: int, amount: int | float, reason: str="") -> None:
    if amount <= 0: raise ValueError("Importo non valido")
    d = _load()
    a_from = _ensure_acct(d, guild_id, from_uid)
    a_to   = _ensure_acct(d, guild_id, to_uid)
    if float(a_from["bank"].get("balance",0)) < amount: raise ValueError("Fondi insufficienti")
    a_from["bank"]["balance"] = float(a_from["bank"]["balance"]) - float(amount)
    a_to["bank"]["balance"]   = float(a_to["bank"].get("balance",0)) + float(amount)
    a_from["updated_at"] = a_to["updated_at"] = _now()
    _save(d)
    _audit(guild_id, from_uid, -amount, "BANK_TRANSFER_OUT", reason, meta={"to": to_uid})
    _audit(guild_id, to_uid, amount, "BANK_TRANSFER_IN", reason, meta={"from": from_uid})

def _audit(gid: int, uid: int, amount: float, op: str, reason: str="", meta: dict | None=None):
    rec = {"t": _now(), "guild_id": gid, "user_id": uid, "amount": amount, "op": op, "reason": reason, "meta": meta or {}}
    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")