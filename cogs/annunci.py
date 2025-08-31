from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from views.annuncio_select_view import AnnuncioSelectView

STAFF_ROLE_ID = 1408613549168918528  # <-- cambia con il tuo ruolo staff

def is_staff(member: discord.Member) -> bool:
    return any(r.id == STAFF_ROLE_ID for r in member.roles)

class Annunci(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="annuncio", description="Crea un annuncio scegliendo il tipo da un menù")
    async def annuncio(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or not is_staff(interaction.user):
            return await interaction.response.send_message("⛔ Solo lo staff può usare questo comando.", ephemeral=True)

        view = AnnuncioSelectView()
        await interaction.response.send_message("📢 **Scegli il tipo di annuncio da creare:**", view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Annunci(bot))