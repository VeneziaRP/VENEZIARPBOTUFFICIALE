import json
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands

ROLES_FILE = Path("data/roles.json")
ROLES_FILE.parent.mkdir(parents=True, exist_ok=True)

# ========= SCHEMA COMPLETO RUOLI =========
# Puoi modificare nomi/colori senza toccare il resto.
SCHEMA = [
    # ===== Gestione alta =====
    {"key":"fondatore",           "name":"👑 Fondatore",              "color":"#f1c40f", "perms":"admin"},
    {"key":"co_fondatore",        "name":"👥 Co-Fondatore",           "color":"#f39c12", "perms":"manager"},
    {"key":"owner",               "name":"🔑 Owner",                  "color":"#f39c12", "perms":"manager"},
    {"key":"co_owner",            "name":"🔑 Co-Owner",               "color":"#e67e22", "perms":"manager"},
    {"key":"amministrazione",     "name":"🛡 Amministrazione",        "color":"#e67e22", "perms":"manager"},
    {"key":"responsabile_staff",  "name":"🧑‍💼 Responsabile Staff",     "color":"#9b59b6", "perms":"manager_lite"},
    {"key":"supervisore",         "name":"🎯 Supervisore",            "color":"#8e44ad", "perms":"manager_lite"},
    {"key":"community_manager",   "name":"🌐 Community Manager",      "color":"#2980b9", "perms":"manager_lite"},

    # ===== Staff operativo =====
    {"key":"recruiter_staff",     "name":"🤝 Recruiter Staff",       "color":"#27ae60", "perms":"mod"},
    {"key":"trainer",             "name":"🎓 Trainer / Formatore",   "color":"#2ecc71", "perms":"mod"},
    {"key":"admin_sr",            "name":"🔧 Admin Sr",              "color":"#2980b9", "perms":"mod_plus"},
    {"key":"admin",               "name":"🔧 Admin",                 "color":"#3498db", "perms":"mod_plus"},
    {"key":"admin_jr",            "name":"🔧 Admin Jr",              "color":"#5dade2", "perms":"mod_plus"},
    {"key":"moderatore_sr",       "name":"🛡 Moderatore Sr",          "color":"#16a085", "perms":"mod"},
    {"key":"moderatore",          "name":"🛡 Moderatore",             "color":"#1abc9c", "perms":"mod"},
    {"key":"moderatore_jr",       "name":"🛡 Moderatore Jr",          "color":"#48c9b0", "perms":"mod"},
    {"key":"helper",              "name":"🟡 Helper",                "color":"#f4d03f", "perms":"helper"},
    {"key":"staffer",             "name":"🟢 Staffer",               "color":"#27ae60", "perms":"mod"},
    {"key":"staffer_ferie",       "name":"💤 Staffer in ferie",       "color":"#7f8c8d", "perms":"none"},

    # ===== Separatori (solo estetica) =====
    {"key":"sep_staff",           "name":"— STAFF —",                "color":"#95a5a6", "perms":"none"},
    {"key":"sep_fazioni",         "name":"— FAZIONI —",              "color":"#95a5a6", "perms":"none"},
    {"key":"sep_lavori",          "name":"— LAVORI —",               "color":"#95a5a6", "perms":"none"},
    {"key":"sep_economy",         "name":"— ECONOMY —",              "color":"#95a5a6", "perms":"none"},
    {"key":"sep_pings",           "name":"— PINGS —",                "color":"#95a5a6", "perms":"none"},
    {"key":"sep_speciali",        "name":"— RUOLI SPECIALI —",       "color":"#95a5a6", "perms":"none"},

    # ===== Dipartimenti extra =====
    {"key":"grafico",             "name":"🎨 Grafico / Designer",    "color":"#9b59b6", "perms":"none"},
    {"key":"content_creator",     "name":"🎥 Content Creator",       "color":"#8e44ad", "perms":"none"},
    {"key":"pr",                  "name":"📢 Comunicazioni / PR",    "color":"#e67e22", "perms":"none"},
    {"key":"developer_bot",       "name":"💻 Developer BOT",         "color":"#2ecc71", "perms":"none"},
    {"key":"tester_qa",           "name":"🧪 Tester / QA",           "color":"#16a085", "perms":"none"},
    {"key":"event_manager",       "name":"🎟 Event Manager",         "color":"#d35400", "perms":"none"},

    # ===== Fazioni RP =====
    {"key":"capo_fazione",        "name":"👑 Capo di una Fazione",   "color":"#9b59b6", "perms":"none"},
    {"key":"polizia_stato",       "name":"🚓 Polizia di Stato",      "color":"#3498db", "perms":"none"},
    {"key":"carabinieri",         "name":"🚔 Carabinieri",           "color":"#e74c3c", "perms":"none"},
    {"key":"guardia_finanza",     "name":"💰 Guardia di Finanza",    "color":"#f1c40f", "perms":"none"},
    {"key":"vigili_fuoco",        "name":"🚒 Vigili del Fuoco",      "color":"#e67e22", "perms":"none"},
    {"key":"croce_bianca",        "name":"🚑 Croce Bianca Venezia",  "color":"#e74c3c", "perms":"none"},
    {"key":"polizia_municipale",  "name":"🏙 Polizia Municipale",    "color":"#2ecc71", "perms":"none"},

    # ===== Lavori & Economy =====
    {"key":"concessionario",      "name":"👔 Concessionario",        "color":"#d35400", "perms":"none"},
    {"key":"magistrato",          "name":"⚖ Magistrato",            "color":"#95a5a6", "perms":"none"},
    {"key":"economy_fdo",         "name":"⚙ Economy FDO",           "color":"#27ae60", "perms":"none"},
    {"key":"economy_medici",      "name":"🏥 Economy Medici",        "color":"#16a085", "perms":"none"},

    # ===== Utenti =====
    {"key":"turista",             "name":"🟢 Turista di Venezia",    "color":"#2ecc71", "perms":"member"},
    {"key":"cittadino",           "name":"🏠 Cittadino di Venezia",  "color":"#1abc9c", "perms":"member"},
    {"key":"attesa_whitelist",    "name":"⏳ Attesa-Whitelist",      "color":"#e67e22", "perms":"none"},
    {"key":"non_verificato",      "name":"🔴 non verificato",        "color":"#c0392b", "perms":"none"},
    {"key":"muted",               "name":"🚫 muted",                 "color":"#7f8c8d", "perms":"muted"},

    # ===== Pings =====
    {"key":"annunci",             "name":"📢 Annunci",               "color":"#f1c40f", "perms":"none", "mentionable":True},
    {"key":"eventi",              "name":"🔔 Eventi",                "color":"#f39c12", "perms":"none", "mentionable":True},
    {"key":"attivita_game",       "name":"🟡 Attività Game",         "color":"#f4d03f", "perms":"none", "mentionable":True},
    {"key":"changelogs",          "name":"🛠 Changelogs",            "color":"#f7dc6f", "perms":"none", "mentionable":True},

    # ===== Speciali =====
    {"key":"server_booster",      "name":"💎 VRP | Server Booster",  "color":"#9b59b6", "perms":"none"},
    {"key":"membro_speciale",     "name":"⭐ VRP | Membro Speciale",  "color":"#e67e22", "perms":"none"},
    {"key":"membro_vip",          "name":"🎖 VRP | Membro VIP",       "color":"#e67e22", "perms":"none"},

    # ===== Bot =====
    {"key":"bot",                 "name":"🤖 BOT",                   "color":"#3498db", "perms":"bot"},
]

