import json
import os
import re
from datetime import timedelta

import discord
from discord.ext import commands
from discord import app_commands

# ========= CONFIGURAZIONE =========
# Metti qui l'ID del canale log moderazione (se 0 -> niente log)
MOD_LOG_CHANNEL_ID = 0  # es. 1401906324932919296

# Percorso file warn (persistente)
WARNS_PATH = "data/warns.json"
# =================================

def _ensure_warns_file():
    os.makedirs(os.path.dirname(WARNS_PATH), exist_ok=True)
    if not os.path.exists(WARNS_PATH):
        with open(WARNS_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f)

def load_warns() -> dict:
    _ensure_warns_file()
    with open(WARNS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_warns(data: dict):
    with open(WARNS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def add_warn(guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
    data = load_warns()
    g = data.setdefault(str(guild_id), {})
    warns = g.setdefault(str(user_id), [])
    warns.append({"mod": moderator_id, "reason": reason})
    save_warns(data)
    return len(warns)

def remove_warns(guild_id: int, user_id: int, amount: int) -> int:
    data = load_warns()
    g = data.setdefault(str(guild_id), {})
    warns = g.setdefault(str(user_id), [])
    removed = min(amount, len(warns))
    if removed:
        del warns[:removed]
        save_warns(data)
    return removed

def get_warns(guild_id: int, user_id: int) -> list:
    data = load_warns()
    return data.get(str(guild_id), {}).get(str(user_id), [])

def parse_duration(text: str) -> timedelta | None:
    """
    Supporta: s (secondi), m (minuti), h (ore), d (giorni)
    Esempi: '30m', '2h', '1d', '45s'
    """
    m = re.fullmatch(r"(\d+)\s*([smhdSMHD])", text.strip())
    if not m:
        return None
    value = int(m.group(1))
    unit = m.group(2).lower()
    if unit == "s":
        return timedelta(seconds=value)
    if unit == "m":
        return timedelta(minutes=value)
    if unit == "h":
        return timedelta(hours=value)
    if unit == "d":
        return timedelta(days=value)
    return None

async def send_modlog(guild: discord.Guild, embed: discord.Embed):
    if MOD_LOG_CHANNEL_ID:
        ch = guild.get_channel(MOD_LOG_CHANNEL_ID)
        if ch and isinstance(ch, discord.TextChannel):
            try:
                await ch.send(embed=embed)
            except Exception:
                pass

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # =============== WARN ===============
    @app_commands.command(name="warn", description="Avvisa un utente con un warn.")
    @app_commands.describe(user="Utente da avvisare", reason="Motivo del warn")
    @app_commands.default_permissions(manage_messages=True)
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        count = add_warn(interaction.guild_id, user.id, interaction.user.id, reason)

        # DM all'utente (best effort)
        try:
            dm = await user.create_dm()
            await dm.send(
                f"⚠️ Sei stato **warnato** in **{interaction.guild.name}** da {interaction.user.mention}.\n"
                f"Motivo: **{reason}**\n"
                f"Warn totali: **{count}**"
            )
        except Exception:
            pass

        emb = discord.Embed(
            title="⚠️ Warn assegnato",
            description=f"{user.mention} ha ricevuto un warn.",
            color=discord.Color.orange()
        )
        emb.add_field(name="Motivo", value=reason, inline=False)
        emb.add_field(name="Warn totali", value=str(count), inline=True)
        emb.add_field(name="Moderatore", value=interaction.user.mention, inline=True)
        emb.set_thumbnail(url=user.display_avatar.url)
        emb.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=emb)
        await send_modlog(interaction.guild, emb)

    @app_commands.command(name="warnings", description="Mostra i warn di un utente.")
    @app_commands.describe(user="Utente")
    @app_commands.default_permissions(manage_messages=True)
    async def warnings(self, interaction: discord.Interaction, user: discord.Member):
        warns = get_warns(interaction.guild_id, user.id)
        if not warns:
            await interaction.response.send_message(f"✅ {user.mention} non ha warn.", ephemeral=True)
            return

        lines = [f"**{i+1}.** {w['reason']} — <@{w['mod']}>"
                 for i, w in enumerate(warns)]
        text = "\n".join(lines[:20])
        if len(lines) > 20:
            text += f"\n… e altri {len(lines)-20}"

        emb = discord.Embed(
            title=f"📄 Warn di {user}",
            description=text,
            color=discord.Color.orange()
        )
        emb.set_thumbnail(url=user.display_avatar.url)
        emb.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @app_commands.command(name="unwarn", description="Rimuove uno o più warn da un utente.")
    @app_commands.describe(user="Utente", amount="Quanti warn rimuovere (default 1)")
    @app_commands.default_permissions(manage_messages=True)
    async def unwarn(self, interaction: discord.Interaction, user: discord.Member, amount: int = 1):
        removed = remove_warns(interaction.guild_id, user.id, amount)
        if removed == 0:
            await interaction.response.send_message("ℹ️ Nessun warn da rimuovere.", ephemeral=True)
            return

        remaining = len(get_warns(interaction.guild_id, user.id))
        emb = discord.Embed(
            title="✅ Warn rimossi",
            description=f"Rimossi **{removed}** warn a {user.mention}.",
            color=discord.Color.green()
        )
        emb.add_field(name="Warn rimanenti", value=str(remaining))
        await interaction.response.send_message(embed=emb)
        await send_modlog(interaction.guild, emb)

    # =============== MUTE (timeout) ===============
    @app_commands.command(name="mute", description="Imposta un timeout su un utente (mute).")
    @app_commands.describe(user="Utente", duration="Durata (es. 10m, 2h, 1d)", reason="Motivo")
    @app_commands.default_permissions(moderate_members=True)
    async def mute(self, interaction: discord.Interaction, user: discord.Member, duration: str, reason: str):
        td = parse_duration(duration)
        if not td:
            await interaction.response.send_message("❌ Durata non valida. Usa es: `10m`, `2h`, `1d`.", ephemeral=True)
            return
        try:
            await user.timeout(discord.utils.utcnow() + td, reason=reason)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Non ho permessi per mutare questo utente.", ephemeral=True)
            return

        emb = discord.Embed(
            title="🔇 Utente mutato (timeout)",
            description=f"{user.mention} è stato mutato per **{duration}**.",
            color=discord.Color.red()
        )
        emb.add_field(name="Motivo", value=reason, inline=False)
        emb.add_field(name="Moderatore", value=interaction.user.mention, inline=True)
        emb.set_thumbnail(url=user.display_avatar.url)
        emb.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=emb)
        await send_modlog(interaction.guild, emb)

    @app_commands.command(name="unmute", description="Rimuove il timeout (mute) da un utente.")
    @app_commands.describe(user="Utente", reason="Motivo (opzionale)")
    @app_commands.default_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, user: discord.Member, reason: str = "Unmute"):
        try:
            await user.timeout(None, reason=reason)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Non ho permessi per smutare questo utente.", ephemeral=True)
            return

        emb = discord.Embed(
            title="🔊 Utente smutato",
            description=f"Rimosso il timeout a {user.mention}.",
            color=discord.Color.green()
        )
        emb.add_field(name="Motivo", value=reason, inline=False)
        emb.add_field(name="Moderatore", value=interaction.user.mention, inline=True)
        emb.set_thumbnail(url=user.display_avatar.url)
        emb.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=emb)
        await send_modlog(interaction.guild, emb)

    # =============== KICK / BAN ===============
    @app_commands.command(name="kick", description="Espelle un utente.")
    @app_commands.describe(user="Utente", reason="Motivo")
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        try:
            await user.kick(reason=reason)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Non ho permessi per kickare questo utente.", ephemeral=True)
            return

        emb = discord.Embed(
            title="👢 Utente espulso",
            description=f"{user.mention} è stato espulso.",
            color=discord.Color.red()
        )
        emb.add_field(name="Motivo", value=reason, inline=False)
        emb.add_field(name="Moderatore", value=interaction.user.mention, inline=True)
        emb.set_thumbnail(url=user.display_avatar.url)
        emb.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=emb)
        await send_modlog(interaction.guild, emb)

    @app_commands.command(name="ban", description="Banna un utente.")
    @app_commands.describe(user="Utente", reason="Motivo", delete_days="Giorni di messaggi da eliminare (0-7, default 0)")
    @app_commands.default_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str, delete_days: app_commands.Range[int, 0, 7] = 0):
        try:
            await interaction.guild.ban(user, reason=reason, delete_message_days=delete_days)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Non ho permessi per bannare questo utente.", ephemeral=True)
            return

        emb = discord.Embed(
            title="⛔ Utente bannato",
            description=f"{user.mention} è stato bannato.",
            color=discord.Color.dark_red()
        )
        emb.add_field(name="Motivo", value=reason, inline=False)
        emb.add_field(name="Elimina messaggi", value=f"{delete_days} giorni", inline=True)
        emb.add_field(name="Moderatore", value=interaction.user.mention, inline=True)
        emb.set_thumbnail(url=user.display_avatar.url)
        emb.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=emb)
        await send_modlog(interaction.guild, emb)

    @app_commands.command(name="unban", description="Sbanna un utente con ID.")
    @app_commands.describe(user_id="ID utente da sbannare", reason="Motivo (opzionale)")
    @app_commands.default_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str = "Unban"):
        try:
            user_obj = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user_obj, reason=reason)
        except discord.NotFound:
            await interaction.response.send_message("❌ Utente non trovato nei ban.", ephemeral=True)
            return
        except ValueError:
            await interaction.response.send_message("❌ ID non valido.", ephemeral=True)
            return

        emb = discord.Embed(
            title="✅ Utente sbannato",
            description=f"È stato rimosso il ban a **{user_obj}**.",
            color=discord.Color.green()
        )
        emb.add_field(name="Motivo", value=reason, inline=False)
        emb.add_field(name="Moderatore", value=interaction.user.mention, inline=True)
        emb.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=emb)
        await send_modlog(interaction.guild, emb)

    # =============== PURGE / SLOWMODE ===============
    @app_commands.command(name="purge", description="Cancella gli ultimi N messaggi.")
    @app_commands.describe(amount="Numero di messaggi da cancellare (1-100)")
    @app_commands.default_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 100]):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"🧹 Eliminati **{len(deleted)}** messaggi.", ephemeral=True)

    @app_commands.command(name="slowmode", description="Imposta la slowmode sul canale.")
    @app_commands.describe(seconds="Secondi (0 per disattivare)", channel="Canale (vuoto = questo)")
    @app_commands.default_permissions(manage_channels=True)
    async def slowmode(self, interaction: discord.Interaction, seconds: app_commands.Range[int, 0, 21600], channel: discord.TextChannel | None = None):
        ch = channel or interaction.channel
        await ch.edit(slowmode_delay=seconds)
        await interaction.response.send_message(f"🐌 Slowmode su {ch.mention}: **{seconds}s**.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))