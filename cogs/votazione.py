import os
import json
import discord
from discord.ext import commands
from discord import app_commands
from views.votazione_view import VotazioneView

VOTI_ROLE_ID = 1408613579283890176   # 🟡・Attività Game
CITTADINI_ROLE_ID = 1408613574850379959
CANALE_VOTAZIONI_ID = 1408588715277680680
DATA_FILE = "data/votazione_data.json"


class Votazione(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _load_saved(self) -> dict:
        try:
            if not os.path.exists(DATA_FILE):
                return {}
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                txt = f.read().strip()
                return json.loads(txt) if txt else {}
        except Exception:
            return {}

    @app_commands.command(name="votazione", description="Apri una nuova votazione per l'SSU")
    @app_commands.checks.has_permissions(manage_guild=True)  # solo staff
    async def votazione(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        canale = guild.get_channel(CANALE_VOTAZIONI_ID)
        if not isinstance(canale, discord.TextChannel):
            return await interaction.followup.send("❌ Canale votazioni non trovato. Controlla l'ID.", ephemeral=True)

        # 1) Se esiste una votazione salvata e il messaggio è ancora presente, NON crearne una nuova
        saved = self._load_saved()
        if saved:
            try:
                if saved.get("canale_id") == canale.id:
                    old_msg = await canale.fetch_message(saved.get("messaggio_id"))
                    if old_msg:
                        return await interaction.followup.send(
                            f"ℹ️ Esiste già una votazione attiva: {old_msg.jump_url}",
                            ephemeral=True
                        )
            except discord.NotFound:
                # il messaggio non esiste più: procederemo creando una nuova votazione
                pass
            except Exception:
                pass

        # 2) Crea la View
        view = VotazioneView(interaction.user, self.bot)

        # 3) Embed iniziale
        embed = discord.Embed(
            title="📊 VOTAZIONE APERTA — VeneziaRP",
            description=(
                "📣 **Cari cittadini di Venezia!**\n"
                "È il momento di decidere: **vogliamo aprire il server per una nuova sessione RP?**\n\n"
                "✅ Se desideri giocare oggi, clicca sul pulsante **Vota** qui sotto!\n"
                "📌 Quando raggiungeremo **5 voti**, potremo **avviare ufficialmente l'SSU**.\n\n"
                "⏰ **Vota ora e preparati a vivere nuove storie nella nostra amata Venezia!**"
            ),
            color=discord.Color.blurple()
        )
        if guild and guild.icon:
            embed.set_footer(text=f"{guild.name} | Voto di apertura", icon_url=guild.icon.url)
        else:
            embed.set_footer(text=f"{guild.name} | Voto di apertura" if guild else "Voto di apertura")

        content = f"<@&{VOTI_ROLE_ID}> \n<@&{CITTADINI_ROLE_ID}>"

        # 4) Invia il messaggio con la view
        msg = await canale.send(content=content, embed=embed, view=view)

        # 5) Aggancia la view al messaggio
        await view.aggancia_messaggio(msg)

        # 🔧 6) Salva subito lo stato iniziale (così si crea data/votazione_data.json)
        await view.salva_dati()

        # 7) Registra la view come persistente
        try:
            self.bot.add_view(view)
        except Exception:
            pass

        await interaction.followup.send("✅ Votazione creata!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Votazione(bot))