# -------- Ordine gerarchico desiderato (alto -> basso) --------
ORDER_KEYS = [
    # Gestione alta
    "fondatore","co_fondatore","owner","co_owner","amministrazione",
    "responsabile_staff","supervisore","community_manager",
    # Staff operativo
    "recruiter_staff","trainer","admin_sr","admin","admin_jr",
    "moderatore_sr","moderatore","moderatore_jr","helper","staffer","staffer_ferie",
    "sep_staff",
    # Dipartimenti
    "grafico","content_creator","pr","developer_bot","tester_qa","event_manager",
    # Fazioni RP
    "sep_fazioni","capo_fazione","polizia_stato","carabinieri","guardia_finanza",
    "vigili_fuoco","croce_bianca","polizia_municipale",
    # Lavori/Economy
    "sep_lavori","concessionario","magistrato",
    "sep_economy","economy_fdo","economy_medici",
    # Speciali
    "sep_speciali","server_booster","membro_speciale","membro_vip",
    # Pings
    "sep_pings","annunci","eventi","attivita_game","changelogs",
    # Bot e utenti
    "bot","muted","cittadino","turista","attesa_whitelist","non_verificato",
    # @everyone sempre ultimo
]

# -------- Set permessi riutilizzabili --------
def permset(kind: str) -> discord.Permissions:
    if kind == "admin":
        return discord.Permissions(administrator=True)
    if kind == "manager":
        return discord.Permissions(
            manage_guild=True, manage_roles=True, manage_channels=True,
            view_audit_log=True, ban_members=True, kick_members=True,
            manage_messages=True, moderate_members=True, move_members=True,
            mute_members=True, deafen_members=True, manage_threads=True,
        )
    if kind == "manager_lite":
        return discord.Permissions(
            manage_messages=True, moderate_members=True, kick_members=True, ban_members=True,
            move_members=True, mute_members=True, deafen_members=True, manage_threads=True,
        )
    if kind == "mod_plus":
        return discord.Permissions(
            manage_messages=True, moderate_members=True, kick_members=True, ban_members=True,
            move_members=True, mute_members=True, deafen_members=True, manage_threads=True,
        )
    if kind == "mod":
        return discord.Permissions(
            manage_messages=True, moderate_members=True, manage_threads=True,
            move_members=True, mute_members=True, deafen_members=True,
        )
    if kind == "helper":
        return discord.Permissions(manage_messages=True)
    if kind == "member":
        return discord.Permissions(
            send_messages=True, read_message_history=True, attach_files=True,
            embed_links=True, add_reactions=True, use_external_emojis=True,
            connect=True, speak=True, create_public_threads=True,
            create_private_threads=True, send_messages_in_threads=True,
        )
    if kind == "muted":
        return discord.Permissions(send_messages=False, add_reactions=False, speak=False)
    if kind == "bot":
        return discord.Permissions(administrator=True)
    return discord.Permissions.none()

