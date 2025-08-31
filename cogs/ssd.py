# cogs/ssd.py
import discord
from discord.ext import commands
from discord import app_commands
from views.ssd_view import SSDView

# === CONFIG ===
RUOLO_CITTADINO_ID = 1408613574850379959  # @Cittadino di Venezia

class SSD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ssd",
        description="Annuncia la chiusura del server e la fine sessione RP."
    )
    @app_commands.checks.has_permissions(administrator=True)  # Solo admin/staff
    async def ssd(self, interaction: discord.Interaction):
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Usa questo comando in un server.", ephemeral=True)

        mention = f"<@&{RUOLO_CITTADINO_ID}> ⬇️"

        # Embed annuncio
        emb = discord.Embed(
            title="🔒 Fine sessione RP — Server in chiusura",
            description=(
                "Grazie per aver giocato su **VeneziaRP**!\n\n"
                "➡️ **Cosa fare adesso**:\n"
                "• Salva le ultime azioni RP e chiudi eventuali scene aperte\n"
                "• Riconsegna asset/veicoli se necessario\n"
                "• Se hai bisogno dello staff, usa il bottone **🆘**\n\n"
                "⏳ Il server verrà chiuso a breve. A domani!"
            ),
            color=discord.Color.dark_gold()
        )
        if interaction.guild.icon:
            emb.set_thumbnail(url=interaction.guild.icon.url)
        emb.set_footer(text="VeneziaRP • Chiusura sessione")

        await interaction.response.send_message(
            content=mention,
            embed=emb,
            view=SSDView(),
            ephemeral=False  # visibile a tutti
        )

async def setup(bot):
    await bot.add_cog(SSD(bot))