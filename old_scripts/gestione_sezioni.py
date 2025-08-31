import discord
from discord.ext import commands
from discord import app_commands
import json
from pathlib import Path

ROLES_FILE = Path("data/roles.json")

# mappa: sezione_key -> nome leggibile
SEZIONI = {
    "sep_gradi": "📋 Gradi Amministrativi",
    "sep_staff": "🛡️ Staff & Moderazione",
    "sep_fazioni": "📂 Fazioni",
    "sep_lavori": "🧰 Lavori RP",
    "sep_economy": "💸 Economy",
    "sep_licenze": "🪪 Licenze",
    "sep_medaglie": "🏅 Medaglie & Riconoscimenti",
    "sep_pings": "📣 Pings & Eventi",
    "sep_speciali": "💎 Speciali",
    "sep_utenti": "👥 Utenti & Accesso",
}

def load_roles() -> dict:
    if ROLES_FILE.exists():
        try:
            return json.loads(ROLES_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_roles(data: dict):
    ROLES_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

class GestioneSezioni(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.default_permissions(administrator=True)
    @app_commands.command(
        name="aggiungi_ruolo_sezione",
        description="Aggiungi un ruolo esistente a una sezione (per setup_struttura)."
    )
    @app_commands.describe(
        sezione="La sezione in cui inserire il ruolo",
        ruolo="Il ruolo già esistente nel server"
    )
    async def aggiungi_ruolo_sezione(self, itx: discord.Interaction, sezione: str, ruolo: discord.Role):
        roles_map = load_roles()

        # inizializza la lista se manca
        if sezione not in roles_map:
            roles_map[sezione] = []

        # se è un int singolo (vecchio formato), trasformalo in lista
        if isinstance(roles_map[sezione], int):
            roles_map[sezione] = [roles_map[sezione]]

        # sezione contiene già ID?
        if ruolo.id in roles_map[sezione]:
            return await itx.response.send_message(
                f"ℹ️ {ruolo.mention} è già nella sezione {SEZIONI.get(sezione, sezione)}.",
                ephemeral=True
            )

        roles_map[sezione].append(ruolo.id)
        save_roles(roles_map)

        await itx.response.send_message(
            f"✅ Ho aggiunto {ruolo.mention} nella sezione **{SEZIONI.get(sezione, sezione)}**.",
            ephemeral=True
        )

    # autocomplete per le sezioni
    @aggiungi_ruolo_sezione.autocomplete("sezione")
    async def autocomplete_sezione(self, itx: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=name, value=key)
            for key, name in SEZIONI.items()
            if current.lower() in name.lower()
        ][:25]

async def setup(bot: commands.Bot):
    await bot.add_cog(GestioneSezioni(bot))