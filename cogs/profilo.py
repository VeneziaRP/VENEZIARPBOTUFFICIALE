# cogs/profilo.py
from __future__ import annotations
import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone

import discord
from discord.ext import commands
from discord import app_commands

from utils.profili import get_profile, money_fmt, mask_iban

ROLES_FILE = Path("data/roles.json")
AUTO_DELETE_SECONDS = 120
DIV = "━━━━━━━━━━━━━━━━━━━"  # divider minimal


# ------------------ helpers ------------------

def load_roles_map() -> dict:
    if ROLES_FILE.exists():
        try:
            return json.loads(ROLES_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def is_staff_member(member: discord.Member, roles_map: dict) -> bool:
    staff_ids = (roles_map.get("groups") or {}).get("staff", []) or []
    try:
        staff_ids = {int(x) for x in staff_ids}
    except Exception:
        staff_ids = set()
    return member.guild_permissions.manage_guild or any(r.id in staff_ids for r in member.roles)

def fmt_ts(dt: datetime | None) -> str:
    if not dt:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    ts = int(dt.timestamp())
    return f"<t:{ts}:D> • <t:{ts}:R>"

def username_tag(m: discord.Member) -> str:
    if m.discriminator and m.discriminator != "0":
        return f"{m.name}#{m.discriminator}"
    return m.name

def _ids(roles_map: dict, key: str) -> list[int]:
    raw = roles_map.get(key)
    if not raw:
        return []
    if isinstance(raw, int):
        raw = [raw]
    out = []
    for x in raw:
        try:
            out.append(int(x))
        except Exception:
            pass
    return out

def roles_in_section(member: discord.Member, ids: list[int]) -> list[discord.Role]:
    sid = set(ids or [])
    return [r for r in sorted(member.roles, key=lambda r: r.position, reverse=True) if r.id in sid]

def make_embed(member: discord.Member, guild: discord.Guild | None, title: str, lines: list[str]) -> discord.Embed:
    color = (member.top_role.color if member.top_role and member.top_role.color.value else discord.Color.blurple())
    emb = discord.Embed(title=title, description="\n".join(lines), color=color)
    emb.set_thumbnail(url=member.display_avatar.url)
    if guild and guild.icon:
        emb.set_footer(text="VeneziaRP | Scheda profilo", icon_url=guild.icon.url)
    else:
        emb.set_footer(text="VeneziaRP | Scheda profilo")
    return emb

def main_badges(member: discord.Member, roles_map: dict, prof: dict) -> str:
    staff_ids = (roles_map.get("groups") or {}).get("staff", []) or []
    is_staff  = any(r.id in staff_ids or r.permissions.manage_guild for r in member.roles)
    is_boost  = bool(getattr(member, "premium_since", None))
    rid_citt  = roles_map.get("cittadino")
    rid_tur   = roles_map.get("turista")

    badges = []
    if rid_citt and any(r.id == rid_citt for r in member.roles): badges.append("🏛️ Cittadino")
    elif rid_tur and any(r.id == rid_tur for r in member.roles): badges.append("🧳 Turista")
    if is_staff:  badges.append("🛡️ Staff")
    if is_boost:  badges.append("💎 Booster")
    if member.bot: badges.append("🤖 Bot")
    return " • ".join(badges) if badges else "—"


# ---------- section renderers ----------

def render_overview(member: discord.Member, roles_map: dict, prof: dict, guild: discord.Guild | None) -> discord.Embed:
    staff_ids = (roles_map.get("groups") or {}).get("staff", []) or []
    staff_roles = [r for r in member.roles if r.id in staff_ids]
    staff_top = max(staff_roles, key=lambda r: r.position, default=None)

    lines = [
        DIV,
        f"⭐ **Badge:** {main_badges(member, roles_map, prof)}",
        f"🆔 **Utente:** {username_tag(member)}",
        f"📅 **Discord:** {fmt_ts(member.created_at)}",
        f"🏠 **VeneziaRP:** {fmt_ts(member.joined_at)}",
    ]
    if staff_top:
        lines.append(f"⚔️ **Staff:** {staff_top.mention}")

    return make_embed(member, guild, f"👤 Profilo — {member.display_name}", lines)

def render_docs(member: discord.Member, prof: dict, guild: discord.Guild | None) -> discord.Embed:
    pda = (prof.get("docs") or {}).get("porto_armi") or {}
    pda_line = ""
    if pda.get("stato"):
        pda_line = (
            f"\n🔫 **Porto d’Armi:** **{pda.get('numero','—')}**"
            f"{(' • Tipo: '+pda.get('tipo')) if pda.get('tipo') else ''}"
            f"{(' • Scadenza: '+pda.get('scadenza')) if pda.get('scadenza') else ''}"
        )
    lines = [
        DIV,
        f"📄 **Carta identità:** {prof.get('identity_card') or '—'}",
        f"👤 **Nome RP:** {prof.get('nome_rp') or '—'}",
        f"🎂 **Data di nascita:** {prof.get('data_nascita') or '—'}",
        f"📞 **Telefono:** {prof.get('telefono') or '—'}",
        f"🌍 **Nazionalità:** {prof.get('nazionalita') or '—'}",
        f"🏛️ **Cittadinanza:** {prof.get('cittadinanza') or '—'}",
    ]
    if pda_line:
        lines.append(pda_line)
    return make_embed(member, guild, f"🪪  Documenti — {member.display_name}", lines)

def render_licenses(member: discord.Member, prof: dict, guild: discord.Guild | None) -> discord.Embed:
    pats = ((prof.get("docs") or {}).get("patenti") or {})
    def _row(label_emoji: str, key: str) -> str:
        data = pats.get(key) or {}
        ok = bool(data.get("stato"))
        if not ok:
            return f"{label_emoji} — ❌"
        return (
            f"{label_emoji} — ✅"
            f"\n• Numero: {data.get('numero','—')}"
            f"\n• Rilascio: {data.get('rilasciata_il','—')}"
            f"\n• Scadenza: {data.get('scadenza','—')}"
        )
    lines = [
        DIV,
        _row("🏍️ **Patente A**", "A"),
        "",
        _row("🚗 **Patente B**", "B"),
        "",
        _row("🚛 **Patente C**", "C"),
        "",
        _row("⛴️ **Nautica**", "NAUTICA"),
    ]
    return make_embed(member, guild, f"🚗 Patenti & Licenze — {member.display_name}", lines)

def render_work(member: discord.Member, prof: dict, roles_map: dict, guild: discord.Guild | None) -> discord.Embed:
    lavori_ids = _ids(roles_map, "sep_lavori")
    lavori_ruoli = roles_in_section(member, lavori_ids)
    lavoro_name = ", ".join(r.name for r in lavori_ruoli) or (prof.get("lavoro") or prof.get("lavoro_rp") or "—")
    dip = prof.get("dipartimento") or prof.get("dip") or "—"
    assunto = prof.get("assunto_il") or prof.get("assunzione") or ""
    lines = [
        DIV,
        f"👔 **Professione:** {lavoro_name}",
        f"🏛️ **Dipartimento:** {dip}",
    ]
    if assunto:
        lines.append(f"📅 **Assunto il:** {assunto}")
    return make_embed(member, guild, f"💼  Lavoro — {member.display_name}", lines)

def render_bank(member: discord.Member, prof: dict, guild: discord.Guild | None) -> discord.Embed:
    bank = prof.get("bank") or {}
    wallet = money_fmt(prof.get("wallet"))
    saldo  = money_fmt(bank.get("saldo"))
    iban   = mask_iban(bank.get("iban") or prof.get("iban"))
    lines = [
        DIV,
        f"💳 **Portafoglio:** {wallet}",
        f"🏦 **Conto:** {saldo}",
        f"📄 **IBAN:** `{iban}`",
    ]
    return make_embed(member, guild, f"🏦  Banca — {member.display_name}", lines)

def render_assets(member: discord.Member, prof: dict, guild: discord.Guild | None) -> discord.Embed:
    pr = prof.get("proprieta") or {}
    def _list_lines(title, items):
        if not items:
            return f"{title}:\n—"
        out = [f"{title}:"]
        for i in items:
            out.append("• " + (str(i)))
        return "\n".join(out)
    lines = [
        DIV,
        _list_lines("🏡 **Case**", pr.get("case") or []),
        "",
        _list_lines("🏭 **Aziende**", pr.get("aziende") or []),
        "",
        _list_lines("🌾 **Terreni**", pr.get("terreni") or []),
        "",
        _list_lines("💎 **Beni di Lusso**", pr.get("lusso") or pr.get("beni_lusso") or []),
    ]
    return make_embed(member, guild, f"🏠  Proprietà — {member.display_name}", lines)

def render_awards(member: discord.Member, prof: dict, guild: discord.Guild | None) -> discord.Embed:
    rec = prof.get("riconoscimenti") or []
    if not rec:
        body = "Nessun riconoscimento ottenuto."
    else:
        body = "\n".join(
            f"{idx}️⃣ {(r.get('titolo') if isinstance(r, dict) else r)}"
            + (f" — 📅 {r.get('data')}" if isinstance(r, dict) and r.get("data") else "")
            for idx, r in enumerate(rec, start=1)
        )
    lines = [DIV, body]
    return make_embed(member, guild, f"🏅  Riconoscimenti — {member.display_name}", lines)

def render_discord(member: discord.Member, guild: discord.Guild | None) -> discord.Embed:
    booster = "✅ Sì" if getattr(member, "premium_since", None) else "❌ No"
    is_bot  = "✅ Sì" if member.bot else "❌ No"
    lines = [
        DIV,
        f"🆔 **ID Utente:** {member.id}",
        f"📅 **Creato il:** {fmt_ts(member.created_at)}",
        f"🏛️ **Entrato in VeneziaRP:** {fmt_ts(member.joined_at)}",
        f"💎 **Booster:** {booster}",
        f"🤖 **Bot:** {is_bot}",
    ]
    return make_embed(member, guild, f"⚙️  Info Discord — {member.display_name}", lines)


# ---------------- View: un solo messaggio, si edita ----------------

class ProfiloView(discord.ui.View):
    def __init__(self, owner_id: int, member: discord.Member, roles_map: dict):
        super().__init__(timeout=AUTO_DELETE_SECONDS)
        self.owner_id = owner_id
        self.member = member
        self.roles_map = roles_map

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # proprietario oppure staff
        if interaction.user.id == self.owner_id or is_staff_member(interaction.user, self.roles_map):
            return True
        await interaction.response.send_message("❌ Non puoi usare questo menu.", ephemeral=True)
        return False

    @discord.ui.select(
        placeholder="Apri una sezione…",
        options=[
            discord.SelectOption(label="Profilo", value="overview", emoji="👤"),
            discord.SelectOption(label="Documenti", value="docs", emoji="🪪"),
            discord.SelectOption(label="Patenti & Licenze", value="licenses", emoji="🚗"),
            discord.SelectOption(label="Lavoro", value="work", emoji="💼"),
            discord.SelectOption(label="Banca", value="bank", emoji="🏦"),
            discord.SelectOption(label="Proprietà", value="assets", emoji="🏠"),
            discord.SelectOption(label="Riconoscimenti", value="awards", emoji="🏅"),
            discord.SelectOption(label="Info Discord", value="discord", emoji="⚙️"),
        ]
    )
    async def select_section(self, interaction: discord.Interaction, select: discord.ui.Select):
        guild = interaction.guild
        prof = get_profile(self.member.id)

        v = select.values[0]
        if v == "overview":
            emb = render_overview(self.member, self.roles_map, prof, guild)
        elif v == "docs":
            emb = render_docs(self.member, prof, guild)
        elif v == "licenses":
            emb = render_licenses(self.member, prof, guild)
        elif v == "work":
            emb = render_work(self.member, prof, self.roles_map, guild)
        elif v == "bank":
            emb = render_bank(self.member, prof, guild)
        elif v == "assets":
            emb = render_assets(self.member, prof, guild)
        elif v == "awards":
            emb = render_awards(self.member, prof, guild)
        else:
            emb = render_discord(self.member, guild)

        await interaction.response.edit_message(embed=emb, view=self)


# ---------------- Command ----------------

class Profilo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="profilo",
        description="Mostra il profilo VeneziaRP. (Se sei staff puoi indicare un utente.)"
    )
    @app_commands.describe(utente="Utente di cui mostrare il profilo (solo staff).")
    async def profilo(self, itx: discord.Interaction, utente: discord.Member | None = None):
        roles_map = load_roles_map()

        target: discord.Member = utente or itx.user  # type: ignore
        if utente and utente.id != itx.user.id and not is_staff_member(itx.user, roles_map):
            await itx.response.send_message("❌ Puoi vedere solo il **tuo** profilo.", ephemeral=True)
            return

        prof = get_profile(target.id)
        emb = render_overview(target, roles_map, prof, itx.guild)
        view = ProfiloView(owner_id=itx.user.id, member=target, roles_map=roles_map)

        # ✅ Risposta immediata (niente defer)
        await itx.response.send_message(
            embed=emb,
            view=view,
            allowed_mentions=discord.AllowedMentions.none()
        )

        # Auto-delete
        msg = await itx.original_response()
        async def _auto():
            try:
                await asyncio.sleep(AUTO_DELETE_SECONDS)
                await msg.delete()
            except (discord.NotFound, discord.Forbidden):
                pass
        asyncio.create_task(_auto())


async def setup(bot: commands.Bot):
    await bot.add_cog(Profilo(bot))