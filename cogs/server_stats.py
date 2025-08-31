# cogs/server_stats.py
from __future__ import annotations
import json, asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict

import discord
from discord.ext import commands
from discord import app_commands

# ================== CONFIG ==================
# Canale testo dove pubblicare/aggiornare il pannello (OBBLIGATORIO)
STATS_CHANNEL_ID = 1409642533520412702  # <- METTI L'ID del canale testo (es. 1409...)

# Ruoli utenti (per conteggi per-ruolo)
ROLE_TURISTA_ID   = 1408613574150197258
ROLE_CITTADINO_ID = 1408613574850379959

# Sezioni mostrate nell'embed (puoi spegnere ciò che non ti serve)
SHOW_SECTIONS: Dict[str, bool] = {
    "totals": True,        # 👥 Totale, 🧑 Persone, 🤖 Bot
    "presences": True,     # 🟢 Online/🌙 Idle/⛔ DND/⚪ Offline  (serve intent presences)
    "roles": True,         # 🏛️ Cittadini / 🧳 Turisti
    "boosts": True,        # 💎 Booster del server
    "joins": True,         # 📈 Oggi / 📊 7 giorni
    "infra": True,         # 📝 canali, 🔊 voce, 📂 categorie, 🧵 forum, 🎙️ stage, 🎭 ruoli
    "avg_age": True,       # ⏳ Età media account (giorni)
    "last_joined": True,   # 👤 Ultimo iscritto (menzione + quando)
}

# (OPZIONALE) Canali “contatore” da rinominare automaticamente (lascia 0 per disabilitare)
NAME_CHANNELS = {
    "total":   {"id": 0, "label": "👥 Membri"},
    "humans":  {"id": 0, "label": "🧑 Persone"},
    "bots":    {"id": 0, "label": "🤖 Bot"},
    "online":  {"id": 0, "label": "🟢 Online"},
    "boosts":  {"id": 0, "label": "💎 Booster"},
    "today":   {"id": 0, "label": "📈 Oggi"},
    "week":    {"id": 0, "label": "📊 7 giorni"},
}

# Dove salviamo il message_id per non spammare
STATE_FILE = Path("data/stats_msg.json")
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

# Aggiornamento periodico extra (oltre a join/leave)
REFRESH_MINUTES = 1
# ============================================


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def _save_state(data: dict):
    STATE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------- Contatori base ----------
def _count_members(g: discord.Guild) -> tuple[int,int,int]:
    total = g.member_count or len(g.members)
    humans = sum(1 for m in g.members if not m.bot)
    bots = total - humans
    return total, humans, bots

def _count_presences(g: discord.Guild) -> tuple[int,int,int,int]:
    online = idle = dnd = offline = 0
    for m in g.members:
        s = getattr(m, "status", discord.Status.offline)
        if s is discord.Status.online:   online += 1
        elif s is discord.Status.idle:   idle += 1
        elif s is discord.Status.dnd:    dnd += 1
        else:                            offline += 1
    return online, idle, dnd, offline

def _count_boosters(g: discord.Guild) -> int:
    try:
        # premium_subscribers non è sempre popolato; fallback su premium_since
        subs = getattr(g, "premium_subscribers", None)
        if subs is not None:
            return len(subs)
    except Exception:
        pass
    return sum(1 for m in g.members if getattr(m, "premium_since", None))

def _joins_today_week(g: discord.Guild) -> tuple[int,int]:
    now = datetime.now(timezone.utc)
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last7 = now - timedelta(days=7)
    today = week = 0
    for m in g.members:
        ja = getattr(m, "joined_at", None)
        if not ja:
            continue
        if ja >= start_today:
            today += 1
        if ja >= last7:
            week += 1
    return today, week

def _infra_counts(g: discord.Guild) -> tuple[int,int,int,int,int,int]:
    text = voice = category = forum = stage = 0
    for ch in g.channels:
        if isinstance(ch, discord.TextChannel): text += 1
        elif isinstance(ch, discord.VoiceChannel): voice += 1
        elif isinstance(ch, discord.CategoryChannel): category += 1
        elif isinstance(ch, discord.ForumChannel): forum += 1
        elif isinstance(ch, discord.StageChannel): stage += 1
    roles = len(g.roles)
    return text, voice, category, forum, stage, roles

