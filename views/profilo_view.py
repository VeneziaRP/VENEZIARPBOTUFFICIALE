# views/profilo_view.py
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

import discord
from utils.profili import get_profile, money_fmt, mask_iban

ROLES_FILE = Path("data/roles.json")

def load_roles_map() -> dict:
    if ROLES_FILE.exists():
        try:
            return json.loads(ROLES_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _ids(roles_map: dict, key: str) -> list[int]:
    aliases = [key]
    if key == "sep_licenze":
        aliases.append("licenze")
    raw = None
    for k in aliases:
        raw = roles_map.get(k)
        if raw:
            break
    if raw is None:
        return []
    if isinstance(raw, int):
        raw = [raw]
    out: list[int] = []
    for x in raw:
        try: out.append(int(x))
        except: pass
    return out

def _roles_in(member: discord.Member, id_list: list[int]) -> list[discord.Role]:
    s = set(id_list or [])
    return [r for r in sorted(member.roles, key=lambda r: r.position, reverse=True) if r.id in s]

def _fmt_ts(dt: datetime | None) -> str:
    if not dt:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    ts = int(dt.timestamp())
    return f"<t:{ts}:D> • <t:{ts}:R>"

SECTIONS = [
    ("banca",      "🏦 Banca"),
    ("anagrafica", "🪪 Anagrafica"),
    ("documenti",  "📄 Documenti"),
    ("lavoro",     "💼 Lavoro"),
    ("fazioni",    "📂 Fazioni"),
    ("licenze",    "🚗 Patenti/Licenze"),
    ("proprieta",  "🏠 Proprietà"),
    ("riconosc",   "🏅 Riconoscimenti"),
    ("discord",    "⚙️ Info Discord"),
    ("tutto",      "📖 Tutto"),
]

def _base(member: discord.Member, title: str) -> discord.Embed:
    color = member.top_role.color if member.top_role and member.top_role.color.value else discord.Color.blurple()
    e = discord.Embed(title=title, color=color)
    e.set_thumbnail(url=member.display_avatar.url)
    return e

def build_section_embed(member: discord.Member, section: str) -> discord.Embed:
    prof  = get_profile(member.id)
    roles = load_roles_map()

    bank  = prof.get("bank") or {}
    props = prof.get("proprieta") or {}
    ricon = prof.get("riconoscimenti") or []

    if section == "banca":
        e = _base(member, f"🏦 Dati bancari — {member.display_name}")
        e.add_field(name="💳 Portafoglio", value=money_fmt(prof.get("wallet")), inline=True)
        e.add_field(name="IBAN", value=mask_iban(bank.get("iban") or prof.get("iban")), inline=True)
        e.add_field(name="💰 Saldo conto", value=money_fmt(bank.get("saldo")), inline=True)
        return e

    if section == "anagrafica":
        e = _base(member, f"🪪 Anagrafica — {member.display_name}")
        e.add_field(name="Carta identità", value=prof.get("identity_card") or "—", inline=True)
        e.add_field(name="Nome RP", value=prof.get("nome_rp") or "—", inline=True)
        e.add_field(name="Data di nascita", value=prof.get("data_nascita") or "—", inline=True)
        e.add_field(name="Stato civile", value=prof.get("stato_civile") or "—", inline=True)
        e.add_field(name="Famiglia", value=prof.get("famiglia") or "—", inline=True)
        e.add_field(name="Cittadinanza", value=prof.get("cittadinanza") or "—", inline=True)
        return e

    if section == "documenti":
        lic_ids   = _ids(roles, "sep_licenze")
        pat_ruoli = ", ".join(r.name for r in _roles_in(member, lic_ids))
        pat_extra = ", ".join(prof.get("patenti_extra") or [])
        tot       = (pat_ruoli + (", " if pat_ruoli and pat_extra else "") + pat_extra) or "—"
        e = _base(member, f"📄 Documenti — {member.display_name}")
        e.add_field(name="Carta identità", value=prof.get("identity_card") or "—", inline=False)
        e.add_field(name="Patenti/Licenze", value=tot, inline=False)
        return e

    if section == "lavoro":
        lav_ids = _ids(roles, "sep_lavori")
        lavori  = _roles_in(member, lav_ids)
        e = _base(member, f"💼 Lavoro — {member.display_name}")
        e.add_field(name="Lavoro corrente", value=", ".join(r.name for r in lavori) or (prof.get("lavoro") or "—"), inline=False)
        return e

    if section == "fazioni":
        f_ids  = _ids(roles, "sep_fazioni")
        faz    = ", ".join(r.name for r in _roles_in(member, f_ids)) or (", ".join(prof.get("fazioni", [])) or "—")
        e = _base(member, f"📂 Fazioni — {member.display_name}")
        e.add_field(name="Fazioni", value=faz, inline=False)
        return e

    if section == "licenze":
        l_ids    = _ids(roles, "sep_licenze")
        pat_ruoli = ", ".join(r.name for r in _roles_in(member, l_ids))
        pat_extra = ", ".join(prof.get("patenti_extra") or [])
        tot       = (pat_ruoli + (", " if pat_ruoli and pat_extra else "") + pat_extra) or "—"
        e = _base(member, f"🚗 Patenti/Licenze — {member.display_name}")
        e.add_field(name="Patenti/Licenze", value=tot, inline=False)
        return e

    if section == "proprieta":
        e = _base(member, f"🏠 Proprietà — {member.display_name}")
        if props.get("case"):
            e.add_field(name="Case", value="\n".join(props["case"]), inline=False)
        if props.get("veicoli"):
            vlist = []
            for v in props["veicoli"]:
                if isinstance(v, dict):
                    vlist.append(f"{v.get('modello','?')} ({v.get('targa','?')})")
                else:
                    vlist.append(str(v))
            e.add_field(name="Veicoli", value="\n".join(vlist), inline=False)
        if props.get("aziende"):
            e.add_field(name="Aziende", value=", ".join(props["aziende"]), inline=False)
        if not e.fields:
            e.add_field(name="Proprietà", value="—", inline=False)
        return e

    if section == "riconosc":
        e = _base(member, f"🏅 Riconoscimenti — {member.display_name}")
        e.add_field(name="Onorificenze", value=("\n".join(ricon) if ricon else "—"), inline=False)
        return e

    if section == "discord":
        e = _base(member, f"⚙️ Info Discord — {member.display_name}")
        e.add_field(name="Iscritto a Discord", value=_fmt_ts(member.created_at), inline=False)
        e.add_field(name="Entrato in server", value=_fmt_ts(member.joined_at), inline=False)
        staff_ids = (load_roles_map().get("groups") or {}).get("staff", [])
        staff_roles = [r for r in member.roles if r.id in (staff_ids or [])] or [r for r in member.roles if getattr(r.permissions, "manage_guild", False)]
        if staff_roles:
            e.add_field(name="Staff", value=max(staff_roles, key=lambda r: r.position).mention, inline=False)
        return e

    # "tutto"
    e = _base(member, f"📖 Profilo completo — {member.display_name}")
    e.add_field(name="Carta identità", value=prof.get("identity_card") or "—", inline=True)
    e.add_field(name="Nome RP", value=prof.get("nome_rp") or "—", inline=True)
    e.add_field(name="Nascita", value=prof.get("data_nascita") or "—", inline=True)
    lav_ids = _ids(roles, "sep_lavori")
    f_ids   = _ids(roles, "sep_fazioni")
    l_ids   = _ids(roles, "sep_licenze")
    e.add_field(name="Lavoro", value=", ".join(r.name for r in _roles_in(member, lav_ids)) or (prof.get("lavoro") or "—"), inline=False)
    e.add_field(name="Fazioni", value=", ".join(r.name for r in _roles_in(member, f_ids)) or (", ".join(prof.get("fazioni", [])) or "—"), inline=False)
    pat_ruoli = ", ".join(r.name for r in _roles_in(member, l_ids))
    pat_extra = ", ".join(prof.get("patenti_extra") or [])
    e.add_field(name="Patenti/Licenze", value=(pat_ruoli + (", " if pat_ruoli and pat_extra else "") + pat_extra) or "—", inline=False)
    e.add_field(name="Portafoglio", value=money_fmt(prof.get("wallet")), inline=True)
    e.add_field(name="IBAN", value=mask_iban(bank.get("iban") or prof.get("iban")), inline=True)
    e.add_field(name="Saldo conto", value=money_fmt(bank.get("saldo")), inline=True)
    if props.get("case"):
        e.add_field(name="Case", value="\n".join(props["case"]), inline=False)
    if props.get("veicoli"):
        vlist = []
        for v in props["veicoli"]:
            if isinstance(v, dict):
                vlist.append(f"{v.get('modello','?')} ({v.get('targa','?')})")
            else:
                vlist.append(str(v))
        e.add_field(name="Veicoli", value="\n".join(vlist), inline=False)
    if ricon:
        e.add_field(name="Riconoscimenti", value="\n".join(ricon), inline=False)
    return e


# ---------- SELECT + VIEWS ----------

class ProfiloSelect(discord.ui.Select):
    def __init__(self, owner_id: int, target: discord.Member):
        self.owner_id = owner_id
        self.target   = target
        options = [discord.SelectOption(label=label, value=key, emoji=label.split(" ")[0]) for key, label in SECTIONS]
        super().__init__(
            placeholder="▾ Scegli cosa vedere…",
            min_values=1, max_values=1,
            options=options,
            custom_id=f"profile_select:{target.id}:{owner_id}"
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id and not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ Non puoi interagire con questo profilo.", ephemeral=True)
            return False
        return True

    async def callback(self, interaction: discord.Interaction):
        section = self.values[0]
        embed   = build_section_embed(self.target, section)
        # ✅ aggiorna lo STESSO messaggio (niente messaggi nuovi)
        await interaction.response.edit_message(embed=embed, view=self.view)

class ProfiloSelectView(discord.ui.View):
    def __init__(self, owner_id: int, target: discord.Member):
        super().__init__(timeout=180)
        self.add_item(ProfiloSelect(owner_id=owner_id, target=target))


class ProfiloMenuView(discord.ui.View):
    """Compatibile con il tuo cogs/profilo.py attuale.
    Mostra il bottone 'Apri schede' e, al click, sostituisce la view con la select
    sullo STESSO messaggio (niente reply sotto)."""
    def __init__(self, owner_id: int, target: discord.Member):
        super().__init__(timeout=180)
        self.owner_id = owner_id
        self.target   = target

    @discord.ui.button(label="Apri schede", emoji="⬇️", style=discord.ButtonStyle.secondary, custom_id="profilo:dropdown")
    async def apri_menu(self, interaction: discord.Interaction, _btn: discord.ui.Button):
        # ✅ sostituisce la view del messaggio originale
        await interaction.response.edit_message(view=ProfiloSelectView(self.owner_id, self.target))