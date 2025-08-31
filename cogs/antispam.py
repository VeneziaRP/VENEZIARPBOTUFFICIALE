import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from collections import deque
from difflib import SequenceMatcher
from typing import Deque, Dict, Set, Tuple

# ============== CONFIG DI BASE ==============
ANTISPAM_ENABLED_DEFAULT = True
WINDOW_SECONDS = 15          # finestra temporale da osservare
REPEAT_THRESHOLD = 5         # quante volte (uguali/simili) prima di agire
SIMILARITY = 0.92            # 1.0 = identici. 0.92 = molto simili
ACTION = "ban"               # "ban" oppure "timeout"
TIMEOUT_SECONDS = 60 * 60    # se ACTION="timeout", durata del mute (1h)
COOLDOWN_AFTER_ACTION = 30   # eviti doppi ban sullo stesso utente per N s
LOG_CHANNEL_ID = 1411054524453486672           # metti l'ID canale log moderazione (0 = off)

# ruoli/canali esclusi dai controlli
EXEMPT_ROLE_IDS: Set[int] = set()      # es. {123, 456}
WHITELIST_CHANNEL_IDS: Set[int] = set()# es. {789}

# ============================================

def _similar(a: str, b: str) -> float:
    return SequenceMatcher(a=a, b=b).ratio()