def _avg_account_age_days(g: discord.Guild) -> int:
    now = datetime.now(timezone.utc)
    days = []
    for m in g.members:
        ca = getattr(m, "created_at", None)
        if ca:
            days.append((now - ca).days)
    return int(sum(days)/len(days)) if days else 0

def _last_joined(g: discord.Guild) -> Optional[discord.Member]:
    # ultimo che ha joinato (tra quelli che hanno joined_at)
    members_with_ts = [m for m in g.members if getattr(m, "joined_at", None)]
    if not members_with_ts:
        return None
    return max(members_with_ts, key=lambda x: x.joined_at)  # type: ignore[arg-type]


def _count_by_role(g: discord.Guild, role_id: int) -> int:
    r = g.get_role(role_id)
    return len(r.members) if r else 0


# ---------- Embed ----------
def _fmt_ts(dt: Optional[datetime]) -> str:
    if not dt:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    ts = int(dt.timestamp())
    return f"<t:{ts}:D> • <t:{ts}:R>"

def _build_embed(g: discord.Guild) -> discord.Embed:
    emb = discord.Embed(
        title="📊 Statistiche Server",
        description=f"Panoramica di **{g.name}**",
        color=discord.Color.gold()
    )
    emb.timestamp = datetime.now(timezone.utc)

    if g.icon:
        emb.set_thumbnail(url=g.icon.url)
        emb.set_footer(text="VeneziaRP | Statistiche", icon_url=g.icon.url)
    else:
        emb.set_footer(text="VeneziaRP | Statistiche")

    # Totali
    if SHOW_SECTIONS.get("totals", True):
        tot, hum, bot = _count_members(g)
        emb.add_field(name="👥 Totale membri", value=f"**{tot}**", inline=True)
        emb.add_field(name="🧑 Persone", value=f"**{hum}**", inline=True)
        emb.add_field(name="🤖 Bot", value=f"**{bot}**", inline=True)

    # Ruoli chiave: Cittadini/Turisti
    if SHOW_SECTIONS.get("roles", True):
        c = _count_by_role(g, ROLE_CITTADINO_ID)
        t = _count_by_role(g, ROLE_TURISTA_ID)
        emb.add_field(name="🏛️ Cittadini", value=f"**{c}**", inline=True)
        emb.add_field(name="🧳 Turisti", value=f"**{t}**", inline=True)

    # Presenze (richiede intents.presences abilitati)
    if SHOW_SECTIONS.get("presences", True):
        onl, idl, dnd, off = _count_presences(g)
        emb.add_field(name="🟢 Online", value=f"**{onl}**", inline=True)
        emb.add_field(name="🌙 Idle", value=f"**{idl}**", inline=True)
        emb.add_field(name="⛔ DND", value=f"**{dnd}**", inline=True)
        emb.add_field(name="⚪ Offline", value=f"**{off}**", inline=True)

    # Booster
    if SHOW_SECTIONS.get("boosts", True):
        emb.add_field(name="💎 Booster", value=f"**{_count_boosters(g)}**", inline=True)

    # Join oggi / 7 giorni
    if SHOW_SECTIONS.get("joins", True):
        t, w = _joins_today_week(g)
        emb.add_field(name="📈 Oggi", value=f"**+{t}**", inline=True)
        emb.add_field(name="📊 7 giorni", value=f"**+{w}**", inline=True)

    # Infrastruttura
    if SHOW_SECTIONS.get("infra", True):
        text, voice, category, forum, stage, roles = _infra_counts(g)
        infra_txt = (
            f"📝 Testo **{text}** • 🔊 Voce **{voice}** • 📂 Categorie **{category}**\n"
            f"🧵 Forum **{forum}** • 🎙️ Stage **{stage}** • 🎭 Ruoli **{roles}**"
        )
        emb.add_field(name="🧱 Struttura", value=infra_txt, inline=False)

    # Età account media
    if SHOW_SECTIONS.get("avg_age", True):
        emb.add_field(name="⏳ Età media account", value=f"**{_avg_account_age_days(g)} giorni**", inline=True)

    # Ultimo iscritto
    if SHOW_SECTIONS.get("last_joined", True):
        lj = _last_joined(g)
        if lj:
            emb.add_field(name="👤 Ultimo iscritto", value=f"{lj.mention}\n{_fmt_ts(lj.joined_at)}", inline=False)

    return emb


