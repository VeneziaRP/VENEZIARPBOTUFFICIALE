# events/profil_auto.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Iterable, List, Dict, Optional

import discord
from discord.ext import commands

from utils.profili import get_profile, set_profile

ROLES_FILE = Path("data/roles.json")


def _load_roles_map() -> Dict[str, Any]:
    if ROLES_FILE.exists():
        try:
            return json.loads(ROLES_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _to_ids(val: Any) -> List[int]:
    """
    Converte val in lista di int.
    - int -> [int]
    - str numerica -> [int]
    - list/tuple di int/str -> [int, ...]
    - altro/None -> []
    """
    if val is None:
        return []
    if isinstance(val, (list, tuple, set)):
        out: List[int] = []
        for x in val:
            try:
                out.append(int(x))
            except Exception:
                pass
        return out
    try:
        return [int(val)]
    except Exception:
        return []


def _role_names(member: discord.Member, ids: Iterable[int]) -> List[str]:
    idset = set(ids)
    if not idset:
        return []
    roles_sorted = sorted(member.roles, key=lambda r: r.position, reverse=True)
    return [r.name for r in roles_sorted if r.id in idset]


def _top_role_name(member: discord.Member, ids: Iterable[int]) -> Optional[str]:
    idset = set(ids)
    if not idset:
        return None
    roles_sorted = sorted(member.roles, key=lambda r: r.position, reverse=True)
    for r in roles_sorted:
        if r.id in idset:
            return r.name
    return None


class ProfiliAuto(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 👋 Al join: assicura che il profilo esista
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # crea con defaults se manca
        get_profile(member.id)
        # eventualmente inizializza qualche campo base
        set_profile(member.id, nome_rp=None, identity_card=None)

    # 🔄 Aggiorna profilo solo se i ruoli cambiano
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.guild is None or after.guild is None:
            return
        # evita lavoro inutile se i ruoli non sono cambiati
        if set(before.roles) == set(after.roles):
            return

        roles_map = _load_roles_map()

        # --- Cittadinanza ---
        cittadino_id = _to_ids(roles_map.get("cittadino"))
        turista_id   = _to_ids(roles_map.get("turista"))
        is_cittadino = any(r.id in cittadino_id for r in after.roles) if cittadino_id else False
        is_turista   = any(r.id in turista_id   for r in after.roles) if turista_id   else False

        payload: Dict[str, Any] = {}

        if is_cittadino:
            payload["cittadinanza"] = "Cittadino"
        elif is_turista:
            payload["cittadinanza"] = "Turista"

        # --- Lavori (sep_lavori) → prendi il ruolo più alto tra quelli configurati ---
        lavori_ids = _to_ids(roles_map.get("sep_lavori"))
        top_job = _top_role_name(after, lavori_ids)
        payload["lavoro"] = top_job  # può essere None se non ha lavori

        # --- Fazioni (sep_fazioni) ---
        fazioni_ids = _to_ids(roles_map.get("sep_fazioni"))
        payload["fazioni"] = _role_names(after, fazioni_ids)

        # --- Patenti/Licenze (sep_licenze) ---
        licenze_ids = _to_ids(roles_map.get("sep_licenze"))
        payload["patenti_extra"] = _role_names(after, licenze_ids)

        # Applica in un colpo solo
        set_profile(after.id, **payload)

    # 🏦 Esempi helper (se vuoi riusarli altrove)
    async def aggiorna_wallet(self, user_id: int, importo: float):
        prof = get_profile(user_id)
        nuovo = float(prof.get("wallet") or 0) + float(importo)
        set_profile(user_id, wallet=nuovo)

    async def aggiorna_banca(self, user_id: int, importo: float):
        prof = get_profile(user_id)
        bank = dict(prof.get("bank") or {"iban": "", "saldo": 0.0})
        bank["saldo"] = float(bank.get("saldo") or 0) + float(importo)
        set_profile(user_id, bank=bank)


async def setup(bot: commands.Bot):
    await bot.add_cog(ProfiliAuto(bot))