class AntiSpam(commands.Cog):
    """Auto-ban/timeout per spam ripetuto (stesso messaggio tante volte in poco)."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.enabled_guilds: Set[int] = set()  # guild con antispam ON
        self.buffers: Dict[Tuple[int, int], Deque[Tuple[float, str]]] = {}
        self.cooldown_users: Dict[Tuple[int, int], float] = {}  # (guild_id, user_id) -> unlock_ts

    # ----------------- UTIL -----------------
    def _is_exempt(self, member: discord.Member, channel: discord.abc.GuildChannel) -> bool:
        if isinstance(channel, discord.Thread):
            ch = channel.parent or channel
        else:
            ch = channel
        if ch.id in WHITELIST_CHANNEL_IDS:
            return True
        if any(r.id in EXEMPT_ROLE_IDS or r.permissions.administrator for r in member.roles):
            return True
        return False

    async def _log(self, guild: discord.Guild, text: str, embed: discord.Embed | None = None):
        if LOG_CHANNEL_ID:
            ch = guild.get_channel(LOG_CHANNEL_ID)
            if isinstance(ch, discord.TextChannel):
                try:
                    await ch.send(content=text if not embed else text, embed=embed)
                except Exception:
                    pass

    def _get_buffer(self, guild_id: int, user_id: int) -> Deque[Tuple[float, str]]:
        key = (guild_id, user_id)
        if key not in self.buffers:
            self.buffers[key] = deque(maxlen=50)
        return self.buffers[key]

    # ------------- LISTENER MESSAGGI -------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # ignora DM / bot / no guild
        if not message.guild or message.author.bot:
            return

        gid = message.guild.id
        if ANTISPAM_ENABLED_DEFAULT:
            self.enabled_guilds.add(gid)  # attivo di default
        if gid not in self.enabled_guilds:
            return

        # canali/ruoli esenti
        if isinstance(message.channel, (discord.TextChannel, discord.Thread)):
            member = message.author if isinstance(message.author, discord.Member) else message.guild.get_member(message.author.id)
            if member and self._is_exempt(member, message.channel):
                return

        # registra messaggio nel buffer
        ts = asyncio.get_event_loop().time()
        buf = self._get_buffer(message.guild.id, message.author.id)
        buf.append((ts, message.content or ""))

        # pulisci vecchi
        while buf and ts - buf[0][0] > WINDOW_SECONDS:
            buf.popleft()

        # conta ripetizioni simili nell'ultima finestra
        current = message.content or ""
        if not current.strip():
            return

        similar_count = 0
        for _, text in buf:
            if _similar(text, current) >= SIMILARITY:
                similar_count += 1

        if similar_count >= REPEAT_THRESHOLD:
            # controlla cooldown per non agire più volte
            key = (message.guild.id, message.author.id)
            if self.cooldown_users.get(key, 0) > ts:
                return
            self.cooldown_users[key] = ts + COOLDOWN_AFTER_ACTION

            # prova ad agire
            try:
                if ACTION == "ban":
                    await message.guild.ban(message.author, reason="Auto-ban AntiSpam (messaggi ripetuti)")
                    action_done = "BAN"
                elif ACTION == "timeout":
                    until = discord.utils.utcnow() + discord.timedelta(seconds=TIMEOUT_SECONDS)
                    await message.author.timeout(until, reason="Auto-timeout AntiSpam (messaggi ripetuti)")
                    action_done = f"TIMEOUT {TIMEOUT_SECONDS//60}m"
                else:
                    action_done = "FLAG"
                # log embed
                emb = discord.Embed(
                    title="🚨 AntiSpam Triggered",
                    description=f"{message.author.mention} (`{message.author.id}`) — **{action_done}**",
                    color=discord.Color.red()
                )
                emb.add_field(name="Canale", value=message.channel.mention)
                emb.add_field(name="Finestra", value=f"{WINDOW_SECONDS}s")
                emb.add_field(name="Soglia", value=f"{REPEAT_THRESHOLD}× (sim ≥ {SIMILARITY:.2f})")
                emb.add_field(name="Ultimo messaggio", value=(current[:256] + ("…" if len(current) > 256 else "")), inline=False)
                emb.set_thumbnail(url=message.author.display_avatar.url)
                emb.timestamp = discord.utils.utcnow()
                await self._log(message.guild, " ", emb)
            except discord.Forbidden:
                await self._log(message.guild, f"⚠️ AntiSpam: non ho permessi per agire su {message.author} (serve **Ban Members** o **Moderate Members**).")
            except Exception as e:
                await self._log(message.guild, f"❌ AntiSpam errore su {message.author}: `{e}`")

    # ------------- COMANDI ADMIN -------------
    group = app_commands.Group(name="antispam", description="Controlli e settaggi AntiSpam")

    @group.command(name="on", description="Attiva l'AntiSpam in questo server.")
    @app_commands.default_permissions(administrator=True)
    async def antispam_on(self, interaction: discord.Interaction):
        self.enabled_guilds.add(interaction.guild_id)
        await interaction.response.send_message("🛡️ AntiSpam **ATTIVATO** in questo server.", ephemeral=True)

    @group.command(name="off", description="Disattiva l'AntiSpam in questo server.")
    @app_commands.default_permissions(administrator=True)
    async def antispam_off(self, interaction: discord.Interaction):
        self.enabled_guilds.discard(interaction.guild_id)
        await interaction.response.send_message("🛡️ AntiSpam **DISATTIVATO** in questo server.", ephemeral=True)

    @group.command(name="status", description="Mostra lo stato AntiSpam e i parametri correnti.")
    @app_commands.default_permissions(administrator=True)
    async def antispam_status(self, interaction: discord.Interaction):
        emb = discord.Embed(title="🛡️ AntiSpam — Stato", color=discord.Color.green())
        emb.add_field(name="Attivo", value="Sì" if interaction.guild_id in self.enabled_guilds else "No")
        emb.add_field(name="Finestra", value=f"{WINDOW_SECONDS}s")
        emb.add_field(name="Soglia", value=f"{REPEAT_THRESHOLD}×")
        emb.add_field(name="Similarità", value=f"{SIMILARITY:.2f}")
        emb.add_field(name="Azione", value=f"{ACTION} ({TIMEOUT_SECONDS//60}m timeout)" if ACTION=="timeout" else ACTION)
        emb.add_field(name="Log Channel", value=str(LOG_CHANNEL_ID))
        if EXEMPT_ROLE_IDS:
            emb.add_field(name="Ruoli esenti", value=", ".join(map(str, EXEMPT_ROLE_IDS)), inline=False)
        if WHITELIST_CHANNEL_IDS:
            emb.add_field(name="Canali whitelist", value=", ".join(map(str, WHITELIST_CHANNEL_IDS)), inline=False)
        await interaction.response.send_message(embed=emb, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AntiSpam(bot))