async def _rename_counter_channel(g: discord.Guild, channel_id: int, base_label: str, value: int):
    if not channel_id:
        return
    ch = g.get_channel(channel_id)
    if not isinstance(ch, (discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.CategoryChannel, discord.ForumChannel)):
        return
    new_name = f"{base_label}: {value}"
    try:
        if ch.name != new_name:
            await ch.edit(name=new_name, reason="Aggiornamento contatore")
    except (discord.Forbidden, discord.HTTPException):
        pass


class ServerStats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._bg_task: asyncio.Task | None = None

    async def cog_load(self):
        self._bg_task = asyncio.create_task(self._periodic_refresh())

    async def cog_unload(self):
        if self._bg_task:
            self._bg_task.cancel()
            try:
                await self._bg_task
            except Exception:
                pass

    async def _update_panel(self, g: discord.Guild):
        if not STATS_CHANNEL_ID:
            return
        ch = g.get_channel(STATS_CHANNEL_ID)
        if not isinstance(ch, discord.TextChannel):
            return

        emb = _build_embed(g)
        state = _load_state()
        gid = str(g.id)
        msg_id = (state.get(gid) or {}).get("message_id")

        try:
            if msg_id:
                try:
                    msg = await ch.fetch_message(int(msg_id))
                    await msg.edit(embed=emb)
                except discord.NotFound:
                    m = await ch.send(embed=emb)
                    state[gid] = {"channel_id": ch.id, "message_id": m.id}
                    _save_state(state)
            else:
                m = await ch.send(embed=emb)
                state[gid] = {"channel_id": ch.id, "message_id": m.id}
                _save_state(state)
        except Exception:
            pass

    async def _update_name_counters(self, g: discord.Guild):
        # Rinominare i canali contatore se configurati
        tot, hum, bot = _count_members(g)
        await _rename_counter_channel(g, NAME_CHANNELS["total"]["id"],  NAME_CHANNELS["total"]["label"],  tot)
        await _rename_counter_channel(g, NAME_CHANNELS["humans"]["id"], NAME_CHANNELS["humans"]["label"], hum)
        await _rename_counter_channel(g, NAME_CHANNELS["bots"]["id"],   NAME_CHANNELS["bots"]["label"],   bot)

        if SHOW_SECTIONS.get("presences", True):
            onl, idl, dnd, off = _count_presences(g)
            await _rename_counter_channel(g, NAME_CHANNELS["online"]["id"], NAME_CHANNELS["online"]["label"], onl)

        if SHOW_SECTIONS.get("boosts", True):
            await _rename_counter_channel(g, NAME_CHANNELS["boosts"]["id"], NAME_CHANNELS["boosts"]["label"], _count_boosters(g))

        if SHOW_SECTIONS.get("joins", True):
            today, week = _joins_today_week(g)
            await _rename_counter_channel(g, NAME_CHANNELS["today"]["id"], NAME_CHANNELS["today"]["label"], today)
            await _rename_counter_channel(g, NAME_CHANNELS["week"]["id"],  NAME_CHANNELS["week"]["label"],  week)

    async def _update_everywhere(self, g: discord.Guild):
        await self._update_panel(g)
        await self._update_name_counters(g)

    # ------ listener: avvio e cambi membri ------
    @commands.Cog.listener()
    async def on_ready(self):
        # aggiorna tutti i server dove è presente
        for g in self.bot.guilds:
            await self._update_everywhere(g)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self._update_everywhere(member.guild)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self._update_everywhere(member.guild)

    # ------ refresh periodico ------
    async def _periodic_refresh(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                for g in self.bot.guilds:
                    await self._update_everywhere(g)
            except Exception:
                pass
            await asyncio.sleep(REFRESH_MINUTES * 60)

    # ------ comando manuale ------
    @app_commands.command(name="server_stats", description="Pubblica o aggiorna il pannello statistiche nel canale configurato.")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def server_stats(self, itx: discord.Interaction):
        if not STATS_CHANNEL_ID:
            return await itx.response.send_message("❌ Configura STATS_CHANNEL_ID in cogs/server_stats.py.", ephemeral=True)
        await itx.response.defer(ephemeral=True)
        await self._update_everywhere(itx.guild)
        await itx.followup.send("✅ Statistiche aggiornate.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ServerStats(bot))