# =============== COG ===============
class SetupRuoliCompleto(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -- utils --
    def _save_ids(self, mapping: dict):
        ROLES_FILE.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")

    def _load_ids(self) -> dict:
        if ROLES_FILE.exists():
            try:
                return json.loads(ROLES_FILE.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    async def _ensure_role(self, guild: discord.Guild, spec: dict) -> discord.Role:
        # cerca per nome (case-insensitive)
        role = discord.utils.find(lambda r: r.name.lower()==spec["name"].lower(), guild.roles)
        perms = permset(spec["perms"])
        color = discord.Color.from_str(spec["color"])
        mentionable = spec.get("mentionable", False)

        if role is None:
            role = await guild.create_role(
                name=spec["name"], permissions=perms, color=color,
                mentionable=mentionable, reason="Setup ruoli completo"
            )
        else:
            try:
                await role.edit(
                    permissions=perms, color=color, mentionable=mentionable,
                    reason="Allineamento ruoli completo"
                )
            except discord.Forbidden:
                pass
        return role

    async def _order_roles(self, guild: discord.Guild, id_map: dict):
        """Ordina i ruoli secondo ORDER_KEYS (per quanto consentito dal ruolo più alto del bot)."""
        roles = {k: guild.get_role(v) for k, v in id_map.items() if isinstance(v, int) and guild.get_role(v)}
        sequence = [roles[k] for k in ORDER_KEYS if k in roles]

        # Spostiamo dal basso verso l'alto per stabilizzare l'ordine.
        top = len(guild.roles) - 1
        for i, role in enumerate(reversed(sequence)):
            try:
                await role.edit(position=top - i, reason="Ordine ruoli (schema)")
            except discord.Forbidden:
                pass
            except Exception:
                pass

    # -- comandi --
    @app_commands.default_permissions(administrator=True)
    @app_commands.command(name="setup_ruoli_completo", description="Crea/aggiorna tutti i ruoli e salva gli ID.")
    async def setup_ruoli_completo(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        g = interaction.guild
        if not g:
            return await interaction.followup.send("Usa questo comando in un server.", ephemeral=True)

        ids = self._load_ids()
        for spec in SCHEMA:
            role = await self._ensure_role(g, spec)
            ids[spec["key"]] = role.id

        # Salva anche gruppi utili per altri cogs
        ids["groups"] = {
            "staff": [ids[k] for k in [
                "fondatore","co_fondatore","owner","co_owner","amministrazione",
                "responsabile_staff","supervisore","community_manager",
                "recruiter_staff","trainer","admin_sr","admin","admin_jr",
                "moderatore_sr","moderatore","moderatore_jr","helper","staffer"
            ] if k in ids],
            "utenti": [ids[k] for k in ["cittadino","turista","attesa_whitelist","non_verificato","muted"] if k in ids],
            "fazioni": [ids[k] for k in [
                "capo_fazione","polizia_stato","carabinieri","guardia_finanza","vigili_fuoco","croce_bianca","polizia_municipale"
            ] if k in ids],
            "dipartimenti": [ids[k] for k in ["grafico","content_creator","pr","developer_bot","tester_qa","event_manager"] if k in ids],
            "ping": [ids[k] for k in ["annunci","eventi","attivita_game","changelogs"] if k in ids],
            "speciali": [ids[k] for k in ["server_booster","membro_speciale","membro_vip"] if k in ids],
        }
        self._save_ids(ids)

        await interaction.followup.send(
            f"✅ Ruoli creati/allineati: **{len(SCHEMA)}**. Salvati in `data/roles.json`.",
            ephemeral=True
        )

    @app_commands.default_permissions(administrator=True)
    @app_commands.command(name="ruoli_ordina", description="Ordina i ruoli secondo la gerarchia consigliata.")
    async def ruoli_ordina(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        g = interaction.guild
        ids = self._load_ids()
        if not ids:
            return await interaction.followup.send("Prima esegui `/setup_ruoli_completo`.", ephemeral=True)
        await self._order_roles(g, ids)
        await interaction.followup.send("✅ Gerarchia ordinata (per quanto consentito dal ruolo del bot).", ephemeral=True)

    @app_commands.default_permissions(administrator=True)
    @app_commands.command(name="ruoli_report", description="Mostra un riepilogo dei ruoli salvati.")
    async def ruoli_report(self, interaction: discord.Interaction):
        ids = self._load_ids()
        if not ids:
            return await interaction.response.send_message("Nessun dato: esegui `/setup_ruoli_completo`.", ephemeral=True)
        lines = [f"{spec['name']}: {ids.get(spec['key'])}" for spec in SCHEMA]
        await interaction.response.send_message("```\n" + "\n".join(lines) + "\n```", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(SetupRuoliCompleto(bot))